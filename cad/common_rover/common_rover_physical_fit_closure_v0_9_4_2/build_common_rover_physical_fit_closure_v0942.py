#!/usr/bin/env python3
"""Build v0.9.4.2 physical-fit test artifacts (not production parts)."""
from __future__ import annotations
import argparse,hashlib,json,math,struct,subprocess,sys,tempfile,zipfile
from datetime import datetime
from pathlib import Path,PurePosixPath
from typing import Any
import cadquery as cq

VERSION="0.9.4.2"; CLASSIFICATION="PHYSICAL_FIT_VALIDATION_PREPARATION"; RELEASE="HOLD"
FINAL_STATUS="PHYSICAL_FIT_TEST_ARTIFACTS_COMPLETE / USER_PHYSICAL_TEST_PENDING"
REPO_ROOT=Path(r"D:\Paddy_Swarm_Project"); LANE_REL="cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2"; LANE=Path(__file__).resolve().parent
P1_REL="cad/common_rover/common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1"; P1=REPO_ROOT/P1_REL
P0_REL="cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0"; P0=REPO_ROOT/P0_REL
EXPECTED_BRANCH="agent/organize-untracked-cad-assets-20260725"; EXPECTED_HEAD="facb4f63c0d485a53fef48b602f97e0454e8548f"; BASE_OUTSIDE_UNTRACKED=1344
DOWNLOADS=Path(r"D:\Downloads"); ZIP_PREFIX="Paddy_Swarm_Common_Rover_Physical_Fit_Closure_v0_9_4_2_"
AUTHORITY_HASHES={"CURRENT_COMMON_ROVER_AUTHORITY.md":"390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9","README.md":"f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849","docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md":"78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0","rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md":"0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9"}
P1_HASHES={"MANIFEST.txt":"879697e31b9ab4595c2c13c17741ca46e6d14d6137de4d0cac91cc32b90397e5","SHA256SUMS.txt":"9446ff0205256762757396be582c8cbb46b3c2131aa8d150903e8b1297ac26aa","geometry_manifest.json":"99bf05d5c13cb958983f3c2c8c167f2bc7d62ec254d9fef19f3c811384355451","validation_report.json":"9f79843e750884f96c9aa04dc123a87b8c6e006fa2c5f50be652abe453c74c53","build_common_rover_190mm_integration_v0941.py":"fb9cf99aec4275cdc8b1f0fe548826e3be10a8e9fabecb745b616bd736ebe425","tests/test_common_rover_190mm_integration_v0941.py":"5cb0c1e034a8e03d4d5f15e5f9f6fe4aa62cc494fa2c4d97bb75c9a4faabd598"}
P0_HASHES={"MANIFEST.txt":"fbb9d00eda9dda979e3dfcb4596d987260fc79dd6f0160cdf40512fbf438a984","SHA256SUMS.txt":"0bfd7afed7b19543e811a1e08bb98aa8c8151a46465d3254702361ea50794fe5"}
DOCS=["README.md","PHYSICAL_FRAME_150_RECORD.md","FRAME_MEASUREMENT_LEDGER.md","FRAME_Z_DATUM_CONFLICT_UPDATE.md","BATTERY_INSERTION_CLEARANCE.md","H25A1_2S_PHYSICAL_TEST_PLAN.md","H25A1_COLLAR_COUPON_SPEC.md","H25A1_REACTION_COUPON_SPEC.md","H25A1_STATIC_FIXTURE_SPEC.md","BBOX_DUMMY_SPEC.md","BBOX_DUMMY_TEST_PLAN.md","BBOX_150_VS_190_DECISION_GATE.md","MISSING_MEASUREMENTS.md","DESIGN_GATE.md"]
JSONS=["dimensions.json","interfaces.json","test_limits.json","measurement_ledger.json","geometry_manifest.json","validation_report.json"]
CAD=["cad/frame_150_physical_reference.step","cad/battery_reference.step","cad/bbox_dummy_180x114x103.step","cad/bbox_dummy_180x114x103.stl","cad/bbox_dummy_shim_plus2.stl","cad/bbox_dummy_shim_plus4.stl","cad/bbox_dummy_assembly.step","cad/bbox_dummy_bottom_frame.stl","cad/bbox_dummy_top_frame.stl","cad/bbox_dummy_corner_posts_x4.stl","cad/bbox_dummy_removal_envelope.step","cad/bbox_rail_width_gauges_130_132_134.step","cad/bbox_rail_width_gauges_130_132_134.stl","cad/collar_reference.step","cad/collar_fit_coupon_160_161_162.step","cad/collar_fit_coupon_160_161_162.stl","cad/dual_reaction_coupon_41_42_43.step","cad/dual_reaction_coupon_41_42_43.stl","cad/static_reaction_test_fixture.step","cad/static_reaction_test_fixture.stl"]
DRAWINGS=["drawings/frame_top.svg","drawings/frame_side.svg","drawings/frame_front.svg","drawings/FRAME_PHYSICAL_150_TOP.svg","drawings/FRAME_PHYSICAL_150_SIDE.svg","drawings/FRAME_PHYSICAL_150_FRONT.svg","drawings/battery_insertion_section.svg","drawings/bbox_dummy_removal.svg","drawings/h25a1_coupon_map.svg","drawings/h25a1_static_fixture.svg"]
SOURCE=["build_common_rover_physical_fit_closure_v0942.py","tests/test_common_rover_physical_fit_closure_v0942.py"]
RELEASE_FILES=["MANIFEST.txt","SHA256SUMS.txt","COMMIT_PATHS.txt","BUILD_LOG.txt","TEST_LOG.txt"]
PACKAGE_PATHS=sorted(DOCS+JSONS+CAD+DRAWINGS+SOURCE+RELEASE_FILES)

