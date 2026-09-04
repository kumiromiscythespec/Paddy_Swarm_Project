"""Isolated G055/G065 closed-perimeter water dummies; no parent writes.

Coordinates: floor underside Z0, body rim Z28.5, hard-stop/lid underside
Z29.395. The groove belongs to the BODY as in the protected full-box source.
The lid is shared. Only the requested groove bottom changes between bodies.
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
import re
import struct
import subprocess
import tempfile
import zipfile
from datetime import datetime

import cadquery as cq
from cadquery import exporters, importers
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box

ROOT = Path(r'D:\Paddy_Swarm_Project')
LANE = Path(__file__).resolve().parent
REL = LANE.relative_to(ROOT).as_posix()
BRANCH = 'agent/organize-untracked-cad-assets-20260725'
HEAD = '7c149a65053f2292bc4cc0ed06d8941c96852f2b'
PARENT = ROOT/'cad/common_rover/bbox/bbox_compact_field_goldenmate_v003'
SPEC = importlib.util.spec_from_file_location('protected_compact_bbox', PARENT/'build_bbox_compact_field_goldenmate_v003.py')
parent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parent)

VARIANTS = {'G055': 0.55, 'G065': 0.65}
PRIMARY = 'G065'
WALL, FLOOR, LID_T = parent.WALL, parent.FLOOR, parent.LID_T
GAP, CORD, WIDTH = parent.HARDSTOP_GAP, parent.GASKET_CORD, parent.GROOVE_WIDTH
TOL = 1e-6
INNER = (55.0, 53.0)
DEPTH = 25.0
RIM = FLOOR + DEPTH
STOP_Z = RIM + GAP
# Only straight-run lengths are shortened: X by 100 and Y by 16 mm.
# Corner quadrants translate by (+/-50,+/-8); source radii are not scaled.
CONTRACTION = (100.0, 16.0)
OUTER = (160.0-CONTRACTION[0], 74.0-CONTRACTION[1])
GROOVE_INNER = (155.8-CONTRACTION[0], 69.8-CONTRACTION[1])
RADII = {'groove_outer': 6.0, 'groove_inner': 3.9, 'centerline': 4.95,
         'rim_opening': 4.0, 'flange': 8.0, 'lid': 8.0}
FLANGE = (parent.FLANGE_X-CONTRACTION[0], parent.FLANGE_Y-CONTRACTION[1])
PLAN = (parent.LID_X-CONTRACTION[0], parent.LID_Y-CONTRACTION[1])
M4 = [(sx*34.0, sy*34.0) for sx in (-1,1) for sy in (-1,1)]
AUTHORITY_STATUS = '/'.join([
    'SEAL_GEOMETRY_AUDIT_COMPLETE','COUPON_A_ACTUAL_G055_DRY_PASS',
    'COUPON_B_ACTUAL_G065_DRY_PASS','G065_SELECTED_FOR_PRIMARY_WATER_TEST',
    'FULL_BBOX_GROOVE_G050_UNVALIDATED','FULL_BBOX_PRINT_HOLD'])
CAD_STATUS = 'CAD_PASS/CONTRACT_TEST_PASS/G055_G065_WATER_DUMMY_PRINT_READY/WATER_PHYSICAL_TEST_PENDING'
DOCS = ['README.md','COMPACT_SEAL_B_WATER_DUMMY_DESIGN.md','SEAL_GEOMETRY_TRACEABILITY.md',
        'PRINT_INSTRUCTIONS.md','ASSEMBLY_INSTRUCTIONS.md','PHYSICAL_WATER_TEST_PLAN.md',
        'PHYSICAL_RESULT_SHEET.md','PHYSICAL_AUTHORITY_CORRECTION.md']
STEPS = [f'artifacts/water_dummy_{v.lower()}_{part}.step' for v in VARIANTS for part in ('body','assembly','gasket_reference')]
STEPS += ['artifacts/water_dummy_common_lid.step','artifacts/witness_paper_reference.step','artifacts/selected_full_bbox_seal_section_reference.step']
STLS = [f'artifacts/water_dummy_{v.lower()}_body.stl' for v in VARIANTS]+['artifacts/water_dummy_common_lid.stl']
SVGS = [f'previews/{s}.svg' for s in ('water_dummy_top_view','water_dummy_side_section','seal_b_section','corner_gasket_path','m4_compression_layout','witness_paper_location')]
REPORTS = ['design_parameters.json','validation_report.json','contract_test_report.json','printability_report.json',
           'repository_audit.json','manifest.json']
EXPECTED = sorted(['build_water_dummy.py','tests/test_water_dummy.py','audit_start.json','COMMIT_PATHS.txt','SHA256SUMS.txt',*DOCS,*STEPS,*STLS,*SVGS,*REPORTS])

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.PIPE).decode('utf-8').strip()

def audit(full=False):
    baseline=json.loads((LANE/'audit_start.json').read_text())
    paths=sorted(p for p in git('ls-files','--others','--exclude-standard','-z').split('\0') if p and not p.startswith(REL+'/'))
    dirty={p:sha(ROOT/p) for p in git('diff','--name-only').splitlines()}
    protected={p:parent.tree_hash(ROOT/p) for p in baseline['protected']}
    state={'repository':str(Path(git('rev-parse','--show-toplevel')).resolve()),'branch':git('branch','--show-current'),
           'head':git('rev-parse','HEAD'),'staged_count':len(git('diff','--cached','--name-only').splitlines()),
           'dirty':dirty,'outside_untracked_count':len(paths),
           'outside_untracked_paths_sha256':hashlib.sha256('\n'.join(paths).encode()).hexdigest(),
           'protected':protected}
    ok=(Path(state['repository'])==ROOT and state['branch']==BRANCH and state['head']==HEAD
        and state['staged_count']==0 and dirty==baseline['dirty'] and protected==baseline['protected']
        and len(paths)==baseline['untracked_count'] and state['outside_untracked_paths_sha256']==baseline['untracked_paths_sha256'])
    if full:
        h=hashlib.sha256()
        for p in paths:h.update((p+'\n').encode());h.update(bytes.fromhex(sha(ROOT/p)))
        state['outside_untracked_bytes_sha256']=h.hexdigest()
        ok &= h.hexdigest()==baseline['untracked_bytes_sha256']
    actual=sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob('*') if p.is_file())
    ok &= set(actual).issubset(EXPECTED)
    state['lane_path_count']=len(actual)
    state['untracked_total']=len(paths)+len([p for p in git('ls-files','--others','--exclude-standard','-z').split('\0') if p.startswith(REL+'/')])
    state['protected_changed_count']=sum(protected[p]!=baseline['protected'][p] for p in protected)
    state['pass']=bool(ok)
    if not ok: raise RuntimeError('FAIL_CLOSED repository audit '+json.dumps(state))
    return state

def box(*args,**kw): return parent.box(*args,**kw)
def cyl(d,h,xyz): return parent.cyl_z(d,h,xyz)
def rounded(x,y,h,r,z): return parent.rounded_box_xy(x,y,h,r,z)
def ring(outer,inner,h,z): return parent.rounded_ring(*outer,*inner,RADII['groove_outer'],RADII['groove_inner'],h,z)
def volume(shape): return sum(s.Volume() for s in shape.solids().vals())
def common(a,b): return volume(a.intersect(b))
def delta(a,b): return volume(a.cut(b))+volume(b.cut(a))
def bbox(s):
    # Do not let an attached STL tessellation inflate the exact CAD bounds.
    bounds=Bnd_Box();BRepBndLib.AddOptimal_s(s.val().wrapped,bounds,False,False)
    x0,y0,z0,x1,y1,z1=bounds.Get()
    return [round(x1-x0,6),round(y1-y0,6),round(z1-z0,6)]
def distance(a,b):
    d=BRepExtrema_DistShapeShape(a.val().wrapped,b.val().wrapped); d.Perform()
    if not d.IsDone(): raise RuntimeError('distance calculation failed')
    return d.Value()

def self_interference(sh):
    analyzer=BOPAlgo_ArgumentAnalyzer()
    analyzer.SetShape1(sh.val().wrapped)
    analyzer.SelfInterMode=True
    analyzer.Perform()
    if analyzer.HasErrors():raise AssertionError('OCCT self-interference analysis failed')
    return {'faulty':analyzer.HasFaulty(),'fault_count':analyzer.GetCheckResult().Extent()}

@lru_cache(maxsize=None)
def body(depth):
    shell=box(INNER[0]+2*WALL,INNER[1]+2*WALL,RIM,(0,0,RIM/2)).cut(
        box(*INNER,DEPTH+1,(0,0,FLOOR+(DEPTH+1)/2)))
    flange=parent.rounded_ring(*FLANGE,*INNER,RADII['flange'],RADII['rim_opening'],parent.FLANGE_H,RIM-parent.FLANGE_H)
    result=shell.union(flange)
    for x,y in M4:
        result=result.union(cyl(12,8+GAP,(x,y,RIM-8)))
        result=result.cut(cyl(parent.M4_CLEARANCE,10+GAP,(x,y,RIM-9)))
    # Anchor the tool at the EXACT bottom, then overshoot only above the rim.
    # Never center a depth+epsilon tool at a depth-only center.
    return result.cut(ring(OUTER,GROOVE_INNER,depth+0.1,RIM-depth)).clean()

@lru_cache(maxsize=None)
def lid():
    sh=rounded(*PLAN,LID_T,RADII['lid'],0)
    for x,y in M4: sh=sh.cut(cyl(parent.M4_CLEARANCE,LID_T+2,(x,y,-1)))
    return sh.clean()

def closure_lid(): return lid().translate((0,0,STOP_Z))
def witness(): return box(45,40,0.2,(0,0,FLOOR+0.2))

def centerline(z=0):
    return rounded(57.9,55.9,0.1,RADII['centerline'],z-0.1).faces('>Z').val().outerWire()

def gasket(depth):
    path=centerline(RIM-depth+CORD/2)
    profile=cq.Wire.makeCircle(CORD/2,path.positionAt(0),path.tangentAt(0))
    return cq.Workplane(obj=cq.Solid.sweep(profile,[],path,True,False))

@lru_cache(maxsize=None)
def source_body(): return importers.importStep(str(PARENT/'artifacts/compact_field_bbox_body_selected.step'))
@lru_cache(maxsize=None)
def source_lid(): return importers.importStep(str(PARENT/'artifacts/compact_field_bbox_lid_selected.step'))

def source_section():
    straight=box(20,22,13,(40,34,110))
    corner=box(22,22,13,(79,39,110))
    masks=straight.union(corner)
    return parent.compound([source_body().intersect(masks),source_lid().translate((0,0,114.395)).intersect(masks)])

def planar_faces(shape):
    return [f for f in shape.faces().vals() if f.geomType()=='PLANE' and abs(f.normalAt().z)>0.999999]

def probe_surface_z(shape,x,y,zlo,zhi):
    cut=shape.intersect(box(0.1,0.1,zhi-zlo,(x,y,(zlo+zhi)/2)))
    if not cut.solids().vals(): raise AssertionError('probe found no material')
    return cut.val().BoundingBox().zmax

def measure_depth(shape):
    # Independent probes query the actual BRep, not the builder parameter.
    rim=probe_surface_z(shape,0,32,RIM-3,RIM+0.3)
    floor=probe_surface_z(shape,0,27.95,RIM-3,RIM+0.3)
    floors=[f for f in planar_faces(shape) if abs(f.BoundingBox().xlen-OUTER[0])<TOL and abs(f.BoundingBox().ylen-OUTER[1])<TOL]
    if len(floors)!=1: raise AssertionError(f'expected one continuous groove floor; got {len(floors)}')
    if abs(floors[0].Center().z-floor)>TOL: raise AssertionError('face and probe disagree')
    return {'rim_z_mm':rim,'groove_bottom_z_mm':floor,'actual_depth_mm':rim-floor,
            'groove_floor_area_mm2':floors[0].Area(),'groove_floor_wires':len(floors[0].Wires())}

def assert_depth(shape,requested):
    m=measure_depth(shape)
    if abs(m['actual_depth_mm']-requested)>TOL:
        raise AssertionError(f"actual depth {m['actual_depth_mm']:.9f} != requested {requested:.9f}")
    return m

def source_coupon_depth(label):
    sh=importers.importStep(str(PARENT/f'artifacts/compact_seal_coupon_{label}.step'))
    floor=next(f.Center().z for f in planar_faces(sh) if abs(f.Area()-18*WIDTH)<TOL)
    return 8.0-floor

def cylinder_radii(sh):
    return sorted({round(f._geomAdaptor().Cylinder().Radius(),8) for f in sh.faces().vals() if f.geomType()=='CYLINDER'})

def corner_deltas(depth):
    result=[]
    allowed=ring(OUTER,GROOVE_INNER,2,RIM-1)
    for sx in (-1,1):
        for sy in (-1,1):
            mask=box(22,22,5,(sx*29,sy*30,RIM-1.5))
            original=source_body().translate((-sx*50,-sy*8,RIM-113.5)).intersect(mask)
            new=body(depth).intersect(mask)
            result.append(delta(original.cut(allowed),new.cut(allowed)))
    return result

def dry_volume(depth):
    # Closure surrogate fills the cord's sealing boundary; it is NOT a rubber
    # deformation model and never exported as a printable part.
    seal=ring(OUTER,GROOVE_INNER,depth+GAP,RIM-depth)
    closed=body(depth).union(closure_lid()).union(seal).clean()
    air=box(90,90,50,(0,0,20)).cut(closed)
    inside=[s for s in air.solids().vals() if s.isInside(cq.Vector(0,0,FLOOR+1),TOL)]
    if len(inside)!=1 or len(air.solids().vals())!=2:
        raise AssertionError('seal surrogate does not separate a closed internal air region')
    return inside[0].Volume()

def metrics():
    data={}
    for name,depth in VARIANTS.items():
        b=body(depth); g=gasket(depth)
        groove=ring(OUTER,GROOVE_INNER,0.55,RIM-0.55)
        holes=parent.compound([cyl(parent.M4_CLEARANCE,5,(x,y,RIM-1)) for x,y in M4])
        towers=parent.compound([cyl(12,5,(x,y,RIM-1)) for x,y in M4])
        m=assert_depth(b,depth)
        m.update({'requested_depth_mm':depth,'calculated_compression_mm':CORD-depth-GAP,
                  'calculated_compression_percent':100*(CORD-depth-GAP)/CORD,
                  'body_bbox_mm':bbox(b),'lid_bbox_mm':bbox(lid()),
                  'assembled_bbox_mm':bbox(parent.compound([b,closure_lid()])),
                  'rigid_closure_intersection_mm3':common(b,closure_lid()),
                  'm4_hole_edge_to_nominal_cord_mm':distance(holes,g),
                  'tower_to_groove_mm':distance(towers,groove),
                  'corner_delta_outside_requested_groove_mm3':corner_deltas(depth),
                  'internal_dry_volume_mm3':dry_volume(depth),
                  'body_volume_mm3':volume(b),'lid_volume_mm3':volume(lid()),
                  'witness_intersection_mm3':common(witness(),b),
                  'radii_mm':cylinder_radii(b)})
        data[name]=m
    return data

def shapes():
    d={}
    for v,depth in VARIANTS.items():
        prefix=f'artifacts/water_dummy_{v.lower()}'
        d[prefix+'_body.step']=body(depth)
        d[prefix+'_assembly.step']=parent.compound([body(depth),closure_lid(),gasket(depth),witness()])
        d[prefix+'_gasket_reference.step']=gasket(depth)
    d['artifacts/water_dummy_common_lid.step']=lid()
    d['artifacts/witness_paper_reference.step']=witness()
    d['artifacts/selected_full_bbox_seal_section_reference.step']=source_section()
    return d

def export_step(sh,path):
    exporters.export(sh,str(path),exportType='STEP')
    text=path.read_text()
    text=re.sub(r"FILE_NAME\(.*?\);",f"FILE_NAME('{path.name}','2000-01-01T00:00:00',(''),(''),'Open CASCADE','CADQUERY','DETERMINISTIC_HEADER_NOT_BUILD_DATE');",text,flags=re.S)
    # OCCT increments its generic PRODUCT label between exports in one process.
    # Normalize that label only; do not touch topology, geometry or entity IDs.
    text=re.sub(r'Open CASCADE STEP translator (\d+\.\d+) \d+',r'Open CASCADE STEP translator \1 deterministic',text)
    occurrences=iter(range(1,10000))
    text=re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'",lambda _:f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{next(occurrences)}'",text)
    path.write_text(text,encoding='ascii',newline='\n')

def write_json(path,data): path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')

def stl_quality(path):
    raw=path.read_bytes(); count=struct.unpack_from('<I',raw,80)[0]
    if len(raw)!=84+50*count: raise AssertionError('binary STL length mismatch')
    edges=Counter(); winding=Counter(); triangles=[]; vertex_neighbors=defaultdict(list); degenerate=0
    for i in range(count):
        r=struct.unpack_from('<12fH',raw,84+50*i)
        tri=tuple(tuple(round(float(v),7) for v in r[j:j+3]) for j in (3,6,9)); triangles.append(tri)
        a,b,c=tri; u=tuple(b[k]-a[k] for k in range(3));v=tuple(c[k]-a[k] for k in range(3))
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        degenerate+=int(len(set(tri))!=3 or sum(x*x for x in cross)<1e-16)
        for x,y in ((a,b),(b,c),(c,a)):
            key=tuple(sorted((x,y)));edges[key]+=1;winding[key]+=1 if (x,y)==key else -1
        for j,x in enumerate(tri): vertex_neighbors[x].append((tri[(j+1)%3],tri[(j+2)%3]))
    bad_vertices=0
    for pairs in vertex_neighbors.values():
        graph=defaultdict(set)
        for a,b in pairs:graph[a].add(b);graph[b].add(a)
        seen=set(); stack=[next(iter(graph))]
        while stack:
            v=stack.pop()
            if v in seen:continue
            seen.add(v);stack.extend(graph[v]-seen)
        if len(seen)!=len(graph) or any(len(n)!=2 for n in graph.values()):bad_vertices+=1
    duplicate=count-len({tuple(sorted(t)) for t in triangles})
    result={'triangles':count,'bad_edges':sum(n!=2 for n in edges.values()),'bad_winding_edges':sum(n!=0 for n in winding.values()),
            'bad_vertex_links':bad_vertices,'degenerate_triangles':degenerate,'duplicate_triangles':duplicate}
    result['watertight']=result['bad_edges']==0
    result['manifold']=result['watertight'] and bad_vertices==0
    result['pass']=all(result[k]==0 for k in ('bad_edges','bad_winding_edges','bad_vertex_links','degenerate_triangles','duplicate_triangles'))
    return result

def svg(title,body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="720" viewBox="0 0 1100 720">
<rect width="1100" height="720" fill="#f6f8fb"/><style>text{{font-family:Arial,sans-serif;fill:#182d44;font-size:17px}}.small{{font-size:14px}}.body{{fill:#d5e6f5;stroke:#23547c;stroke-width:1}}.seal{{fill:none;stroke:#e19a25;stroke-width:2.1}}.line{{fill:none;stroke:#23547c;stroke-width:1}}</style>
<text x="32" y="43" font-size="28">{title}</text><text x="32" y="73">G065 PRIMARY | G055 COMPARISON | NO CHIMNEY | WATER TEST PENDING</text>{body}
<text x="32" y="689" class="small">Dimensions in mm. Nominal cord is a reference, not a predicted deformed rubber shape.</text></svg>'''

def top_drawing(extra=''):
    s='<g transform="translate(380,360) scale(5,-5)"><rect x="-40" y="-40" width="80" height="80" rx="8" class="body"/><rect x="-27.5" y="-26.5" width="55" height="53" rx="4" fill="#fff" stroke="#23547c" stroke-width="0.5"/><rect x="-28.95" y="-27.95" width="57.9" height="55.9" rx="4.95" class="seal"/>'
    for x,y in M4:s+=f'<circle cx="{x}" cy="{y}" r="6" class="line"/><circle cx="{x}" cy="{y}" r="2.25" fill="#fff" stroke="#23547c" stroke-width="0.5"/>'
    return s+extra+'</g>'

def previews():
    top=top_drawing()
    notes='<text x="640" y="170">External plan: 80 × 80</text><text x="640" y="205">Cavity: 55 × 53 × 25</text><text x="640" y="240">4 × M4, centers ±34 / ±34</text><text x="640" y="275">Groove outer R6 / inner R3.9</text><text x="640" y="310">Cord centerline R4.95</text>'
    section='<g transform="translate(120,590) scale(6,-6)"><path d="M-0 0H62V28.5H58.5V3.5H3.5V28.5H0Z" class="body"/><rect x="-9" y="29.395" width="80" height="8" class="body"/><rect x="8.5" y="3.6" width="45" height="0.2" fill="#b55462"/></g><text x="670" y="235">Lid: 8.0</text><text x="670" y="275">Rim Z28.500</text><text x="670" y="310">Lid underside Z29.395</text><text x="670" y="350">Floor / wall: 3.5</text><text x="670" y="385">Body height: 29.395</text><text x="670" y="420">Assembly height: 37.395</text>'
    gsec='<text x="70" y="160">Groove in BODY; lid underside is flat.</text>'
    for i,(v,depth) in enumerate(VARIANTS.items()):
        x=85+i*520;y=520; k=70
        gsec+=f'<g transform="translate({x},{y}) scale({k},-{k})"><path d="M0 -1.5H5V0H3.55V-{depth}H1.45V0H0Z" class="body"/><rect x="0" y="0.895" width="5" height="0.55" class="body"/><circle cx="2.5" cy="{0.9-depth}" r="0.9" class="seal"/></g><text x="{x}" y="220">{v}: actual depth {depth:.2f}</text><text x="{x}" y="590">Compression reference {CORD-depth-GAP:.3f} mm ({100*(CORD-depth-GAP)/CORD:.2f}%)</text>'
    return dict(zip(SVGS,[svg('Closed water dummy — top view',top+notes),svg('Closed water dummy — side section',section),svg('G055 / G065 actual seal sections',gsec),
        svg('Four real corners — unchanged radius',top+notes+'<text x="640" y="390">Cord length ≈219.102 mm</text><text x="640" y="425">Butt joint on a STRAIGHT run</text>'),
        svg('M4 external compression — 4 corners',top+notes+'<text x="640" y="390">Hard-stop gap 0.895 mm</text><text x="640" y="425">Through-bolts, washers, nuts</text><text x="640" y="460">Holes remain outside pressure seal</text>'),
        svg('Witness paper — clear flat floor',top_drawing('<rect x="-22.5" y="-20" width="45" height="40" fill="#f9e6df" stroke="#b55462" stroke-width="0.5"/>')+'<text x="640" y="210">45 × 40 mm paper reference</text><text x="640" y="250">No paper across gasket</text><text x="640" y="290">No battery / electronics / live wiring</text>')]))

def generate_cad(out):
    (out/'artifacts').mkdir(parents=True,exist_ok=True);(out/'previews').mkdir(exist_ok=True)
    model=shapes()
    for path,sh in model.items():
        if not sh.val().isValid():raise AssertionError('invalid BRep '+path)
        export_step(sh,out/path)
    for path in STLS:
        key=path.replace('.stl','.step');exporters.export(model[key],str(out/path),exportType='STL',tolerance=0.03,angularTolerance=0.08)
    for path,text in previews().items():(out/path).write_text(text,encoding='utf-8',newline='\n')

def inspect(out):
    result={'step':{},'stl':{},'depths':{}}
    for f in STEPS:
        s=importers.importStep(str(out/f));result['step'][f]={'valid':s.val().isValid(),'solids':len(s.solids().vals()),'bbox_mm':bbox(s),'volume_mm3':round(volume(s),6)}
        if f.endswith('_body.step') or f.endswith('_common_lid.step'):
            result['step'][f]['self_interference']=self_interference(s)
            if result['step'][f]['self_interference']['faulty']:raise AssertionError('self-interference '+f)
    for v,d in VARIANTS.items():result['depths'][v]=assert_depth(importers.importStep(str(out/f'artifacts/water_dummy_{v.lower()}_body.step')),d)
    for f in STLS:result['stl'][f]=stl_quality(out/f)
    if not all(x['valid'] for x in result['step'].values()) or not all(x['pass'] for x in result['stl'].values()):raise AssertionError('export quality failed')
    return result

def reproduce():
    with tempfile.TemporaryDirectory(prefix='paddy_seal_dummy_repro_') as tmp:
        out=Path(tmp);body.cache_clear();lid.cache_clear();generate_cad(out);other=inspect(out)
        comparison={f:sha(LANE/f)==sha(out/f) for f in [*STEPS,*STLS,*SVGS]}
    if not all(comparison.values()):raise AssertionError('non-reproducible artifacts '+json.dumps(comparison))
    return {'byte_identical':comparison,'pass_count':sum(comparison.values()),'count':len(comparison),'step_header_policy':'normalized FILE_NAME, generic PRODUCT and occurrence labels; geometry/entity references unchanged','pass':True}

def parameters(data):
    return {'variants':VARIANTS,'primary':PRIMARY,'authority_status':AUTHORITY_STATUS,'cad_status':CAD_STATUS,
        'physical_mapping':{'Coupon_A':{'documented_depth_mm':0.45,'actual_depth_mm':source_coupon_depth('A'),'dry_physical':'PASS'},
                            'Coupon_B':{'documented_depth_mm':0.55,'actual_depth_mm':source_coupon_depth('B'),'dry_physical':'PASS'},
                            'full_body':{'actual_depth_mm':0.50,'physical_seal':'NOT_TESTED'}},
        'dummy':{'plan_mm':PLAN,'cavity_mm':[*INNER,DEPTH],'wall_mm':WALL,'floor_mm':FLOOR,'lid_mm':LID_T,
                 'rim_z_mm':RIM,'lid_bottom_z_mm':STOP_Z,'groove_width_mm':WIDTH,'hard_stop_gap_mm':GAP,'cord_diameter_mm':CORD,
                 'radii_mm':RADII,'m4_centers_mm':M4,'m4_hole_diameter_mm':parent.M4_CLEARANCE,'m4_tower_diameter_mm':12,
                 'parent_straight_run_contraction_mm':CONTRACTION},
        'gasket':{'centerline_perimeter_mm':centerline().Length(),'nominal_cut_length_mm':round(centerline().Length(),2),
                  'rough_cut_then_trim_mm':222.0,'joint_method':'PHYSICAL_OPERATOR_METHOD_PENDING','joint_location':'STRAIGHT_SECTION_NOT_CORNER',
                  'reference':'UNCOMPRESSED_OD1P8; lid overlap is intended elastic interference, not a rigid-part collision'},
        'metrics':data,'external_pressure_boundary_penetrations':0,'chimney':False,
        'full_bbox_print':'HOLD','water_physical_test':'PENDING','cad_depth_tolerance_mm':TOL,
        'promotion':'No existing full-box modification. Physical winner requires a NEW corrected full-box lane.'}

def build():
    audit();generate_cad(LANE)
    exported=inspect(LANE);data=metrics();repro=reproduce()
    write_json(LANE/'design_parameters.json',parameters(data))
    write_json(LANE/'validation_report.json',{'status':'PASS','authority_status':AUTHORITY_STATUS,'geometry':data,'exports':exported,'reproducibility':repro})
    write_json(LANE/'printability_report.json',{'printer':'Bambu A1','build_volume_mm':[256]*3,'body_bbox_mm':bbox(body(0.65)),
        'lid_bbox_mm':bbox(lid()),'body_orientation':'FLOOR_DOWN_OPEN_UP','lid_orientation':'PRINT_SEAL_FACE_UP; invert for assembly',
        'body_support':'EXTERIOR_ONLY_UNDER_TOWERS_AND_FLANGE_IF_REQUIRED; NEVER GROOVE_OR_INNER_SEAL',
        'lid_support':'OFF','slicer':'NOT_RUN_OPERATOR_REVIEW_REQUIRED','tower_underside_z_mm':RIM-8,
        'tower_max_outboard_overhang_beyond_core_mm':[9,10],'flange_overhang_beyond_core_mm':[4,5],
        'body_first_layer_area_mm2':(INNER[0]+2*WALL)*(INNER[1]+2*WALL),'lid_first_layer_area_mm2':volume(lid())/LID_T,
        'warp_risk':'Flat PETG plate: inspect seal-plane flatness; do not force warped parts closed.',
        'first_print':['artifacts/water_dummy_g065_body.stl','artifacts/water_dummy_common_lid.stl']})
    print(json.dumps({'build':'PASS','reproducibility':repro,'geometry':data},indent=2),flush=True)

def indexes():
    missing=[p for p in EXPECTED if not (LANE/p).exists() and p not in {'manifest.json','COMMIT_PATHS.txt','SHA256SUMS.txt'}]
    if missing:raise AssertionError('missing '+str(missing))
    write_json(LANE/'manifest.json',{'paths':EXPECTED,'exact_count':len(EXPECTED),'authority_status':AUTHORITY_STATUS,'cad_status':CAD_STATUS})
    (LANE/'COMMIT_PATHS.txt').write_text('\n'.join(REL+'/'+p for p in EXPECTED)+'\n',encoding='utf-8')
    (LANE/'SHA256SUMS.txt').write_text('\n'.join(f'{sha(LANE/p)}  {p}' for p in EXPECTED if p!='SHA256SUMS.txt')+'\n',encoding='utf-8')

def verify():
    a=audit();i=inspect(LANE);r=reproduce()
    report=json.loads((LANE/'contract_test_report.json').read_text())
    if not report['pass']:raise AssertionError('contract suite failed')
    for line in (LANE/'SHA256SUMS.txt').read_text().splitlines():
        expected,p=line.split('  ',1)
        if sha(LANE/p)!=expected:raise AssertionError('hash mismatch '+p)
    actual=sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob('*') if p.is_file())
    if actual!=EXPECTED:raise AssertionError('path contract failed')
    return {'pass':True,'repository':a,'step_reload_pass':len(i['step']),'stl_pass':len(i['stl']),'reproducibility':r,'paths':len(actual)}

def package():
    verified=verify()
    path=Path(r'D:\Downloads')/('Paddy_Swarm_COMPACT_SEAL_B_WATER_DUMMY_V001_G055_G065_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip')
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in EXPECTED:z.write(LANE/p,'bbox_compact_seal_b_water_dummy_v001/'+p)
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None or len(z.namelist())!=len(EXPECTED):raise AssertionError('ZIP integrity failed')
        for p in EXPECTED:
            if hashlib.sha256(z.read('bbox_compact_seal_b_water_dummy_v001/'+p)).hexdigest()!=sha(LANE/p):raise AssertionError('ZIP bytes differ')
    print(json.dumps({'zip':str(path),'sha256':sha(path),'files':len(EXPECTED),'verify_pass':verified['pass']},indent=2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');ap.add_argument('--verify',action='store_true');ap.add_argument('--audit-full',action='store_true');ap.add_argument('--index',action='store_true');ap.add_argument('--package',action='store_true');a=ap.parse_args()
    if a.build:build()
    if a.audit_full:
        result=audit(True);write_json(LANE/'repository_audit.json',result);print(json.dumps(result,indent=2))
    if a.index:indexes()
    if a.verify:print(json.dumps(verify(),indent=2))
    if a.package:package()

if __name__=='__main__':main()
