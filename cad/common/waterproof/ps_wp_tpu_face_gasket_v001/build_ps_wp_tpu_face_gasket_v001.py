"""PS-WP common TPU face gasket: standalone new geometry, no BBOX mutations.

XY local interface; +X FRONT, +Y LEFT, floor underside Z0. Flat seal datum
Z28.5. Replaceable stops alone set the closed gap. All physical gates pending.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime

import cadquery as cq
from cadquery import exporters, importers
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer

ROOT=Path(r'D:\Paddy_Swarm_Project')
LANE=Path(__file__).resolve().parent
REL=LANE.relative_to(ROOT).as_posix()
BRANCH='agent/organize-untracked-cad-assets-20260725'
HEAD='7c149a65053f2292bc4cc0ed06d8941c96852f2b'
TOL=1e-6
GASKETS={'G20':2.0,'G25':2.5,'G30':3.0}
STOPS={'S16':1.6,'S18':1.8,'S20':2.0,'S22':2.2,'S24':2.4}
WIDTH,LAND_WIDTH=5.0,10.0
CENTER_PLAN,CENTER_R=58.0,6.5
INNER,FLOOR,WALL,DEPTH,LID_T=48.0,3.5,3.5,25.0,6.0
RIM=FLOOR+DEPTH
M4=[(-34.,-34.),(-34.,34.),(34.,-34.),(34.,34.)]
LOCATORS=[(-34.,-34.),(34.,34.)]
EAR_T,STOP_OD,HOLE_D,LOCATOR_D=.8,8.,4.5,8.6
POSITION_ALLOWANCE=.8  # 0.25 body/bolt +0.25 stop/bolt +0.30 ear/stop; nominal only
STATUS='/'.join(['CAD_PASS','CONTRACT_TEST_PASS','PS_WP_TPU_FACE_GASKET_DUMMY_PRINT_READY',
    'G25_S20_PRIMARY_TEST_READY','WATER_PHYSICAL_TEST_PENDING','BBOX_V005_PENDING','CBOX_FIELD_BOX_PENDING'])
DOCS=['README.md','PS_WP_TPU_FACE_GASKET_V001_DESIGN_AUTHORITY.md','ROUND_CORD_FAILURE_CONTEXT.md',
    'TPU_GASKET_VARIANT_MATRIX.md','HARD_STOP_COMPRESSION_MATRIX.md','TPU_PRINT_MEASUREMENT_PLAN.md',
    'DRY_TEST_PLAN.md','WATER_TEST_PLAN.md','PHYSICAL_RESULT_SHEET.md','FUTURE_BBOX_CBOX_INTEGRATION.md']
PARTS=[f'ps_wp_tpu_gasket_{g.lower()}' for g in GASKETS]+[f'stop_{s.lower()}' for s in STOPS]+[
    'ps_wp_water_dummy_body','ps_wp_water_dummy_lid','ps_wp_tpu_thickness_calibration_coupon']
REFERENCES=['ps_wp_water_dummy_assembly_g25_s20','ps_wp_gasket_reference','ps_wp_witness_zone_reference']
STEPS=['artifacts/'+s+'.step' for s in PARTS+REFERENCES]
STLS=['artifacts/'+s+'.stl' for s in PARTS]
SVGS=['previews/'+s+'.svg' for s in ['assembly_top','assembly_section','tpu_face_gasket_section',
    'locating_tab_layout','hard_stop_system','g20_g25_g30_comparison','s16_s18_s20_s22_s24_comparison','witness_zone_layout']]
REPORTS=['design_parameters.json','validation_report.json','contract_test_report.json','repository_audit.json',
    'material_authority_audit.json','physical_measurement_template.json','manifest.json']
EXPECTED=sorted([Path(__file__).name,'tests/test_ps_wp_tpu_face_gasket_v001.py','audit_start.json',
    'COMMIT_PATHS.txt','SHA256SUMS.txt',*DOCS,*STEPS,*STLS,*SVGS,*REPORTS])


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.PIPE).decode('utf-8').strip()


def tree_hash(path):
    files=sorted(p for p in path.rglob('*') if p.is_file())
    h=hashlib.sha256()
    for p in files:h.update((p.relative_to(path).as_posix()+'\n').encode());h.update(bytes.fromhex(sha(p)))
    return {'files':len(files),'sha256':h.hexdigest()}


def audit(full=False):
    baseline=json.loads((LANE/'audit_start.json').read_text(encoding='utf-8'))
    untracked=sorted(p for p in git('ls-files','--others','--exclude-standard','-z').split('\0') if p)
    paths=[p for p in untracked if not p.startswith(REL+'/')]
    own=[p[len(REL)+1:] for p in untracked if p.startswith(REL+'/')]
    dirty={p:sha(ROOT/p) for p in git('diff','--name-only').splitlines()}
    protected={p:tree_hash(ROOT/p) for p in baseline['protected']}
    state={'repository':str(Path(git('rev-parse','--show-toplevel')).resolve()),'branch':git('branch','--show-current'),
        'head':git('rev-parse','HEAD'),'staged_count':len(git('diff','--cached','--name-only').splitlines()),
        'dirty':dirty,'tracked_dirty_count':len(dirty),'outside_untracked_count':len(paths),
        'outside_untracked_paths_sha256':hashlib.sha256('\n'.join(paths).encode()).hexdigest(),'protected':protected,
        'untracked_total':len(untracked),'new_path_count':len(own)}
    ok=(Path(state['repository'])==ROOT and state['branch']==BRANCH and state['head']==HEAD and state['staged_count']==0
        and dirty==baseline['dirty'] and protected==baseline['protected'] and len(paths)==baseline['untracked_count']
        and state['outside_untracked_paths_sha256']==baseline['untracked_paths_sha256'])
    if full:
        h=hashlib.sha256()
        for p in paths:h.update((p+'\n').encode());h.update(bytes.fromhex(sha(ROOT/p)))
        state['outside_untracked_bytes_sha256']=h.hexdigest()
        ok &= h.hexdigest()==baseline['untracked_bytes_sha256']
    files=sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob('*') if p.is_file())
    ok &= set(files).issubset(EXPECTED) and files==own
    state['protected_source_changed_count']=sum(protected[p]!=baseline['protected'][p] for p in protected)
    state['pass']=bool(ok)
    if not ok:raise AssertionError('FAIL_CLOSED repository audit '+json.dumps(state))
    return state


def box(x,y,h,center=(0,0,0)):return cq.Workplane('XY').box(x,y,h).translate(center)
def cyl(d,h,xy=(0,0),z=0):return cq.Workplane('XY').circle(d/2).extrude(h).translate((*xy,z))


def rounded(plan,r,h,z=0):
    return cq.Workplane('XY').box(plan,plan,h,centered=(True,True,False)).edges('|Z').fillet(r).translate((0,0,z))


def ring(width,h,z=0):
    return rounded(CENTER_PLAN+width,CENTER_R+width/2,h,z).cut(
        rounded(CENTER_PLAN-width,CENTER_R-width/2,h+.2,z-.1)).clean()


def capsule(a,b,diameter,h,z=0):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    bridge=box(length,diameter,h,(0,0,z+h/2)).rotate((0,0,0),(0,0,1),math.degrees(math.atan2(dy,dx)))
    bridge=bridge.translate(((a[0]+b[0])/2,(a[1]+b[1])/2,0))
    return bridge.union(cyl(diameter,h,a,z)).union(cyl(diameter,h,b,z)).clean()


def compound(parts):return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))
def volume(s):return sum(v.Volume() for v in s.solids().vals())
def common(a,b):return volume(a.intersect(b))
def delta(a,b):return volume(a.cut(b))+volume(b.cut(a))


def bounds(s):
    b=Bnd_Box();BRepBndLib.AddOptimal_s(s.val().wrapped,b,False,False)
    return b.Get()


def bbox(s):
    b=bounds(s);return [round(b[i+3]-b[i],9) for i in range(3)]


def distance(a,b):
    q=BRepExtrema_DistShapeShape(a.val().wrapped,b.val().wrapped);q.Perform()
    if not q.IsDone():raise AssertionError('distance failed')
    return q.Value()


def self_interference(s):
    q=BOPAlgo_ArgumentAnalyzer();q.SetShape1(s.val().wrapped);q.SelfInterMode=True;q.Perform()
    if q.HasErrors():raise AssertionError('self-interference computation failed')
    return {'faulty':q.HasFaulty(),'count':q.GetCheckResult().Extent()}


def locator_hole(xy,slotted=False,h=5,z=-1):
    if not slotted:return cyl(LOCATOR_D,h,xy,z)
    u=1/math.sqrt(2)
    return capsule((xy[0]-u,xy[1]-u),(xy[0]+u,xy[1]+u),LOCATOR_D,h,z)


def locator_ear(xy,slotted=False):
    sx,sy=(1 if q>0 else -1 for q in xy)
    root=(sx*(22.5+CENTER_R/math.sqrt(2)),sy*(22.5+CENTER_R/math.sqrt(2)))
    bridge=capsule(root,xy,5,EAR_T)
    if slotted:
        u=1/math.sqrt(2);eye=capsule((xy[0]-u,xy[1]-u),(xy[0]+u,xy[1]+u),13,EAR_T)
    else:eye=cyl(13,EAR_T,xy)
    return bridge.union(eye).cut(locator_hole(xy,slotted)).clean()


@lru_cache(maxsize=None)
def gasket(thickness,locating='TWO_POINT'):
    sh=ring(WIDTH,thickness)
    for i,xy in enumerate(LOCATORS if locating=='TWO_POINT' else M4):
        sh=sh.union(locator_ear(xy,locating=='TWO_POINT' and i==1))
    return sh.clean()


@lru_cache(maxsize=1)
def body():
    # 3.5 wall below; 45-degree outward flare carries the broad top seal land.
    lower=rounded(55,5,21)
    w0=rounded(55,5,.1,20.9).faces('>Z').val().outerWire()
    w1=rounded(68,11.5,.1,RIM-1.1).faces('>Z').val().outerWire()
    flare=cq.Workplane('XY').add(w0).add(w1).toPending().loft(ruled=True)
    sh=lower.union(flare).union(rounded(68,11.5,1,RIM-1))
    for x,y in M4:
        a=(26 if x>0 else -26,26 if y>0 else -26)
        sh=sh.union(capsule(a,(x,y),10,8,RIM-8)).union(cyl(12,8,(x,y),RIM-8))
        sh=sh.cut(cyl(HOLE_D,10,(x,y),RIM-9))
    return sh.cut(rounded(INNER,1.5,DEPTH+2,FLOOR)).clean()


@lru_cache(maxsize=1)
def lid():
    sh=rounded(80,6,LID_T)
    for xy in M4:sh=sh.cut(cyl(HOLE_D,LID_T+2,xy,-1))
    return sh.clean()


def stop(h,xy=(0,0),z=0):return cyl(STOP_OD,h,xy,z).cut(cyl(HOLE_D,h+.2,xy,z-.1)).clean()
def stop_set(h):return compound([stop(h,(x,y)) for x in (-7,7) for y in (-7,7)])
def installed_stops(h):return compound([stop(h,xy,RIM) for xy in M4])


def calibration():return compound([box(14,14,t,(x,0,t/2)) for x,t in zip((-20,0,20),GASKETS.values())])


WITNESS={'FRONT':(18,0,8,12),'REAR':(-18,0,8,12),'LEFT':(0,18,12,8),'RIGHT':(0,-18,12,8),
    'CORNER1':(16,16,12,12),'CORNER2':(-16,16,12,12),'CORNER3':(-16,-16,12,12),'CORNER4':(16,-16,12,12)}


def witness():return compound([box(w,h,.2,(x,y,FLOOR+.2)) for x,y,w,h in WITNESS.values()])


def assembly(g=2.5,s=2.0):
    # FREE-THICKNESS gasket: overlap with lid is intended nominal compression,
    # not a rigid collision and not a rubber deformation prediction.
    return compound([body(),lid().translate((0,0,RIM+s)),gasket(g).translate((0,0,RIM)),installed_stops(s),witness()])


@lru_cache(maxsize=1)
def model():
    sh=[gasket(t) for t in GASKETS.values()]+[stop_set(h) for h in STOPS.values()]+[body(),lid(),calibration(),
        assembly(),gasket(2.5),witness()]
    return dict(zip(STEPS,sh))


def measure_thickness(shape,requested=None,solids=None):
    hs=[bbox(cq.Workplane(obj=s))[2] for s in shape.solids().vals()]
    if solids is not None and len(hs)!=solids:raise AssertionError('wrong solid count')
    if requested is not None and any(abs(h-requested)>TOL for h in hs):raise AssertionError(f'generated thickness {hs} != requested {requested}')
    return hs


def measure_seal(shape,requested):
    # Isolate the straight active band, not the thinner locating ears.
    probe=shape.intersect(box(.1,15,5,(0,29,2)))
    b=bounds(probe);width=b[4]-b[1];thickness=b[5]-b[2]
    if abs(width-WIDTH)>TOL or abs(thickness-requested)>TOL:raise AssertionError('actual seal section mismatch')
    return {'width_mm':width,'thickness_mm':thickness,'bottom_z_mm':b[2],'top_z_mm':b[5]}


def dry_volume(gap):
    # A topological closure surrogate only; does not prove printed waterproofing.
    closed=body().union(lid().translate((0,0,RIM+gap))).union(ring(WIDTH,gap,RIM)).clean()
    air=box(100,100,60,(0,0,25)).cut(closed)
    inside=[s for s in air.solids().vals() if s.isInside(cq.Vector(0,0,5),TOL)]
    if len(inside)!=1 or len(air.solids().vals())!=2:raise AssertionError('unclosed pressure boundary')
    return inside[0].Volume()/1000


def compression_matrix():
    rows=[]
    primary_pairs={('G20','S16'),('G25','S18'),('G25','S20'),('G25','S22'),('G30','S24')}
    for g,t in GASKETS.items():
        for s,h in STOPS.items():
            c=1-h/t
            expanded=WIDTH*t/h
            margin=(LAND_WIDTH-expanded)/2-POSITION_ALLOWANCE
            rows.append({'gasket':g,'stop':s,'nominal_ratio':c,'classification':'NOMINAL_DESIGN_REFERENCE',
                'provisional_constant_perimeter_volume_width_mm':expanded,'land_margin_after_080_position_error_mm':margin,
                'test_role':'PRIMARY' if (g,s)==('G25','S20') else 'PLANNED_COMPARISON' if (g,s) in primary_pairs else 'REFERENCE_ONLY_NOT_FIRST_PRINT',
                'warning':'NO_COMPRESSION_OR_GAP' if c<=0 else 'UNSUPPORTED_EXTREME_NOT_APPROVED' if margin<0 else 'HIGH_COMPRESSION_PHYSICAL_HOLD' if c>.30 else 'PHYSICAL_PENDING'})
    return rows


def measured_compression(thicknesses,spacers,gaps):
    def stats(values,n):
        if len(values)!=n or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<=0 for x in values):raise ValueError('complete positive finite measurements required')
        return {'min':min(values),'max':max(values),'mean':sum(values)/len(values),'range':max(values)-min(values)}
    t=stats(thicknesses,8);s=stats(spacers,4);g=stats(gaps,4)
    return {'free_thickness':t,'spacers':s,'measured_closed_gap':g,
        'compression_min':1-g['max']/t['min'],'compression_nominal_estimate':1-g['mean']/t['mean'],
        'compression_max':1-g['min']/t['max'],'automatic_water_promotion':False}


def geometry_metrics():
    b,l=body(),lid();g=gasket(2.5);active=ring(WIDTH,2.5)
    holes=compound([cyl(HOLE_D,6,xy,-1) for xy in M4]);stops=installed_stops(2).translate((0,0,-RIM))
    land=ring(LAND_WIDTH,.1,RIM-.1)
    matrix=compression_matrix();locator_study={}
    for mode in ('TWO_POINT','FOUR_POINT'):
        sh=gasket(2.5,mode)
        locator_study[mode]={'solids':len(sh.solids().vals()),'valid':sh.val().isValid(),
            'active_band_difference_mm3':delta(sh.intersect(active),active),'bounds_mm':bbox(sh),
            'volume_mm3':volume(sh),'selection':'SELECTED_ROUND_PLUS_RADIAL_SLOT' if mode=='TWO_POINT' else 'NOT_SELECTED_FOUR_ROUND_HOLES_CAN_OVERCONSTRAIN'}
    support=[]
    for row in matrix:
        if row['test_role'] not in ('PRIMARY','PLANNED_COMPARISON'):continue
        w=row['provisional_constant_perimeter_volume_width_mm']
        reservation=ring(w,.1,RIM-.1)
        missing=[]
        for i in range(8):
            theta=i*math.pi/4
            shifted=reservation.translate((POSITION_ALLOWANCE*math.cos(theta),POSITION_ALLOWANCE*math.sin(theta),0))
            missing.append(volume(shifted.cut(b)))
        support.append({'gasket':row['gasket'],'stop':row['stop'],'reservation_width_mm':w,
            'position_allowance_mm':POSITION_ALLOWANCE,'max_unsupported_volume_mm3':max(missing),
            'model':'CONSTANT_PERIMETER_VOLUME_RESERVATION_NOT_TPU_DEFORMATION_PREDICTION'})
    ratios=[]
    for h in (4,5,6):
        inertia=80*h**3/12
        ratios.append({'lid_thickness_mm':h,'strip_width_mm':80,'section_I_mm4':inertia,
            'relative_bending_compliance_vs_6mm':(6/h)**3})
    return {'body_bounds_mm':bbox(b),'lid_bounds_mm':bbox(l),'assembly_bounds_mm':bbox(assembly()),
        'internal_cavity_mm':[INNER,INNER,DEPTH],'dry_internal_volume_ml':dry_volume(2),
        'wall_mm':WALL,'floor_mm':FLOOR,'lid_mm':LID_T,'seal_datum_z_mm':RIM,'seal_land_width_mm':LAND_WIDTH,
        'gasket_centerline_plan_mm':CENTER_PLAN,'gasket_centerline_radius_mm':CENTER_R,
        'gasket_outer_radius_mm':CENTER_R+WIDTH/2,'gasket_inner_radius_mm':CENTER_R-WIDTH/2,
        'gasket_outer_plan_mm':CENTER_PLAN+WIDTH,'gasket_inner_plan_mm':CENTER_PLAN-WIDTH,
        'gasket_centerline_perimeter_mm':4*(CENTER_PLAN-2*CENTER_R)+2*math.pi*CENTER_R,
        'seal_land_missing_body_mm3':volume(land.cut(b)),'seal_land_missing_lid_mm3':volume(ring(LAND_WIDTH,.1).cut(l)),
        'm4_active_seal_intersection_mm3':common(holes,active),'stop_active_seal_intersection_mm3':common(stops,active),
        'm4_active_seal_clearance_mm':distance(holes,active),'stop_active_seal_clearance_mm':distance(stops,active),
        'locating_stop_intersection_mm3':common(g,stops),'rigid_body_lid_intersection_mm3':common(b,l.translate((0,0,RIM+2))),
        'tab_lid_intersection_at_min_stop_mm3':common(g.cut(active),l.translate((0,0,1.6))),
        'tab_free_height_at_min_gap_mm':1.6-EAR_T,'witness_body_intersection_mm3':common(witness(),b),
        'm4_count':4,'m4_centers_mm':M4,'hole_diameter_mm':HOLE_D,'stop_outer_diameter_mm':STOP_OD,
        'locators':locator_study,'locator_tab_thickness_mm':EAR_T,'locator_radial_clearance_mm':(LOCATOR_D-STOP_OD)/2,
        'locator_slot_length_mm':LOCATOR_D+2,'lid_stiffness_geometric_comparison':ratios,
        'nominal_lateral_registration_budget_mm':POSITION_ALLOWANCE,
        'lateral_budget_basis':'0.25 body-hole/nominal-M4 +0.25 stop-hole/nominal-M4 +0.30 ear/stop; print distortion not included',
        'lid_selection_basis':'6mm: 3.375x section bending stiffness of 4mm at equal material/span; no absolute stiffness claim without printed material/force data',
        'compression_matrix':matrix,'external_penetration_count':0,'joint_count':0,
        'planned_configuration_land_support':support,
        'nominal_primary_compression_ratio':.2,'round_cord_geometry_dependency':False,
        'body_volume_mm3':volume(b),'lid_volume_mm3':volume(l)}


def export_step(sh,path):
    exporters.export(sh,str(path),exportType='STEP')
    text=path.read_text()
    text=re.sub(r"FILE_NAME\(.*?\);",f"FILE_NAME('{path.name}','2000-01-01T00:00:00',(''),(''),'Open CASCADE','CADQUERY','DETERMINISTIC_METADATA');",text,flags=re.S)
    text=re.sub(r'Open CASCADE STEP translator (\d+\.\d+) \d+',r'Open CASCADE STEP translator \1 deterministic',text)
    occurrences=iter(range(1,10000))
    text=re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'",lambda _:f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{next(occurrences)}'",text)
    path.write_text(text,encoding='ascii',newline='\n')


def export_stl(shape,path):
    vertices,faces=shape.val().tessellate(.02,.08)
    lines=['solid PS_WP_TPU_FACE_GASKET_V001']
    for face in faces:
        a,b,c=[vertices[i] for i in face];n=(b-a).cross(c-a).normalized()
        lines.append('  facet normal '+' '.join(f'{v:.12g}' for v in n.toTuple()));lines.append('    outer loop')
        for v in (a,b,c):lines.append('      vertex '+' '.join(f'{q:.9f}' for q in v.toTuple()))
        lines.extend(['    endloop','  endfacet'])
    lines.append('endsolid PS_WP_TPU_FACE_GASKET_V001')
    path.write_text('\n'.join(lines)+'\n',encoding='ascii',newline='\n')


def ascii_triangles(path):
    vs=[tuple(map(float,s.split()[1:])) for s in path.read_text().splitlines() if s.lstrip().startswith('vertex ')]
    if len(vs)%3:raise AssertionError('STL vertex count')
    return [tuple(vs[i:i+3]) for i in range(0,len(vs),3)]


def stl_quality(path):
    triangles=[tuple(tuple(round(q,7) for q in v) for v in t) for t in ascii_triangles(path)]
    edges=Counter();wind=Counter();neighbors=defaultdict(list);degenerate=0
    for tri in triangles:
        a,b,c=tri;u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        degenerate+=int(len(set(tri))<3 or sum(q*q for q in cross)<1e-16)
        for x,y in ((a,b),(b,c),(c,a)):
            k=tuple(sorted((x,y)));edges[k]+=1;wind[k]+=1 if (x,y)==k else -1
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
    # Mesh connectivity is independently measured through shared vertices.
    adjacency=defaultdict(set)
    for a,b,c in triangles:adjacency[a].update((b,c));adjacency[b].update((a,c));adjacency[c].update((a,b))
    remaining=set(adjacency);components=0;component_bounds=[]
    while remaining:
        components+=1;stack=[next(iter(remaining))];points=[]
        while stack:
            v=stack.pop()
            if v not in remaining:continue
            remaining.remove(v);points.append(v);stack.extend(adjacency[v]&remaining)
        component_bounds.append([max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)])
    r={'triangles':len(triangles),'connected_components':components,'component_bounds_mm':component_bounds,'bad_edges':sum(n!=2 for n in edges.values()),
        'bad_winding_edges':sum(n!=0 for n in wind.values()),'bad_vertex_links':bad_vertices,'degenerate_triangles':degenerate,
        'duplicate_triangles':len(triangles)-len({tuple(sorted(t)) for t in triangles})}
    r['watertight']=r['bad_edges']==0;r['manifold']=r['watertight'] and bad_vertices==0
    r['pass']=all(r[k]==0 for k in ('bad_edges','bad_winding_edges','bad_vertex_links','degenerate_triangles','duplicate_triangles'))
    return r


def stl_dimensions(path):
    vs=[v for t in ascii_triangles(path) for v in t]
    return [max(v[i] for v in vs)-min(v[i] for v in vs) for i in range(3)]


def stl_seal_dimensions(path):
    # Direct triangle geometry at the straight run: vertices there include
    # both inner/outer edges and both print faces, and exclude locating tabs.
    vs=[v for t in ascii_triangles(path) for v in t if abs(v[0])<=22.500001 and 25<v[1]<33]
    if not vs:raise AssertionError('no actual STL seal run vertices')
    return {'width_mm':max(v[1] for v in vs)-min(v[1] for v in vs),
        'thickness_mm':max(v[2] for v in vs)-min(v[2] for v in vs)}


def actual_assembly_gap(sh):
    parts=[cq.Workplane(obj=s) for s in sh.solids().vals()]
    lids=[s for s in parts if all(abs(a-b)<TOL for a,b in zip(bbox(s),[80,80,LID_T]))]
    bodies=[s for s in parts if abs(bbox(s)[2]-RIM)<TOL]
    if len(lids)!=1 or len(bodies)!=1:raise AssertionError('ambiguous assembly body/lid')
    return bounds(lids[0])[2]-bounds(bodies[0])[5]


def generate_cad(out):
    (out/'artifacts').mkdir(parents=True,exist_ok=True);(out/'previews').mkdir(exist_ok=True)
    for f,sh in model().items():
        if not sh.val().isValid():raise AssertionError('invalid '+f)
        export_step(sh,out/f)
    for f in STLS:export_stl(model()[f.replace('.stl','.step')],out/f)
    for f,svg in previews().items():(out/f).write_text(svg,encoding='utf-8',newline='\n')


def inspect(out):
    r={'step':{},'stl':{},'actual_gaskets':{},'actual_stops':{}}
    for f in STEPS:
        s=importers.importStep(str(out/f));r['step'][f]={'valid':s.val().isValid(),'solids':len(s.solids().vals()),'bounds_mm':bbox(s)}
        if not r['step'][f]['valid']:raise AssertionError('STEP reload invalid '+f)
        if f in [f'artifacts/{p}.step' for p in PARTS[:3]+PARTS[8:10]]:
            q=self_interference(s);r['step'][f]['self_interference']=q
            if q['faulty']:raise AssertionError('STEP self-intersection '+f)
    for g,t in GASKETS.items():
        prefix=f'artifacts/ps_wp_tpu_gasket_{g.lower()}'
        r['actual_gaskets'][g]={'step':measure_seal(importers.importStep(str(out/(prefix+'.step'))),t),'stl':stl_seal_dimensions(out/(prefix+'.stl'))}
        if any(abs(r['actual_gaskets'][g]['stl'][k]-v)>TOL for k,v in [('width_mm',5),('thickness_mm',t)]):raise AssertionError('STL gasket dimensions')
    for name,h in STOPS.items():
        prefix=f'artifacts/stop_{name.lower()}'
        r['actual_stops'][name]={'step_thicknesses_mm':measure_thickness(importers.importStep(str(out/(prefix+'.step'))),h,4),
            'stl_thickness_mm':stl_dimensions(out/(prefix+'.stl'))[2]}
        if abs(r['actual_stops'][name]['stl_thickness_mm']-h)>TOL:raise AssertionError('STL stop thickness')
    r['actual_primary_assembly_gap_mm']=actual_assembly_gap(importers.importStep(str(out/'artifacts/ps_wp_water_dummy_assembly_g25_s20.step')))
    if abs(r['actual_primary_assembly_gap_mm']-2)>TOL:raise AssertionError('actual assembly gap')
    for f in STLS:
        r['stl'][f]=stl_quality(out/f)
        if not r['stl'][f]['pass']:raise AssertionError('STL quality '+f+' '+json.dumps(r['stl'][f]))
        if '/stop_' in f:
            name=Path(f).stem.removeprefix('stop_').upper();h=STOPS[name]
            if len(r['stl'][f]['component_bounds_mm'])!=4 or any(abs(b[2]-h)>TOL for b in r['stl'][f]['component_bounds_mm']):raise AssertionError('individual STL stop working thickness')
    return r


def regression():
    r=[]
    with tempfile.TemporaryDirectory(prefix='paddy_pswp_actual_geometry_') as tmp:
        out=Path(tmp)
        for name,t in GASKETS.items():
            f=out/(name+'.step');export_step(gasket(t),f);actual=measure_seal(importers.importStep(str(f)),t)
            bad=out/(name+'_wrong_plus010.step');export_step(gasket(t+.1),bad)
            rejected=False
            try:measure_seal(importers.importStep(str(bad)),t)
            except AssertionError:rejected=True
            if not rejected:raise AssertionError('wrong gasket accepted')
            r.append({'part':name,'requested_mm':t,'actual_mm':actual['thickness_mm'],'plus010_rejected':True})
        for name,h in STOPS.items():
            f=out/(name+'.step');export_step(stop_set(h),f);actual=measure_thickness(importers.importStep(str(f)),h,4)
            bad=out/(name+'_wrong_plus010.step');export_step(stop_set(h+.1),bad)
            rejected=False
            try:measure_thickness(importers.importStep(str(bad)),h,4)
            except AssertionError:rejected=True
            if not rejected:raise AssertionError('wrong stop accepted')
            a=out/(name+'_assembly.step');export_step(assembly(2.5,h),a)
            gap=actual_assembly_gap(importers.importStep(str(a)))
            if abs(gap-h)>TOL:raise AssertionError('actual interchangeable assembly gap')
            r.append({'part':name,'requested_mm':h,'actual_mm':actual,'plus010_rejected':True,'assembly_gap_mm':gap})
    return r


def reproduce():
    with tempfile.TemporaryDirectory(prefix='paddy_pswp_reproduce_') as tmp:
        gasket.cache_clear();body.cache_clear();lid.cache_clear();model.cache_clear()
        out=Path(tmp);generate_cad(out);inspect(out)
        comparison={f:sha(LANE/f)==sha(out/f) for f in [*STEPS,*STLS,*SVGS]}
    if not all(comparison.values()):raise AssertionError('reproducibility '+json.dumps(comparison))
    return {'byte_identical':comparison,'count':len(comparison),'pass_count':sum(comparison.values()),
        'step_metadata_policy':'Normalize FILE_NAME, generic PRODUCT and NAUO occurrence labels only; geometry untouched'}


def material_audit():
    return {'product':'PHYSICAL_PENDING','shore_hardness':'PHYSICAL_PENDING','specimen':'CURRENT_TPU_SPECIMEN',
        'search_scope':'Repository cad/common, cad/common_rover, cad, docs, rovers; Markdown/JSON/text material records',
        'findings':[{'path':'cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1/MISSING_MEASUREMENTS.md','finding':'TPU Shore/manufacturer HOLD'},
            {'path':'cad/ps_webcam_rainhood_v005_tpu_storm_skin/reports/DIMENSIONAL_AUTHORITY.md','finding':'TPU_SHORE UNKNOWN_PHYSICAL; approximate95A is explicitly NOT authority'},
            {'path':'cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0/hardware.json','finding':'TPU95A_FUTURE_CANDIDATE is not a proven current spool'},
            {'path':'cad/dummy_panicle_v0_1/README.md','finding':'Generic TPU95A design specification, no current spool identity'}],
        'authority_conclusion':'No documented exact current manufacturer+Shore authority found; do not invent95A'}


def physical_template():
    c=22.5+CENTER_R/math.sqrt(2)
    points=[(29,0),(0,29),(-29,0),(0,-29),(c,c),(-c,c),(-c,-c),(c,-c)]
    return {'specimen_id':None,'material_product':None,'shore_hardness':None,'printer_settings':None,
        'gasket_candidate':'G25','stop_candidate':'S20','face_orientation':'BUILD_PLATE_FACE_TOWARD_BODY_PRIMARY',
        'measurement_xy_mm':dict(zip([f'T{i}' for i in range(1,9)],points)),
        'T1_T8_free_thickness_mm':[None]*8,'S1_S4_spacer_thickness_mm':[None]*4,
        'G1_G4_measured_closed_gap_mm':[None]*4,'actual_compression':None,
        'dry_10_cycles_result':'PENDING','upright_60min':'PENDING','front_tilt':'PENDING','rear_tilt':'PENDING',
        'left_tilt':'PENDING','right_tilt':'PENDING','witness':'PENDING','first_wet_zone':'PENDING',
        'tpu_movement':'PENDING','tpu_damage':'PENDING','petg_damage':'PENDING','water_level_mm':None,
        'water_temperature_c':None,'promotion':'WATER_PHYSICAL_TEST_PENDING'}


def parameters(metrics):
    return {'architecture':'PS-WP-TPU-FACE-GASKET-V001','status':STATUS,'gaskets_mm':GASKETS,'stops_mm':STOPS,
        'seal_width_mm':WIDTH,'flat_land_width_mm':LAND_WIDTH,'primary':'G25/S20','tolerance_mm':TOL,
        'material':material_audit(),'metrics':metrics,
        'history':{'round_cord_small_dummy':'PASS','round_cord_full_bbox_long_duration':'FAIL',
            'failure_mode':'UNRESOLVED_SLOW_INGRESS','old_rubber_material':'EPDM','old_rubber_nominal_diameter_mm':3.0,
            'old_rubber_light_caliper_approx_mm':3.4,'old_1p8_label':'HISTORICAL_ASSUMPTION_NOT_CURRENT_PHYSICAL_AUTHORITY',
            'source':'LATEST_USER_TASK; no mutation of historical lanes; no exact leak cause asserted'},
        'contract':{'gasket_joint_count':0,'seal_loop_interruption_count':0,'narrow_cord_groove':False,
            'seal_band_hole_count':0,'body_reprint_required_for_gasket_change':False,'lid_reprint_required_for_gasket_change':False,
            'external_penetration_count':0,'adhesive_required':False},
        'print':'HOLD_SLICER_NOT_RUN','water':'PHYSICAL_PENDING','bbox_v005':'PENDING_NOT_CREATED','cbox_field_box':'PENDING_NOT_CREATED'}


def write_json(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')


def build():
    audit();generate_cad(LANE);geometry=geometry_metrics();quality=inspect(LANE);reg=regression();repro=reproduce()
    write_json(LANE/'design_parameters.json',parameters(geometry))
    write_json(LANE/'material_authority_audit.json',material_audit());write_json(LANE/'physical_measurement_template.json',physical_template())
    write_json(LANE/'validation_report.json',{'status':'GENERATED_CONTRACT_PENDING','geometry':geometry,'quality':quality,'regression':reg,'reproducibility':repro})
    for f,text in documents(geometry).items():(LANE/f).write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'build':'GENERATED_CONTRACT_PENDING','geometry':geometry,'quality':quality,'regression':reg,'reproducibility':repro},indent=2))


def finalize(report):
    if not report['pass']:raise AssertionError('contract not PASS')
    write_json(LANE/'contract_test_report.json',report)
    v=json.loads((LANE/'validation_report.json').read_text());v['status']=STATUS;write_json(LANE/'validation_report.json',v)
    (LANE/'COMMIT_PATHS.txt').write_text('\n'.join(REL+'/'+f for f in EXPECTED)+'\n',encoding='utf-8',newline='\n')
    write_json(LANE/'manifest.json',{'exact_count':len(EXPECTED),'paths':EXPECTED,'lane':REL,'status':STATUS,
        'runtime':'Python3.12 / CadQuery2.8 / OCCT7.9; python -B required','cad_source':'standalone generator; prior CAD is not imported',
        'audit_requires_protected_repository_sources':True})
    for name in ('repository_audit.json','SHA256SUMS.txt'):
        if not (LANE/name).exists():(LANE/name).write_text('',encoding='ascii')
    write_json(LANE/'repository_audit.json',audit(full=True))
    (LANE/'SHA256SUMS.txt').write_text(''.join(f'{sha(LANE/f)}  {f}\n' for f in EXPECTED if f!='SHA256SUMS.txt'),encoding='ascii',newline='\n')


def verify():
    state=audit(full=True)
    if sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob('*') if p.is_file())!=EXPECTED:raise AssertionError('exact paths')
    for line in (LANE/'SHA256SUMS.txt').read_text().splitlines():
        h,f=line.split('  ',1)
        if sha(LANE/f)!=h:raise AssertionError('SHA '+f)
    if not json.loads((LANE/'contract_test_report.json').read_text())['pass']:raise AssertionError('contract pending')
    quality=inspect(LANE);repro=reproduce()
    print(json.dumps({'verify':'PASS','audit':state,'quality':quality,'reproducibility':repro},indent=2))


def handoff():
    verify();target=Path(r'D:\Downloads')/('Paddy_Swarm_PS_WP_TPU_FACE_GASKET_V001_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in EXPECTED:z.write(LANE/f,LANE.name+'/'+f)
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None or sorted(z.namelist())!=sorted(LANE.name+'/'+f for f in EXPECTED):raise AssertionError('ZIP integrity')
        for f in EXPECTED:
            if hashlib.sha256(z.read(LANE.name+'/'+f)).hexdigest()!=sha(LANE/f):raise AssertionError('ZIP member SHA')
    print(json.dumps({'zip':str(target),'sha256':sha(target),'members':len(EXPECTED)}))


def preview_frame(projection):
    # Explicit display axes avoid OCCT's automatic camera roll. Display-only
    # transforms never modify the exported STEP/STL parts.
    return cq.Plane((0,0,0),xDir=(0,1,0) if projection==(1,0,0) else (1,0,0),normal=projection)


def previews():
    def panel(sh,x,y,w,h,projection):
        display=preview_frame(projection).toLocalCoords(sh.val())
        raw=exporters.getSVG(display,opts={'width':w,'height':h,'projectionDir':(0,0,1),'showHidden':False,
            'strokeWidth':max(bbox(sh))/800,'marginLeft':20,'marginTop':20})
        return raw[raw.index('<svg'):].replace('<svg',f'<svg x="{x}" y="{y}"',1)
    def page(title,subtitle,panels,notes):
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="820" viewBox="0 0 1200 820">'
        svg+='<rect width="1200" height="820" fill="#f8fafc"/><style>text{font-family:Arial,sans-serif;fill:#17324c;font-size:18px}</style>'
        svg+=f'<text x="30" y="40" style="font-size:26px">{title}</text><text x="30" y="75">{subtitle}</text>'+''.join(panels)
        for i,s in enumerate(notes):svg+=f'<text x="30" y="{640+30*i}">{s}</text>'
        return svg+'<text x="30" y="803" style="font-size:14px">PS-WP-TPU-FACE-GASKET-V001 | mm | CAD geometry only; WATER PHYSICAL TEST PENDING</text></svg>'
    exposed=compound([body(),gasket(2.5).translate((0,0,RIM)),installed_stops(2)])
    section=assembly().intersect(box(100,.8,50,(0,0,20)))
    detail=compound([body(),lid().translate((0,0,RIM+2)),gasket(2.5).translate((0,0,RIM))]).intersect(box(.8,17,12,(0,29,29)))
    post_section=assembly().intersect(box(.8,16,23,(34,34,28)))
    compare_g=compound([gasket(t).translate((i*100,0,0)) for i,t in enumerate(GASKETS.values())])
    compare_s=compound([stop(h,(i*15,0)) for i,h in enumerate(STOPS.values())])
    papers='<g transform="translate(380,360) scale(7,-7)"><rect x="-24" y="-24" width="48" height="48" rx="1.5" fill="#e4edf5" stroke="#17324c" stroke-width=".15"/>'
    for name,(x,y,w,h) in WITNESS.items():
        papers+=f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" fill="#fff" stroke="#3c7299" stroke-width=".12"/>'
        papers+=f'<g transform="translate({x},{y}) scale(1,-1)"><text text-anchor="middle" dominant-baseline="middle" style="font-size:1.4px">{name}</text></g>'
    papers+='</g><text x="690" y="240">FRONT = +X; LEFT = +Y</text><text x="690" y="280">8 separate paper zones</text><text x="690" y="320">Do not bridge the gasket</text><text x="690" y="360">Floor datum Z3.5</text>'
    pages=[page('Common TPU face-gasket dummy — top','Lid removed: G25 gasket, four S20 stops, two non-sealing locating ears.',
        [panel(exposed,20,100,1130,505,(0,0,1))],['PETG plan 80 x80; active gasket outer63 / inner53; width5.0.','Round locator at (-34,-34); radial slot at (+34,+34).','Four M4 positions (+/-34,+/-34). Stops are independent removable parts.']),
        page('G25 / S20 — closed assembly section','Section Y=0. Free-thickness TPU reference overlaps lid by nominal0.5 mm.',
        [panel(section,20,110,1130,490,(0,-1,0))],['Cavity48 x48 x25; floor3.5; lower wall3.5; lid6.0.','Seal datum Z28.5; closed lid underside Z30.5; assembly top Z36.5.','No gland, chimney or cable. CAD closure is not a water-performance prediction.']),
        page('Wide flat face — no cord groove','Section through a straight seal run; original Z is vertical.',
        [panel(detail,20,110,1130,490,(1,0,0))],['TPU width5.0; free thickness2.5; nominal gap2.0 ->20% design compression.','PETG flat land width10.0 gives room for lateral bulging; physical behavior is unproven.','TPU/lid overlap in reference is intentional; actual print gasket stays2.5 mm thick.']),
        page('Locating architecture trade study','Left SELECTED: one round + one radial slot. Right reference: four round ears.',
        [panel(gasket(2.5),20,110,560,490,(0,0,1)),panel(gasket(2.5,'FOUR_POINT'),620,110,560,490,(0,0,1))],
        ['The active continuous seal loop is identical in both geometries.','Ears0.8 thick; holes8.6 over stop OD8.0; radial clearance0.3 nominal.','Slot10.6 x8.6 relieves registration error. Four-point physical distortion not tested.']),
        page('Replaceable hard stop — M4 corner section','S20 sets a2.0 mm gap between flat PETG datum faces.',
        [panel(post_section,20,110,1130,490,(1,0,0))],['Stop OD8.0 / bore4.5; four identical collars per configuration.','Body lug thickness8 + S20 gap2 + lid6 =16 mm plastic stack.','Actual bolt / washers / nut / thread engagement must be checked; no PETG tapping.']),
        page('G20 / G25 / G30 — same active XY geometry','Left2.0; center2.5 PRIMARY; right3.0 mm. All printed flat, no support.',
        [panel(compare_g,20,110,1130,490,(0,-1,1))],['Only the active band thickness varies; locating ears remain0.8 mm.','Measure T1-T8 with light caliper force, not a squeezed TPU reading.','BUILD_PLATE_FACE and TOP_PRINT_FACE are recorded separately.']),
        page('S16 / S18 / S20 / S22 / S24','Working thickness1.6 /1.8 /2.0 /2.2 /2.4 mm; four per STL set.',
        [panel(compare_s,20,110,1130,490,(0,-1,.35))],['Start with S20 only. Other configurations are not all first-print targets.','For G25: S18=28%, S20=20%, S22=12% nominal design reference.','No labels on working faces. Keep each set in a separately labeled bag.']),
        page('Segmented witness-paper layout','Exact CAD zone coordinates; labels are on paper only, not on seal faces.',
        [papers],['Upright60 min; external observation at10 and30 min. Do not open during the60 min stage.','Then if PASS: four tilts greater than10 degrees,10 min each.','Record first wet zone; wipe all exterior water away before opening.'])]
    return dict(zip(SVGS,pages))


def documents(g):
    history='''# Round-cord failure context — read-only history

Latest user physical update is recorded HERE only; no old lane is rewritten.

- G065 small closed dummy: ROUND_CORD_SMALL_DUMMY = PASS. Its previous successful water test is NOT revoked.
- Full BBOX V004: ROUND_CORD_FULL_BBOX_LONG_DURATION = FAIL. Temporary exposure passed, but the cumulative 60-minute full-box test developed gradual ingress.
- FAILURE_MODE = UNRESOLVED_SLOW_INGRESS. Exact entry location/cause is not proven. Do not blame the joint, chimney, PETG porosity or groove as an established cause.
- Old round rubber: user identified EPDM, nominal diameter3 mm; later light-caliper measurement approximately3.4 mm. Historical1.8 mm labels are NOT current physical rubber authority.

Read-only source review:

1. `cad/common_rover/bbox/bbox_compact_seal_b_water_dummy_v001`: records the G055/G065 actual-depth correction; later user G065 water PASS remains valid for that specimen.
2. `cad/common_rover/bbox/bbox_compact_field_goldenmate_v004_g065`: its CAD-era record still says full-box water pending; the newer user60-minute FAIL supersedes that status in this delta record, without patching the protected package.
3. `cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8`: external vertical M4 architecture isolated intentional screw-hole water paths; its old material labels are historical, not new TPU inputs.
4. `cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority`:2.4 mm local-wall coupon selection; full-lid/gland water performance cannot be inferred from that local fit.

The TPU geometry is independent from ALL round-cord diameters. A one-piece loop removes the deliberate butt joint, but printed TPU waterproofing is still unproven. Neither the old small-dummy PASS nor a future common-dummy PASS qualifies BBOX/CBOX automatically.
'''
    variants='''# TPU gasket variant matrix

| Variant | Active width | Free thickness | Locating-ear thickness | Initial use |
|---|---:|---:|---:|---|
| G20 |5.0 mm|2.0 mm|0.8 mm|Later comparison with S16|
| G25 |5.0 mm|2.5 mm|0.8 mm|PRIMARY with S20|
| G30 |5.0 mm|3.0 mm|0.8 mm|Later comparison with S24|

All use centerline58 x58 mm, radiusR6.5; outer63 x63 R9, inner53 x53 R4. One continuous rectangular flat-band solid. No butt joint, cut location or adhesive needed for loop continuity. The thinner ears are NOT sealing surfaces.

Locating trade:

- Selected two-point system: round hole at(-34,-34), radial slot at(+34,+34). The holes register around removable stop collars, which are registered by M4 shanks. Install stops/bolts loosely before the lid so the gasket is located without adhesive.
- Round hole8.6 over stop OD8 gives0.3 mm radial clearance. Slot10.6 x8.6, oriented along the corner diagonal, accommodates longitudinal registration error. It does not prove absence of printed TPU distortion.
- Four-corner option: same intact seal band, four round locating ears. CAD fits, but extra constraints and material offer no demonstrated advantage before physical testing. Not selected; no extra print variant produced.
- Ears0.8 mm stay below every stop gap; minimum nominal tab-to-lid space0.8 mm at S16. Working stop faces never bear through TPU ears.

Inspect rounded bridges, ear holes, elephant foot, stringing and tear onset. Do not enlarge or cut the active seal band to resolve fit.
'''
    matrix='# Hard-stop compression matrix\n\nAll ratios below are NOMINAL_DESIGN_REFERENCE, not physical results.\n\n| Gasket | S16 | S18 | S20 | S22 | S24 |\n|---|---:|---:|---:|---:|---:|\n'
    for name,t in GASKETS.items():matrix+='|'+name+'|'+'|'.join(f'{100*(1-h/t):.1f}%' for h in STOPS.values())+'|\n'
    matrix+='''
Primary G25/S20:20%. Adjacent later G25/S18:28%, G25/S22:12%. Nominal20% comparisons G20/S16 and G30/S24.
Zero/negative compression combinations are NOT sealing tests; configurations over30% are high-compression physical HOLD, not an approved operating window. Do not force the gasket or damage PETG to reach a stop.

The same body and lid fit every spacer set; all four collars must be from ONE set. Files contain four separate collars, OD8 / bore4.5, at22 x22 mm print-set bounds. No marks alter flat working faces. Label bags/files rather than sealing/stop surfaces. Do not print every set initially.

Flat PETG land is10 mm rather than the suggested5.5-6: an area-conserving, constant-perimeter rectangular estimate needs width5*t/gap. G25/S20 gives6.25 mm, G25/S18 gives6.944444 mm. A nominal registration budget includes0.25 body-hole/bolt +0.25 stop-hole/bolt +0.30 ear/stop =0.80 mm; printed distortion is additional and unmeasured. Land margins after this budget are1.075 and0.727778 mm respectively. The planned configurations have independent eight-direction CAD reservation-support checks. Actual TPU bulging, porosity and stretch are NOT simulated by this estimate.
The extreme G30/S16 needs9.375 mm and has NEGATIVE0.4875 mm land margin after the0.80 budget: UNSUPPORTED_EXTREME_NOT_APPROVED. It is a mathematical reference, NOT a test configuration. All provided parts remain interchangeable for their intended pairings, but not all15 cross-combinations are acceptable sealing configurations. Test a window physically later; none is claimed now.

Actual compression uses FREE measured TPU thickness and independently measured CLOSED face gap:

`r = (t_free - gap_closed) / t_free`

Conservative range: `r_min = 1 - gap_max/t_min`; mean estimate `1 - gap_mean/t_mean`; `r_max = 1 - gap_min/t_max`.
Measure S1-S4 AND closed gaps G1-G4: unequal spacers or lid warp can make nominal spacer thickness an invalid global-gap assumption. Missing measurements remain PENDING; no automatic physical promotion.
'''
    measurement='''# TPU print and measurement plan

Material: CURRENT_TPU_SPECIMEN. Exact manufacturer/product and Shore hardness PHYSICAL_PENDING. Search evidence is in material_authority_audit.json. Existing approximate95A design assumptions do not identify the current spool. Record brand, spool label, lot, hardness if documented, drying and actual slicer settings; do not invent95A.

First print order:

1. TPU thickness calibration coupon: three14 x14 pads at X=-20,0,+20, nominal2.0/2.5/3.0 mm. They are separate pads, not a structural part. Print flat without support; keep pad order identified. Measure with light contact.
2. G25 complete gasket only. Flat on plate; nominal Z thickness2.5 mm. No support, adhesive joint or cut.
3. S20 PETG stop set only: four2.0 mm collars, flat. Do not sand selectively to hide unequal thickness without recording the new dimensions.
4. Common PETG body and lid after dimensional checks.

TPU: inspect elephant foot, closed holes, width/perimeter accuracy, stringing, layer gaps, face roughness and tears. Record BUILD_PLATE_FACE and TOP_PRINT_FACE separately. PRIMARY orientation: BUILD_PLATE_FACE toward BODY. If needed compare the reverse orientation later while keeping other variables constant; log each orientation as a separate run.

Use light caliper contact only. Do not squeeze TPU to obtain a target reading.
T1-T4: straight midpoints(+29,0),(0,+29),(-29,0),(0,-29).
T5-T8: near-corners at (+/+),(-/+),(-/-),(+/-) coordinates approximately27.096194 mm each axis.
Record T1-T8; calculate MIN/MAX/MEAN/RANGE. Measure all four PETG spacers S1-S4. With gentle even closure to stops, measure effective local gaps G1-G4; do not assume perfectly rigid/parallel printed faces.

Copy physical_measurement_template.json outside the protected lane for actual observations. Fill measured arrays only with actual values, then:

`python -B build_ps_wp_tpu_face_gasket_v001.py --measurements <filled-result.json>`

The calculator requires8 thickness readings,4 stop readings and4 closed-gap readings. It rejects missing, non-finite or non-positive values. Output includes range-based compression estimates; it does not grant water approval.

Printer: Bambu A1,256-cube build envelope. Body open-up; floor down. Lower wall/floor3.5; broad seal land has a45-degree outer flare plus a1 mm flat cap. External M4 lug undersides may need build-plate-only support. Keep all support away from the seal, cavity and stop datum faces.
Lid6 mm: flat on plate, preferred future sealing face UP to avoid plate-texture assumptions. Its two flat faces and through-hole pattern allow installation inverted. Body/lid print orientation is independent from TPU face orientation.
TPU and all spacers: flat, support OFF. Stop faces and gasket faces must not be damaged by brim removal. Use separately labeled bags for spacer sets; no label is on a working face.
SLICER_NOT_RUN / PROCESS_PENDING. Review watertight toolpaths, solid skins, material settings, support blockers and flatness in the actual slicer. Nominal CAD precision is not printer accuracy. No invented universal TPU print profile.
'''
    dry='''# Dry physical test — G25/S20

Only measured and inspected parts enter this test; CAD PASS does not equal dry mechanical PASS.

1. Inspect all parts; record material identity if available and printed face orientation.
2. Measure gasket T1-T8, spacers S1-S4 and later actual closed gaps G1-G4.
3. Loosely register the two thin TPU ears over the external stop collars/M4 positions; no adhesive. Confirm the closed5 mm seal band sits fully on the flat land.
4. Install all FOUR S20 collars. Do not mix thickness sets. Check collars seat directly against PETG, not on TPU.
5. Fit lid and four M4 through-bolts with metal washers/nuts. Plastic stack is8+2+6=16 mm for G25/S20; select actual hardware to include washers, full nut engagement and adequate exposed thread. Exact stocked bolt/washer/nut dimensions are not established. No PETG tapping.
6. Tighten evenly in diagonals until the stops contact. Do not use destructive tightening or force warped parts flat. Stop if collars cannot seat or the lid rocks.
7. Confirm no TPU extrusion into the cavity or excessive outer extrusion; no pinched/loaded locating ears.
8. Check copy-paper insertion around the seal: NONE preferred; a gap is a dry-test failure, not permission to overtighten.
9. Open/close10 times. Inspect TPU tear, permanent set, locating-tab damage, PETG whitening and cracks; check dimensions and gasket location again.

Record DRY_MECHANICAL_PASS or FAIL from actual observations only. WATER testing remains blocked until dry PASS. Material hardness, allowable bolt torque and compression robustness are still physical questions.
'''
    water='''# Water test — primary G25/S20

Only after DRY_MECHANICAL_PASS. EMPTY / INERT dummy only: no battery, live cable or powered electronics. This dummy has no gland/chimney/cable passage.

Place eight separate completely dry tissue/paper segments: FRONT, REAR, LEFT, RIGHT, CORNER1, CORNER2, CORNER3, CORNER4. Use the exact layout/labels in witness_zone_layout.svg; do not bridge or touch the seal. Define FRONT=+X, LEFT=+Y consistently.
Record specimen IDs, print faces, material/spool, actual thickness/gaps, water temperature, water level relative to seal plane and test start time. Apply the same documented exposure conditions to comparisons; water depth is not a new pressure rating.

1. Upright cumulative60 minutes. Observe externally at10 and30 minutes. DO NOT OPEN during the60-minute stage. AFTER the full60 minutes, wipe the exterior completely, open and record upright witness PASS/FAIL. If PASS, prepare fresh dry segmented paper and reassemble for the tilt stages.
2. If upright PASS, front tilt greater than10 degrees for10 minutes.
3. Rear tilt greater than10 degrees for10 minutes.
4. Left tilt greater than10 degrees for10 minutes.
5. Right tilt greater than10 degrees for10 minutes.
6. At the end of EACH completed stage, wipe the entire exterior fully before opening. Record that stage's witness condition and first wet zone; photograph before disturbing paper. Use fresh dry paper for the next direction, recheck gasket seating, and log the extra closure cycle. Do not infer four separate directional PASS results from one undifferentiated final witness.

Do not silently infer intermediate first-leak time from final wet paper. If timing/location is unclear, record UNKNOWN and use separate controlled localization runs. Do not interrupt the prescribed cumulative stage to peek inside.
Record each stage PASS/FAIL, witness COMPLETELY_DRY/TRACE/WET, first zone NONE/FRONT/REAR/LEFT/RIGHT/CORNER1-4/UNKNOWN, TPU movement NONE/SMALL/FAIL, TPU damage NONE/MARK/TEAR/PERMANENT_SET, PETG NONE/WHITENING/CRACK.

Promotion requires actual60-minute upright PASS + all four tilts PASS + completely dry witness + gasket stayed located + no TPU tear + no PETG damage:

`PS_WP_TPU_G25_S20_WATER_PHYSICAL_PASS`

No water PASS is claimed in this CAD package. If PASS, later compare G25/S22 or G25/S18 to investigate a manufacturing/compression window; no window is established by one PASS.
If FAIL, retain the common body/lid and first localize the leak. Compare S18 (more compression) and S22 (less) using the same G25 gasket/body/lid and record damage/set history. Only then consider G20/G30 if stiffness is unsuitable. Do not immediately redesign the box or mask failure with sealant.
'''
    result='''# Physical result sheet — BLANK / PENDING

No synthetic measurement is a physical result. Record actual values in a new result record; preserve this released template.

Specimen / date / operator: ____
TPU product / lot / documented Shore / condition: ____
Printer / material settings / face orientation: ____
Gasket ID: ____ ; spacer set ID: ____

T1 ____ T2 ____ T3 ____ T4 ____ T5 ____ T6 ____ T7 ____ T8 ____ mm (light contact)
Thickness MIN ____ MAX ____ MEAN ____ RANGE ____ mm
S1 ____ S2 ____ S3 ____ S4 ____ mm
G1 ____ G2 ____ G3 ____ G4 ____ mm (actual closed face gap)
Compression MIN ____ mean/nominal estimate ____ MAX ____
Dry10-cycle result: PENDING / PASS / FAIL; notes ____
Copy-paper gaps / extrusion / set / locating-tab condition: ____

| Observation | Result |
|---|---|
|60min upright|PENDING|
|External10min /30min checks, without opening|____|
|Front tilt >10deg /10min|PENDING|
|Rear tilt >10deg /10min|PENDING|
|Left tilt >10deg /10min|PENDING|
|Right tilt >10deg /10min|PENDING|
|Witness: COMPLETELY_DRY / TRACE / WET|PENDING|
|First wet zone: NONE / FRONT / REAR / LEFT / RIGHT / CORNER1-4 / UNKNOWN|PENDING|
|TPU movement: NONE / SMALL / FAIL|PENDING|
|TPU damage: NONE / MARK / TEAR / PERMANENT_SET|PENDING|
|PETG: NONE / WHITENING / CRACK|PENDING|

Water level relative to seal / temperature / exposure details: ____
Witness photos before disturbance: ____
Promotion: WATER_PHYSICAL_TEST_PENDING until ALL criteria pass.
'''
    future='''# Future common-interface integration — NOT performed

PS-WP-TPU-FACE-GASKET-V001 is a common waterproof-interface development lane, not a BBOX-specific conversion.
The invariant concept is a continuous flat5 mm band, constant offset rounded corners, non-sealing external locating tabs and independently replaceable gap-setting stops. Future changes should adjust straight-run lengths with the generator/standard, not scale XYZ or silently change band thickness/width.

After actual common-dummy PASS only:

- Next phase A: NEW BBOX V005 TPU face-gasket conversion.
- Next phase B: NEW CBOX field-box TPU face-gasket baseline.

Neither conversion is included now. Each larger enclosure needs its own stiffness/fastener spacing, material-printability, leak-path and full-box water validation. Small-dummy PASS is not a BBOX/CBOX water rating or field durability result.
Later establish tolerance to TPU thickness variation, replacements, repeated cycles, locally printed parts and dirty/wet assembly. No robustness window or field reproducibility is claimed in V001.

Future cable policy: PRIMARY mechanical cable gland; SECONDARY optional RTV/sealant/caulking; TERTIARY chimney/water-shedding shape. Sealant must not be the sole primary mechanism. Current dummy has none of these penetrations.
'''
    authority=f'''# PS-WP-TPU-FACE-GASKET-V001 design authority

Common-interface CAD development only. Physical gasket/compression/water performance remains pending.

- One common PETG body:80 x80 x28.5 mm nominal; one common lid80 x80 x6.
- Local floor undersideZ0; seal datumZ28.5. Cavity48 x48 x25; actual primary closed dry-air volume {g['dry_internal_volume_ml']:.6f} mL using a closure surrogate, not water simulation.
- Lower wall/floor3.5 mm. Outer45-degree flare terminates under a1 mm flat cap supporting the10 mm seal land.
- G20/G25/G30: flat active band5 mm, nominal free thickness2/2.5/3; same centerline58 x58 R6.5. OuterR9, innerR4. Perimeter {g['gasket_centerline_perimeter_mm']:.6f} mm. No cord groove, split or butt joint.
- Two external TPU ears0.8 thick; round8.6 hole and radial10.6 x8.6 slot register on removable stop OD8.0. No adhesive required. Full assembly including ears approximately81.707107 x81.707107 x36.5 for G25/S20.
- Four M4 through locations(+/-34,+/-34), bore4.5, exterior body lug thickness8. Stops OD8/bore4.5; S16/S18/S20/S22/S24 working thickness1.6/1.8/2/2.2/2.4. No integrated permanent gap stop. Body/lid reprint is not required for variant exchange.
- Primary G25/S20 gives nominal20%, not measured physical compression. Stop working faces do not clamp TPU ears.

Lid selection calculation: for an80 mm-wide strip, I=b*t^3/12 is426.666667 mm4 at4 mm,833.333333 at5 mm and1440 at6 mm. At equal material/span,6 mm has3.375 times the bending section stiffness of4 mm. Select6 mm within the requested4-6 range. Printed modulus, bolt force, warp and absolute deflection are unknown; this is not a pressure/stiffness qualification. Measure four closed gaps and test uniform seating.

CAD geometric isolation and measured exported dimensions are recorded in validation_report.json; negative+0.10 mm regressions cover every gasket and spacer. Separate STEP reload, STL topology/connectivity and byte reproduction checks are mandatory.
All pressure-boundary penetrations:0. M4/stop intersection with active seal:0. Closure-air separation is only a check that no intentional geometric path exists. FDM porosity, surface condition, TPU behavior and permanent set require actual tests.

Geometry avoids support on seal faces/gaskets/stops. External body ears may need supports; slicer NOT RUN. Stop/gasket measurement and dry-cycle tests precede water testing.

{STATUS}

These CAD labels apply only with contract_test_report PASS and builder --verify PASS. They do not mean TPU_WATERPROOF_PASS.
'''
    readme=f'''# PS-WP TPU Face Gasket V001

{STATUS}

NEW common lane: `{REL}`. No BBOX/CBOX conversion and no historical artifact mutation.

First print: TPU thickness calibration pads -> measure -> G25 gasket -> T1-T8 -> S20 PETG stops -> measure -> common body/lid -> dry10 cycles -> closed water test. Do not print every variant before primary evidence.

Primary G25/S20: one-piece5 mm-wide,2.5 mm-thick TPU loop and four2 mm PETG collars; nominal20% compression. Body and lid are reusable for all candidates. Two thin external locating ears register around the stop collars without interrupting the seal. Fit without adhesive.
Flat PETG land10 mm accommodates nominal lateral bulging; there is NO old2.1 mm round-cord groove. Lid6 mm selected from the4-6 range by section-stiffness comparison. No actual TPU brand or Shore is invented.

Latest round-cord history: small G065 dummy PASS remains valid; full V00460-minute water test FAIL with UNRESOLVED_SLOW_INGRESS. User old EPDM nominal3 mm / light-caliper approximately3.4 mm replaces the1.8 physical assumption. None of those diameters drive TPU geometry.

CAD:14 STEP /11 STL /8 SVG. Primary assembly uses the FREE2.5 mm gasket reference, so its0.5 mm overlap with the closed lid is intended nominal elastic compression, not a rigid collision or deformation prediction. Only individual printable STL files are printed; never print the assembly.

Python3.12 / CadQuery2.8 / OCCT7.9; use -B to keep caches out of protected lanes:

```
python -B build_ps_wp_tpu_face_gasket_v001.py --build
python -B tests/test_ps_wp_tpu_face_gasket_v001.py
python -B build_ps_wp_tpu_face_gasket_v001.py --verify
python -B build_ps_wp_tpu_face_gasket_v001.py --zip
```

Geometry generator is standalone; repository verification needs the preserved authority paths in audit_start.json. ZIP contains only this lane. Git add/commit/push/branch changes are forbidden during this task. COMMIT_PATHS is an inventory, not staging permission.
See TPU_PRINT_MEASUREMENT_PLAN.md for orientations/support/slicer review and measured-compression calculator. No water, BBOX, CBOX, durability or field PASS is claimed.
'''
    return dict(zip(DOCS,[readme,authority,history,variants,matrix,measurement,dry,water,result,future]))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');ap.add_argument('--verify',action='store_true');ap.add_argument('--zip',action='store_true');ap.add_argument('--measurements',type=Path)
    args=ap.parse_args()
    if args.build:build()
    elif args.verify:verify()
    elif args.zip:handoff()
    elif args.measurements:
        inp=json.loads(args.measurements.read_text(encoding='utf-8'));print(json.dumps(measured_compression(inp['T1_T8_free_thickness_mm'],inp['S1_S4_spacer_thickness_mm'],inp['G1_G4_measured_closed_gap_mm']),indent=2))
    else:ap.error('choose --build / --verify / --zip / --measurements')