FRAME={"upper_outer_x":540.0,"upper_outer_y":181.0,"lower_outer_x":442.0,"lower_outer_y":181.0,"structural_height":150.0,"upper_clear_x":500.0,"upper_clear_y":100.0,"lower_clear_x":400.0,"lower_clear_y":140.0,"vertical_2020":110.0,"tolerance":1.0,"status":"REOPENED_PRIMARY_COMPACT_BASELINE"}
Z_RECORD={"absolute_frame_z":"HOLD","ground_to_bottom_measured":68.0,"derived_top":218.0,"later_reported_top":212.0,"conflict":6.0,"previous_internal_z":90.7,"previous_internal_z_classification":"VALID_MEASUREMENT_DIFFERENT_DATUM","previous_internal_z_use":"DO_NOT_USE_AS_BBOX_INSERTION_HEIGHT","battery_insertion_clear_height":108.0,"battery_insertion_clear_classification":"MEASURED"}
BATTERY={"maker":"GOLDENMATE","chemistry":"LiFePO4","voltage":12.8,"capacity_ah":10.0,"energy_wh":128.0,"x":150.9,"y":99.4,"z":92.5,"mass_kg":1.2,"label_claim":"IP67","terminals":"PRESENT","with_terminals_in_108_passage":"PHYSICAL_PASS_USER_REPORTED"}
DUMMY={"x":180.0,"y":114.0,"z":103.0,"shims":[2.0,4.0],"test_heights":[103.0,105.0,107.0],"nominal_clearances":[5.0,3.0,1.0],"construction":"SPLIT_SKELETON_GAUGE","removal":"-X","physical_fit":"PENDING_USER_TEST","waterproof":False}
COLLAR={"od":15.9,"id":10.1,"width":3.0,"pockets":[16.0,16.1,16.2],"type":"SOLID_SET_SCREW_SHAFT_COLLAR"}
SCREWS={"nominal":"M4","quantity":2,"angle":90.0,"major_od":3.8,"length":4.0,"projection":1.0,"radial_keepout":8.95,"pitch":"HOLD"}
REACTION={"slots":[4.1,4.2,4.3],"fixture_slot":4.2,"candidate":"A2_DUAL_REPLACEABLE_REACTION_KEY","final":"HOLD_PHYSICAL_TEST"}
BEARING={"od":25.9,"seat":26.0,"central_clearance":12.0}; KP000={"mount_hole_center":53.0,"policy":"INHERITED_NO_NEW_MANUFACTURING_CAD"}
SPROCKET={"teeth":12,"phase":15.0,"spacing":30.0,"tip_radius":33.07,"root_radius":29.47,"tip_width":7.5,"root_width":9.5,"axial_width":44.0,"pitch_diameter":76.3943726841,"root_overlap":4.0,"external_difference":0.0}

def git(*a:str)->str:return subprocess.check_output(["git",*a],cwd=REPO_ROOT,text=True,encoding="utf-8").strip()
def sha(p:Path)->str:
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def write(p:Path,s:str)->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.rstrip()+"\n",encoding="utf-8",newline="\n")
def write_json(p:Path,v:Any)->None:write(p,json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True))
def box(x:float,y:float,z:float,cx=0.,cy=0.,cz=0.)->cq.Workplane:return cq.Workplane("XY").box(x,y,z).translate((cx,cy,cz))
def cylinder(r:float,h:float,x=0.,y=0.,z=0.,direction=(0,0,1))->cq.Workplane:return cq.Workplane(obj=cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(*direction)))
def comp(parts:list[Any])->cq.Compound:
 vals=[]
 for p in parts:vals.extend(p.vals() if isinstance(p,cq.Workplane) else (p.Solids() if isinstance(p,cq.Compound) else [p]))
 return cq.Compound.makeCompound(vals)
def export(s:Any,p:Path)->None:p.parent.mkdir(parents=True,exist_ok=True);cq.exporters.export(s,str(p))
def audit_dir(root:Path,expected_count:int,expected:dict[str,str])->dict[str,Any]:
 files=[p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts];actual={k:sha(root/k) for k in expected};return {"path":root.relative_to(REPO_ROOT).as_posix(),"file_count":len(files),"hashes":actual,"status":"CAD_PASS" if len(files)==expected_count and actual==expected else "FAIL"}
def authority_audit()->dict[str,Any]:
 actual={k:sha(REPO_ROOT/k) for k in AUTHORITY_HASHES};return {"hashes":actual,"status":"CAD_PASS" if actual==AUTHORITY_HASHES else "FAIL"}
