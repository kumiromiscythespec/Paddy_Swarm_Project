"""G065 full-box promotion. Read-only parents; exclusive, new-lane output.

Local top-interface fixes are explicit: remove four groove roofs and restore
the lid seal land below the chimney. Chimney geometry at/above lid Z8 is frozen.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import tempfile
import zipfile
from datetime import datetime

import cadquery as cq
from cadquery import importers, exporters

ROOT = Path(r'D:\Paddy_Swarm_Project')
LANE = Path(__file__).resolve().parent
REL = LANE.relative_to(ROOT).as_posix()
BRANCH = 'agent/organize-untracked-cad-assets-20260725'
HEAD = '7c149a65053f2292bc4cc0ed06d8941c96852f2b'
DUMMY = ROOT/'cad/common_rover/bbox/bbox_compact_seal_b_water_dummy_v001'
spec = importlib.util.spec_from_file_location('protected_g065_dummy', DUMMY/'build_water_dummy.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
p = d.parent
PARENT = d.PARENT
RIM, STOP, DEPTH, TOL = 113.5, 114.395, 0.65, 1e-6
STATUS = '/'.join(['COMPACT_SEAL_G065_WATER_PHYSICAL_PASS','LOCAL_BBOX_V004_CAD_PASS',
    'CONTRACT_TEST_PASS','FULL_BODY_PRINT_READY','FULL_LID_PRINT_READY',
    'FULL_BBOX_WATERPROOF_PHYSICAL_PENDING','GLOBAL_VEHICLE_INTEGRATION_PHYSICAL_PENDING'])
DOCS = ['README.md','COMPACT_FIELD_BBOX_V004_G065_DESIGN_AUTHORITY.md',
    'G065_WATER_PHYSICAL_RESULT_PROMOTION.md','V003_G050_SUPERSESSION_RECORD.md',
    'SEAL_GEOMETRY_TRACEABILITY.md','BUILDER_GROOVE_DEPTH_REGRESSION.md',
    'BATTERY_CLEARANCE_AUDIT.md','PRINT_INSTRUCTIONS.md','FULL_BBOX_WATER_TEST_PLAN.md',
    'BATTERY_FIT_AND_RESTRAINT_TEST_PLAN.md','GLOBAL_INTEGRATION_HOLDS.md']
STEP_NAMES = ['compact_field_bbox_v004_g065_body','compact_field_bbox_v004_g065_lid',
    'compact_field_bbox_v004_g065_assembly','goldenmate_battery_reference','battery_removal_sweep',
    'battery_terminal_keepout','g065_seal_section_reference','water_dummy_g065_seal_reference',
    'v003_g050_seal_reference','main_cable_reference','chimney_reference','tpu_runners',
    'strap_and_anchor_reservation_reference']
STEPS = ['artifacts/'+s+'.step' for s in STEP_NAMES]
STLS = ['artifacts/'+s+'.stl' for s in [STEP_NAMES[0],STEP_NAMES[1],'tpu_runners']]
SVGS = ['previews/'+s+'.svg' for s in ['v004_top','v004_side','v004_front',
    'g065_full_box_seal_section','g050_vs_g065_section','battery_lid_clearance',
    'chimney_clearance','battery_removal']]
REPORTS = ['design_parameters.json','validation_report.json','contract_test_report.json',
    'repository_audit.json','geometry_delta_audit.json','physical_result.json','manifest.json']
EXPECTED = sorted(['build_bbox_v004_g065.py','tests/test_bbox_v004_g065.py','audit_start.json',
    'COMMIT_PATHS.txt','SHA256SUMS.txt',*DOCS,*STEPS,*STLS,*SVGS,*REPORTS])
sha, git, volume, common, delta, bbox, distance = d.sha, d.git, d.volume, d.common, d.delta, d.bbox, d.distance
box = p.box


def audit(full=False):
    baseline=json.loads((LANE/'audit_start.json').read_text())
    paths=sorted(s for s in git('ls-files','--others','--exclude-standard','-z').split('\0') if s and not s.startswith(REL+'/'))
    dirty={s:sha(ROOT/s) for s in git('diff','--name-only').splitlines()}
    protected={s:p.tree_hash(ROOT/s) for s in baseline['protected']}
    state={'repository':str(Path(git('rev-parse','--show-toplevel')).resolve()),
        'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),
        'staged_count':len(git('diff','--cached','--name-only').splitlines()),'dirty':dirty,
        'tracked_dirty_count':len(dirty),'outside_untracked_count':len(paths),'protected':protected,
        'outside_untracked_paths_sha256':hashlib.sha256('\n'.join(paths).encode()).hexdigest()}
    ok=(Path(state['repository'])==ROOT and state['branch']==BRANCH and state['head']==HEAD
        and state['staged_count']==0 and dirty==baseline['dirty'] and protected==baseline['protected']
        and len(paths)==baseline['untracked_count'] and state['outside_untracked_paths_sha256']==baseline['untracked_paths_sha256'])
    if full:
        h=hashlib.sha256()
        for s in paths:h.update((s+'\n').encode());h.update(bytes.fromhex(sha(ROOT/s)))
        state['outside_untracked_bytes_sha256']=h.hexdigest()
        ok &= h.hexdigest()==baseline['untracked_bytes_sha256']
    files=sorted(f.relative_to(LANE).as_posix() for f in LANE.rglob('*') if f.is_file())
    own=sorted(s[len(REL)+1:] for s in git('ls-files','--others','--exclude-standard','-z').split('\0') if s.startswith(REL+'/'))
    ok &= set(files).issubset(EXPECTED) and files==own
    state.update(new_path_count=len(files),untracked_total=len(paths)+len(own),
        protected_source_changed_count=sum(protected[s]!=baseline['protected'][s] for s in protected),pass_result=bool(ok))
    if not ok:raise AssertionError('FAIL_CLOSED repository '+json.dumps(state))
    return state


def ring(height,z):
    return p.rounded_ring(160,74,155.8,69.8,6,3.9,height,z)


@lru_cache(maxsize=None)
def body(depth=DEPTH):
    if depth < .5:raise ValueError('Immutable G050 base cannot generate a shallower groove')
    # Exact bottom anchor; overshoot is ONLY ABOVE, including former M4 roofs.
    return d.source_body().cut(ring(depth+p.HARDSTOP_GAP+.1,RIM-depth)).clean()


def seal_land_bridge():
    # Fill only the lid-thickness part of the chimney aperture lying OUTSIDE
    # the unchanged 155 x 69 battery opening. No change above lid Z8.
    move=(*p.CHIMNEY_POSITIONS[p.CHIMNEY_SELECTED],0)
    aperture=p.v002_chimney.cavity_tool().translate(move)
    lid_band=box(180,96,8,(0,0,4)).cut(box(155,69,10,(0,0,4)))
    return aperture.intersect(lid_band)


@lru_cache(maxsize=None)
def lid():return d.source_lid().union(seal_land_bridge()).clean()


def closure_lid():return lid().translate((0,0,STOP))


def chimney():return d.source_lid().intersect(box(220,220,60,(0,0,38)))


def centerline(z):return p.rounded_box_xy(157.9,71.9,.1,4.95,z-.1).faces('>Z').val().outerWire()


def gasket(depth=DEPTH):
    wire=centerline(RIM-depth+.9)
    profile=cq.Wire.makeCircle(.9,wire.positionAt(0),wire.tangentAt(0))
    return cq.Workplane(obj=cq.Solid.sweep(profile,[],wire,True,False))


def measure_depth(shape):
    rim=d.probe_surface_z(shape,20,38.5,RIM-3,RIM+.3)
    floor=d.probe_surface_z(shape,20,35.95,RIM-3,RIM+.3)
    fs=[f for f in d.planar_faces(shape) if abs(f.BoundingBox().xlen-160)<TOL and abs(f.BoundingBox().ylen-74)<TOL]
    if len(fs)!=1 or len(fs[0].Wires())!=2:raise AssertionError('not one continuous annular groove floor')
    if abs(fs[0].Center().z-floor)>TOL:raise AssertionError('independent face/probe mismatch')
    return {'rim_z_mm':rim,'floor_z_mm':floor,'actual_depth_mm':rim-floor,
        'floor_area_mm2':fs[0].Area(),'floor_wires':len(fs[0].Wires())}


def assert_depth(shape,requested):
    m=measure_depth(shape)
    if abs(m['actual_depth_mm']-requested)>TOL:raise AssertionError(f"actual {m['actual_depth_mm']} != requested {requested}")
    return m


def seal_section(b,l):
    mask=box(4,15,6,(20,36,113.5))
    return p.compound([b.intersect(mask),l.intersect(mask)])


def reference_dummy_section():
    b=importers.importStep(str(DUMMY/'artifacts/water_dummy_g065_body.step')).translate((20,8,85))
    l=importers.importStep(str(DUMMY/'artifacts/water_dummy_common_lid.step')).translate((20,8,STOP))
    return seal_section(b,l)


@lru_cache(maxsize=1)
def model():
    parts=[body(),lid(),p.compound([body(),closure_lid(),p.battery_reference(),p.tpu_pads(),p.strap_reference(),
        p.main_cable_reference(True),gasket()]),p.battery_reference(),p.removal_sweep(),p.terminal_keepout(),
        seal_section(body(),closure_lid()),reference_dummy_section(),
        seal_section(d.source_body(),d.source_lid().translate((0,0,STOP))),
        p.main_cable_reference(),chimney(),p.tpu_pads().translate((0,0,-p.FLOOR)),p.support_reference()]
    return dict(zip(STEPS,parts))


def metrics():
    b,l=body(),lid();g=gasket();battery=p.battery_reference()
    holes=p.compound([p.cyl_z(4.5,15,(x,y,105)) for x,y in p.M4_POINTS])
    towers=p.compound([p.cyl_z(12,8.895,(x,y,105.5)) for x,y in p.M4_POINTS])
    allowed=ring(2,RIM-1)
    upper=box(220,220,60,(0,0,38))
    old_naive=d.source_body().cut(ring(.85,RIM-.65))
    land=ring(.5,0)
    section=seal_section(b,closure_lid());ref=reference_dummy_section()
    corners=[]; full_corner_regions=[]
    db=importers.importStep(str(DUMMY/'artifacts/water_dummy_g065_body.step'))
    dl=importers.importStep(str(DUMMY/'artifacts/water_dummy_common_lid.step'))
    for sx in (-1,1):
        for sy in (-1,1):
            mask=box(22,22,6,(sx*79,sy*39,113.5))
            a=p.compound([b.intersect(mask),closure_lid().intersect(mask)])
            r=p.compound([db.translate((sx*50,sy*8,85)).intersect(mask),dl.translate((sx*50,sy*8,STOP)).intersect(mask)])
            full_corner_regions.append(delta(a,r))
            seal_wall=p.rounded_ring(170,86,155,69,8,4,6,110.5)
            corners.append(delta(a.intersect(seal_wall),r.intersect(seal_wall)))
    return {'requested_depth_mm':DEPTH,'actual_step_geometry':assert_depth(b,DEPTH),
        'source_g050':assert_depth(d.source_body(),.5),'source_g065':d.assert_depth(db,.65),
        'internal_mm':[155,69,110],'body_bounds_mm':bbox(b),'lid_bounds_mm':bbox(l),'tpu_bounds_mm':bbox(model()[STEPS[11]]),
        'wall_mm':3.5,'floor_mm':3.5,'groove_width_mm':2.1,'cord_diameter_mm':1.8,'hard_stop_mm':STOP-RIM,
        'radii_mm':{'outer':6,'inner':3.9,'centerline':4.95},'gasket_length_mm':centerline(0).Length(),
        'nominal_compression_mm':1.8-DEPTH-(STOP-RIM),'nominal_compression_percent':100*(1.8-DEPTH-(STOP-RIM))/1.8,
        'battery':p.BATTERY,'battery_clearance_total_xy_mm':[4.1,3.5],'terminal_to_rim_mm':9.6,
        'terminal_to_lid_mm':distance(p.battery_reference().solids('>X'),closure_lid()),
        'battery_to_chimney_mm':distance(battery,chimney().translate((0,0,STOP))),
        'battery_to_m4_tower_mm':distance(battery,towers),'battery_to_body_mm3':common(battery,b),
        'battery_to_lid_mm3':common(battery,closure_lid()),'battery_to_chimney_mm3':common(battery,chimney().translate((0,0,STOP))),
        'battery_to_m4_tower_mm3':common(battery,towers),'removal_fixed_body_mm3':common(p.removal_sweep(),b),
        'rigid_closure_mm3':common(b,closure_lid()),'m4_to_gasket_mm3':common(holes,g),
        'm4_hole_to_gasket_min_mm':distance(holes,g),'gasket_to_body_mm3':common(g,b),
        'lid_missing_seal_land_mm3':volume(land.cut(l)),
        'parent_lid_missing_seal_land_mm3':volume(land.cut(d.source_lid())),
        'parent_naive_g065_gasket_overlap_mm3':common(old_naive,g),
        'body_removed_volume_mm3':volume(d.source_body().cut(b)),
        'body_added_volume_mm3':volume(b.cut(d.source_body())),
        'body_outside_groove_difference_mm3':delta(b.cut(allowed),d.source_body().cut(allowed)),
        'lid_added_volume_mm3':volume(l.cut(d.source_lid())),
        'lid_removed_volume_mm3':volume(d.source_lid().cut(l)),
        'lid_outside_local_bridge_difference_mm3':delta(l.cut(seal_land_bridge()),d.source_lid().cut(seal_land_bridge())),
        'chimney_above_lid_difference_mm3':delta(l.intersect(upper),d.source_lid().intersect(upper)),
        'seal_straight_section_difference_mm3':delta(section,ref),'seal_corner_differences_mm3':corners,
        'full_corner_region_difference_mm3':full_corner_regions,
        'full_corner_region_difference_reason':'Chimney mouth inside the seal; chimney presence is an allowed difference. Seal-wall region is independently zero-diff.',
        'lid_bridge_bounds_mm':bbox(seal_land_bridge()),'lower_chimney_opening_before_mm':[42,37],
        'lower_chimney_opening_after_mm':[42,27.5],
        'body_valid':b.val().isValid(),'lid_valid':l.val().isValid(),
        'm4_count':len(p.M4_POINTS),'m4_centers_mm':p.M4_POINTS,
        'local_interface_adjustment':'LID_Z0_TO_8_ONLY; GASKET_LAND_RESTORED; GROOVE_ROOFS_REMOVED',
        'vertical_removal_condition':'LID_REMOVED_AND_STRAP_RELEASED',
        'chimney_pg9_mm':15.2,'chimney_local_wall_mm':2.4}


def ascii_triangles(path):
    vertices=[tuple(map(float,line.split()[1:])) for line in path.read_text().splitlines() if line.lstrip().startswith('vertex ')]
    if len(vertices)%3:raise AssertionError('STL vertex count')
    return [tuple(vertices[i:i+3]) for i in range(0,len(vertices),3)]


def export_stl(shape,path):
    # ASCII double-precision vertices avoid binary STL float32 Z quantization
    # at Z112.85, which would exceed the requested 1e-6 depth tolerance.
    vertices,faces=shape.val().tessellate(.02,.08)
    lines=['solid V004_G065']
    for face in faces:
        a,b,c=[vertices[i] for i in face]
        n=(b-a).cross(c-a).normalized()
        lines.append('  facet normal '+' '.join(f'{v:.12g}' for v in n.toTuple()))
        lines.append('    outer loop')
        for v in (a,b,c):lines.append('      vertex '+' '.join(f'{q:.9f}' for q in v.toTuple()))
        lines.extend(['    endloop','  endfacet'])
    lines.append('endsolid V004_G065')
    path.write_text('\n'.join(lines)+'\n',encoding='ascii',newline='\n')


def stl_quality(path):
    triangles=[tuple(tuple(round(x,7) for x in v) for v in t) for t in ascii_triangles(path)]
    edges=Counter();winding=Counter();neighbors=defaultdict(list);degenerate=0
    for tri in triangles:
        a,b,c=tri;u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        degenerate+=int(len(set(tri))<3 or sum(x*x for x in cross)<1e-16)
        for x,y in ((a,b),(b,c),(c,a)):
            k=tuple(sorted((x,y)));edges[k]+=1;winding[k]+=1 if (x,y)==k else -1
        for i,x in enumerate(tri):neighbors[x].append((tri[(i+1)%3],tri[(i+2)%3]))
    bad_vertices=0
    for pairs in neighbors.values():
        graph=defaultdict(set)
        for a,b in pairs:graph[a].add(b);graph[b].add(a)
        stack=[next(iter(graph))];seen=set()
        while stack:
            v=stack.pop()
            if v in seen:continue
            seen.add(v);stack.extend(graph[v]-seen)
        bad_vertices+=int(len(seen)!=len(graph) or any(len(s)!=2 for s in graph.values()))
    r={'triangles':len(triangles),'bad_edges':sum(n!=2 for n in edges.values()),
        'bad_winding_edges':sum(n!=0 for n in winding.values()),'bad_vertex_links':bad_vertices,
        'degenerate_triangles':degenerate,'duplicate_triangles':len(triangles)-len({tuple(sorted(t)) for t in triangles})}
    r['watertight']=r['bad_edges']==0;r['manifold']=r['watertight'] and bad_vertices==0
    r['pass']=all(r[k]==0 for k in ('bad_edges','bad_winding_edges','bad_vertex_links','degenerate_triangles','duplicate_triangles'))
    return r


def stl_surface(triangles,x,y):
    zs=[]
    for a,b,c in triangles:
        if max(a[2],b[2],c[2])-min(a[2],b[2],c[2])>1e-7:continue
        z=a[2]
        if not RIM-3<z<RIM+.3:continue
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-12:continue
        u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        if min(u,v,1-u-v)>=-1e-8:zs.append(z)
    if not zs:raise AssertionError('no STL surface at probe')
    return max(zs)


def stl_depth(path):
    triangles=ascii_triangles(path)
    rim=stl_surface(triangles,20,38.5);floor=stl_surface(triangles,20,35.95)
    return {'rim_z_mm':rim,'floor_z_mm':floor,'actual_depth_mm':rim-floor,'encoding':'ASCII_9_DECIMAL_VERTEX'}


def regression():
    results=[]
    with tempfile.TemporaryDirectory(prefix='paddy_v004_depth_') as tmp:
        for depth in (.5,.55,.65):
            path=Path(tmp)/f'probe_{depth}.step';d.export_step(body(depth),path)
            measured=assert_depth(importers.importStep(str(path)),depth)
            stl=path.with_suffix('.stl');export_stl(body(depth),stl);sm=stl_depth(stl)
            if abs(sm['actual_depth_mm']-depth)>TOL:raise AssertionError('STL depth regression')
            bad=Path(tmp)/f'negative_{depth}.step';d.export_step(body(depth+.10),bad)
            rejected=False
            try:assert_depth(importers.importStep(str(bad)),depth)
            except AssertionError:rejected=True
            if not rejected:raise AssertionError('+0.10 error accepted')
            results.append({'requested_mm':depth,'step_actual_mm':measured['actual_depth_mm'],
                'stl_actual_mm':sm['actual_depth_mm'],'plus_010_negative_rejected':rejected})
    return results


def generate_cad(out):
    (out/'artifacts').mkdir(parents=True,exist_ok=True);(out/'previews').mkdir(exist_ok=True)
    for f,sh in model().items():
        if not sh.val().isValid():raise AssertionError('invalid '+f)
        d.export_step(sh,out/f)
    for f in STLS:export_stl(model()[f.replace('.stl','.step')],out/f)
    for f,text in previews().items():(out/f).write_text(text,encoding='utf-8',newline='\n')


def inspect(out):
    report={'step':{},'stl':{}}
    for f in STEPS:
        sh=importers.importStep(str(out/f))
        r={'valid':sh.val().isValid(),'solids':len(sh.solids().vals()),'bounds_mm':bbox(sh)}
        if f in STEPS[:2]:r['self_interference']=d.self_interference(sh)
        if not r['valid'] or r.get('self_interference',{}).get('faulty'):raise AssertionError('STEP invalid '+f)
        report['step'][f]=r
    report['step_depth']=assert_depth(importers.importStep(str(out/STEPS[0])),DEPTH)
    report['stl_depth']=stl_depth(out/STLS[0])
    if abs(report['stl_depth']['actual_depth_mm']-DEPTH)>TOL:raise AssertionError('STL depth mismatch')
    for f in STLS:
        report['stl'][f]=stl_quality(out/f)
        if not report['stl'][f]['pass']:raise AssertionError('STL invalid '+f+' '+json.dumps(report['stl'][f]))
    return report


def reproduce():
    with tempfile.TemporaryDirectory(prefix='paddy_v004_repro_') as tmp:
        out=Path(tmp);body.cache_clear();lid.cache_clear();model.cache_clear()
        generate_cad(out);inspect(out)
        result={f:sha(LANE/f)==sha(out/f) for f in [*STEPS,*STLS,*SVGS]}
    if not all(result.values()):raise AssertionError('byte reproducibility '+json.dumps(result))
    return {'count':len(result),'pass_count':sum(result.values()),'byte_identical':result,
        'step_metadata':'Canonical FILE_NAME, generic PRODUCT and NAUO labels only; no geometry rewriting'}


def physical_result():
    return {'source':'USER_PHYSICAL_RESULT_IN_V004_TASK','specimen':'WATER_DUMMY_G065',
        'groove_actual_mm':.65,'groove_width_mm':2.1,'cord_mm':1.8,'hard_stop_mm':.895,
        'upright_60_min':'PASS','front_tilt_gt10_deg':'PASS','rear_tilt_gt10_deg':'PASS',
        'left_tilt_gt10_deg':'PASS','right_tilt_gt10_deg':'PASS','witness':'COMPLETELY_DRY',
        'leak':'NONE','gasket_movement':'NONE','petg_damage':'NONE',
        'witness_paper_tear':'TEST_ARTIFACT_NOT_WATER_INGRESS','paper_tear_cause':'ADHESIVE_HANDLING',
        'classification':'COMPACT_SEAL_G065_WATER_PHYSICAL_PASS',
        'full_v004_waterproof':'PHYSICAL_PENDING','chimney_gland_full_box_waterproof':'PHYSICAL_PENDING'}


def parameters(m):
    return {'status':STATUS,'requested_depth_mm':DEPTH,'cad_tolerance_mm':TOL,'battery':p.BATTERY,
        'internal_mm':[155,69,110],'wall_mm':3.5,'floor_mm':3.5,'tpu_mm':1,'strap_width_mm':20,
        'physical_history':{'A':{'documented':.45,'actual':.55,'dry':'PASS','water':'NOT_TESTED'},
            'B':{'documented':.55,'actual':.65,'dry':'PASS','water':'PASS_VIA_G065_DUMMY'},
            'V003':{'actual':.5,'status':'SUPERSEDED_UNVALIDATED_SEAL_GEOMETRY'}},
        'source_lanes':[str(PARENT),str(DUMMY)],'metrics':m,
        'local_top_adjustments':['G065 bottom +0.15 depth from G050; remove mid-boss groove roofs',
            'Restore lid seal land Z0..8; lower chimney mouth 42x37 -> 42x27.5; upper chimney unchanged'],
        'slicer':'HOLD_SLICER_NOT_RUN','full_water':'PHYSICAL_PENDING','global_integration':'PHYSICAL_PENDING'}


def write_json(path,data):d.write_json(path,data)


def build():
    audit();generate_cad(LANE)
    m=metrics();quality=inspect(LANE);reg=regression();repro=reproduce()
    write_json(LANE/'design_parameters.json',parameters(m))
    write_json(LANE/'physical_result.json',physical_result())
    write_json(LANE/'geometry_delta_audit.json',{k:v for k,v in m.items() if any(s in k for s in ('difference','removed_volume','added_volume','parent_','bridge','lower_chimney'))})
    write_json(LANE/'validation_report.json',{'status':'GEOMETRY_GENERATED_CONTRACT_PENDING','geometry':m,
        'quality':quality,'depth_regression':reg,'reproducibility':repro})
    for name,text in documents(m).items():(LANE/name).write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'generated':True,'metrics':m,'reproducibility':repro,'regression':reg},indent=2))


def finalize(report):
    if not report['pass']:raise AssertionError('tests failed')
    write_json(LANE/'contract_test_report.json',report)
    validation=json.loads((LANE/'validation_report.json').read_text());validation['status']=STATUS
    write_json(LANE/'validation_report.json',validation)
    (LANE/'COMMIT_PATHS.txt').write_text('\n'.join(REL+'/'+f for f in EXPECTED)+'\n',encoding='utf-8',newline='\n')
    # Complete indexes after all content; avoid self-referential SHA claims.
    write_json(LANE/'manifest.json',{'lane':REL,'exact_count':len(EXPECTED),'paths':EXPECTED,
        'rebuild':'python -B build_bbox_v004_g065.py --build; python -B tests/test_bbox_v004_g065.py; python -B build_bbox_v004_g065.py --verify',
        'requires_read_only_parents':[str(PARENT),str(DUMMY)],'status':STATUS})
    for name in ('repository_audit.json','SHA256SUMS.txt'):
        if not (LANE/name).exists():(LANE/name).write_text('',encoding='ascii')
    write_json(LANE/'repository_audit.json',audit(full=True))
    (LANE/'SHA256SUMS.txt').write_text(''.join(f'{sha(LANE/f)}  {f}\n' for f in EXPECTED if f!='SHA256SUMS.txt'),encoding='ascii',newline='\n')


def verify():
    state=audit(full=True)
    actual=sorted(f.relative_to(LANE).as_posix() for f in LANE.rglob('*') if f.is_file())
    if actual!=EXPECTED:raise AssertionError('exact path mismatch')
    for line in (LANE/'SHA256SUMS.txt').read_text().splitlines():
        digest,name=line.split('  ',1)
        if sha(LANE/name)!=digest:raise AssertionError('SHA mismatch '+name)
    if not json.loads((LANE/'contract_test_report.json').read_text())['pass']:raise AssertionError('contract not PASS')
    quality=inspect(LANE);repro=reproduce()
    print(json.dumps({'verify':'PASS','repository':state,'quality':quality,'reproducibility':repro},indent=2))


def handoff():
    verify()
    target=Path(r'D:\Downloads')/('Paddy_Swarm_COMPACT_FIELD_BBOX_V004_G065_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in EXPECTED:z.write(LANE/f,LANE.name+'/'+f)
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None:raise AssertionError('ZIP CRC')
        if sorted(z.namelist())!=sorted(LANE.name+'/'+f for f in EXPECTED):raise AssertionError('ZIP manifest')
        for f in EXPECTED:
            if hashlib.sha256(z.read(LANE.name+'/'+f)).hexdigest()!=sha(LANE/f):raise AssertionError('ZIP bytes')
    print(json.dumps({'zip':str(target),'sha256':sha(target),'members':len(EXPECTED)}))


# Generated documentation and actual-CAD SVG preview functions follow.


def previews():
    def panel(sh,x,y,w,h,projection):
        # OCCT's default X-view up vector is -Y. Rotate DISPLAY geometry only
        # so the original physical Z is vertical in section/front previews.
        if projection==(1,0,0):sh=sh.rotate((0,0,0),(1,0,0),90)
        source=exporters.getSVG(sh.val(),opts={'width':w,'height':h,'projectionDir':projection,
            'showHidden':False,'strokeWidth':max(bbox(sh))/800,'marginLeft':20,'marginTop':20})
        return source[source.index('<svg'):].replace('<svg',f'<svg x="{x}" y="{y}"',1)
    def page(title,subtitle,panels,notes):
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="820" viewBox="0 0 1200 820">'
        svg+='<rect width="1200" height="820" fill="#f8fafc"/><style>text{font-family:Arial,sans-serif;fill:#152e47;font-size:18px}</style>'
        svg+=f'<text x="30" y="40" style="font-size:27px">{title}</text><text x="30" y="75">{subtitle}</text>'
        svg+=''.join(panels)
        for i,line in enumerate(notes):svg+=f'<text x="30" y="{650+i*29}">{line}</text>'
        return svg+'<text x="30" y="800" font-size="14">Actual BRep outlines | mm | G065 dummy water PASS; full V004 box water test PENDING</text></svg>'
    m=model();section=m[STEPS[6]];old=m[STEPS[8]]
    cut=box(220,1,200,(0,0,90));assembled=p.compound([body(),closure_lid(),p.battery_reference()])
    sealed_side=assembled.intersect(cut)
    chimney_cut=box(1,180,190,(-50,0,95))
    new_cl=closure_lid().intersect(chimney_cut)
    old_cl=d.source_lid().translate((0,0,STOP)).intersect(chimney_cut)
    data=[
        page('V004 G065 — body and lid top views','M4 x8 unchanged. Full continuous gasket receiver restored.',
            [panel(body(),20,105,560,510,(0,0,1)),panel(lid(),620,105,560,510,(0,0,1))],
            ['Body overall 180 x96 x114.395; cavity 155 x69 x110.','Lid overall 180 x104 x58, including chimney / hood.','Groove 2.1 wide x0.650000 deep. Cord 1.8. Hard-stop 0.895.']),
        page('V004 — side section Y=0','Body, lid and battery shown as separate rigid references.',
            [panel(sealed_side,20,105,1150,510,(0,-1,0))],
            ['Battery body 150.9 x65.5 x92.5; terminal-inclusive height 99.4.','TPU bottom runners 1.0. Terminal-to-rim 9.6; terminal-to-lid 10.495.','G050 to G065 depth delta +0.150000, not the historical +0.10 builder bug.']),
        page('V004 — front view along X','Upper chimney and all vehicle-independent package dimensions preserved.',
            [panel(assembled,20,100,1150,515,(1,0,0))],
            ['Internal Y69; battery Y65.5; total lateral clearance 3.5.','M4 through-bolts / washers / nuts outside seal.','No new wall or floor penetration.']),
        page('Water-passed G065 seal — actual section','Left: translated water dummy. Right: V004 full box.',
            [panel(m[STEPS[7]],20,120,560,490,(1,0,0)),panel(section,620,120,560,490,(1,0,0))],
            ['Section Boolean symmetric difference = 0 mm3.','Groove width 2.1, depth 0.65; hard-stop 0.895; cord OD1.8.','Nominal compression reference 0.255 mm /14.17%, not a rubber deformation simulation.']),
        page('V003 G050 vs V004 G065','Left: unvalidated actual G050. Right: promoted actual G065.',
            [panel(old,20,120,560,490,(1,0,0)),panel(section,620,120,560,490,(1,0,0))],
            ['Old floor Z113.000000; new floor Z112.850000; unchanged rim Z113.500000.','Actual groove depth +0.150000. All parents remain read-only.','Four mid-boss groove roofs removed to avoid nominal-cord interference.']),
        page('Battery / lid clearance','Actual Y=0 section; terminal is at the +X end.',
            [panel(sealed_side,20,105,1150,510,(0,-1,0))],
            ['Terminal top Z103.9; rim Z113.5; lid underside Z114.395.','Terminal / lid 10.495 mm. Battery / body / lid intersections = 0.','20 mm strap is independent from lid; anchor and strap physical fit remain pending.']),
        page('Chimney seal-land closure — X=-50 section','Left: V003 interruption. Right: local lid-thickness sealing bridge.',
            [panel(old_cl,20,110,560,500,(1,0,0)),panel(new_cl,620,110,560,500,(1,0,0))],
            ['Bridge 42 x9.5 x8 mm; added material 3192 mm3, entirely within lid Z0..8.','Lower opening 42 x37 ->42 x27.5. Chimney at Z8 and above: zero-diff.','PG9 hole 15.2 and local wall 2.4 unchanged. Gland water performance still pending.']),
        page('Vertical battery removal','Lid removed and strap released. Sweep is a reference, not a printed part.',
            [panel(p.compound([body(),p.removal_sweep()]),20,105,1150,510,(1,-1,1))],
            ['Battery vertical sweep / fixed body intersection = 0 mm3.','TPU pads reused exactly, translated to Z0 only for printing.','Secure the 1.2 kg battery before dry tilt; no battery during initial water tests.'])]
    return dict(zip(SVGS,data))


def documents(m):
    water='''# Full V004 empty-box water test

The G065 dummy passed; this full box, its chimney, layer structure and gland have NOT passed yet.

1. Inspect the printed PETG body and lid for cracks, porosity, warp and seal-plane defects.
2. Measure groove depth at accessible straight checkpoints: target actual 0.65 mm; verify width 2.1 mm.
3. Install the 1.8 mm cord with its joint on a straight section. Do not stretch it to conceal poor seating.
4. Place completely dry witness paper inside; keep paper and cables out of the seal.
5. Fit metal M4 through-bolts, washers and nuts; tighten evenly to hard-stop. Do not force warped parts.
6. Inspect the entire gasket for extrusion and correct seating.
7. Use an EMPTY or inert box only: NO battery, powered electronics or live cable.
8. Test 60 minutes upright, then front/rear/left/right tilts each greater than 10 degrees; record duration and water level for each tilt.
9. Include the chimney/gland area with a safe unpowered specimen of the actual cable and gland. A plugged hole alone does not qualify the actual gland.
10. Wipe the outside completely dry before opening; inspect witness, gasket and PETG.

Only actual V004 upright + all four tilts + actual chimney/gland condition + completely dry witness + no gasket displacement + no PETG damage may promote COMPACT_FIELD_BBOX_V004_WATER_PHYSICAL_PASS.
Record any adhesive-handling tear separately; do not confuse it with wetting or dismiss genuine wetting.
Until then FULL_BBOX_WATERPROOF = PHYSICAL_PENDING. No field or powered-water approval.
'''
    physical='''# G065 physical water result promotion

Source: user's V004 task; specimen WATER_DUMMY_G065, not the full V004 box.
Actual groove width 2.1 mm; actual depth 0.650000 mm; cord diameter 1.8 mm; hard-stop 0.895 mm.

- 60 min upright: PASS.
- Front, rear, left and right tilt >10 degrees: PASS for every direction.
- Witness: COMPLETELY_DRY; leak: NONE.
- Gasket movement: NONE; PETG damage: NONE.
- Witness-paper tear: TEST_ARTIFACT_NOT_WATER_INGRESS; caused by adhesive handling after disassembly.

Classification: COMPACT_SEAL_G065_WATER_PHYSICAL_PASS.
This promotes the tested seal cross-section / closed perimeter only. Full-box and chimney/gland water performance remain PHYSICAL_PENDING.
'''
    trace=f'''# Exact G065 seal traceability

Read-only measured authority: `{DUMMY}`. Generated G065 STEP measures {m['source_g065']['actual_depth_mm']:.9f} mm, not an old parameter label.
V004 has width 2.1, actual depth 0.65, hard-stop 0.895, cord OD1.8, outer R6.0, inner R3.9 and centerline R4.95.
Nominal cord compression reference is 0.255 mm (14.166667%); this is not a prediction of rubber deformation.
Full centerline perimeter {m['gasket_length_mm']:.6f} mm, versus dummy 219.101767 mm. Trim the physical cord/joint to fit; do not use a stretched cord as a dimensional workaround.

Actual translated straight section symmetric difference: {m['seal_straight_section_difference_mm3']} mm3.
Four actual corner seal-wall symmetric differences: {m['seal_corner_differences_mm3']} mm3.
The broader left/front corner comparison includes {m['full_corner_region_difference_mm3'][1]:.6f} mm3 of allowed chimney-mouth difference INSIDE the seal; this is separately reported and excluded only from the seal-wall comparison.
Allowed differences are perimeter length, body size, eight rather than four external M4 compression stations, and chimney presence.

M4 architecture remains external vertical through-bolts, flat lid and 0.895 hard-stop. Hole-to-cord minimum is {m['m4_hole_to_gasket_min_mm']:.6f} mm, and intersection is zero. This is smaller than the corner-only dummy distance; full-box clamping uniformity must be physically checked.

Two necessary local top-interface corrections (task section 6) are NOT hidden:

1. Extend the groove cutter upward beyond hard-stop to remove four obsolete mid-boss roofs. The naive depth-only body intersects nominal cord by {m['parent_naive_g065_gasket_overlap_mm3']:.6f} mm3. New intersection is zero. The groove bottom alone moves down 0.15 mm.
2. Restore a 42 x9.5 x8 mm lid-thickness bridge outside the 155 x69 battery opening. V003 was missing 42 x2.1 mm of lid seal land beneath its chimney opening. V004 has zero missing seal land. The lower chimney mouth changes from 42 x37 to 42 x27.5 mm; the chimney ABOVE the 8 mm lid, PG9 hole, 2.4 wall, recess and counterbore are exactly unchanged.

The new lid contains {m['lid_added_volume_mm3']:.6f} mm3 additional material and no removed material. Body removed volume {m['body_removed_volume_mm3']:.6f} mm3; no added body material; zero body delta outside groove envelope. These are local seal corrections, not a battery/upper-chimney redesign.
'''
    clear=f'''# Battery clearance audit

GoldenMate: 150.9 x65.5 plan; body height 92.5; terminal-inclusive height 99.4; mass 1.2 kg. The 99.4 dimension is NEVER a plan width.
Cavity 155 x69 x110; wall/floor 3.5 PETG. TPU 1.0 beneath battery; battery datum bottom Z4.5.

- X total clearance 4.1 mm (2.05 per side).
- Y total clearance 3.5 mm (1.75 per side).
- Terminal-to-rim 9.6 mm.
- Actual terminal-to-lid minimum {m['terminal_to_lid_mm']:.6f} mm.
- Actual battery-to-upper-chimney BRep distance {m['battery_to_chimney_mm']:.6f} mm.
- Actual battery-to-M4-tower BRep distance {m['battery_to_m4_tower_mm']:.6f} mm.

For comparison, conservative plan-only tower estimate is 2.55 mm and terminal-height-to-chimney-base estimate is 18.495 mm; those old scalar estimates are not the actual 3D minima for this asymmetric battery. Do not mislabel the updated distance calculations as a geometry movement.
Battery/body, battery/lid, battery/chimney and battery/M4 intersections: zero. Fixed-body vertical removal sweep intersection: zero with lid REMOVED and strap RELEASED.
No lid battery loading. The strap/anchors remain reservation geometry, not qualified load-carrying hardware. Secure physical restraint before dry tilt.
'''
    printing='''# Print instructions

Printer envelope: Bambu A1 256 x256 x256 mm. Material: PETG body/lid; removable runners TPU.

First full-box print set after CAD/contracts PASS:

1. `artifacts/compact_field_bbox_v004_g065_body.stl`
2. `artifacts/compact_field_bbox_v004_g065_lid.stl`
3. `artifacts/tpu_runners.stl` later for dry battery fitting (two independent 30 x55 x1 runners).

Body 180 x96 x114.395: floor down, open side up. Exterior flange and tower undersides may need build-plate-only supports. Block supports from groove, inside sealing surfaces and battery cavity. No groove support.
Lid 180 x104 x58: flat seal face at Z0 on a clean flat build plate, chimney upright. This avoids printing the large lid suspended on its chimney. Inspect plate texture, flatness and first-layer artifacts on the sealing face; do not release a distorted seal surface. Support hood/outer details only if required; do not leave trapped support in the chimney. The lower opening is 42 x27.5 mm after the sealing bridge correction; check access and support removal in slicer.
TPU combined layout 126 x55 x1: pads flat at Z0; no permanent bond required.

STL uses ASCII 9-decimal vertices to preserve actual groove depth to 1e-6 mm at CAD scale. This precision is not a claim of printer accuracy.
Slicer NOT RUN: HOLD_SLICER_NOT_RUN / PROCESS_PENDING. Confirm walls, bridge/hood support and watertight extrusion paths in Bambu Studio before starting. CAD print-ready is not a physical or field qualification.
Never overtighten M4 to flatten warped PETG. Metal washers/nuts; select actual bolt stack from printed hardware, not a fictitious fastener measurement.
'''
    fit='''# Dry battery fit and restraint sequence

Perform empty-box water testing FIRST. Ensure the box is completely dry before introducing the battery.

1. Insert the real GoldenMate, verify X/Y fit and terminal clearance.
2. Verify vertical insertion/removal without catching the seal or chimney; remove lid and release strap.
3. Test removable 1.0 mm TPU runners for fit and creep: TPU_PHYSICAL_FIT_PENDING.
4. Fit the 20 mm independent strap; no shell penetration and no battery load into the lid.
5. Verify actual strap anchoring, buckle and handling; STRAP_PHYSICAL_FIT_PENDING. Reference anchor zones are not installed anchors.
6. Only with confirmed independent restraint, tilt the dry box manually and ensure the 1.2 kg battery cannot become free mass.

Do not combine the battery with initial water qualification. Load, vibration, long-term creep and integrated-vehicle operation remain later physical tests.
'''
    global_hold='''# Global integration holds

GLOBAL_VEHICLE_INTEGRATION_PHYSICAL_PENDING.
Absolute BBOX X/Y transform and Front Interface physical installation are unresolved. No invented global transform is exported.
These do not block a locally validated full-box print. All CAD here uses the local floor-underside Z0 frame.
Local print-ready is separate from full-box waterproof pending, battery/TPU/strap fit pending and global vehicle integration pending.
No field qualification, powered-water approval, cutting, drilling or external hardware installation is authorized by this CAD package.
'''
    supersession='''# V003 G050 supersession

Read-only V003 actual full-body STEP groove depth is 0.500000 mm; it has NOT been physically water tested.
V003_FULL_BODY_G050 = SUPERSEDED_UNVALIDATED_SEAL_GEOMETRY. Existing artifacts remain intact.

History:

- Coupon A: documented 0.45, actual 0.55, dry mechanical PASS, water NOT TESTED.
- Coupon B: documented 0.55, actual 0.65, dry mechanical PASS; G065 closed dummy water PASS.
- V003 selected full body: actual 0.50, unvalidated.
- V004: actual 0.65, inherited G065 seal authority; full-box water test still PENDING.

V003 -> V004 full-body depth change is +0.150000 mm. The historical coupon builder +0.10 mm error is a DIFFERENT fact.
'''
    regression_doc='''# Actual geometry depth regression

The cutter is bottom-anchored at rim - requested depth; overshoot is above the rim only.
Requests 0.50, 0.55 and 0.65 each generate an actual STEP and ASCII STL and measure their geometry, not parameter labels.
STEP uses two independent solid probes at rim (20,38.5) and groove (20,35.95), plus one planar annular floor face with two boundary wires.
STL uses point-in-triangle surface queries at the same XY locations, not a BRep assumption.
Tolerance 1e-6 mm; expected V004 rim Z113.5, bottom Z112.85, depth0.65.
For every request, an additional STEP with +0.10 actual depth must be REJECTED by the requested-depth validator.
The full V004 actual depth is also checked after STEP reload and STL export.
ASCII STL avoids float32 quantization at Z112.85. Tessellation chordal error is separate from planar depth measurement.
'''
    authority=f'''# Compact Field BBOX V004 G065 design authority

{STATUS}

Release labels apply only with contract_test_report.json PASS and successful builder --verify.
{physical}
{supersession}
{trace}
{clear}

Battery packaging, upper chimney, output references and parent lanes are protected. Local print release does not release full-box waterproofing or global integration.
'''
    readme=f'''# Compact Field BBOX V004 — G065 full-body/lid print candidate

{STATUS}

Source package: `{PARENT}`. Water-tested seal: `{DUMMY}`. Both read-only.
Torque/drivetrain and unrelated lanes are out of scope. No Git stage/commit/branch changes.

Actual G050 -> G065 depth +0.150000 mm. **Not only a depth edit:** the V003 lid opening broke 42 mm of seal land, and four mid-boss roofs contacted the nominal cord. V004 restores the local lid-thickness sealing bridge and removes only groove roofs. Lower chimney opening changes to 42 x27.5; chimney above Z8, PG9/recess/2.4 wall are unchanged. See SEAL_GEOMETRY_TRACEABILITY.md before printing.

Body 180 x96 x114.395; lid 180 x104 x58; cavity155 x69 x110; all fit A1. First print body and lid, then empty-box water test, then fully dry battery fit/TPU/strap test.
Full-box water and chimney/gland performance are PHYSICAL_PENDING. The user's successful water test was the G065 closed dummy only.

Run from this lane with Python3.12/CadQuery2.8 and -B:

```
python -B build_bbox_v004_g065.py --build
python -B tests/test_bbox_v004_g065.py
python -B build_bbox_v004_g065.py --verify
python -B build_bbox_v004_g065.py --zip
```

The builder depends on protected parent source in the repository; ZIP is an audited new-lane handoff, not a bundled copy of all historical authorities. Do not stage from COMMIT_PATHS without separate user authorization.
STL material/quality checks and depth precision do not establish slicer success. HOLD_SLICER_NOT_RUN.
Strap reference is reservation-only; actual anchoring must be proven before restraining the 1.2kg battery.
'''
    return dict(zip(DOCS,[readme,authority,physical,supersession,trace,regression_doc,clear,printing,water,fit,global_hold]))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');ap.add_argument('--verify',action='store_true');ap.add_argument('--zip',action='store_true')
    args=ap.parse_args()
    if args.build:build()
    elif args.verify:verify()
    elif args.zip:handoff()
    else:ap.error('choose --build, --verify or --zip')
