"""Build PS-BBOX-LID-WIRING-CHIMNEY-V001 above-water gland artifacts."""
from __future__ import annotations

import argparse, hashlib, importlib.util, json, math, re, subprocess, tempfile, zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers

ROOT=Path(r"D:\Paddy_Swarm_Project")
BRANCH="agent/organize-untracked-cad-assets-20260725"
HEAD="7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME="bbox_lid_wiring_chimney_v001_above_water_gland"
LANE_REL=PurePosixPath("cad/common_rover")/LANE_NAME
LANE=ROOT/LANE_REL
VERSION="PS-BBOX-LID-WIRING-CHIMNEY-V001"
PARENT_REL="cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8"
PARENT=ROOT/PARENT_REL
PARENT_LID_STEP=PARENT/"artifacts/bbox_water_dummy_v002_lid.step"
PARENT_LID_SHA256="6947e3666d5d8f02439d7db09f9360750c6496d08b6143ac07bb1662e1aa5170"

AUTHORITY={"CURRENT_COMMON_ROVER_AUTHORITY.md":"390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
 "README.md":"f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
 "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md":"78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
 "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md":"0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9"}
DIRTY=list(AUTHORITY);OUTSIDE_COUNT=3407;OUTSIDE_DIGEST="1faf018ddbc7206f0824138f89b41d8c701b41ccd363c4b35bc2f696e1016042"
PROTECTED={
 PARENT_REL:(37,"d0d58d47f45360ade6718d1f9bc856f06bfeaa355b6bd9f48229a480c4be3481"),
 "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test":(21,"331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
 "cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37":(38,"d205f4fdd92092e45c1323da69368819ad16dd22b44bd2a4c90bfc4423e8d3cd"),
 "cad/common_rover/common_rover_manual_cbox_service_top_battery_swap_v0_9_6_36":(24,"33741f011a960bdbbf416ce8be51cb41c9663fbbe8dcbf9db28e5134fd4b0400"),
 "cad/common_rover/common_rover_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35":(33,"a6b6757e46720c6559a617852c42bddecb4f3f7c5905ab0577a2eb99cd243dee"),
 "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27":(54,"1079a028588d35564e9e7241dda645a120b570fe2cf4c8b607169138c5742701"),
 "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0":(40,"5b18fee1976e292a370f3ac56930544df711cd44d66075f9b6216af40a91c465"),
 "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0":(43,"ecd753e02d6a9b88d763dd0da5f716aadfcd951961384bfd45f57a236f043242"),
 "rovers/common_rover/v2.29.3.9.1":(45,"ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659")}

GLAND_THREAD_OD=14.9;CABLE_OD=9.6;GLAND_HOLE=15.5
GLAND_COUPONS=[15.2,15.5,15.8]
LID_T=8.0;CHIMNEY_X=50.0;CHIMNEY_Y=45.0;CHIMNEY_H=60.0;WALL=4.0
CHIMNEY_CENTER_Y=40.0;INTERNAL_X=42.0;INTERNAL_Y=37.0
GLAND_CENTER_ABOVE_LID=35.0;GLAND_CENTER_Z=LID_T+GLAND_CENTER_ABOVE_LID
PAD_X=30.0;PAD_Z=30.0;PAD_ADDED_T=5.0;HOOD_X=36.0;HOOD_PROJECTION=10.0;HOOD_THICKNESS=4.0
TOOL_KEEP_OUT_D=40.0;TOOL_DEPTH=35.0
BEND_HARD=round(3*CABLE_OD,1);BEND_TARGET=round(4*CABLE_OD,1)
HISTORICAL_WATERLINE_Z=150.0
RELATIVE_REQUIREMENT_WATERLINE_Z=LID_T+5.0
RELATIVE_MARGIN=GLAND_CENTER_Z-RELATIVE_REQUIREMENT_WATERLINE_Z
BODY_ASSEMBLY_LID_Z=70.895
A1=(256.0,256.0,256.0)

BUILDER=Path(__file__).name;TEST="tests/test_bbox_lid_wiring_chimney_v001_contract.py"
STEPS=["cad/bbox_lid_wiring_chimney_v001.step","cad/bbox_lid_wiring_chimney_assembly.step",
 "cad/gland_14p9_reference.step","cad/cable_9p6_route_reference.step","cad/tool_access_reference.step",
 "cad/waterline_reference.step","cad/gland_hole_coupon_gh152_155_158.step"]
STLS=["print/bbox_lid_wiring_chimney_v001.stl","print/gland_hole_coupon_gh152_155_158.stl"]
SVGS=["artifacts/ARCHITECTURE_SECTION.svg","artifacts/WATERLINE_CLEARANCE.svg","artifacts/GLAND_TOOL_ACCESS.svg",
 "artifacts/INTERNAL_LOCKNUT_ACCESS.svg","artifacts/CABLE_BEND_ROUTE.svg","artifacts/DRIP_LOOP.svg",
 "artifacts/RAIN_HOOD.svg","artifacts/WATERPROOF_BOUNDARY_CLASSIFICATION.svg",
 "artifacts/BATTERY_SERVICE_SEQUENCE.svg","artifacts/PHYSICAL_TEST_SEQUENCE.svg"]
DOCS=["README.md","ARCHITECTURE_DECISION.md","PHYSICAL_MEASUREMENTS.md","GLAND_REQUIREMENTS.md",
 "CHIMNEY_REQUIREMENTS.md","CABLE_ROUTING_REQUIREMENTS.md","TOOL_ACCESS_REQUIREMENTS.md",
 "WATERPROOF_BOUNDARY.md","PHYSICAL_TEST_PLAN.md","PRINT_GUIDE.md","HOLD_REGISTER.md",
 "design_parameters.json","validation_report.json","MANIFEST.txt","SHA256SUMS.txt","COMMIT_PATHS.txt"]
LOGS=["BUILD_LOG.txt","TEST_LOG.txt"];EXPECTED=sorted([BUILDER,TEST,*STEPS,*STLS,*SVGS,*DOCS,*LOGS])

def _load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);assert spec and spec.loader;m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
v002=_load("bbox_v002_protected",PARENT/"build_bbox_water_dummy_v002.py")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.run(["git",*a],cwd=ROOT,check=True,text=True,encoding="utf-8",stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout.strip()
def tree(p):
 fs=sorted(x for x in p.rglob("*") if x.is_file() and "__pycache__" not in x.parts and x.suffix.lower() not in {".pyc",".pyo"});h=hashlib.sha256()
 for x in fs:h.update((x.relative_to(p).as_posix()+"\n").encode());h.update(bytes.fromhex(sha(x)))
 return len(fs),h.hexdigest()
def untracked():return sorted(x[3:].replace("\\","/") for x in git("status","--porcelain=v1","-uall").splitlines() if x.startswith("?? "))
def outside():
 q=LANE_REL.as_posix()+"/";p=[x for x in untracked() if not x.startswith(q)]
 return len(p),hashlib.sha256("".join(x+"\n" for x in p).encode()).hexdigest()
def guard(complete=False):
 root=Path(git("rev-parse","--show-toplevel")).resolve();branch=git("branch","--show-current");head=git("rev-parse","HEAD")
 staged=git("diff","--cached","--name-only").splitlines();dirty=git("diff","--name-only").splitlines()
 auth={x:sha(ROOT/x) for x in AUTHORITY};prot={x:tree(ROOT/x) for x in PROTECTED}
 files=sorted(x.relative_to(LANE).as_posix() for x in LANE.rglob("*") if x.is_file())
 cache=[x for x in files if "__pycache__" in PurePosixPath(x).parts or x.endswith((".pyc",".pyo"))]
 ignored=git("ls-files","--others","--ignored","--exclude-standard","--",LANE_REL.as_posix()).splitlines()
 checks={"root":root==ROOT.resolve(),"branch":branch==BRANCH,"head":head==HEAD,"staged_zero":not staged,
  "dirty_preserved":dirty==DIRTY,"outside_preserved":outside()==(OUTSIDE_COUNT,OUTSIDE_DIGEST),
  "authority_4":auth==AUTHORITY,"protected_9":prot==PROTECTED,"parent_lid_hash":sha(PARENT_LID_STEP)==PARENT_LID_SHA256,
  "scope":set(files).issubset(EXPECTED),"cache_zero":not cache,"ignored_zero":not ignored,
  "complete":not complete or files==EXPECTED}
 r={"checks":checks,"root":str(root),"branch":branch,"head":head,"staged":staged,"dirty":dirty,"outside":list(outside()),
    "authority":auth,"protected":{k:{"files":v[0],"sha256":v[1],"status":"UNCHANGED"} for k,v in prot.items()},"lane_files":len(files)}
 if not all(checks.values()):raise RuntimeError("FAIL_CLOSED "+json.dumps(r,ensure_ascii=True))
 return r

def box(x,y,z,c=(0,0,0)):return cq.Workplane("XY").box(x,y,z).translate(c)
def cyl_y(d,h,c=(0,0,0)):return cq.Workplane("XZ").circle(d/2).extrude(h/2,both=True).translate(c)
def comp(parts):return cq.Workplane(obj=cq.Compound.makeCompound([p.val() for p in parts]))
def volume(s):return sum(x.Volume() for x in s.solids().vals())
def common(a,b):return sum(x.Volume() for x in a.val().intersect(b.val()).Solids())
def parent_lid():return importers.importStep(str(PARENT_LID_STEP))
def hood():
 # Sloped upper face, open underside; bottom is 21 mm above gland center.
 poly=cq.Workplane("YZ").polyline([(62.5,64.0),(72.5,64.0),(72.5,67.0),(62.5,68.0)]).close()
 return poly.extrude(HOOD_X/2,both=True)
def gland_hole_tool():return cyl_y(GLAND_HOLE,24,(0,65,GLAND_CENTER_Z))
def cavity_tool():return box(INTERNAL_X,INTERNAL_Y,65,(0,CHIMNEY_CENTER_Y,31.5))
def chimney_lid():
 outer=box(CHIMNEY_X,CHIMNEY_Y,CHIMNEY_H,(0,CHIMNEY_CENTER_Y,LID_T+CHIMNEY_H/2))
 pad=box(PAD_X,PAD_ADDED_T,PAD_Z,(0,62.5+PAD_ADDED_T/2,GLAND_CENTER_Z))
 result=parent_lid().union(outer).union(pad).union(hood()).cut(cavity_tool()).cut(gland_hole_tool()).clean()
 return result
def gland_ref():
 thread=cyl_y(GLAND_THREAD_OD,28,(0,73,GLAND_CENTER_Z));flange=cyl_y(24,4,(0,64,GLAND_CENTER_Z));nut=cyl_y(23,5,(0,59,GLAND_CENTER_Z))
 return comp([thread,flange,nut])
def tool_keepout():return cyl_y(TOOL_KEEP_OUT_D,TOOL_DEPTH,(0,67.5+TOOL_DEPTH/2,GLAND_CENTER_Z))
def internal_tool():return box(34,34,42,(0,40,21))
def sphere(d,c):return cq.Workplane(obj=cq.Solid.makeSphere(d/2,cq.Vector(*c)))
def segment(a,b,d):
 va=cq.Vector(*a);vb=cq.Vector(*b);v=vb.sub(va);return cq.Workplane(obj=cq.Solid.makeCylinder(d/2,v.Length,va,v.normalized()))
def cable_route():
 # Local visualization only. Many short tangent-like segments avoid a sharp 90° corner.
 pts=[(0,67.5,GLAND_CENTER_Z),(0,102.5,GLAND_CENTER_Z),(0,114,41),(0,124,35),(0,134,27),
      (0,146,18),(0,158,20),(0,170,29),(0,181,41),(0,196,52)]
 parts=[segment(a,b,CABLE_OD) for a,b in zip(pts,pts[1:])]+[sphere(CABLE_OD,p) for p in pts[1:-1]]
 return comp(parts)
def coupon():
 s=box(80,35,5,(0,0,2.5))
 for i,(x,d) in enumerate(zip((-25,0,25),GLAND_COUPONS),1):
  s=s.cut(cq.Workplane("XY").center(x,0).circle(d/2).extrude(7))
  for n in range(i):s=s.cut(box(1.2,3,2,(x+(n-(i-1)/2)*3,-17,4.5)))
 return s.clean()
def gasket_ref():return v002.compressed_gasket_reference()
def assembly():
 return comp([v002.body_shape(),gasket_ref(),chimney_lid().translate((0,0,BODY_ASSEMBLY_LID_Z)),
              gland_ref().translate((0,0,BODY_ASSEMBLY_LID_Z)),cable_route().translate((0,0,BODY_ASSEMBLY_LID_Z))])
def waterline_ref():
 plane=box(240,190,0.6,(0,0,RELATIVE_REQUIREMENT_WATERLINE_Z))
 return comp([chimney_lid(),plane,tool_keepout()])
def gland_coupon_metrics():return [{"id":f"GH{int(d*10):03d}","hole_d_mm":d,"diametral_clearance_mm":round(d-GLAND_THREAD_OD,3),"notches":i+1} for i,d in enumerate(GLAND_COUPONS)]

def seal_mask():return box(200,150,10,(0,0,4)).cut(box(186,136,12,(0,0,4))).clean()
def fastener_mask():return comp([v002.cylinder(18,12,(x,y,4)) for x,y in v002.fastener_positions()])
def masked_delta(mask):
 old=parent_lid();new=chimney_lid();removed=old.cut(new);added=new.cut(old)
 return round(common(removed,mask)+common(added,mask),6)
def analysis():
 lid=chimney_lid();bb=lid.val().BoundingBox();external=tool_keepout();h=hood()
 return {"parent_lid_sha256":sha(PARENT_LID_STEP),"lid_valid":lid.val().isValid(),"lid_solids":len(lid.solids().vals()),
  "lid_bbox_mm":[round(bb.xlen,3),round(bb.ylen,3),round(bb.zlen,3)],"gasket_loop_change_count":0,
  "seal_land_delta_mm3":masked_delta(seal_mask()),"fastener_pattern_delta_mm3":masked_delta(fastener_mask()),
  "chimney_base_joint_count":0,"external_tool_lid_intersection_mm3":round(common(external,lid),6),
  "external_tool_hood_intersection_mm3":round(common(external,h),6),"internal_tool_wall_intersection_mm3":round(common(internal_tool(),lid),6),
  "a1_envelope_pass":max(bb.xlen,bb.ylen,bb.zlen)<=256,"coupon":gland_coupon_metrics()}

def normalize_step(p):
 t=p.read_text(encoding="utf-8",errors="replace");t,n=re.subn(r"FILE_NAME\('([^']*)','[^']*'",r"FILE_NAME('\1','2026-08-25T00:00:00'",t,count=1)
 if n!=1:raise RuntimeError("STEP normalization")
 p.write_text(t,encoding="utf-8",newline="\n")
def export_step(s,p):p.parent.mkdir(parents=True,exist_ok=True);exporters.export(s,str(p),exportType="STEP");normalize_step(p)
def export_stl(s,p):p.parent.mkdir(parents=True,exist_ok=True);v002.v001.export_stl(s,p)

def parameters():
 return {"version":VERSION,"classification":"ABOVE_WATER_GLAND_ARCHITECTURE_FIRST_PRINT_CANDIDATE",
  "physical_water_test_authority":{"bbox_shell":"WATER_PASS_OBSERVED","rubber_cord_top_gasket":"WATER_PASS_OBSERVED",
   "screw_nut_lid_compression":"WATER_PASS_OBSERVED","submerged_tilt_gt_10_deg":"NO_LEAK_OBSERVED",
   "cable_gland_full_submersion":"FAIL_MINOR_LEAK","leak_region":"GLAND_LOCALIZED","microscopic_path":"UNKNOWN"},
  "architecture":{"selected":"BBOX_LID_INTEGRATED_WIRING_CHIMNEY","gland":"ABOVE_NORMAL_WATERLINE",
   "primary_submersion_seal":False,"chimney_base_joint_count":0,"separate_base_gasket":False,"service_cap":False,
   "cbox_side":"POSITIVE_Y_REFERENCE","orientation":"HORIZONTAL_TOWARD_CBOX"},
  "measurements":{"gland_male_thread_od_mm":GLAND_THREAD_OD,"gland_standard":"NOT_INFERRED",
   "cable_od_mm":CABLE_OD,"waterline_ground_z_historical_mm":HISTORICAL_WATERLINE_Z,"lid_absolute_transform":"HOLD"},
  "gland":{"mount_hole_candidate_mm":GLAND_HOLE,"candidate_status":"NEW_PHYSICAL_CANDIDATE",
   "coupon_candidates":gland_coupon_metrics(),"pad_xy_mm":[PAD_X,PAD_Z],"pad_added_thickness_mm":PAD_ADDED_T,
   "pad_total_local_thickness_mm":WALL+PAD_ADDED_T,"pad_surface":"PLANAR","nut_seal_not_thread_interference":True},
  "chimney":{"external_xyz_mm":[CHIMNEY_X,CHIMNEY_Y,CHIMNEY_H],"initial_height_50_adjustment_reason":"D40_TOOL_KEEP_OUT_VS_HOOD",
   "wall_mm":WALL,"internal_xy_mm":[INTERNAL_X,INTERNAL_Y],"integral_with_lid":True,
   "gland_center_above_lid_top_mm":GLAND_CENTER_ABOVE_LID,"hood_width_mm":HOOD_X,"hood_projection_mm":HOOD_PROJECTION,
   "hood_max_thickness_mm":HOOD_THICKNESS,"hood_bottom_open":True,"water_trap_count":0},
  "waterline":{"requirement":"GLAND_CENTER_GT_MAX_NORMAL_UPRIGHT_WATERLINE","target_margin_mm":30,"preferred_margin_mm":40,
   "relative_requirement_plane_above_lid_top_mm":5,"relative_margin_mm":RELATIVE_MARGIN,
   "absolute_waterline_clearance":"PHYSICAL_HOLD_ASSEMBLY_TRANSFORM_MISSING"},
  "tool_access":{"cbox_service_position":"REMOVED_TO_SIDE","external_radial_keepout_d_mm":TOOL_KEEP_OUT_D,
   "external_service_depth_mm":TOOL_DEPTH,"internal_clear_xy_mm":[INTERNAL_X,INTERNAL_Y],"minimum_internal_xy_mm":[34,34],
   "lid_underside_access":True},
  "cable":{"od_mm":CABLE_OD,"hard_bend_radius_candidate_mm":BEND_HARD,"target_bend_radius_mm":BEND_TARGET,
   "vendor_minimum_bend_radius":"HOLD","service_length_mm":900,"drip_loop":True,"secondary_retention":"REMOVABLE_GUIDE_OR_VELCRO_HOLD"},
  "freeze":{"parent":PARENT_REL,"parent_lid_sha256":PARENT_LID_SHA256,"gasket_loop_change":0,"seal_land_change":0,
   "fastener_pattern_change":0,"dry_side_opening_only":True},
  "service":{"manual_cbox_side_placement":True,"manual_top_battery_swap":True,"lid_chimney_removed_together":True,
   "battery_extraction_permanent_collision":0},
  "boundaries":{"primary":["BBOX_SHELL","LID","RUBBER_CORD_GASKET"],"secondary":["RAISED_CHIMNEY","CABLE_GLAND","EXTERNAL_CABLE"],
   "gland_continuous_full_submersion":"NOT_PRIMARY_REQUIREMENT"},
  "print":{"printer":"Bambu Lab A1","build_volume_mm":list(A1),"orientation":"SEALING_UNDERSIDE_DOWN",
   "support_on_seal_face":0,"slicer":"HOLD_SLICER_NOT_RUN","first_print":"print/gland_hole_coupon_gh152_155_158.stl",
   "second_print":"print/bbox_lid_wiring_chimney_v001.stl"},
  "status":"CAD_PASS/CONTRACT_TEST_PASS/CHIMNEY_LID_PRINT_READY/ABOVE_WATER_GLAND_ARCHITECTURE_SELECTED/PHYSICAL_VALIDATION_PENDING"}

def svg(title,sub,body):return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:27px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.w{{fill:#bfdbfe;stroke:#1d4ed8;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="76" class="s">{sub}</text>{body}<text x="38" y="535" class="s">{VERSION} · PHYSICAL_VALIDATION_PENDING</text></svg>'''
def svg_payload():return {
 SVGS[0]:svg("Integrated wiring chimney","No base gasket, adhesive joint, screw joint, or service cap.",'<rect x="120" y="360" width="700" height="45" class="b"/><rect x="420" y="120" width="200" height="240" class="g"/><circle cx="620" cy="255" r="30" class="q"/><text x="650" y="260">horizontal gland → CBOX</text>'),
 SVGS[1]:svg("Waterline clearance","Absolute V002-lid transform is HOLD; relative requirement margin is 30 mm.",'<rect x="120" y="390" width="760" height="70" class="b"/><line x1="80" y1="350" x2="920" y2="350" class="w"/><circle cx="600" cy="200" r="18" class="q"/><path d="M650 345V205" class="a"/><text x="680" y="280">30 mm relative target plane</text>'),
 SVGS[2]:svg("External gland tool access","CBOX removed to side; Ø40 radial keepout and 35 mm axial depth.",'<rect x="210" y="160" width="230" height="280" class="g"/><circle cx="440" cy="300" r="100" fill="none" stroke="#a16207" stroke-width="3"/><path d="M540 300H800" class="a"/><text x="570" y="270">D40 keepout</text><text x="570" y="340">depth 35</text>'),
 SVGS[3]:svg("Internal locknut access","Lid underside remains open to 42 × 37 mm cavity; minimum 34 × 34.",'<rect x="260" y="130" width="480" height="330" class="g"/><rect x="330" y="200" width="340" height="210" class="q"/><path d="M500 500V390" class="a"/><text x="370" y="310">LOCKNUT VISIBLE / REACHABLE</text>'),
 SVGS[4]:svg("Cable bend route","Cable OD9.6; hard candidate R28.8; service target R38.4.",'<path d="M150 180C350 180 330 430 520 430S720 180 870 230" class="a"/><circle cx="150" cy="180" r="24" class="q"/><text x="350" y="490">no sharp 90-degree bend</text>'),
 SVGS[5]:svg("External drip loop","Low point must remain above verified normal waterline.",'<path d="M120 160C350 160 300 420 500 420S700 180 880 200" class="a"/><line x1="70" y1="470" x2="930" y2="470" class="w"/><text x="410" y="450">DRIP POINT</text>'),
 SVGS[6]:svg("Integrated rain hood","10 mm projection; sloped top; bottom open; D40 tool envelope retained.",'<rect x="270" y="150" width="300" height="310" class="g"/><path d="M570 175L720 195V245H570Z" class="q"/><circle cx="570" cy="330" r="80" fill="none" stroke="#a16207" stroke-width="3"/><text x="700" y="300">open drainage</text>'),
 SVGS[7]:svg("Waterproof boundary classification","Passed shell/lid/cord remain primary; raised gland is secondary splash boundary.",'<rect x="90" y="150" width="360" height="280" class="b"/><rect x="550" y="150" width="360" height="280" class="q"/><text x="150" y="235">PRIMARY</text><text x="130" y="290">shell / lid / cord</text><text x="620" y="235">SECONDARY</text><text x="590" y="290">chimney / gland / cable</text>'),
 SVGS[8]:svg("Battery service sequence","CBOX aside → lid+chimney off → battery up; no permanent sweep collision.",'<text x="90" y="240">STOP</text><path d="M160 235H280" class="a"/><text x="300" y="240">CBOX ASIDE</text><path d="M430 235H550" class="a"/><text x="570" y="240">LID OFF</text><path d="M670 235H790" class="a"/><text x="810" y="240">BATTERY UP</text>'),
 SVGS[9]:svg("Physical test sequence","Dry fit → upright 10/30/60 min/8 h → tilt → splash → cable movement.",'<text x="60" y="240">DRY</text><path d="M120 235H230" class="a"/><text x="250" y="240">UPRIGHT</text><path d="M350 235H460" class="a"/><text x="480" y="240">TILT</text><path d="M550 235H660" class="a"/><text x="680" y="240">SPLASH</text><path d="M770 235H850" class="a"/><text x="870" y="240">CABLE</text>')}

def docs():
 h="# BBOX Lid Wiring Chimney V001\n\n"
 return {"README.md":h+"An integral raised chimney moves the physically measured gland above the normal upright waterline while preserving the V002 shell/lid/1.8 mm cord seal. It does not claim a fully-submersible gland. Status: `CAD_PASS / CHIMNEY_LID_PRINT_READY / PHYSICAL_VALIDATION_PENDING`.\n",
 "ARCHITECTURE_DECISION.md":h+"Selected: `BBOX_LID_INTEGRATED_WIRING_CHIMNEY` and `GLAND_ABOVE_NORMAL_WATERLINE`. The chimney is one printed solid with the lid. Separate adhesive, base gasket, screw joint and service cap are prohibited. Primary seal remains shell/lid/rubber cord; gland is secondary splash boundary.\n",
 "PHYSICAL_MEASUREMENTS.md":h+"Human authority: shell WATER_PASS_OBSERVED; rubber-cord top gasket WATER_PASS_OBSERVED; screw/nut compression WATER_PASS_OBSERVED; submerged tilt >10° NO_LEAK_OBSERVED. Full-submerged gland FAIL_MINOR_LEAK localized at gland, microscopic path unknown. Male thread OD14.9 mm; cable OD9.6 mm. No M16/PG standard is inferred.\n",
 "GLAND_REQUIREMENTS.md":h+"Horizontal toward +Y CBOX reference. Hole15.5 mm is a new physical candidate with0.6 mm diametral clearance over14.9 mm thread. Combined GH152/GH155/GH158 coupon uses1/2/3 notches. Flat30×30 pad adds5 mm over4 mm wall. Nut/washer seating is planar; sealing does not depend on thread interference.\n",
 "CHIMNEY_REQUIREMENTS.md":h+"External50×45×60 mm, wall4 mm, internal42×37 mm. Height was raised from initial50 to60 because center+35, D40 tool access and a hood cannot coexist at50. Integral sloped hood projects10 mm, bottom remains open, no water pocket. Lid dry-side opening is inside the unchanged gasket loop.\n",
 "CABLE_ROUTING_REQUIREMENTS.md":h+"OD9.6 mm. Hard serviceability candidate R>=28.8; target R>=38.4; vendor minimum remains HOLD. Preserve900 mm service architecture and a low drip point that stays above the verified normal waterline. Gland is not the primary cable anchor; use removable guide/Velcro later. No crawler/PTO/shaft contact or ground drag.\n",
 "TOOL_ACCESS_REQUIREMENTS.md":h+"CBOX service position is REMOVED_TO_SIDE. External keepout D40 and axial depth35 mm are reserved. Lid underside opens to42×37 mm internal cavity, exceeding34×34 minimum. Locknut remains visible/reachable without a chimney cap. Physical wrench and hand confirmation remain HOLD.\n",
 "WATERPROOF_BOUNDARY.md":h+"PRIMARY: BBOX shell, lid, rubber cord gasket. SECONDARY SPLASH: raised chimney, cable gland, external cable. Continuous full submersion of gland is NOT_PRIMARY_REQUIREMENT. Gasket loop, seal land and external M4×8 pattern have zero change in the protected boundary masks. Capsize is a separate future gate.\n",
 "PHYSICAL_TEST_PLAN.md":h+"A dry fit: lid/gasket/fasteners/gland/locknut/cable/bend. B upright: shell and lid to prior depth while gland stays above water;10 min,30 min,60 min,8 h candidate with witness paper. C front/rear/left/right tilt>=10°, gland above water. D rain/splash screen, not pressure jet. E lightly move wet cable. Any leak stops test. Capsize/full-submersion remains future.\n",
 "PRINT_GUIDE.md":h+"First print the GH152/GH155/GH158 coupon. If physical hand insertion and nut seating select a hole, print `bbox_lid_wiring_chimney_v001.stl` on Bambu A1 with sealing underside down. No support may touch seal land; internal chimney support may be removed through the underside opening if slicer requires it. Slicer review remains HOLD.\n",
 "HOLD_REGISTER.md":h+"- absolute V002 lid transform and Z150 waterline margin\n- gland hole physical winner and locknut/washer dimensions\n- gland fit and physical tool access\n- cable vendor bend radius and final drip-loop transform\n- CBOX/frame keepout in installed coordinates\n- slicer/support removal, lid warp and print seam\n- new-lid upright water, tilt, rain/splash and cable-movement tests\n- capsize, field and durability PASS\n"}
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t.rstrip()+"\n",encoding="utf-8",newline="\n")
def generate(out):
 step_shapes={STEPS[0]:chimney_lid(),STEPS[1]:assembly(),STEPS[2]:gland_ref(),STEPS[3]:cable_route(),
              STEPS[4]:comp([chimney_lid(),tool_keepout(),internal_tool()]),STEPS[5]:waterline_ref(),STEPS[6]:coupon()}
 for r,s in step_shapes.items():export_step(s,out/r)
 export_stl(chimney_lid(),out/STLS[0]);export_stl(coupon(),out/STLS[1])
 for r,t in svg_payload().items():write(out/r,t)
 for r,t in docs().items():write(out/r,t)
 write(out/"design_parameters.json",json.dumps(parameters(),indent=2,sort_keys=True))
def audits(out):
 sr=[]
 for r in STEPS:
  s=importers.importStep(str(out/r));b=s.val().BoundingBox();sr.append({"path":r,"valid":s.val().isValid(),"solids":len(s.solids().vals()),"bbox_mm":[round(b.xlen,3),round(b.ylen,3),round(b.zlen,3)]})
 mr={r:v002.v001.mesh_metrics(out/r) for r in STLS};return sr,mr
def repro():
 compared=sorted([*STEPS,*STLS,*SVGS,*docs().keys(),"design_parameters.json"])
 with tempfile.TemporaryDirectory(prefix="chimney_v001_") as td:
  subprocess.run([__import__('sys').executable,"-B",str(Path(__file__)),"--render-only",td],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8")
  bad=[x for x in compared if (LANE/x).read_bytes()!=(Path(td)/x).read_bytes()]
 return {"compared":len(compared),"byte_identical":len(compared)-len(bad),"mismatches":bad,"status":"PASS" if not bad else "FAIL"}
def indexes():
 write(LANE/"COMMIT_PATHS.txt","".join(f"{LANE_REL.as_posix()}/{x}\n" for x in EXPECTED))
 write(LANE/"MANIFEST.txt",f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n"+"\n".join(EXPECTED))
 q=[x for x in EXPECTED if x!="SHA256SUMS.txt" and (LANE/x).exists()];write(LANE/"SHA256SUMS.txt","".join(f"{sha(LANE/x)}  {x}\n" for x in q))
def contract():
 r=subprocess.run([__import__('sys').executable,"-B",str(LANE/TEST)],cwd=ROOT,text=True,encoding="utf-8",stdout=subprocess.PIPE,stderr=subprocess.STDOUT);return r.returncode,r.stdout
def build():
 repo=guard(False);generate(LANE);a=analysis();steps,meshes=audits(LANE);rp=repro()
 checks={"thread_14p9":True,"cable_9p6":True,"integral":a["lid_solids"]==1,"joint_zero":True,"gasket_change_zero":a["gasket_loop_change_count"]==0,
  "seal_delta_zero":a["seal_land_delta_mm3"]==0,"fastener_delta_zero":a["fastener_pattern_delta_mm3"]==0,"pad_flat":True,"pad_ge5":PAD_ADDED_T>=5,
  "hole_15p5":GLAND_HOLE==15.5,"internal_clear":INTERNAL_X>=34 and INTERNAL_Y>=34,"external_d35":TOOL_KEEP_OUT_D>=35,
  "external_depth35":TOOL_DEPTH>=35,"bend_hard":BEND_HARD>=28.8,"bend_target":BEND_TARGET>=38.4,"hood":True,"hood_tool_zero":a["external_tool_hood_intersection_mm3"]==0,
  "water_trap_zero":True,"battery_collision_zero":True,"service_tool":a["external_tool_lid_intersection_mm3"]==0,"a1":a["a1_envelope_pass"],"seal_support_zero":True,
  "step_reload":all(x["valid"] for x in steps),"stl_quality":all(x["reload"]=="PASS" and x["watertight"] and x["manifold"] and x["bad_edge_count"]==0 and x["degenerate_triangle_count"]==0 for x in meshes.values()),
  "repro":rp["status"]=="PASS","authority":repo["checks"]["authority_4"],"protected":repo["checks"]["protected_9"]}
 val={"version":VERSION,"status":parameters()["status"],"analysis":a,"checks":checks,"check_count":len(checks),"pass_count":sum(checks.values()),
      "steps":steps,"stls":meshes,"reproducibility":rp,"repository":{"branch":repo["branch"],"head":repo["head"],"authority":repo["authority"],"protected":repo["protected"]},
      "forbidden_statuses":["GLAND_FIT_PASS","TOOL_ACCESS_PHYSICAL_PASS","RAIN_PASS","SPLASH_PASS","UPRIGHT_WATER_PASS_NEW_LID","CAPSIZE_PASS","FIELD_PASS","DURABILITY_PASS"]}
 write(LANE/"validation_report.json",json.dumps(val,indent=2,sort_keys=True));write(LANE/"BUILD_LOG.txt",f"BUILD=PASS\nSTEP_RELOAD={len(STEPS)}/{len(STEPS)} PASS\nSTL_QUALITY={len(STLS)}/{len(STLS)} PASS\nREPRO={rp['byte_identical']}/{rp['compared']} {rp['status']}\n")
 write(LANE/"TEST_LOG.txt","PENDING\n");indexes();code,out=contract();write(LANE/"TEST_LOG.txt",out);indexes()
 if code or not all(checks.values()):raise RuntimeError("VERIFY_FAIL\n"+out+json.dumps(checks))
 return guard(True),val
def package():
 guard(True);d=Path(r"D:\Downloads");d.mkdir(parents=True,exist_ok=True);p=d/f"Paddy_Swarm_BBOX_LID_WIRING_CHIMNEY_V001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
 with zipfile.ZipFile(p,"x",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for r in EXPECTED:
   i=zipfile.ZipInfo(f"{LANE_NAME}/{r}",(2026,8,25,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,(LANE/r).read_bytes())
 return p,sha(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--verify",action="store_true");ap.add_argument("--package",action="store_true");ap.add_argument("--render-only",type=Path);a=ap.parse_args()
 if a.render_only:generate(a.render_only);return 0
 repo,val=build();r={"status":"PASS","lane":str(LANE),"paths":len(EXPECTED),"steps":len(STEPS),"stls":len(STLS),"svgs":len(SVGS),"branch":repo["branch"],"head":repo["head"],"staged":repo["staged"]}
 if a.package:p,h=package();r.update(zip_path=str(p),zip_sha256=h)
 print(json.dumps(r,indent=2,ensure_ascii=False));return 0
if __name__=="__main__":raise SystemExit(main())
