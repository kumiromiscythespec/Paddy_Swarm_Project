"""Generate preview-only STL meshes without CadQuery.

These meshes are for visual/dimensional review.  The manufacturing source remains
CadQuery and must be regenerated with build_all.py before printing.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import triangulate

import parameters as p

OUT = Path(__file__).resolve().parent / "exports" / "stl"


def circle_points(radius: float, n: int = 128, center=(0.0, 0.0)):
    cx, cy = center
    return [
        (cx + radius * math.cos(2 * math.pi * i / n), cy + radius * math.sin(2 * math.pi * i / n))
        for i in range(n)
    ]


def bolt_points(count: int, diameter: float, phase_deg: float = 22.5):
    r = diameter / 2.0
    return [
        (r * math.cos(math.radians(phase_deg + i * 360.0 / count)), r * math.sin(math.radians(phase_deg + i * 360.0 / count)))
        for i in range(count)
    ]


def extrude_polygon(poly: Polygon, height: float, z0: float = 0.0) -> trimesh.Trimesh:
    triangles = [t for t in triangulate(poly) if poly.covers(t)]
    vertices2d = {}
    coords = []

    def idx2(pt):
        key = (round(float(pt[0]), 8), round(float(pt[1]), 8))
        if key not in vertices2d:
            vertices2d[key] = len(coords)
            coords.append(key)
        return vertices2d[key]

    tri_indices = []
    for tri in triangles:
        pts = list(tri.exterior.coords)[:-1]
        if len(pts) != 3:
            continue
        tri_indices.append([idx2(pt) for pt in pts])

    rings = [poly.exterior, *poly.interiors]
    ring_indices = []
    for ring in rings:
        pts = list(ring.coords)
        ring_indices.append([idx2(pt) for pt in pts])

    n2 = len(coords)
    vertices = np.array([(x, y, z0) for x, y in coords] + [(x, y, z0 + height) for x, y in coords], dtype=float)
    faces = []
    for a, b, c in tri_indices:
        faces.append((c, b, a))
        faces.append((a + n2, b + n2, c + n2))

    for indices in ring_indices:
        for i in range(len(indices) - 1):
            a = indices[i]
            b = indices[i + 1]
            faces.append((a, b, b + n2))
            faces.append((a, b + n2, a + n2))

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.array(faces, dtype=np.int64), process=True)
    return mesh


def polygon_plate(outer, holes, height, z0=0.0):
    poly = Polygon(outer, holes=holes)
    return extrude_polygon(poly, height, z0)


def annular_plate(outer_r, inner_r, height, z0=0.0, holes=()):
    inner_loops = [circle_points(inner_r, 128)] if inner_r > 0 else []
    inner_loops.extend(holes)
    return polygon_plate(circle_points(outer_r, 192), inner_loops, height, z0)


def box(extents, center):
    mesh = trimesh.creation.box(extents=np.asarray(extents, dtype=float))
    mesh.apply_translation(np.asarray(center, dtype=float))
    return mesh


def cylinder(radius, height, center=(0, 0, 0), sections=96):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation((center[0], center[1], center[2] + height / 2.0))
    return mesh


def revolve_profile(profile, segments=192):
    # Profile is a closed loop of (radius, z) points.
    vertices = []
    index = {}
    for i, (r, z) in enumerate(profile):
        if abs(r) < 1e-9:
            index[(i, "axis")] = len(vertices)
            vertices.append((0.0, 0.0, z))
        else:
            for j in range(segments):
                a = 2.0 * math.pi * j / segments
                index[(i, j)] = len(vertices)
                vertices.append((r * math.cos(a), r * math.sin(a), z))

    faces = []
    n = len(profile)
    for i in range(n):
        k = (i + 1) % n
        ri = profile[i][0]
        rk = profile[k][0]
        for j in range(segments):
            j2 = (j + 1) % segments
            if abs(ri) < 1e-9 and abs(rk) < 1e-9:
                continue
            if abs(ri) < 1e-9:
                faces.append((index[(i, "axis")], index[(k, j)], index[(k, j2)]))
            elif abs(rk) < 1e-9:
                faces.append((index[(i, j)], index[(k, "axis")], index[(i, j2)]))
            else:
                faces.append((index[(i, j)], index[(k, j)], index[(k, j2)]))
                faces.append((index[(i, j)], index[(k, j2)], index[(i, j2)]))
    return trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces), process=True)


def voxel_boolean(add_meshes, subtract_meshes=(), pitch=0.7):
    """Fast preview merge.

    Preview STL files intentionally keep intersecting shells instead of running
    expensive booleans. Subtractive details are represented in the CadQuery
    manufacturing source and may be absent from these preview meshes.
    """
    result = trimesh.util.concatenate([m.copy() for m in add_meshes])
    result.process(validate=True)
    return result


def export(mesh, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{stem}.stl"
    mesh.export(path)
    return path


def tank_body():
    profile = [
        (0.0, 0.0),
        (p.TANK_OUTER_DIAMETER / 2.0, 0.0),
        (p.TANK_OUTER_DIAMETER / 2.0, p.TANK_BODY_HEIGHT),
        (p.TANK_INNER_DIAMETER / 2.0, p.TANK_BODY_HEIGHT),
        (p.TANK_INNER_DIAMETER / 2.0, p.TANK_BASE_THICKNESS),
        (0.0, p.TANK_BASE_THICKNESS),
    ]
    shell = revolve_profile(profile)
    holes = [circle_points(p.TANK_BOLT_HOLE_DIAMETER / 2, 32, c) for c in bolt_points(p.TANK_BOLT_COUNT, p.TANK_BOLT_CIRCLE)]
    flange = annular_plate(p.TANK_FLANGE_DIAMETER / 2, p.TANK_INNER_DIAMETER / 2, p.TANK_FLANGE_THICKNESS, p.TANK_BODY_HEIGHT, holes)
    ribs = []
    for i in range(p.TANK_VERTICAL_RIB_COUNT):
        a = math.radians(i * 360 / p.TANK_VERTICAL_RIB_COUNT)
        r = p.TANK_OUTER_DIAMETER / 2 + p.TANK_VERTICAL_RIB_DEPTH / 2
        rib = box((p.TANK_VERTICAL_RIB_DEPTH, p.TANK_VERTICAL_RIB_WIDTH, p.TANK_BODY_HEIGHT - 16), (r, 0, 8 + (p.TANK_BODY_HEIGHT - 16) / 2))
        T = trimesh.transformations.rotation_matrix(a, (0, 0, 1))
        rib.apply_transform(T)
        ribs.append(rib)
    pilot = cylinder(4.0, 1.2, (0, 0, -0.1))
    return voxel_boolean([shell, flange, *ribs], [pilot], pitch=0.7)


def tank_lid():
    holes = [circle_points(p.TANK_BOLT_HOLE_DIAMETER / 2, 28, c) for c in bolt_points(p.TANK_BOLT_COUNT, p.TANK_BOLT_CIRCLE)]
    holes += [
        circle_points(p.BULKHEAD_NOMINAL_HOLE / 2, 48, (p.BULKHEAD_OUTLET_X, 0)),
        circle_points(p.BULKHEAD_NOMINAL_HOLE / 2, 48, (p.BULKHEAD_INLET_X, 0)),
        circle_points(p.GAUGE_HOLE_DIAMETER / 2, 40, (p.GAUGE_PORT_X, 0)),
    ]
    plate = polygon_plate(circle_points(p.TANK_LID_DIAMETER / 2, 192), holes, p.TANK_LID_THICKNESS)
    bosses = []
    for x, d in [(p.BULKHEAD_OUTLET_X, p.BULKHEAD_NOMINAL_HOLE), (p.BULKHEAD_INLET_X, p.BULKHEAD_NOMINAL_HOLE), (p.GAUGE_PORT_X, p.GAUGE_HOLE_DIAMETER)]:
        bosses.append(annular_plate(d / 2 + 4, d / 2, 5, p.TANK_LID_THICKNESS))
        bosses[-1].apply_translation((x, 0, 0))
    ribs = []
    for i in range(8):
        rib = box((38, 3, 5), (22, 0, p.TANK_LID_THICKNESS + 2.5))
        rib.apply_transform(trimesh.transformations.rotation_matrix(math.radians(i * 45), (0, 0, 1)))
        ribs.append(rib)
    return voxel_boolean([plate, *bosses, *ribs], pitch=0.55)


def baffle():
    plate = box((p.BAFFLE_WIDTH, p.BAFFLE_THICKNESS, p.BAFFLE_HEIGHT), (0, 0, p.BAFFLE_HEIGHT / 2))
    foot1 = box((p.BAFFLE_FOOT_LENGTH, p.BAFFLE_FOOT_WIDTH, p.BAFFLE_THICKNESS), (-p.BAFFLE_WIDTH / 2 + p.BAFFLE_FOOT_LENGTH / 2, 0, p.BAFFLE_THICKNESS / 2))
    foot2 = foot1.copy(); foot2.apply_translation((p.BAFFLE_WIDTH - p.BAFFLE_FOOT_LENGTH, 0, 0))
    return voxel_boolean([plate, foot1, foot2], pitch=0.45)


def tank_stand():
    outer = [(-p.STAND_SIZE/2, -p.STAND_SIZE/2), (p.STAND_SIZE/2, -p.STAND_SIZE/2), (p.STAND_SIZE/2, p.STAND_SIZE/2), (-p.STAND_SIZE/2, p.STAND_SIZE/2)]
    holes = [circle_points(p.STAND_DRAIN_CLEARANCE_DIAMETER/2, 64)]
    holes += [circle_points(p.STAND_MOUNT_HOLE_DIAMETER/2, 24, (sx*p.STAND_MOUNT_OFFSET, sy*p.STAND_MOUNT_OFFSET)) for sx in (-1,1) for sy in (-1,1)]
    plate = polygon_plate(outer, holes, p.STAND_BASE_THICKNESS)
    cradle = annular_plate(p.STAND_CRADLE_OUTER_DIAMETER/2, p.STAND_CRADLE_INNER_DIAMETER/2, p.STAND_CRADLE_HEIGHT, p.STAND_BASE_THICKNESS)
    return voxel_boolean([plate, cradle], pitch=0.65)


def sight_guard():
    # Single-shell U channel for preview; mounting tabs remain in CadQuery source.
    section=[(-13,-1.5),(13,-1.5),(13,16.5),(10,16.5),(10,1.5),(-10,1.5),(-10,16.5),(-13,16.5)]
    return polygon_plate(section, [], 170.0)


def dip_tube():
    tube = annular_plate(p.DIP_TUBE_OUTER_DIAMETER/2, p.DIP_TUBE_INNER_DIAMETER/2, p.DIP_TUBE_LENGTH)
    cutters=[]
    for i in range(4):
        cut=box((6,20,14),(p.DIP_TUBE_OUTER_DIAMETER/2,0,7))
        cut.apply_transform(trimesh.transformations.rotation_matrix(math.radians(i*90),(0,0,1)))
        cutters.append(cut)
    return voxel_boolean([tube], cutters, pitch=0.35)


def bellows():
    z0=p.BELLOWS_FLANGE_THICKNESS; z1=p.BELLOWS_FREE_HEIGHT-p.BELLOWS_FLANGE_THICKNESS
    samples=p.BELLOWS_CONVOLUTION_COUNT*16+1
    outer=[]; inner=[]
    mean=(p.BELLOWS_MAX_DIAMETER+p.BELLOWS_MIN_DIAMETER)/4
    amp=(p.BELLOWS_MAX_DIAMETER-p.BELLOWS_MIN_DIAMETER)/4
    minr=p.BELLOWS_MIN_DIAMETER/2; maxr=p.BELLOWS_MAX_DIAMETER/2
    for i in range(samples):
        z=z0+(z1-z0)*i/(samples-1)
        phase=i/(samples-1)
        r=mean+amp*math.sin(2*math.pi*p.BELLOWS_CONVOLUTION_COUNT*phase)
        wall=p.BELLOWS_WALL+(p.BELLOWS_ROOT_WALL-p.BELLOWS_WALL)*(1-(r-minr)/(maxr-minr))
        outer.append((r,z)); inner.append((r-wall,z))
    profile=[(minr-2,z0),*outer,(minr-2,z1),*reversed(inner)]
    shell=revolve_profile(profile,256)
    hole_loops=[circle_points(p.BELLOWS_BOLT_HOLE_DIAMETER/2,24,c) for c in bolt_points(p.BELLOWS_BOLT_COUNT,p.BELLOWS_BOLT_CIRCLE)]
    low=annular_plate(p.BELLOWS_FLANGE_DIAMETER/2,minr-2,p.BELLOWS_FLANGE_THICKNESS,0,hole_loops)
    high=annular_plate(p.BELLOWS_FLANGE_DIAMETER/2,minr-2,p.BELLOWS_FLANGE_THICKNESS,z1,hole_loops)
    return voxel_boolean([shell,low,high],pitch=0.8)


def square_plate(size, thick, hole_specs):
    outer=[(-size/2,-size/2),(size/2,-size/2),(size/2,size/2),(-size/2,size/2)]
    holes=[circle_points(d/2,28,c) for c,d in hole_specs]
    return polygon_plate(outer,holes,thick)


def fixed_base():
    specs=[(c,p.BELLOWS_BOLT_HOLE_DIAMETER) for c in bolt_points(p.BELLOWS_BOLT_COUNT,p.BELLOWS_BOLT_CIRCLE)]
    specs += [(c,p.GUIDE_HOLE_DIAMETER) for c in bolt_points(p.GUIDE_ROD_COUNT,p.GUIDE_ROD_CIRCLE,90)]
    specs += [((-p.AIR_PORT_X,0),p.AIR_PORT_HOLE_DIAMETER),((p.AIR_PORT_X,0),p.AIR_PORT_HOLE_DIAMETER)]
    specs += [((sx*(p.BASE_SIZE/2-12),sy*(p.BASE_SIZE/2-12)),6.5) for sx in (-1,1) for sy in (-1,1)]
    return square_plate(p.BASE_SIZE,p.BASE_THICKNESS,specs)


def foot_plate():
    specs=[(c,p.BELLOWS_BOLT_HOLE_DIAMETER) for c in bolt_points(p.BELLOWS_BOLT_COUNT,p.BELLOWS_BOLT_CIRCLE)]
    specs += [(c,p.GUIDE_HOLE_DIAMETER+2) for c in bolt_points(p.GUIDE_ROD_COUNT,p.GUIDE_ROD_CIRCLE,90)]
    # Preview omits underside ribs to keep one closed shell; ribs remain in CadQuery source.
    return square_plate(p.FOOT_PLATE_SIZE,p.FOOT_PLATE_THICKNESS,specs)


def clamp_ring():
    holes=[circle_points(p.BELLOWS_BOLT_HOLE_DIAMETER/2,24,c) for c in bolt_points(p.BELLOWS_BOLT_COUNT,p.BELLOWS_BOLT_CIRCLE)]
    return annular_plate(p.CLAMP_RING_OUTER_DIAMETER/2,p.CLAMP_RING_INNER_DIAMETER/2,p.CLAMP_RING_THICKNESS,holes=holes)


def guide_bushing():
    profile=[(p.GUIDE_HOLE_DIAMETER/2,0),(p.GUIDE_BUSHING_OUTER_DIAMETER/2,0),(p.GUIDE_BUSHING_OUTER_DIAMETER/2,p.GUIDE_BUSHING_LENGTH),(p.GUIDE_BUSHING_FLANGE_DIAMETER/2,p.GUIDE_BUSHING_LENGTH),(p.GUIDE_BUSHING_FLANGE_DIAMETER/2,p.GUIDE_BUSHING_LENGTH+p.GUIDE_BUSHING_FLANGE_THICKNESS),(p.GUIDE_HOLE_DIAMETER/2,p.GUIDE_BUSHING_LENGTH+p.GUIDE_BUSHING_FLANGE_THICKNESS)]
    return revolve_profile(profile,128)


def spring_anchor():
    body=box((28,18,18),(0,0,9))
    vert=cylinder(2.75,20,(0,0,-1))
    horiz=cylinder(3.25,24,(0,0,0),64); horiz.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,(1,0,0))); horiz.apply_translation((0,0,11))
    return voxel_boolean([body],[vert,horiz],pitch=0.4)


def stroke_stop():
    collar=annular_plate(10,(p.GUIDE_ROD_DIAMETER+0.7)/2,12)
    slit=box((5,12,14),(8,0,6))
    hole=cylinder(2.1,24,(0,0,0),64); hole.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,(1,0,0))); hole.apply_translation((6.5,0,6))
    return voxel_boolean([collar],[slit,hole],pitch=0.35)


def foot_pad():
    base=box((p.FOOT_PAD_LENGTH,p.FOOT_PAD_WIDTH,p.FOOT_PAD_THICKNESS),(0,0,p.FOOT_PAD_THICKNESS/2))
    ribs=[box((6,86,1.5),(x,0,p.FOOT_PAD_THICKNESS+0.75)) for x in range(-60,61,20)]
    return voxel_boolean([base,*ribs],pitch=0.5)


def hose_support():
    base=box((42,30,6),(0,0,3))
    # Preview uses a half-ring saddle approximated by a full ring and front opening.
    ring=annular_plate((p.HOSE_OUTER_DIAMETER+6)/2,(p.HOSE_OUTER_DIAMETER+1)/2,18)
    ring.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,(1,0,0))); ring.apply_translation((0,-9,10))
    cutter=box((50,30,30),(0,0,33))
    holes=[cylinder(2.25,7,(-15,0,-0.5)),cylinder(2.25,7,(15,0,-0.5))]
    return voxel_boolean([base,ring],[cutter,*holes],pitch=0.45)


def check_valve_bracket():
    inner=p.CHECK_VALVE_OUTER_DIAMETER+p.CHECK_VALVE_BRACKET_CLEARANCE; outer=inner+8
    ring=annular_plate(outer/2,inner/2,16)
    split=box((5,outer,18),(outer/2-2,0,8))
    tab1=box((16,8,16),(outer/2+5,7,8)); tab2=box((16,8,16),(outer/2+5,-7,8))
    hole=cylinder(2.1,outer+28,(0,0,0),64); hole.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,(1,0,0))); hole.apply_translation((outer/2+5,0,8))
    return voxel_boolean([ring,tab1,tab2],[split,hole],pitch=0.4)


def bulkhead_coupon():
    outer=[(-60,-21),(60,-21),(60,21),(-60,21)]
    holes=[circle_points(d/2,48,(x,0)) for x,d in zip((-45,-15,15,45),(21.6,21.8,22.0,22.2))]
    return polygon_plate(outer,holes,5)


def gasket_coupon():
    holes=[circle_points(2.25,24,c) for c in [(34,0),(-34,0),(0,34),(0,-34)]]
    base=annular_plate(42,30,6,holes=holes)
    ring1=annular_plate(40,36.5,0.8,6); ring2=annular_plate(34.5,31,1.1,6)
    return voxel_boolean([base,ring1,ring2],pitch=0.45)


def mini_bellows(wall,x):
    outer=[]; inner=[]; samples=49
    for i in range(samples):
        z=3+39*i/(samples-1); r=14+2*math.sin(2*math.pi*3*i/(samples-1)); outer.append((r,z)); inner.append((r-wall,z))
    profile=[(10,0),(19,0),(19,3),*outer,(19,42),(19,45),(10,45),(10,42),*reversed(inner),(10,3)]
    m=revolve_profile(profile,128); m.apply_translation((x,0,0)); return m


def bellows_wall_coupon():
    return trimesh.util.concatenate([mini_bellows(1.4,-45),mini_bellows(1.6,0),mini_bellows(1.8,45)])


def main():
    parts={
        "PVSP-WT-001_tank_body":tank_body,
        "PVSP-WT-002_tank_lid":tank_lid,
        "PVSP-WT-003_baffle":baffle,
        "PVSP-WT-004_tank_stand":tank_stand,
        "PVSP-WT-005_sight_tube_guard":sight_guard,
        "PVSP-WT-006_dip_tube":dip_tube,
        "PVSP-BL-001_bellows_tpu":bellows,
        "PVSP-BL-002_fixed_base":fixed_base,
        "PVSP-BL-003_foot_plate":foot_plate,
        "PVSP-BL-004_clamp_ring":clamp_ring,
        "PVSP-BL-006_guide_bushing":guide_bushing,
        "PVSP-BL-007_spring_anchor":spring_anchor,
        "PVSP-BL-008_stroke_stop":stroke_stop,
        "PVSP-BL-009_foot_pad_tpu":foot_pad,
        "PVSP-AD-001_hose_support":hose_support,
        "PVSP-AD-002_check_valve_bracket":check_valve_bracket,
        "PVSP-CAL-001_bulkhead_hole_coupon":bulkhead_coupon,
        "PVSP-CAL-002_gasket_compression_coupon":gasket_coupon,
        "PVSP-CAL-003_bellows_wall_coupon":bellows_wall_coupon,
    }
    for stem,fn in parts.items():
        mesh=fn(); path=export(mesh,stem)
        print(f"{stem}: watertight={mesh.is_watertight} bounds={np.round(mesh.extents,1).tolist()} -> {path}")

if __name__=="__main__":
    main()