def repository_guard(complete=False)->dict[str,Any]:
 root=Path(git("rev-parse","--show-toplevel")).resolve();branch=git("branch","--show-current");head=git("rev-parse","HEAD");tracked=sorted(git("diff","--name-only").splitlines());staged=sorted(git("diff","--cached","--name-only").splitlines());untracked=sorted(git("ls-files","--others","--exclude-standard").splitlines());lane=sorted(x[len(LANE_REL)+1:] for x in untracked if x.startswith(LANE_REL+"/"));outside=[x for x in untracked if not x.startswith(LANE_REL+"/")];ignored=git("ls-files","--others","-i","--exclude-standard","--",LANE_REL).splitlines();forbidden=[p for p in LANE.rglob("*") if p.is_file() and (p.suffix.lower() in {".pyc",".dxf",".3mf",".gcode"} or "__pycache__" in p.parts)]
 checks={"root":root==REPO_ROOT.resolve(),"branch":branch==EXPECTED_BRANCH,"head":head==EXPECTED_HEAD,"tracked_preserved":set(tracked)==set(AUTHORITY_HASHES),"staged_zero":not staged,"outside_untracked":len(outside)==BASE_OUTSIDE_UNTRACKED,"lane_scope":set(lane).issubset(PACKAGE_PATHS),"lane_complete":set(lane)==set(PACKAGE_PATHS) if complete else True,"authority":authority_audit()["status"]=="CAD_PASS","parent1":audit_dir(P1,68,P1_HASHES)["status"]=="CAD_PASS","parent0":audit_dir(P0,43,P0_HASHES)["status"]=="CAD_PASS","ignored_zero":not ignored,"forbidden_zero":not forbidden}
 if not all(checks.values()):raise RuntimeError({"guard":checks,"tracked":tracked,"staged":staged,"outside":len(outside),"lane":lane,"ignored":ignored,"forbidden":[str(p) for p in forbidden]})
 return {"root":str(root),"branch":branch,"head":head,"tracked":tracked,"staged":staged,"untracked_total":len(untracked),"outside_untracked":len(outside),"lane_untracked":len(lane),"checks":checks,"status":"CAD_PASS"}

def frame150()->cq.Compound:
 parts=[]
 for y in (-80.5,80.5):parts += [box(442,20,40,0,y,88),box(540,20,20,49,y,208)]
 for x in (-211,211):parts.append(box(20,181,20,x,0,78))
 for x in (-211,309):parts.append(box(20,181,20,x,0,208))
 for x in (-211,211):
  for y in (-80.5,80.5):parts.append(box(20,20,110,x,y,163))
 return comp(parts)
def battery()->cq.Workplane:return box(150.9,99.4,92.5,0,0,46.25)
POST_X=84.;POST_Y=51.;FRAME_T=6.;POST_SIDE=8.;POST_LENGTH=97.;SOCKET=8.3
def perimeter(z0:float,top:bool)->cq.Workplane:
 p=box(180,114,6,0,0,z0+3).cut(box(164,98,8,0,0,z0+3))
 for x in (-POST_X,POST_X):
  for y in (-POST_Y,POST_Y):
   cutz=z0+1.5 if top else z0+4.5;p=p.cut(box(SOCKET,SOCKET,3.2,x,y,cutz))
 return p.clean()
def vertical_posts()->cq.Compound:return comp([box(8,8,97,x,y,51.5) for x in (-POST_X,POST_X) for y in (-POST_Y,POST_Y)])
def skeleton()->cq.Compound:return comp([perimeter(0,False),perimeter(97,True),vertical_posts()])
def post_print_plate()->cq.Compound:return comp([box(97,8,8,0,y,4) for y in (-18,-6,6,18)])
def shim(h:float)->cq.Workplane:
 p=box(180,114,h,0,0,h/2).cut(box(164,98,h+2,0,0,h/2));return p.clean()
def bbox_exploded()->cq.Compound:return comp([perimeter(0,False),perimeter(97,True),vertical_posts(),shim(2).translate((0,0,110)),shim(4).translate((0,0,120))])
def removal_envelope()->cq.Compound:return comp([box(380,114,103,-200,0,51.5),box(380,114,4,-200,0,105)])
def rail_gauges()->cq.Compound:
 parts=[]
 for x,w in zip((-70,0,70),(130.,132.,134.)):
  parts += [box(60,8,3,x,-w/2+4,1.5),box(60,8,3,x,w/2-4,1.5),box(8,w,3,x-26,0,1.5)]
 return comp(parts)
def collar()->cq.Compound:
 ring=cq.Workplane("XY").circle(15.9/2).circle(10.1/2).extrude(3);sx=cylinder(1.9,4,5.05,0,1.5,(1,0,0));sy=cylinder(1.9,4,0,5.05,1.5,(0,1,0));return comp([ring,sx,sy])
def raised(text:str,x:float,y:float,z:float)->cq.Workplane:return cq.Workplane("XY").text(text,3.5,.8,halign="center",valign="center").translate((x,y,z))
def collar_coupon()->cq.Workplane:
 p=box(72,28,6,0,0,3)
 for x,d,t in zip((-24,0,24),(16.,16.1,16.2),("160","161","162")):
  p=p.cut(cylinder(d/2,8,x,2,-1));p=p.union(raised(t,x,-9,5.8))
 return p.clean()
def reaction_coupon()->cq.Workplane:
 p=box(72,28,6,0,0,3)
 for x,w,t in zip((-24,0,24),(4.1,4.2,4.3),("41","42","43")):
  p=p.cut(box(w,12,8,x,10,4));p=p.union(raised(t,x,-8,5.8))
 return p.clean()
