"""PTO offset placement gauges. No installed transform or structural release.

Working X faces are 0 and L. Geometry in reference assemblies is an exploded
component board, NOT a rover installation or a source of physical clearances.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

import cadquery as cq
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

ROOT=Path(r'D:\Paddy_Swarm_Project')
LANE=Path(__file__).resolve().parent
REL='cad/common_rover/pto/pto_offset_spacer_test_v001'
BRANCH='agent/organize-untracked-cad-assets-20260725'
HEAD='7c149a65053f2292bc4cc0ed06d8941c96852f2b'
TOL=1e-6
CANDIDATES={'P20':20.0,'P22':22.0,'P25':25.0}
KP_PHYSICAL=66.1
PULLEY_PHYSICAL=100.1
OVERHANG=(PULLEY_PHYSICAL-KP_PHYSICAL)/2
STATUS='CAD_PASS/CONTRACT_TEST_PASS/PLACEMENT_GAUGE_PRINT_READY/STRUCTURAL_SPACER_INTERFACE_PENDING/PHYSICAL_CLEARANCE_TEST_PENDING/SLIDE_CLUTCH_FINAL_ENVELOPE_PENDING'
FRONT='cad/common_rover/frame/front_interface_dual_pto_20t_v001'
FRONT2='cad/common_rover/frame/front_interface_dual_pto_20t_v002'
PTO20='cad/common_rover/pto/pto_20t_od10_physical_envelope_v001'
SIXTY='cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26'
DRIVE='cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003'
SOURCE_STEP={
 '20t_reference':PTO20+'/artifacts/pto_20t_od10_physical_envelope.step',
 '60t_existing_cad_reference':SIXTY+'/artifacts/temp_htd5m_60t_dual_shaft_collar_embedded_m4_provisional_v0_9_6_26.step',
 'candidate_c_drivetrain_reference':DRIVE+'/cad/candidate_C_12T_misumi_groove1_keeperless.step',
}
PRINTS=[f'pto_offset_spacer_{int(v)}' for v in CANDIDATES.values()]+['pto_offset_gauge_triplet']
REFERENCES=[f'pto_offset_{n.lower()}_reference_assembly' for n in CANDIDATES]+[
 'kp000_physical_reference','60t_physical_envelope_reference','20t_reference','current_frame_end_reference',
 'pto_shaft_reference','60t_existing_cad_reference','kp000_existing_cad_reference','candidate_c_drivetrain_reference']
STEPS=['artifacts/'+n+'.step' for n in PRINTS+REFERENCES]
STLS=['artifacts/'+n+'.stl' for n in PRINTS]
SVGS=['previews/'+n+'.svg' for n in [
 'p20_top','p22_top','p25_top','p20_clearance_section','p22_clearance_section','p25_clearance_section',
 '60t_kp000_overhang_diagram','candidate_comparison','clutch_corridor_comparison']]
DOCS=['README.md','PTO_OFFSET_SPACER_TEST_V001_DESIGN.md','PHYSICAL_MEASUREMENT_SOURCES.md',
 '60T_KP000_CLEARANCE_DERIVATION.md','SPACER_VARIANT_COMPARISON.md','SLIDE_CLUTCH_CORRIDOR_HOLD.md',
 'PHYSICAL_TEST_PLAN.md','PHYSICAL_RESULT_SHEET.md','SOURCE_INTERFACE_AUDIT.md','REFERENCE_ASSEMBLY_LIMITS.md']
REPORTS=['design_parameters.json','validation_report.json','contract_test_report.json','source_authority_audit.json',
 'collision_report.json','physical_result_template.json','repository_audit.json','manifest.json']
EXPECTED=sorted([Path(__file__).name,'tests/test_pto_offset_spacer_test_v001.py','audit_start.json',
 'COMMIT_PATHS.txt','SHA256SUMS.txt',*STEPS,*STLS,*SVGS,*DOCS,*REPORTS])


def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()


def git(*args):
 return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT,stderr=subprocess.PIPE).decode('utf-8').strip()


def tree_hash(path):
 files=sorted(p for p in path.rglob('*') if p.is_file());h=hashlib.sha256()
 for p in files:h.update((p.relative_to(path).as_posix()+'\n').encode());h.update(bytes.fromhex(sha(p)))
 return {'files':len(files),'sha256':h.hexdigest()}


def audit(full=False):
 base=json.loads((LANE/'audit_start.json').read_text(encoding='utf-8'))
 untracked=sorted(p for p in git('ls-files','--others','--exclude-standard','-z').split('\0') if p)
 outside=[p for p in untracked if not p.startswith(REL+'/')]
 own=[p[len(REL)+1:] for p in untracked if p.startswith(REL+'/')]
 state={'repository':str(Path(git('rev-parse','--show-toplevel')).resolve()),'branch':git('branch','--show-current'),
  'head':git('rev-parse','HEAD'),'staged_count':len(git('diff','--cached','--name-only').splitlines()),
  'dirty':{p:sha(ROOT/p) for p in git('diff','--name-only').splitlines()},
  'protected':{p:tree_hash(ROOT/p) for p in base['protected']},'untracked_total':len(untracked),
  'outside_untracked_count':len(outside),'new_path_count':len(own),
  'outside_untracked_paths_sha256':hashlib.sha256(('\n'.join(outside)+'\n').encode()).hexdigest()}
 ok=(Path(state['repository'])==ROOT and state['branch']==BRANCH and state['head']==HEAD and state['staged_count']==0
  and state['dirty']==base['dirty'] and state['protected']==base['protected']
  and len(outside)==base['untracked_count'] and state['outside_untracked_paths_sha256']==base['untracked_paths_sha256'])
 if full:
  h=hashlib.sha256()
  for p in outside:h.update((p+'\n').encode());h.update(bytes.fromhex(sha(ROOT/p)))
  state['outside_untracked_bytes_sha256']=h.hexdigest();ok &= h.hexdigest()==base['untracked_bytes_sha256']
 files=sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob('*') if p.is_file())
 ok &= files==own and set(files).issubset(EXPECTED)
 state['tracked_dirty_count']=len(state['dirty'])
 state['protected_source_changed_count']=sum(state['protected'][p]!=base['protected'][p] for p in base['protected'])
 state['pass']=bool(ok)
 if not ok:raise AssertionError('FAIL_CLOSED '+json.dumps(state))
 return state


def box(x,y,z,center):return cq.Workplane('XY').box(x,y,z).translate(center)
def cyl(d,h,z=0):return cq.Workplane('XY').circle(d/2).extrude(h).translate((0,0,z))
def compound(parts):return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))
def volume(sh):return sum(s.Volume() for s in sh.solids().vals())
def common(a,b):return volume(a.intersect(b))
def distance(a,b):
 d=BRepExtrema_DistShapeShape(a.val().wrapped,b.val().wrapped);d.Perform()
 if not d.IsDone():raise AssertionError('distance failed')
 return d.Value()
def bounds(sh):
 b=sh.val().BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def size(sh):
 b=bounds(sh);return [b[i+3]-b[i] for i in range(3)]


@lru_cache(None)
def old_front():
 spec=importlib.util.spec_from_file_location('read_only_front_v001',ROOT/FRONT/'build_front_interface_dual_pto_20t_v001.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return m


@lru_cache(None)
def source_shape(name):return cq.importers.importStep(str(ROOT/SOURCE_STEP[name]))


def kp_cad():return cq.Workplane(obj=old_front().kp000(0)).translate((0,0,-104))


def kp_physical():
 # Only measured relevant X span is new physical authority. Axial depth17,
 # height35, nominal bore10 and its centered placement remain CAD references.
 return box(KP_PHYSICAL,17,35,(0,0,17.5)).cut(cyl(10,19,-9.5).rotate((0,0,0),(1,0,0),90).translate((0,0,18.5))).clean()


def frame_reference():
 # Select one existing 500x20x40 reference rail. Translate its end to localX0.
 rails=old_front().frame_500_reference().Solids()
 rail=min(rails,key=lambda s:abs(s.Center().y-80.5)+abs(s.Center().z-40))
 return cq.Workplane(obj=rail).translate((-100,-80.5,-20))


def frame_end_excerpt():return frame_reference().intersect(box(80,22,42,(-40,0,20)))


def pulley_envelope():
 # Physical radial max100.1. Axial26 is a DISPLAY/reference extent from
 # v09626, NOT a measured full 3D installed rotating envelope.
 return cyl(PULLEY_PHYSICAL,26)


SEGMENTS={'2':'abged','0':'abcdef','5':'afgcd'}


def digit_cuts(digit,x):
 # Readable seven-segment digits, not font-dependent. Top-face engraving only.
 segments={
  'a':(4.4,1.0,x,3.8),'g':(4.4,1.0,x,0),'d':(4.4,1.0,x,-3.8),
  'b':(1,3.8,x+1.7,1.9),'c':(1,3.8,x+1.7,-1.9),
  'e':(1,3.8,x-1.7,-1.9),'f':(1,3.8,x-1.7,1.9)}
 parts=[box(w,h,.8,(cx,cy,7.8)) for s in SEGMENTS[digit] for w,h,cx,cy in [segments[s]]]
 result=parts[0]
 for p in parts[1:]:result=result.union(p)
 return result.clean()


@lru_cache(None)
def gauge(length):
 if length not in CANDIDATES.values():raise ValueError('not a released test candidate')
 label=str(int(length));sh=box(length,18,8,(length/2,0,4))
 for digit,x in zip(label,(length/2-3.25,length/2+3.25)):sh=sh.cut(digit_cuts(digit,x))
 return sh.clean()


def triplet():return compound([gauge(v).translate((0,i*25,0)) for i,v in enumerate(CANDIDATES.values())])


def reference_board(length):
 # Exploded catalogue, no rigid registration to the physical rover.
 # Only frame-end/gauge contact is a local measurement demonstration.
 return compound([
  frame_end_excerpt(),gauge(length).translate((0,0,12)),
  kp_physical().translate((100,0,0)),
  source_shape('20t_reference').rotate((0,0,0),(1,0,0),90).translate((175,10,20)),
  cyl(10,40).rotate((0,0,0),(1,0,0),90).translate((220,20,20)),
  pulley_envelope().rotate((0,0,0),(1,0,0),90).translate((70,130,50.05)),
  source_shape('60t_existing_cad_reference').rotate((0,0,0),(1,0,0),90).translate((195,130,51)),
  source_shape('candidate_c_drivetrain_reference').translate((320,100,0)),
 ])


@lru_cache(None)
def models():
 m={f'artifacts/pto_offset_spacer_{int(v)}.step':gauge(v) for v in CANDIDATES.values()}
 m['artifacts/pto_offset_gauge_triplet.step']=triplet()
 m.update({f'artifacts/pto_offset_{n.lower()}_reference_assembly.step':reference_board(v) for n,v in CANDIDATES.items()})
 m.update({'artifacts/kp000_physical_reference.step':kp_physical(),
  'artifacts/kp000_existing_cad_reference.step':kp_cad(),
  'artifacts/60t_physical_envelope_reference.step':pulley_envelope(),
  'artifacts/current_frame_end_reference.step':frame_reference(),
  'artifacts/pto_shaft_reference.step':cyl(10,40)})
 m.update({'artifacts/'+n+'.step':source_shape(n) for n in SOURCE_STEP})
 if set(m)!=set(STEPS):raise AssertionError('model inventory')
 return m


def actual_working_length(sh):
 # Read generated BRep faces, not a nominal parameter or merely a whole bbox.
 faces=[f for f in sh.faces().vals() if f.geomType()=='PLANE' and abs(f.normalAt().x)>.999999
  and f.Area()>140]
 if len(faces)!=2:raise AssertionError('two broad unmodified datum faces required')
 faces.sort(key=lambda f:f.Center().x)
 if any(abs(f.Area()-144)>TOL for f in faces):raise AssertionError('working face damage')
 if faces[0].normalAt().dot(faces[1].normalAt())>-.999999:raise AssertionError('nonparallel faces')
 d=BRepExtrema_DistShapeShape(faces[0].wrapped,faces[1].wrapped);d.Perform()
 return {'length_mm':d.Value(),'face_areas_mm2':[f.Area() for f in faces],
  'face_x_mm':[f.Center().x for f in faces],'measurement_patch_y_mm':[-5,5],'measurement_patch_z_mm':[2,6]}


def require_length(sh,requested):
 r=actual_working_length(sh)
 if abs(r['length_mm']-requested)>TOL:raise AssertionError('actual working length differs from request')
 return r


def export_step(sh,path):
 cq.exporters.export(sh,str(path),exportType='STEP');s=path.read_text(encoding='ascii')
 s=re.sub(r"FILE_NAME\(.*?\);",f"FILE_NAME('{path.name}','2000-01-01T00:00:00',(''),(''),'Open CASCADE','CADQUERY','DETERMINISTIC_METADATA');",s,flags=re.S)
 s=re.sub(r'Open CASCADE STEP translator (\d+\.\d+) \d+',r'Open CASCADE STEP translator \1 deterministic',s)
 nums=iter(range(1,100000));s=re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'",lambda _:f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{next(nums)}'",s)
 path.write_text(s,encoding='ascii',newline='\n')


def export_stl(sh,path):
 vertices,triangles=sh.val().tessellate(.02,.08);lines=['solid PTO_PLACEMENT_GAUGE']
 for tri in triangles:
  a,b,c=[vertices[i] for i in tri];n=(b-a).cross(c-a).normalized()
  lines.extend(['  facet normal '+' '.join(f'{v:.12g}' for v in n.toTuple()),'    outer loop'])
  for p in (a,b,c):lines.append('      vertex '+' '.join(f'{v:.9f}' for v in p.toTuple()))
  lines.extend(['    endloop','  endfacet'])
 lines.append('endsolid PTO_PLACEMENT_GAUGE');path.write_text('\n'.join(lines)+'\n',encoding='ascii',newline='\n')


def triangles(path):
 v=[tuple(map(float,s.split()[1:])) for s in path.read_text(encoding='ascii').splitlines() if s.lstrip().startswith('vertex ')]
 if len(v)%3:raise AssertionError('invalid STL vertices')
 return [tuple(v[i:i+3]) for i in range(0,len(v),3)]


def stl_quality(path):
 ts=triangles(path);edges=Counter();wind=Counter();links=defaultdict(list);graph=defaultdict(set);deg=0
 for a,b,c in ts:
  cross=(cq.Vector(*b)-cq.Vector(*a)).cross(cq.Vector(*c)-cq.Vector(*a))
  deg+=int(cross.Length<1e-9 or len({a,b,c})<3)
  for x,y in ((a,b),(b,c),(c,a)):
   k=tuple(sorted((x,y)));edges[k]+=1;wind[k]+=1 if (x,y)==k else -1
   graph[x].add(y);graph[y].add(x)
  for x,y,z in ((a,b,c),(b,c,a),(c,a,b)):links[x].append((y,z))
 badlinks=0
 for pairs in links.values():
  g=defaultdict(set)
  for a,b in pairs:g[a].add(b);g[b].add(a)
  seen=set();stack=[next(iter(g))]
  while stack:
   p=stack.pop()
   if p in seen:continue
   seen.add(p);stack.extend(g[p]-seen)
  badlinks+=int(len(seen)!=len(g) or any(len(n)!=2 for n in g.values()))
 remaining=set(graph);components=[]
 while remaining:
  pts=[];stack=[next(iter(remaining))]
  while stack:
   p=stack.pop()
   if p not in remaining:continue
   remaining.remove(p);pts.append(p);stack.extend(graph[p]&remaining)
  components.append([max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)])
 r={'triangles':len(ts),'connected_components':len(components),'component_bounds_mm':components,
  'bad_edges':sum(v!=2 for v in edges.values()),'bad_winding_edges':sum(v!=0 for v in wind.values()),
  'bad_vertex_links':badlinks,'degenerate_triangles':deg,'duplicate_triangles':len(ts)-len({tuple(sorted(t)) for t in ts})}
 r['watertight']=r['bad_edges']==0;r['manifold']=r['watertight'] and not badlinks
 r['pass']=not any(r[k] for k in ['bad_edges','bad_winding_edges','bad_vertex_links','degenerate_triangles','duplicate_triangles'])
 return r


def stl_working_length(path):
 # End-face triangles actually covering the measurement patch, excluding text.
 ends=[]
 for tri in triangles(path):
  if max(v[0] for v in tri)-min(v[0] for v in tri)<1e-8 and max(v[2] for v in tri)-min(v[2] for v in tri)>1:
   ends.append(tri[0][0])
 if not ends:raise AssertionError('STL datum triangles missing')
 return max(ends)-min(ends)


def source_audit():
 k=kp_cad();s=source_shape('60t_existing_cad_reference');twenty=source_shape('20t_reference')
 return {'interface_proven':False,'structural_load_authority':'NOT_APPROVED',
  'primary_use':'FIT_POSITION_CLEARANCE_TEST_NON_LOAD_BEARING_GAUGE',
  'front_l_bracket':'REJECTED_FOR_CURRENT_PHYSICAL_ASSEMBLY',
  'primary_local_datum':'500_MM_MEMBER_END_FACE_LOCAL_X0',
  'second_mounting_face':'PHYSICAL_IDENTIFICATION_PENDING',
  'direction_of_controlled_installation_offset':'PHYSICAL_CONFIRMATION_PENDING',
  'frame_length_status':'REFERENCE_FRAME_ENVELOPE_DESIGN_CANDIDATE_NOT_PHYSICAL_AUTHORITY',
  'installed_transform':'PHYSICAL_PENDING; do not derive it from front-interface old global origin',
  'kp000':{'physical_span_mm':KP_PHYSICAL,'physical_class':'PHYSICAL_DIRECT_LATEST_USER_TASK',
   'cad_span_actual_mm':size(k)[0],'cad_minus_physical_mm':size(k)[0]-KP_PHYSICAL,
   'cad_source':FRONT+'/build_front_interface_dual_pto_20t_v001.py:kp000',
   'other_reference_dimensions_mm':{'axial_depth':17,'height':35,'axis_height':18.5,'nominal_bore':10},
   'reference_limits':'Simplified housing; mounting holes, collar projection, hole-to-end offsets and current physical pose NOT established'},
  '60t':{'physical_max_mm':PULLEY_PHYSICAL,'physical_class':'PHYSICAL_DIRECT_LATEST_USER_TASK',
   'cad_max_actual_mm':max(size(s)[:2]),'cad_minus_physical_mm':max(size(s)[:2])-PULLEY_PHYSICAL,
   'cad_axial_actual_mm':size(s)[2],'cad_source':SOURCE_STEP['60t_existing_cad_reference'],
   'installed_exact_source_identity':'NOT_PROVEN; latest found v09626 is PROVISIONAL, not an installation record',
   'envelope':'100.1 diameter physical radial reference;26 axial DISPLAY/CAD_REFERENCE_ONLY',
   'not_included':'runout, actual axial stack and installed hardware projections need measurement'},
  '20t':{'source':SOURCE_STEP['20t_reference'],'cad_flange_actual_mm':size(twenty)[0],
   'cad_axial_actual_mm':size(twenty)[2],'latest_observation':'PHYSICAL_FIT_OBSERVATION: relevant ring outside no larger than KP000',
   'new_exact_od_inferred_from_observation':None,'interference_dominant':False,
   'classification':'CURRENT_PHYSICAL_OBSERVATION; source34.8 is earlier independent measurement reference, not inferred here',
   'shaft':'nominal10; source bore measurement9.8 remains distinct; do not claim bore fit from CAD'},
  'shaft_key':{'pto_nominal_diameter_mm':10,'source':PTO20+'/physical_measurements.json',
   'display_length_mm':40,'cut_length':'HOLD_NOT_RELEASED',
   'drive_path':'SHAFT_KEY_MISUMI_GROOVE1_CANDIDATE_C_UNCHANGED',
   'pto_path':'EXISTING_DUAL_SETSCREW_20T_REFERENCE_NOT_MODIFIED',
   'drive_effective_key_mm':16.7,'new_key_or_bore_geometry_created':False},
  'old_shim':{'lane':'cad/common_rover/pto/pto_axial_shim_spacer_test_v001',
   'thicknesses_mm':[.5,1.0],'cross_section_mm':[10.2,13.8],
   'function':'rotating inner-race to PTO pulley axial shim; NOT evidence for20/22/25 placement spacer'},
  'slide_clutch':{'final_envelope':'PHYSICAL_PENDING_CAD_PENDING','solid_created':False,
   'old_servo_idler':'Different ON/OFF mechanism; not a final slide-clutch authority'},
  'source_step_sha256':{p:sha(ROOT/p) for p in SOURCE_STEP.values()},
  'search_terms':['KP000','PTO','20T','60T','front interface','front output','shaft','slide clutch','clutch',
   '500 mm frame','2040','current drivetrain','physical assembly','spacer','axial shim','bearing support'],
  'search_scope':['cad/common_rover/frame','cad/common_rover/pto','cad/common_rover/drivetrain',
   'cad/common_rover/physical_authority','current narrow-frame lane','v09626 60T lane','v0951 DRIVE source'],
  'decisive_evidence':'physical_authority/common_rover_bbox_installed_transform_front_interface_audit_v001/FRONT_INTERFACE_PHYSICAL_STATUS_AUDIT.md: full front-interface registration NOT_PROVEN'}


PAIRS=['60T_TO_KP000','60T_TO_PTO_SHAFT','60T_TO_20T','60T_TO_FRAME','60T_TO_KNOWN_DRIVETRAIN']
ACCESS=['KP000_BOLT','T_NUT','KP000_SETSCREW','20T_SETSCREW','SHAFT_REMOVAL','WRENCH_HEX_KEY',
 '60T_BELT_PATH','20T_BELT_PATH','FUTURE_TENSIONING','PULLEY_REMOVAL']


def candidate_records():
 roles={'P20':'MINIMUM_SPACE_CANDIDATE','P22':'BALANCED_CANDIDATE','P25':'HIGHER_CLEARANCE_CANDIDATE'}
 return [{'id':n,'working_offset_mm':v,'role':roles[n],'nominal_residual_mm':v-OVERHANG,
  'residual_class':'DERIVED_NOMINAL_CLEARANCE_NOT_PHYSICAL_NOT_INSTALLED_CAD',
  'minimum_installed_static_clearance_mm':None,'installed_interference':'HOLD_MISSING_REGISTERED_GEOMETRY',
  'interference_pairs':{p:{'intersection_mm3':None,'minimum_mm':None,'status':'HOLD_MISSING_INSTALLED_TRANSFORMS'} for p in PAIRS},
  'tool_and_service':{p:'HOLD_ACTUAL_INTERFACE_AND_TOOL_PATH_PENDING' for p in ACCESS},
  'available_clutch_corridor_mm':None,'clutch_corridor_status':'DATUM_MEASUREMENTS_PENDING',
  'conditional_corridor_expression':f'C0 - {v:.1f}',
  'conditional_corridor_change_vs_p20_mm':20-v,
  'corridor_condition':'ONLY IF same fixed boundary and positive offset consumes same-axis corridor; direction and C0 unmeasured',
  'pto_axis_local_x_mm':None,'axis_status':'N/A_GAUGE_DOES_NOT_DEFINE_VERIFIED_KP000_ATTACHMENT',
  'physical_selection':'PHYSICAL_TEST_PENDING','structural_status':'NOT_APPROVED'} for n,v in CANDIDATES.items()]


def physical_template():
 fields={'printed_actual_length_mm':None,'static_60t_clearance_mm':None,'minimum_full_rotation_clearance_mm':None,
  'kp000_interference':'PENDING','20t_interference':'PENDING','frame_interference':'PENDING',
  'tool_access':'PENDING','remaining_clutch_corridor_mm':None,'result':'HOLD','photo_id':None}
 return {'member_end_local_datum_used':'PENDING','kp000_flush_to_intended_datum':'PENDING',
  'identified_face_A':None,'identified_face_B':None,'measured_offset_direction':None,
  'independently_secured_assembly':'PENDING','gauges_removed_before_rotation':'PENDING',
  'candidates':{n:dict(fields) for n in CANDIDATES},'selected_shortest_candidate':None,
  'selection_reason':None,'promotion':'PHYSICAL_TEST_PENDING','structural_load_authority':'NOT_APPROVED'}


def geometry_metrics():
 r={}
 for n,v in CANDIDATES.items():
  s=gauge(v);frame=frame_end_excerpt();placed=s.translate((0,0,12))
  a=actual_working_length(s)
  r[n]={**a,'bounds_mm':size(s),'volume_mm3':volume(s),'engraving_removed_mm3':v*18*8-volume(s),
   'bench_frame_gauge_overlap_mm3':common(placed,frame),'bench_frame_gauge_distance_mm':distance(placed,frame),
   'bench_contact_status':'INTENDED_DATUM_DEMONSTRATION_ONLY_NOT_INSTALLATION',
   'measurement_patch_first_layer_avoidance_mm':2.0}
 return {'gauges':r,'working_direction':'GAUGE_LOCAL_X','height_mm':8,'width_mm':18,
  'measurement_face_area_mm2':144,'text_depth_mm':.6,'minimum_text_edge_to_end_mm':4.55,
  'working_chamfer_mm':0,'material':'PETG','support':'OFF','gauge_shaft_hole_count':0,
  'gauge_mounting_hole_count':0,'load_transfer_function':False,
  'kp_physical_reference_actual_x_mm':size(kp_physical())[0],
  '60t_physical_envelope_actual_od_mm':size(pulley_envelope())[0],
  'derived_overhang_mm':OVERHANG,'frame_reference_bounds_mm':size(frame_reference()),
  'frame_end_local_x_mm':bounds(frame_reference())[3],
  'clutch_solid_count':0,'l_bracket_count':0,'triangular_joint_count':0}


def inspect(out):
 steps={};meshes={};actual={}
 for f in STEPS:
  sh=cq.importers.importStep(str(out/f))
  r={'reload':'PASS' if sh.val().isValid() else 'FAIL','solids':len(sh.solids().vals()),'bounds_mm':size(sh)}
  if f in ['artifacts/'+n+'.step' for n in PRINTS]:
   check=BOPAlgo_ArgumentAnalyzer();check.SetShape1(sh.val().wrapped);check.SelfInterMode=True;check.Perform()
   r['self_intersections']=int(check.HasFaulty());
   if r['self_intersections']:raise AssertionError('self-intersection '+f)
  if r['reload']!='PASS':raise AssertionError('invalid STEP '+f)
  steps[f]=r
 for f in STLS:
  q=stl_quality(out/f)
  if not q['pass']:raise AssertionError('bad STL '+f)
  meshes[f]=q
 for n,v in CANDIDATES.items():
  stem=f'artifacts/pto_offset_spacer_{int(v)}'
  a=require_length(cq.importers.importStep(str(out/(stem+'.step'))),v)
  a['stl_working_length_mm']=stl_working_length(out/(stem+'.stl'))
  if abs(a['stl_working_length_mm']-v)>TOL:raise AssertionError('STL length')
  actual[n]=a
 return {'step':steps,'stl':meshes,'actual_working_dimensions':actual}


def regression():
 rows=[]
 with tempfile.TemporaryDirectory(prefix='paddy_pto_gauge_regression_') as td:
  for n,v in CANDIDATES.items():
   p=Path(td)/(n+'.step');export_step(gauge(v),p)
   actual=require_length(cq.importers.importStep(str(p)),v)
   # A separate deliberately too-long BRep must fail actual-face measurement.
   wrong=gauge(v).union(box(.1,18,8,(v+.05,0,4))).clean()
   export_step(wrong,Path(td)/'wrong.step');rejected=False
   try:require_length(cq.importers.importStep(str(Path(td)/'wrong.step')),v)
   except AssertionError:rejected=True
   if not rejected:raise AssertionError('systematic +0.10 regression missed')
   rows.append({'id':n,'actual_mm':actual['length_mm'],'requested_mm':v,'plus010_rejected':rejected})
 return rows


def make_svg(title,subtitle,body,notes):
 text='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">'
 text+='<rect width="1200" height="800" fill="#f8fafc"/><style>text{font-family:Arial,sans-serif;fill:#18334a;font-size:18px}.dim{stroke:#136f93;stroke-width:2;fill:none}.hold{fill:#9c4316}</style>'
 text+=f'<text x="30" y="42" style="font-size:26px">{title}</text><text x="30" y="78">{subtitle}</text>'+body
 for i,line in enumerate(notes):text+=f'<text x="30" y="{645+31*i}">{line}</text>'
 return text+'<text x="30" y="781" style="font-size:14px">PTO OFFSET TEST V001 | NON-LOAD-BEARING GAUGES | PHYSICAL CLEARANCE TEST PENDING</text></svg>'


def svg_cad(sh,x,y,w,h,normal=(0,0,1)):
 frame=cq.Plane((0,0,0),xDir=(1,0,0),normal=normal)
 display=frame.toLocalCoords(sh.val())
 s=cq.exporters.getSVG(display,opts={'width':w,'height':h,'projectionDir':(0,0,1),'showHidden':False,
  'strokeWidth':max(size(sh))/500,'marginLeft':30,'marginTop':25})
 return s[s.index('<svg'):].replace('<svg',f'<svg x="{x}" y="{y}"',1)


def previews():
 out={}
 for n,v in CANDIDATES.items():
  body=svg_cad(gauge(v),40,120,530,450)
  body+=f'<text x="650" y="175">X=0 to X={v:.0f}: exact working length</text><text x="650" y="225">Two end faces: 18 x 8 mm each</text><text x="650" y="275">Top engraving {int(v)}: 0.6 mm deep</text><text x="650" y="325">Measure end patches at Z2..6 mm</text><text x="650" y="390" class="hold">NO mounting holes / NO shaft bore</text><text x="650" y="430" class="hold">NOT a permanent bearing spacer</text>'
  out[f'previews/{n.lower()}_top.svg']=make_svg(n+' — printable placement gauge','Top view; text is absent from the two working end faces.',body,
   ['PETG; flat bottom Z0; support OFF. Check first-layer expansion away from measurement patches.',
    'Identify physical face B and offset direction before using the gauge against member-end datum A.',
    'Secure the assembly independently and REMOVE ALL GAUGES before hand rotation.'])
  body='<rect x="65" y="235" width="300" height="160" fill="#d2dee8" stroke="#18334a"/><text x="80" y="430">Frame-end reference excerpt</text>'
  end=365+v*9
  body+=f'<rect x="365" y="275" width="{v*9}" height="72" fill="#9cd7e7" stroke="#136f93"/><line x1="365" y1="170" x2="365" y2="455" class="dim"/><line x1="{end}" y1="170" x2="{end}" y2="455" stroke="#bd6319" stroke-dasharray="8 5" stroke-width="2"/><line x1="365" y1="205" x2="{end}" y2="205" class="dim"/><text x="{(365+end)/2-28}" y="190">{v:.1f} mm</text><text x="285" y="490">A: LOCAL X0</text><text x="{end+10}" y="240" class="hold">B: gauge face only</text><text x="{end+10}" y="280" class="hold">KP000 mating face not identified</text><text x="{end+10}" y="360">Nominal residual = {v:.0f} - 17 = {v-OVERHANG:.1f} mm</text><text x="{end+10}" y="405" class="hold">Actual 60T minimum clearance: HOLD</text>'
  out[f'previews/{n.lower()}_clearance_section.svg']=make_svg(n+' — datum / clearance interpretation','NOT an installed PTO section. No old global-X or L-bracket datum is used.',body,
   ['Only the two GAUGE faces establish the indicated separation. There is no released KP000 mounting stack.',
    '3 / 5 / 8 mm are derived design references, not physical clearances or installed-CAD PASS results.',
    'PTO axis local X and full-rotation clearance require measured component registration.'])
 r=50.05*3.7;k=33.05*3.7
 body=f'<circle cx="300" cy="355" r="{r}" fill="#fff1df" stroke="#b66516" stroke-width="3"/><rect x="{300-k}" y="315" width="{2*k}" height="80" fill="#c8e1e8" stroke="#136f93"/><line x1="300" y1="150" x2="300" y2="560" stroke="#566776" stroke-dasharray="6 6"/><text x="165" y="585">Centered projection comparison only</text><text x="570" y="200">60T measured maximum: 100.1 mm</text><text x="570" y="250">KP000 measured relevant span: 66.1 mm</text><text x="570" y="315">(100.1 - 66.1) / 2 = 17.0 mm per side</text><text x="570" y="375">PHYSICAL_DERIVED, not a measured gap</text><text x="570" y="450" class="hold">CAD references: 60T 102.0; KP000 67.0 mm</text><text x="570" y="495" class="hold">No proof these centers coincide when installed</text>'
 out['previews/60t_kp000_overhang_diagram.svg']=make_svg('60T / KP000 — measured span comparison','The circle is a radial reference, not exact pulley teeth or a complete runout envelope.',body,
  ['CAD-minus-physical differences: 60T +1.9 mm; KP000 +0.9 mm. Existing source CAD is unchanged.',
   '20T is not dominant by the latest physical observation; no new exact 20T OD is inferred.',
   'Existing 20T reference STEP is retained separately at its earlier measured flange OD34.8 mm.'])
 body=''
 for i,(n,v) in enumerate(CANDIDATES.items()):
  x=30+i*390
  body+=svg_cad(gauge(v),x,140,375,300,normal=(0,-1,1))
  body+=f'<text x="{x+25}" y="460">{n}: {v:.1f} x 18 x 8 mm</text><text x="{x+25}" y="505">Residual reference: {v-OVERHANG:.1f} mm</text><text x="{x+25}" y="550" class="hold">PHYSICAL TEST PENDING</text>'
 out['previews/candidate_comparison.svg']=make_svg('P20 / P22 / P25 — no CAD winner','One-piece PETG gauges; engraved labels do not change working dimensions.',body,
  ['Shortest acceptable candidate is selected only after real registration, tool access and full hand rotation.',
   'Optional triplet STL contains three separate parts, no connecting sprue or shared working surface.',
   'No torque, belt-tension, structural or powered approval is granted.'])
 body='<text x="70" y="155">C0 = measured corridor before the proposed offset (currently UNKNOWN)</text>'
 for i,(n,v) in enumerate(CANDIDATES.items()):
  y=220+i*110
  body+=f'<text x="70" y="{y}">{n}</text><rect x="145" y="{y-24}" width="{v*11}" height="35" fill="#d2dee8"/><text x="470" y="{y}">Offset {v:.0f}; conditional corridor C0 - {v:.0f}</text><text x="470" y="{y+35}" class="hold">Absolute available corridor: PHYSICAL_PENDING</text>'
 body+='<text x="70" y="580" class="hold">NO final clutch solid, width, stroke, tool envelope or clutch-fit PASS.</text>'
 out['previews/clutch_corridor_comparison.svg']=make_svg('Clutch corridor — conditional comparison only','Bars show proposed offset consumed, NOT remaining usable clutch space.',body,
  ['Only if the SAME fixed boundary applies and the offset consumes the SAME axis: P22 loses2, P25 loses5 vs P20.',
   'Offset direction and both corridor boundary faces must be physically identified before using that formula.',
   'Tool access, belt service and shaft withdrawal may dominate; none is proven by a shorter offset alone.'])
 return out


def generate(out):
 (out/'artifacts').mkdir(parents=True,exist_ok=True);(out/'previews').mkdir(exist_ok=True)
 for f,sh in models().items():export_step(sh,out/f)
 for f in STLS:export_stl(models()[f.replace('.stl','.step')],out/f)
 for f,s in previews().items():(out/f).write_text(s+'\n',encoding='utf-8',newline='\n')


def reproduce():
 with tempfile.TemporaryDirectory(prefix='paddy_pto_gauge_reproduce_') as td:
  models.cache_clear();gauge.cache_clear();source_shape.cache_clear();old_front.cache_clear()
  out=Path(td);generate(out)
  r={p:sha(LANE/p)==sha(out/p) for p in STEPS+STLS+SVGS}
 if not all(r.values()):raise AssertionError('reproducibility '+json.dumps(r))
 return {'geometry_and_svg_byte_identical':r,'count':len(r),'pass_count':sum(r.values()),
  'step_policy':'Normalize FILE_NAME, translator PRODUCT counter and NAUO labels only; never alter STEP geometry'}


def documents():
 matrix='|Candidate|Working length mm|Nominal residual mm|Role|Installed clearance / winner|\n|---|---:|---:|---|---|\n'
 for r in candidate_records():matrix+=f"|{r['id']}|{r['working_offset_mm']:.1f}|{r['nominal_residual_mm']:.1f}|{r['role']}|HOLD / PHYSICAL_TEST_PENDING|\n"
 readme=f'''# PTO Front Output Offset Spacer Test V001

{STATUS}

## Important outcome

These are NON-LOAD-BEARING PLACEMENT GAUGES, not permanent structural spacers.
The requested file stems retain `pto_offset_spacer_20/22/25`, but each part only
establishes a directly measurable separation between its two parallel end faces.
Do not install one under a bearing, on a shaft or in a loaded drivetrain.

Repository evidence does not prove the new frame-end/KP000 second mounting face,
offset direction, support load path or installed rigid transforms. The existing
Front Interface V002 is explicitly NOT_PROVEN_MANUFACTURED_OR_INSTALLED. Its
old global coordinates cannot supply those missing measurements.

The user rejects the front L-bracket. Local X0 is the physical member-end face,
not a triangular joint, L-bracket, global vehicle origin or old CAD X value.
The nominal 500 mm member length remains a reference candidate, not promoted
physical authority. Identify the exact mating face B before using a gauge.

{matrix}
Residuals are L - (100.1 - 66.1)/2, not measured or installed-CAD clearances.
No winner is selected. Available clutch corridor and PTO local shaft X remain
N/A / PHYSICAL_PENDING; the gauge alone does not define them.

## Print first

PETG; flat bottom down; support OFF. Individual bounds are 20/22/25 x 18 x 8 mm.
Top engraving is 20/22/25, 0.6 mm deep, clear of both end faces. Measure at
Y=-5..+5 and Z=2..6 mm to avoid first-layer elephant foot. Optional triplet STL
contains three separate gauges; no sprue connects any working surfaces.
Use an actual Bambu A1 slicer review; slicer has NOT been run. No invented print
time or load rating. Inspect both working faces for warp, burrs and parallelism.

Secure the PTO assembly independently. Use gauges only while stopped; REMOVE
ALL GAUGES before any hand rotation. Never operate a motor with these gauges.
If the actual bearing/support cannot be safely secured, keep rotation HOLD.

## Package / verification

15 STEP, 4 printable STL, 9 SVG, source, tests and reports. Reference assembly
STEPs are EXPLODED COMPONENT BOARDS, not a mounted rover or printable assembly.
The 60T physical envelope uses diameter 100.1; its displayed 26 mm axial extent
is from provisional CAD and is NOT a complete measured rotating envelope.
Source 20T and Candidate C/MISUMI geometry are reused as reference only.

Python 3.12.13 / CadQuery 2.8.0. Use -B; do not create cache in protected lanes.

```
python -B build_pto_offset_spacer_test_v001.py --build
python -B tests/test_pto_offset_spacer_test_v001.py
python -B build_pto_offset_spacer_test_v001.py --verify
python -B build_pto_offset_spacer_test_v001.py --zip
```

Builder requires the original protected repository references. It never runs
their builders' write entry points. COMMIT_PATHS is an inventory, not permission
to stage. No BBOX, CBOX, frame, PTO, drivetrain or physical authority was patched.
'''
 design='''# PTO offset gauge design

PRIMARY_USE = FIT / POSITION / CLEARANCE TEST.
STRUCTURAL_LOAD_AUTHORITY = NOT_APPROVED.

Three rectangular one-piece gauges have exact X-direction face separation
20.0, 22.0 and 25.0 mm. Width18 and height8 mm give 144 mm2 per end face.
Both complete end faces are planar, parallel, unchamfered and unlabelled.
The designated measurement patch is Y=-5..+5, Z=2..6 mm on each end.
Do not measure across the engraved top, a first-layer lip or an angled edge.

Top labels use broad 1 mm native CAD strokes, engraved 0.6 mm deep. The smallest
label-to-end distance is 4.55 mm. There is no font/runtime dependency, shaft
bore, keyway, bolt pattern, KP000 mounting seat, 2040 clamping feature or torque
transfer feature. No triangular joint or L-bracket is added. These blocks do
not claim a final two-surface attachment that the sources do not establish.

Gauge-local X0 is its datum face A. For a static setup it can register against
the physically identified member-end face. Face B is the opposite gauge face;
which KP000/support face should register there, and whether that represents the
intended offset, must be physically established before interpreting placement.
The gauge does not define the PTO axis by L+33.05 or any old global coordinate.

Reference physical KP span66.1 and 60T max100.1 are retained without rounding.
All other simplified KP dimensions and the 60T axial extent are explicitly
CAD references. Original source parts are not scaled, overwritten or promoted.

Structural spacers, final support plates, shaft cuts, belt tension, permanent
load paths, powered operation and final slide-clutch design are outside scope.
'''
 sources=f'''# Physical measurement sources

Latest user task:

|Feature|Value|Classification|
|---|---:|---|
|KP000 relevant outside span|66.1 mm|PHYSICAL_DIRECT|
|60T maximum measured outside dimension|100.1 mm|PHYSICAL_DIRECT|
|20T relevant ring outside no larger than KP000|Qualitative only|PHYSICAL_FIT_OBSERVATION|
|Front L-bracket cannot be inserted structurally|Rejected for current assembly|USER_PHYSICAL_ASSEMBLY_DECISION|

Derived per-side overhang = (100.1-66.1)/2 = 17.0 mm, PHYSICAL_DERIVED.
It is not a directly measured gap. Candidate residuals are GEOMETRIC DESIGN
REFERENCES only. No new exact 20T OD is inferred from the qualitative statement.

Repository comparison, measured from loaded CAD:

- KP000 source `{FRONT}/build_front_interface_dual_pto_20t_v001.py` gives
  67 x17 x35 mm; X delta CAD-physical = +0.9 mm. Simplified housing omits
  unmeasured current collar/hardware details. Reference bore10, axis height18.5.
- `{SOURCE_STEP['60t_existing_cad_reference']}` gives 102 x102 x26 mm;
  radial maximum delta CAD-physical = +1.9 mm. This is a PROVISIONAL candidate;
  repository evidence does not identify it as the user's actual installed part.
  Earlier v0951 source is 102 x102 x20 mm, same radial discrepancy.
- `{SOURCE_STEP['20t_reference']}` is an earlier independent physical-envelope
  source, flange34.8, total axial23, measured bore9.8 versus nominal shaft10.
  It is retained unchanged as REFERENCE, not inferred from the latest observation.
- Existing PTO shim lane uses thickness0.5/1.0, ID10.2/OD13.8, only between
  rotating inner-ring and pulley faces. It does not identify this offset interface.
- Physical dimensional authority 2026-09-01 retains drive centers122/123 and
  nominal/PTO target122.5 mm from floor. No installed X/Y transform follows.
- MISUMI shaft/key record retains effective key16.7, original19.7 minus3.0 mm.
  Current exact purchased shaft length remains unresolved. No shaft cut is released.

The new 100.1 mm cylinder is a radial comparison envelope; 26 mm display width
is a CAD-only reference. Runout, current axial hardware and frame-relative axis
registration must be measured to create a conservative installed 3D sweep.
'''
 derivation='''# 60T / KP000 overhang derivation

KP000_PHYSICAL_SPAN = 66.1 mm (PHYSICAL_DIRECT).
60T_PHYSICAL_MAX = 100.1 mm (PHYSICAL_DIRECT).

60T_OVERHANG_RELATIVE_TO_KP000_PER_SIDE = (100.1 - 66.1)/2 = 17.0 mm.
Classification: PHYSICAL_DERIVED, centered projected-envelope comparison.
It does not prove coincident physical centers or a directly measured clearance.

P20 nominal residual = 20 - 17 = 3 mm.
P22 nominal residual = 22 - 17 = 5 mm.
P25 nominal residual = 25 - 17 = 8 mm.

These are DERIVED_NOMINAL_CLEARANCE, not PASS results. Real minimum clearance
depends on offset direction, axis position, asymmetry, axial overlap, runout,
hardware protrusions, bearing orientation and frame registration.
No runout tolerance has been silently invented or included in those values.
Do not infer a full 3D clearance from one scalar outside-span difference.
'''
 variants=f'''# Spacer / gauge variant comparison

{matrix}
All three reuse the same 18 x8 mm end section and independent PETG gauge
construction. Printed working lengths require caliper measurements; CAD does
not compensate by changing requested20/22/25 dimensions.

Actual installed interference, bolt/T-nut/set-screw access, 20T screw access,
shaft withdrawal, wrench/hex-key paths, both belt paths, tensioning and pulley
removal are HOLD for every candidate. Null values in collision_report.json
mean NOT EVALUATED from an installed transform, never zero interference.

No automatic P20 selection. Start static checks at P25 if helpful, then compare
P22 and P20 after safe independent support is established. Select the shortest
candidate that physically passes ALL interference and service checks.
'''
 corridor='''# Slide-clutch corridor — HOLD

SLIDE_CLUTCH_FINAL_ENVELOPE = PHYSICAL_PENDING / CAD_PENDING.
No clutch solid, width, stroke or fabricated tool keep-out is created.
The existing servo sliding-idler ON/OFF study is not a final slide-clutch body.

AVAILABLE_CLUTCH_CORRIDOR for P20, P22, P25 = UNKNOWN (null), not zero.
No current registered pair of opposing corridor boundaries was proven.

Conditional comparison only:

If C0 is a physically measured common pre-offset corridor, and positive offset
consumes that SAME axis against a fixed opposite boundary, then:

- P20: C0 -20 mm.
- P22: C0 -22 mm, 2 mm less than P20.
- P25: C0 -25 mm, 5 mm less than P20.

Those conditions are not physically confirmed. If the offset direction differs,
do not use the formula or its signs. There is NO FINAL_CLUTCH_FIT_PASS.
Measure both corridor faces, offset direction, installed bolt heads and tool
access. A shorter offset is not better if it blocks belt/shaft service.
'''
 plan='''# PTO offset spacer physical test plan

1. Power disconnected; no motor operation. Inspect gauges, large labels, flat
   parallel end faces and absence of stringing/first-layer lips at the patches.
2. Measure each printed working length at three places on the end patches.
   Record actual minimum/maximum and nominal candidate ID; do not assume CAD
   dimensions equal printed dimensions.
3. Identify the physical member-end face A (LOCAL_X0), actual KP000/support
   face B, and the direction of proposed offset. Photograph both contacts.
   Confirm that the working distance represents the intended assembly shift.
   If not identifiable, record HOLD; a gauge is not a structural interpretation.
4. With independent safe support, check the KP000 flush/end relationship.
   Do not use the gauge to carry a bearing or belt load. Do not improvise the
   rejected L-bracket. No shaft-mounted use of these blocks is permitted.
5. Compare P25, P22, P20 statically if convenient. For each measure 60T static
   gap, frame gap, 20T gap, bearing/hardware clearance and clutch-side corridor.
6. Verify KP000 bolts, T-nuts, bearing and20T set screws, wrench/hex-key paths,
   shaft removal, belt paths, future tensioning and pulley removal. Record each
   as PASS/FAIL/HOLD; do not waive service access to select a shorter candidate.
7. Secure the assembly by an independently established safe method. REMOVE ALL
   GAUGES and hands from pinch zones before rotating. If no safe fixture exists,
   DO NOT rotate; keep PHYSICAL_CLEARANCE_TEST_PENDING.
8. Manually rotate the 60T/drivetrain through at least one complete revolution
   per safely established candidate. Stop immediately at contact or binding;
   never force through. Record minimum gap through the full sweep, eccentric
   contact, KP000/20T/frame contact and component movement.
9. Select the SHORTEST candidate with no contact throughout rotation, adequate
   actual service access and best usable clutch corridor. Do not automatically
   prefer P20. If none passes, record NONE and measured reason.

Only actual physical fit evidence may promote PTO_OFFSET_SPACER_PHYSICAL_FIT_PASS
and PTO_OFFSET_SELECTED_LENGTH. That promotion selects an offset dimension;
it does NOT release these non-load-bearing gauges as permanent spacers.
Structural support, shaft cutting, belt tension, powered/torque/field tests
remain separate future tasks. No field-load or PTO-load PASS is created here.
'''
 sheet='''# PTO OFFSET SPACER PHYSICAL TEST — blank result sheet

Date/operator: ____   specimen/print settings: ____
500 mm member end used as local datum: YES / NO / HOLD
KP000 flush to intended datum: YES / NO / HOLD
Face A description/photo: ____
Face B description/photo: ____
Offset direction and sign: ____
Assembly independently secured: YES / NO
All gauges removed before hand rotation: YES / NO

'''
 for n in CANDIDATES:
  sheet+=f'''## {n}

Printed actual length readings: ____ / ____ / ____ mm
Static 60T clearance: ____ mm
Minimum clearance during >=1 full hand revolution: ____ mm
KP000 interference: NONE / YES / HOLD
20T interference: NONE / YES / HOLD
Frame interference: NONE / YES / HOLD
Eccentricity contact / movement: ____
Tool access: PASS / FAIL / HOLD; detail ____
KP000 bolts / T-nuts / bearing set screws / 20T set screws: ____
Shaft removal / wrench / hex-key path: ____
60T belt / 20T belt / tensioning / pulley removal: ____
Remaining usable clutch corridor: ____ mm; boundary faces ____
Result: PASS / FAIL / HOLD; photo ____

'''
 sheet+='''## Final

Selected shortest acceptable candidate: 20 / 22 / 25 / NONE / PENDING
Reason: ____
Physical fit promotion: PENDING
Structural-load authority: NOT_APPROVED
No blank field is a zero-clearance or PASS result.
'''
 interface=f'''# Source / interface audit

Exact second attachment face and current installed transform are NOT PROVEN.

Read-only evidence:

1. `{FRONT2}/DESIGN_AUTHORITY.md`: architecture candidate uses a400 mm beam,
   support plates, bearings at Y50/100, pulley Y130, all physical validation pending.
2. `{FRONT}/build_front_interface_dual_pto_20t_v001.py`: reference rail end is
   old CAD X100 while PTO axis is old CAD X0. A rigid translation cannot turn
   that unvalidated relationship into the user's new flush end/KP000 datum.
3. `cad/common_rover/physical_authority/common_rover_bbox_installed_transform_front_interface_audit_v001/FRONT_INTERFACE_PHYSICAL_STATUS_AUDIT.md`
   expressly says V002 is not proven manufactured/installed and needs registration.
4. Existing narrow-frame upper rail CAD length540 and front reference500 are
   separate candidates. Current physical end face is used; neither stock length
   is promoted or modified.
5. Existing axial shim0.5/1.0 has a different rotating-face function. It cannot
   justify a new20/22/25 shaft ring or a bearing under-block.
6. Existing servo idler clutch study and MISUMI/Candidate C drivetrain have no
   proven rigid transform into the requested new front offset configuration.

Decision: fail closed on structural release, continue only with the user-authorized
placement-gauge fallback. Gauge faces A/B define an exact free separation but
not a bearing axis. There is no guessed shaft hole, bolt pattern, load path,
T-nut contact or permanent bearing seat. See source_authority_audit.json.
'''
 limits='''# Reference assemblies — not installed geometry

P20/P22/P25 reference STEP files are exploded component boards. Only the gauge
touching an80 mm display excerpt of the member-end reference demonstrates a
possible measurement use. The end-face data is X0 locally; frame reference
STEP retains the original500 x20 x40 source-member geometry after translation.

Display locations are NOT physical measurements, proposed PTO centers, or
global vehicle coordinates. Do not measure clearances between catalogue parts.

Included separate parts:

- existing frame reference excerpt and candidate gauge;
- KP000 relevant66.1 span with other source dimensions marked CAD_REFERENCE;
- exact earlier20T physical-envelope source, unchanged;
- nominal10 shaft, display length40 ONLY, no new cut length or keyway;
- measured100.1 radial envelope with26 axial CAD display extent;
- unchanged provisional v09626 60T CAD at102 for discrepancy inspection;
- unchanged Candidate C / MISUMI Groove-1 drivetrain reference.

No fake slide-clutch solid is included. No dimensioned unknown keep-out STEP
is justified. The clutch unknown boundary is explained in SVG/JSON/docs instead.
No new supports, actual fasteners or L-bracket are present. No catalogue-part
collision result is promoted to an installed assembly result.

Required real checks against KP000, shaft,20T, frame and nearby drivetrain are
all present in collision_report.json with null volume/distance and explicit
HOLD_MISSING_INSTALLED_TRANSFORMS. This is NOT a zero-intersection declaration.
Source dimensions alone cannot establish a conservative installed3D clearance.
'''
 return {name:s.rstrip()+'\n' for name,s in zip(DOCS,[readme,design,sources,derivation,variants,corridor,plan,sheet,interface,limits])}


def parameters():
 return {'version':'PTO_FRONT_OUTPUT_OFFSET_SPACER_TEST_V001','status':STATUS,
  'part_class':'NON_LOAD_BEARING_PLACEMENT_GAUGE','structural_load_authority':'NOT_APPROVED',
  'candidates':candidate_records(),'geometry':geometry_metrics(),'source':source_audit(),
  'final_selected_length_mm':None,'slicer':'HOLD_SLICER_NOT_RUN','printer':'BAMBU_A1',
  'powered':'NOT_APPROVED','physical_clearance':'PHYSICAL_TEST_PENDING',
  'global_vehicle_x_used':False,'final_clutch_solid_created':False}


def write_json(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')


def build():
 audit();generate(LANE);q=inspect(LANE);r=regression();repro=reproduce()
 for n,s in documents().items():(LANE/n).write_text(s,encoding='utf-8',newline='\n')
 write_json(LANE/'design_parameters.json',parameters())
 write_json(LANE/'source_authority_audit.json',source_audit())
 write_json(LANE/'physical_result_template.json',physical_template())
 write_json(LANE/'collision_report.json',{'scope':'NO_INSTALLED_TRANSFORM; no false zero clearances','candidates':candidate_records()})
 write_json(LANE/'validation_report.json',{'status':'GENERATED_CONTRACT_PENDING','quality':q,'regression':r,
  'geometry':geometry_metrics(),'reproducibility':repro,'installed_interference':'HOLD_MISSING_INSTALLED_TRANSFORMS'})
 print(json.dumps({'build':'GENERATED_CONTRACT_PENDING','STEP':len(STEPS),'STL':len(STLS),'SVG':len(SVGS),
  'exact_paths':len(EXPECTED),'actual_dimensions':q['actual_working_dimensions'],'reproducibility':repro},indent=2))


def finalize(report):
 if not report['pass']:raise AssertionError('contract failed')
 write_json(LANE/'contract_test_report.json',report)
 data=json.loads((LANE/'validation_report.json').read_text(encoding='utf-8'));data['status']=STATUS
 data['documentation_reproducibility']={n:(LANE/n).read_bytes()==s.encode('utf-8') for n,s in documents().items()}
 if not all(data['documentation_reproducibility'].values()):raise AssertionError('document drift')
 write_json(LANE/'validation_report.json',data)
 write_json(LANE/'manifest.json',{'exact_paths':EXPECTED,'count':len(EXPECTED),'status':STATUS,'lane':REL,
  'printable_files':STLS,'reference_steps_not_printable':[f for f in STEPS if Path(f).stem in REFERENCES]})
 (LANE/'COMMIT_PATHS.txt').write_text('\n'.join(REL+'/'+p for p in EXPECTED)+'\n',encoding='utf-8',newline='\n')
 for name in ('repository_audit.json','SHA256SUMS.txt'):
  if not (LANE/name).exists():(LANE/name).write_text('',encoding='ascii')
 write_json(LANE/'repository_audit.json',audit(full=True))
 (LANE/'SHA256SUMS.txt').write_text(''.join(f'{sha(LANE/p)}  {p}\n' for p in EXPECTED if p!='SHA256SUMS.txt'),encoding='ascii',newline='\n')


def verify():
 state=audit(full=True)
 if sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob('*') if p.is_file())!=EXPECTED:raise AssertionError('exact paths')
 lines=(LANE/'SHA256SUMS.txt').read_text(encoding='ascii').splitlines()
 if len(lines)!=len(EXPECTED)-1:raise AssertionError('hash inventory')
 for line in lines:
  h,p=line.split('  ',1)
  if sha(LANE/p)!=h:raise AssertionError('hash mismatch '+p)
 if not json.loads((LANE/'contract_test_report.json').read_text())['pass']:raise AssertionError('contract not passed')
 for n,s in documents().items():
  if (LANE/n).read_bytes()!=s.encode('utf-8'):raise AssertionError('documentation byte drift')
 q=inspect(LANE);r=reproduce()
 print(json.dumps({'verify':'PASS','audit':state,'quality_count':{'step':len(q['step']),'stl':len(q['stl'])},
  'geometry_and_svg_reproduction':r,'documentation_reproduction':len(DOCS)},indent=2))


def handoff():
 verify();target=Path(r'D:\Downloads')/('Paddy_Swarm_PTO_OFFSET_SPACER_TEST_V001_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
 with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in EXPECTED:z.write(LANE/p,LANE.name+'/'+p)
 with zipfile.ZipFile(target) as z:
  if z.testzip() is not None or sorted(z.namelist())!=sorted(LANE.name+'/'+p for p in EXPECTED):raise AssertionError('ZIP manifest')
  for p in EXPECTED:
   if hashlib.sha256(z.read(LANE.name+'/'+p)).hexdigest()!=sha(LANE/p):raise AssertionError('ZIP bytes')
 print(json.dumps({'zip':str(target),'sha256':sha(target),'members':len(EXPECTED)}))


if __name__=='__main__':
 ap=argparse.ArgumentParser();group=ap.add_mutually_exclusive_group(required=True)
 group.add_argument('--build',action='store_true');group.add_argument('--verify',action='store_true');group.add_argument('--zip',action='store_true')
 args=ap.parse_args()
 if args.build:build()
 elif args.verify:verify()
 else:handoff()