def static_fixture()->cq.Workplane:
 p=box(50,50,8,0,0,4).cut(cylinder(10.5/2,10,0,0,-1)).cut(cylinder(16.1/2,3.3,0,0,4.8))
 p=p.cut(box(10,4.2,3.3,10,0,6.45)).cut(box(4.2,10,3.3,0,10,6.45))
 for x in (-18,18):p=p.cut(cylinder(2.5,10,x,-18,-1))
 return p.clean()
def static_fixture_assembly()->cq.Compound:return comp([static_fixture(),collar().translate((0,0,5)),cylinder(5,40,0,0,-15)])

def measurement_ledger()->dict[str,Any]:return {"schema":"paddy_swarm.common_rover.measurement_ledger.v0.9.4.2","rows":[{"id":"F001","name":"FRAME_UPPER_OUTER","value":[540,181],"classification":"MEASURED"},{"id":"F002","name":"FRAME_LOWER_OUTER","value":[442,181],"classification":"MEASURED"},{"id":"F003","name":"FRAME_STRUCTURAL_HEIGHT","value":150,"classification":"MEASURED"},{"id":"F004","name":"PREVIOUS_INTERNAL_Z","value":90.7,"classification":"VALID_MEASUREMENT_DIFFERENT_DATUM","use":"DO_NOT_USE_AS_BBOX_INSERTION_HEIGHT"},{"id":"F005","name":"BATTERY_INSERTION_CLEAR_HEIGHT","value":108,"classification":"MEASURED"},{"id":"B001","name":"BATTERY_BODY","value":[150.9,99.4,92.5],"classification":"MEASURED"},{"id":"B002","name":"BATTERY_MASS","value":1.2,"classification":"MEASURED"},{"id":"B003","name":"BATTERY_WITH_TERMINALS_INSERTION","value":"PHYSICAL_PASS","classification":"USER_REPORTED"},{"id":"H001","name":"COLLAR","value":[15.9,10.1,3.0],"classification":"MEASURED"},{"id":"H002","name":"SET_SCREWS","value":{"quantity":2,"angle":90,"length":4,"projection":1},"classification":"MEASURED_USER_CONFIRMED"},{"id":"R001","name":"BEARING_6000_OD","value":25.9,"classification":"MEASURED"},{"id":"K001","name":"KP000_HOLE_CENTER","value":53.0,"classification":"MEASURED"}]}
def dimensions()->dict[str,Any]:return {"version":VERSION,"classification":CLASSIFICATION,"frame":FRAME,"z_record":Z_RECORD,"battery":BATTERY,"bbox_dummy":DUMMY,"collar":COLLAR,"set_screws":SCREWS,"reaction":REACTION,"bearing":BEARING,"kp000":KP000,"protected_sprocket":SPROCKET,"rail_gauges":[130,132,134]}
def interfaces()->dict[str,Any]:return {"bbox_dummy":{"purpose":"OUTER_ENVELOPE_PASSAGE_GAUGE","load_bearing":False,"actual_battery_after_dummy_pass_only":True,"idler_level":"PASSAGE_DATUM_ONLY","final_load_path":"FRAME_DEDICATED_SUPPORT_RAIL_SKID_BBOX","removal":"-X"},"h25a1":{"load_path":"SHAFT_TWO_M4_METAL_COLLAR_REPLACEABLE_REACTION_KEY_HUB_12T","fixture":"STATIC_ONLY","powered":False,"radial_tooth_root_hole":False},"frame_decision":{"150":"PRIMARY_IF_103_PHYSICAL_PASS_WITH_3_TO_5_MM_PRACTICAL_CLEARANCE","190":"HIGH_CLEARANCE_ALTERNATIVE_HOLD"}}
def limits()->dict[str,Any]:return {"bbox":{"B1":{"height":103,"cycles":10},"B2":{"height":105,"cycles":5},"B3":{"height":107,"cycles":5},"recommended_clearance":[3,5],"record":["TOP","LEFT","RIGHT","FRONT_REAR","SNAGGING","CONTACT"]},"collar_fit":["CANNOT_INSERT","PRESS_FIT","SNUG","SLIGHT_PLAY","EXCESSIVE_PLAY","REMOVABLE_WITHOUT_DAMAGE"],"static_torque_nm":[0.25,0.5,0.75],"static_fail":["SHAFT_SLIP","COLLAR_ROTATION","SCREW_MOVEMENT","KEY_DAMAGE","PETG_WHITENING","CRACK","PERMANENT_PLAY"],"powered_rotation":False,"field":False}
def geometry_manifest()->dict[str,Any]:
 f=frame150().BoundingBox();s=skeleton().BoundingBox();fixture=static_fixture().val().BoundingBox();shim_rows=[]
 for h in (2.,4.):
  b=shim(h).val().BoundingBox();shim_rows.append({"height":h,"x":b.xlen,"y":b.ylen})
 return {"schema":"paddy_swarm.common_rover.physical_fit.v0.9.4.2","classification":CLASSIFICATION,"release":RELEASE,"frame_bounds":{"x":f.xlen,"y":f.ylen,"z":f.zlen,"zmin":f.zmin,"zmax":f.zmax},"dummy_bounds":{"x":s.xlen,"y":s.ylen,"z":s.zlen},"dummy_parts":{"bottom":"PRINT_FLAT_SUPPORT_FREE","top":"PRINT_FLAT_SUPPORT_FREE_FLIP_FOR_ASSEMBLY","posts_x4":"PRINT_LAID_FLAT_SUPPORT_FREE","assembled_stl":"REFERENCE_ONLY_DO_NOT_PRINT_MONOLITHIC","roof":"NONE","open_sides":True},"shim_bounds":shim_rows,"coupon_bounds":{"collar":[72,28,6.6],"reaction":[72,28,6.6]},"printability":{"printer":"Bambu A1","bed_xy":[256,256],"largest_print_footprint_xy":[200,134],"all_designated_print_files_fit":True,"support":"NOT_REQUIRED_CANDIDATE","monolithic_dummy_stl":"REFERENCE_ONLY"},"fixture":{"bounds":[fixture.xlen,fixture.ylen,fixture.zlen],"shaft_bore":10.5,"collar_pocket":16.1,"dual_slot":4.2,"mount_holes":2,"static_only":True},"h25a1":{"external_12t_difference":0.0,"radial_tooth_root_hole":False,"radial_keepout":8.95},"parents":{"v0941":audit_dir(P1,68,P1_HASHES),"v0940":audit_dir(P0,43,P0_HASHES)}}
def validation()->dict[str,Any]:
 checks={"FRAME_150_RECORD":"CAD_PASS","BATTERY_INSERTION_108":"MEASURED","BATTERY_WITH_TERMINALS":"PHYSICAL_PASS_USER_REPORTED","BBOX_103_DUMMY":"PRINT_READY_CANDIDATE","BBOX_103_PHYSICAL_FIT":"PENDING_USER_TEST","BBOX_105":"PENDING_USER_TEST","BBOX_107":"PENDING_USER_TEST","FRAME_150_FINAL_SELECTION":"HOLD_UNTIL_DUMMY_TEST","FRAME_190":"ALTERNATIVE_HOLD","COLLAR_COUPONS":"PRINT_READY_CANDIDATE","REACTION_COUPONS":"PRINT_READY_CANDIDATE","H25A1_FINAL_REACTION_KEY":"HOLD_UNTIL_COUPON_TEST","H25A1_STATIC_FIXTURE":"PRINT_READY_CANDIDATE_PHYSICAL_PENDING","H25A1_STATIC_TORQUE":"PHYSICAL_PENDING","POWERED_ROTATION":"NOT_APPROVED","FIELD":"NOT_APPROVED"}
 missing=["ABSOLUTE_GROUND_FRAME_Z_DATUM","FINAL_BBOX_SUPPORT_HEIGHT","FINAL_BBOX_LID_GASKET_STACK","BATTERY_TERMINAL_XYZ_WIRE_BEND","WATERPROOF_CONNECTOR_MODEL","GASKET_MATERIAL_COMPRESSION","BBOX_FINISHED_MASS","CBOX_ELECTRONICS","PIVOT_ROTATION_CENTER","DIAGONAL_FINAL_CUT_LENGTH","PTO_BELT_TRANSFORMS","TRACK_LATERAL_MOVEMENT","M4_THREAD_PITCH_IF_REQUIRED"]
 return {"version":VERSION,"classification":CLASSIFICATION,"release":RELEASE,"checks":checks,"missing_future_measurements":missing,"current_artifact_blockers":[],"physical_fit_test_ready":True,"user_physical_test_pending":True,"powered_rotation_approved":False,"field_approved":False,"final_status":FINAL_STATUS}

def H()->str:return f"# Common Rover Physical Fit Closure v{VERSION}\n\nClassification: `{CLASSIFICATION}`  \nRelease: `{RELEASE}`  \nStatus: `{FINAL_STATUS}`\n"
def documents(v:dict[str,Any])->dict[str,str]:
 h=H();d={}
 d["README.md"]=h+"\nSmall, low-material artifacts close physical-fit uncertainty before final waterproof boxes or powered drivetrain. Parent lanes remain read-only. The assembled dummy STL is reference-only; print the bottom, top, and laid-flat post files.\n"
 d["PHYSICAL_FRAME_150_RECORD.md"]=h+"\nCurrent compact baseline: upper540×181, lower442×181, height150±1, clear500×100 and400×140, four110mm verticals. `CURRENT_PHYSICAL_FRAME_150MM = REOPENED_PRIMARY_COMPACT_BASELINE`; 190mm remains high-clearance alternative.\n"
 d["FRAME_MEASUREMENT_LEDGER.md"]=h+"\n|Item|Value|Class/use|\n|---|---:|---|\n|Upper outer|540×181|MEASURED|\n|Lower outer|442×181|MEASURED|\n|Height|150|MEASURED|\n|Vertical|110×4|MEASURED|\n|Previous internal Z|90.7|VALID_MEASUREMENT_DIFFERENT_DATUM; not insertion height|\n|Battery insertion passage|108.0|MEASURED; fit authority|\n|Battery with terminals|pass|PHYSICAL_PASS USER_REPORTED|\n"
 d["FRAME_Z_DATUM_CONFLICT_UPDATE.md"]=h+"\n68+150=218 conflicts with later top≈212 by6mm. ABSOLUTE_FRAME_Z remains HOLD. The present fit closure uses relative108mm passage only and does not reinterpret90.7.\n"
 d["BATTERY_INSERTION_CLEARANCE.md"]=h+"\nThe idler-shaft-side observation datum to upper underside is108.0 MEASURED. It is a passage datum, not an approved support. The real terminal-equipped battery passed physically. Dummy heights103/105/107 leave nominal5/3/1mm; only user cycles can establish practical clearance.\n"
 d["H25A1_2S_PHYSICAL_TEST_PLAN.md"]=h+"\nPrint coupons first. Select collar and slot fits, assemble actual collar/two screws/φ10 rod in fixture, apply0.25→0.50→0.75N·m with inspection after each. Stop on any slip, movement, whitening, crack, key damage, or permanent play. POWERED_ROTATION is NOT_APPROVED.\n"
 d["H25A1_COLLAR_COUPON_SPEC.md"]=h+"\nOne support-free plate has through/open-back pockets16.00/16.10/16.20 with raised labels160/161/162. Collar W3 is removable from either side. Record insertion class and damage; final pocket is PHYSICAL_TEST_REQUIRED.\n"
 d["H25A1_REACTION_COUPON_SPEC.md"]=h+"\nOne support-free plate has open edge slots4.1/4.2/4.3 with labels41/42/43. Screw-centre keepout is R8.95. Check engagement, play, removal and PETG edge damage. Final slot remains HOLD.\n"
 d["H25A1_STATIC_FIXTURE_SPEC.md"]=h+"\n50×50×8 sacrificial reaction block: through φ10.5 shaft bore, top16.1×3.2 collar recess, two perpendicular4.2 slots, two clamp holes. STEP includes metal references; STL contains only printable PETG block. Static use only; no 12T printing or powered test.\n"
 d["BBOX_DUMMY_SPEC.md"]=h+"\nOuter gauge180×114×103. Split skeleton: flat bottom/top perimeter frames plus four97×8×8 posts printed laid flat. No roof or waterproof features. Assembled STL is inspection reference only. Add flat2/4mm shims for105/107. Rail gauges compare130/132/134; prefer130/132.\n"
 d["BBOX_DUMMY_TEST_PLAN.md"]=h+"\nB1:103 insert/remove×10. B2:105×5. B3:107×5. Record top/left/right/front-rear, snagging and contact. 107 rubbing is limit data, not automatic product failure. Test actual battery only after dummy PASS and do not load the non-structural skeleton with1.2kg without separate support.\n"
 d["BBOX_150_VS_190_DECISION_GATE.md"]=h+"\nRecommend150 only if103mm dummy physically passes without hard contact, retains practical3–5mm clearance, withdraws−X, and service is acceptable. Otherwise reopen190. Until user test: FRAME_150_FINAL_SELECTION=HOLD; FRAME_190=ALTERNATIVE_HOLD; no150/190 final cutting.\n"
 d["MISSING_MEASUREMENTS.md"]=h+"\nNo additional measurement blocks these artifacts. Future manufacturing HOLD:\n"+"\n".join(f"- `{x}`" for x in v["missing_future_measurements"])+"\n"
 d["DESIGN_GATE.md"]=h+"\n"+"\n".join(f"- `{k}`: `{x}`" for k,x in v["checks"].items())+"\n\nCAD/PRINT_READY is not PHYSICAL_PASS. Waterproof, powered, and field release remain prohibited.\n"
 return d
def svg(title:str,body:str)->str:return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 500"><style>text{{font-family:Arial;fill:#17212b}}.f{{fill:none;stroke:#334e68;stroke-width:2}}.m{{fill:#d9eafd;stroke:#245b8a}}.h{{fill:#fbd5d5;stroke:#a33}}.d{{stroke:#168aad;stroke-width:3;stroke-dasharray:9 6}}.a{{stroke:#b33;stroke-width:5}}</style><rect width="100%" height="100%" fill="#fbfcfe"/><text x="24" y="32" font-size="22">{title}</text>{body}<text x="24" y="480" font-size="13">v0.9.4.2 · PHYSICAL FIT TEST ONLY · HOLD</text></svg>'
def drawings()->None:
 top='<rect class="m" x="230" y="140" width="540" height="181"/><rect class="f" x="250" y="180" width="500" height="100"/><rect class="f" x="280" y="165" width="442" height="140"/><text x="380" y="130">upper outer540×181 / clear500×100</text><text x="360" y="335">lower outer442×181 / clear400×140</text>'
 side='<rect class="m" x="230" y="150" width="540" height="150"/><rect class="h" x="320" y="192" width="180" height="103"/><line class="d" x1="100" y1="187" x2="900" y2="187"/><text x="790" y="180">upper underside</text><text x="520" y="250">108 passage</text><text x="240" y="320">110 vertical columns / structural150</text><text x="520" y="290">dummy103</text>'
 front='<rect class="m" x="410" y="130" width="181" height="150"/><rect class="h" x="444" y="177" width="114" height="103"/><text x="620" y="150">outer Y181</text><text x="620" y="190">lower clearY140</text><text x="620" y="230">dummyY114 →13/side</text>'
 vals={"frame_top.svg":top,"FRAME_PHYSICAL_150_TOP.svg":top,"frame_side.svg":side,"FRAME_PHYSICAL_150_SIDE.svg":side,"frame_front.svg":front,"FRAME_PHYSICAL_150_FRONT.svg":front,"battery_insertion_section.svg":'<line class="f" x1="100" y1="120" x2="900" y2="120"/><line class="f" x1="100" y1="390" x2="900" y2="390"/><rect class="m" x="310" y="159" width="300" height="231"/><rect class="h" x="280" y="133" width="360" height="257" fill-opacity=".25"/><line class="d" x1="280" y1="128" x2="640" y2="128"/><line class="d" x1="280" y1="123" x2="640" y2="123"/><text x="650" y="120">108 MEASURED passage</text><text x="650" y="160">battery body92.5 + terminal keepout</text><text x="650" y="205">dummy103 / +2 / +4</text><text x="650" y="250">90.7 = OTHER_DATUM</text>',"bbox_dummy_removal.svg":'<rect class="m" x="520" y="165" width="280" height="180"/><path class="a" d="M520 255H130"/><text x="570" y="150">180×114×103 skeleton</text><text x="150" y="235">complete withdrawal −X</text><text x="150" y="285">check posts/crawler/idler/hand</text>',"h25a1_coupon_map.svg":'<rect class="m" x="120" y="150" width="330" height="180"/><circle class="f" cx="200" cy="225" r="38"/><circle class="f" cx="285" cy="225" r="40"/><circle class="f" cx="375" cy="225" r="42"/><text x="185" y="300">160</text><text x="270" y="300">161</text><text x="360" y="300">162</text><rect class="h" x="540" y="150" width="330" height="180"/><path class="f" d="M610 150V245M705 150V245M800 150V245"/><text x="590" y="300">41</text><text x="690" y="300">42</text><text x="785" y="300">43</text>',"h25a1_static_fixture.svg":'<rect class="m" x="250" y="120" width="300" height="300"/><circle class="f" cx="400" cy="270" r="48"/><path class="h" d="M448 250H520V290H448M380 222V150H420V222"/><circle class="f" cx="400" cy="270" r="30"/><text x="580" y="180">φ10.5 shaft</text><text x="580" y="220">16.1 collar recess</text><text x="580" y="260">dual4.2 slots / R8.95</text><text x="580" y="300">0.25→0.50→0.75 N·m</text>'}
 for n,b in vals.items():write(LANE/"drawings"/n,svg(n.replace("_"," "),b))

def build()->dict[str,Any]:
 before=repository_guard(False);f=frame150();bat=battery();sk=skeleton();s2=shim(2);s4=shim(4);ex=bbox_exploded();rg=rail_gauges();col=collar();cc=collar_coupon();rc=reaction_coupon();fx=static_fixture();fxa=static_fixture_assembly()
 jobs=[(f,CAD[0]),(bat,CAD[1]),(sk,CAD[2]),(sk,CAD[3]),(s2,CAD[4]),(s4,CAD[5]),(ex,CAD[6]),(perimeter(0,False),CAD[7]),(perimeter(0,False),CAD[8]),(post_print_plate(),CAD[9]),(removal_envelope(),CAD[10]),(rg,CAD[11]),(rg,CAD[12]),(col,CAD[13]),(cc,CAD[14]),(cc,CAD[15]),(rc,CAD[16]),(rc,CAD[17]),(fxa,CAD[18]),(fx,CAD[19])]
 for shape,rel in jobs:export(shape,LANE/rel)
 drawings();dim=dimensions();inter=interfaces();lim=limits();ledger=measurement_ledger();geom=geometry_manifest();valid=validation()
 for n,x in [("dimensions.json",dim),("interfaces.json",inter),("test_limits.json",lim),("measurement_ledger.json",ledger),("geometry_manifest.json",geom),("validation_report.json",valid)]:write_json(LANE/n,x)
 for n,x in documents(valid).items():write(LANE/n,x)
 write(LANE/"MANIFEST.txt","\n".join(PACKAGE_PATHS));write(LANE/"COMMIT_PATHS.txt","\n".join(f"{LANE_REL}/{p}" for p in PACKAGE_PATHS));write(LANE/"BUILD_LOG.txt",f"BUILD PASS\nversion={VERSION}\nPython={sys.version.split()[0]}\nCadQuery={cq.__version__}\npreflight_untracked={before['untracked_total']}\nparents=CAD_PASS");write(LANE/"TEST_LOG.txt","PENDING_TEST_EXECUTION")
 hashed=[p for p in PACKAGE_PATHS if p!="SHA256SUMS.txt"];write(LANE/"SHA256SUMS.txt","\n".join(f"{sha(LANE/p)}  {p}" for p in hashed));t=subprocess.run([sys.executable,"-B",str(LANE/"tests/test_common_rover_physical_fit_closure_v0942.py")],cwd=REPO_ROOT,text=True,encoding="utf-8",stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if t.returncode:raise RuntimeError(t.stdout)
 write(LANE/"TEST_LOG.txt",t.stdout);write(LANE/"SHA256SUMS.txt","\n".join(f"{sha(LANE/p)}  {p}" for p in hashed));return {"status":"CAD_PASS","guard":repository_guard(True),"validation":valid}
def stl_semantic(p:Path)->dict[str,Any]:
 data=p.read_bytes();n=struct.unpack_from("<I",data,80)[0]
 if len(data)!=84+50*n:raise RuntimeError(f"bad STL {p}")
 mins=[math.inf]*3;maxs=[-math.inf]*3;positive=0
 for i in range(n):
  vals=struct.unpack_from("<12f",data,84+50*i);pts=[vals[3:6],vals[6:9],vals[9:12]];a=[pts[1][j]-pts[0][j] for j in range(3)];b=[pts[2][j]-pts[0][j] for j in range(3)];c=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]);positive+=sum(x*x for x in c)>1e-12
  for q in pts:
   for j in range(3):mins[j]=min(mins[j],q[j]);maxs[j]=max(maxs[j],q[j])
 if positive!=n:raise RuntimeError(f"degenerate STL {p}")
 return {"triangles":n,"bounds":[maxs[j]-mins[j] for j in range(3)]}
def verify_files()->dict[str,Any]:
 missing=[p for p in PACKAGE_PATHS if not (LANE/p).is_file()];extras=sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.relative_to(LANE).as_posix() not in PACKAGE_PATHS);manifest=(LANE/"MANIFEST.txt").read_text(encoding="utf-8").splitlines();hashes={}
 for line in (LANE/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():digest,rel=line.split("  ",1);hashes[rel]=digest
 bad=[p for p,x in hashes.items() if sha(LANE/p)!=x];d=json.loads((LANE/"dimensions.json").read_text());v=json.loads((LANE/"validation_report.json").read_text());g=json.loads((LANE/"geometry_manifest.json").read_text());stls={p.name:stl_semantic(p) for p in (LANE/"cad").glob("*.stl")}
 checks={"package":not missing and not extras and manifest==PACKAGE_PATHS,"hashes":not bad,"frame":d["frame"]["structural_height"]==150 and d["z_record"]["battery_insertion_clear_height"]==108,"datum":d["z_record"]["previous_internal_z_classification"]=="VALID_MEASUREMENT_DIFFERENT_DATUM","battery":d["battery"]["x"]==150.9 and d["battery"]["mass_kg"]==1.2,"dummy":d["bbox_dummy"]["test_heights"]==[103.,105.,107.] and g["dummy_bounds"]=={"x":180.0,"y":114.0,"z":103.0},"coupons":d["collar"]["pockets"]==[16.,16.1,16.2] and d["reaction"]["slots"]==[4.1,4.2,4.3],"stl":len(stls)==10,"release":not v["powered_rotation_approved"] and not v["field_approved"]}
 if not all(checks.values()):raise RuntimeError({"checks":checks,"missing":missing,"extras":extras,"bad":bad,"stls":stls})
 return {"status":"CAD_PASS","file_count":len(PACKAGE_PATHS),"stl_count":len(stls),"checks":checks,"bad_hashes":bad}
def standalone_rebuild()->dict[str,Any]:
 with tempfile.TemporaryDirectory(prefix="ps_cr_v0942_") as td:
  o=Path(td);jobs=[(frame150(),"frame.step"),(skeleton(),"dummy.step"),(skeleton(),"dummy.stl"),(shim(2),"s2.stl"),(shim(4),"s4.stl"),(collar_coupon(),"c.step"),(collar_coupon(),"c.stl"),(reaction_coupon(),"r.step"),(reaction_coupon(),"r.stl"),(static_fixture(),"f.step"),(static_fixture(),"f.stl")]
  for s,n in jobs:export(s,o/n)
  b=skeleton().BoundingBox();checks={"outputs":len(list(o.iterdir()))==len(jobs),"dummy":all(abs(x-y)<1e-6 for x,y in zip((b.xlen,b.ylen,b.zlen),(180,114,103))),"nonempty":all((o/n).stat().st_size for _,n in jobs)}
  if not all(checks.values()):raise RuntimeError(checks)
  return {"status":"CAD_PASS","output_count":len(jobs),"checks":checks}
def make_zip()->tuple[Path,str]:
 p=DOWNLOADS/f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
 if p.exists():raise FileExistsError(p)
 with zipfile.ZipFile(p,"x",zipfile.ZIP_DEFLATED) as z:
  for rel in PACKAGE_PATHS:z.write(LANE/rel,rel)
 with zipfile.ZipFile(p) as z:
  names=z.namelist();bad=[n for n in names if PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts]
  if z.testzip() or len(names)!=len(set(names)) or bad or sorted(names)!=PACKAGE_PATHS:raise RuntimeError("ZIP contract")
 return p,sha(p)
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument("--build",action="store_true");ap.add_argument("--verify",action="store_true");ap.add_argument("--standalone-verify",action="store_true");ap.add_argument("--standalone-rebuild",action="store_true");ap.add_argument("--zip",action="store_true");a=ap.parse_args();r={}
 if not any(vars(a).values()):a.build=a.verify=True
 if a.build:r["build"]=build()
 if a.verify or a.standalone_verify:
  if a.verify:r["guard"]=repository_guard(True)
  r["verify"]=verify_files()
 if a.standalone_verify or a.standalone_rebuild:r["standalone_rebuild"]=standalone_rebuild()
 if a.zip:
  p,h=make_zip();r["zip"]={"path":str(p),"sha256":h}
 print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
