#!/usr/bin/env python3
"""Build the Common Rover v0.9.4.1 physical-integration revision.

All absolute-Z, pivot, waterproofing, and final drivetrain uncertainties are
kept fail-closed.  The generated solids are reference/envelope geometry unless
the machine-readable authority explicitly says otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import cadquery as cq

VERSION="0.9.4.1"
CLASSIFICATION="PHYSICAL_INTEGRATION_REVISION"
RELEASE="HOLD"
FINAL_STATUS="CAD_REVISION_COMPLETE / PHYSICAL_VALIDATION_PENDING"
REPO_ROOT=Path(r"D:\Paddy_Swarm_Project")
LANE_REL="cad/common_rover/common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1"
LANE=Path(__file__).resolve().parent
PARENT_REL="cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0"
PARENT=REPO_ROOT/PARENT_REL
EXPECTED_BRANCH="agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD="facb4f63c0d485a53fef48b602f97e0454e8548f"
BASE_OUTSIDE_UNTRACKED=1276
DOWNLOADS=Path(r"D:\Downloads")
ZIP_PREFIX="Paddy_Swarm_Common_Rover_190mm_Frame_H25A1_2S_BBOX_CBOX_v0_9_4_1_"

AUTHORITY_HASHES={
 "CURRENT_COMMON_ROVER_AUTHORITY.md":"390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
 "README.md":"f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
 "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md":"78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
 "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md":"0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_HASHES={
 "MANIFEST.txt":"fbb9d00eda9dda979e3dfcb4596d987260fc79dd6f0160cdf40512fbf438a984",
 "SHA256SUMS.txt":"0bfd7afed7b19543e811a1e08bb98aa8c8151a46465d3254702361ea50794fe5",
 "geometry_manifest.json":"06c2785bf772912a3019a59004586ddad136d3e58320682c376d93f9f1add198",
 "validation_report.json":"13cdca78fc4a12a29ba5128ecf366cb986fdf635b6f73751af1604fba314f5d5",
 "build_common_rover_physical_integration_v0940.py":"15bc112e287c8b8f42fafbe6f9b64d1db677fcda6e49b8056bf88db7e0164cd3",
 "tests/test_common_rover_physical_integration_v0940.py":"ae648f03f0752acf3837e0184104986510c336b4f176631bded6d6da381acbdb",
}

DOCS=["README.md","PHYSICAL_FRAME_150_REFERENCE.md","FRAME_190_REVISION.md","FRAME_Z_DATUM_CONFLICT.md","DIAGONAL_BEAM_DERIVATION.md","PIVOT_INTERFACE.md","PTO_20T20T.md","KP000_INTERFACE.md","BEARING_6000_UPDATE.md","H25A1_2S_DESIGN.md","H25A1_2S_COLLAR_MEASUREMENTS.md","H25A1_2S_REACTION_KEY.md","H25A1_2S_TEST_PLAN.md","BATTERY_MEASUREMENT.md","BBOX_ARCHITECTURE.md","BBOX_CASSETTE.md","BBOX_BUOYANCY.md","BBOX_TEST_PLAN.md","CBOX_ARCHITECTURE.md","BBOX_CBOX_X_SERIAL_LAYOUT.md","INTERFERENCE_REPORT.md","SERVICEABILITY_REPORT.md","MISSING_MEASUREMENTS.md","DESIGN_GATE.md"]
JSONS=["dimensions.json","interfaces.json","coordinate_system.json","hardware.json","test_limits.json","geometry_manifest.json","validation_report.json"]
CAD=["cad/frame_150_reference.step","cad/frame_190_candidate.step","cad/frame_190_candidate_reference.stl","cad/diagonal_beam_reference.step","cad/h25a1_2s_assembly.step","cad/h25a1_2s_body.step","cad/h25a1_2s_cover.step","cad/collar_reference.step","cad/collar_fit_coupon.stl","cad/dual_reaction_coupon.stl","cad/reaction_key.step","cad/battery_reference.step","cad/bbox_candidate.step","cad/bbox_removal_envelope.step","cad/bbox_support_rails.step","cad/cbox_candidate.step","cad/cbox_support.step","cad/full_integration_190.step","cad/full_integration_190_reference.stl"]
DRAWINGS=["drawings/top_view.svg","drawings/front_view.svg","drawings/side_view.svg","drawings/frame_150_vs_190.svg","drawings/waterline_190.svg","drawings/diagonal_geometry.svg","drawings/diagonal_cut_drawing.svg","drawings/h25a1_2s_section.svg","drawings/bbox_section.svg","drawings/bbox_removal_sequence.svg","drawings/bbox_cbox_x_serial.svg"]
SOURCE=["build_common_rover_190mm_integration_v0941.py","tests/test_common_rover_190mm_integration_v0941.py"]
RELEASE_FILES=["MANIFEST.txt","SHA256SUMS.txt","COMMIT_PATHS.txt","BUILD_LOG.txt","TEST_LOG.txt"]
PACKAGE_PATHS=sorted(DOCS+JSONS+CAD+DRAWINGS+SOURCE+RELEASE_FILES)

OLD_FRAME={"upper_outer_x":540.0,"upper_outer_y":181.0,"lower_outer_x":442.0,"lower_outer_y":181.0,"height":150.0,"vertical_2020":110.0,"upper_clear_x":500.0,"upper_clear_y":100.0,"lower_clear_x":400.0,"lower_clear_y":140.0,"internal_effective_z":90.7}
NEW_FRAME={**OLD_FRAME,"height":190.0,"vertical_2020":150.0,"internal_effective_z":130.7,"increment":40.0}
Z_DATUM={"ground":0.0,"waterline":150.0,"scenario_a_bottom":68.0,"scenario_a_old_top":218.0,"scenario_a_new_top":258.0,"scenario_b_old_top":212.0,"scenario_b_new_top":252.0,"absolute_new_top":"HOLD","new_top_range":[252.0,258.0],"new_upper_inside_range":[232.0,238.0],"support_surface_range":[101.3,107.3],"terminal_top":225.0,"terminal_vs_reported_old_top_deficit":13.0,"terminal_overhead_clearance_range":[7.0,13.0]}
DIAGONAL={"delta_x":98.0,"structural_height":190.0,"concept_center_distance":math.hypot(98.0,190.0),"final_cut_length":None,"final_cut_status":"HOLD_ACTUAL_PIVOT_ROTATION_CENTER_AND_END_OFFSETS","pivot_nominal":[32.0,20.0,20.0],"pivot_hardware":"M6","sole_friction_lock":"NOT_APPROVED"}
KP000={"width_x":67.0,"depth_y":17.0,"height_z":35.0,"axis_height":18.5,"axis_tolerance":0.5,"bore":10.0,"collar_protrusion":6.0,"mount_hole_center":53.0,"crawler_count":8,"pto_related_count":4,"total":12}
BEARING={"od":25.9,"seat":26.0,"diametral_clearance":0.1,"central_clearance":12.0,"physical_fit":"PENDING"}
COLLAR={"od":15.9,"id":10.1,"width":3.0,"type":"SOLID_SET_SCREW_SHAFT_COLLAR"}
SET_SCREWS={"nominal":"M4","quantity":2,"angle":90.0,"major_od_measured":3.8,"length":4.0,"projection":1.0,"pitch":"HOLD"}
SPROCKET={"teeth":12,"phase":15.0,"spacing":30.0,"tip_radius":33.07,"root_radius":29.47,"tip_width":7.5,"root_width":9.5,"axial_width":44.0,"pitch_diameter":76.3943726841,"embed_depth":4.0}
BATTERY={"maker":"GOLDENMATE","chemistry":"LiFePO4","voltage":12.8,"capacity_ah":10.0,"energy_wh":128.0,"label_claim":"IP67","x":150.9,"y":99.4,"body_z":92.5,"mass_kg":1.2,"terminal_top_ground":225.0,"terminal_geometry":"HOLD"}
BBOX={"x":180.0,"y":114.0,"max_z":130.7,"main_z":105.0,"local_top_z":25.7,"local_top_y":94.0,"center_x":-100.0,"removal_axis":"-X","normal_swap_lid_open":False,"blind_mate":False,"idler_support":False,"waterproof_release":"HOLD","status":"CONDITIONAL_PASS_ENVELOPE_ONLY"}
CBOX={"x":180.0,"y":94.0,"z":45.0,"center_x":100.0,"fixed":True,"independent_support":True,"electronics":"HOLD","status":"CAD_PASS_ENVELOPE_ONLY"}
LAYOUT={"selected":"LAYOUT_A_BBOX_REAR_CBOX_FRONT","bbox_interval_x":[-190.0,-10.0],"central_gap":20.0,"cbox_interval_x":[10.0,190.0],"end_clearance_each":10.0,"x_serial":True,"vertical_stacking":False,"layout_b":"REJECT_FRONT_DRIVETRAIN_SERVICE_CONGESTION"}

def run_git(*args:str)->str: return subprocess.check_output(["git",*args],cwd=REPO_ROOT,text=True,encoding="utf-8").strip()
def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
 return h.hexdigest()
def write(path:Path,text:str)->None:
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text.rstrip()+"\n",encoding="utf-8",newline="\n")
def write_json(path:Path,value:Any)->None: write(path,json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True))
def box(x:float,y:float,z:float,cx:float,cy:float,cz:float)->cq.Workplane: return cq.Workplane("XY").box(x,y,z).translate((cx,cy,cz))
def cyl_axis(radius:float,length:float,start:tuple[float,float,float],direction:tuple[float,float,float])->cq.Workplane: return cq.Workplane(obj=cq.Solid.makeCylinder(radius,length,cq.Vector(*start),cq.Vector(*direction)))
def compound(parts:list[Any])->cq.Compound:
 vals=[]
 for p in parts: vals.extend(p.vals() if isinstance(p,cq.Workplane) else ([p] if not isinstance(p,cq.Compound) else p.Solids()))
 return cq.Compound.makeCompound(vals)
def export(shape:Any,path:Path)->None: path.parent.mkdir(parents=True,exist_ok=True); cq.exporters.export(shape,str(path))

def authority_audit()->dict[str,Any]:
 actual={p:sha(REPO_ROOT/p) for p in AUTHORITY_HASHES}; return {"actual":actual,"expected":AUTHORITY_HASHES,"status":"CAD_PASS" if actual==AUTHORITY_HASHES else "FAIL"}
def parent_audit()->dict[str,Any]:
 actual={p:sha(PARENT/p) for p in PARENT_HASHES}; files=[p for p in PARENT.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
 return {"path":PARENT_REL,"file_count":len(files),"hashes":actual,"expected_hashes":PARENT_HASHES,"status":"CAD_PASS" if len(files)==43 and actual==PARENT_HASHES else "FAIL"}
def repository_guard(require_complete:bool=False)->dict[str,Any]:
 root=Path(run_git("rev-parse","--show-toplevel")).resolve(); branch=run_git("branch","--show-current"); head=run_git("rev-parse","HEAD")
 tracked=sorted(run_git("diff","--name-only").splitlines()); staged=sorted(run_git("diff","--cached","--name-only").splitlines()); untracked=sorted(run_git("ls-files","--others","--exclude-standard").splitlines())
 lane=sorted(p[len(LANE_REL)+1:] for p in untracked if p.startswith(LANE_REL+"/")); outside=[p for p in untracked if not p.startswith(LANE_REL+"/")]
 ignored=run_git("ls-files","--others","-i","--exclude-standard","--",LANE_REL).splitlines(); forbidden=[p for p in LANE.rglob("*") if p.is_file() and (p.suffix.lower() in {".pyc",".dxf",".3mf",".gcode"} or "__pycache__" in p.parts)]
 checks={"root":root==REPO_ROOT.resolve(),"branch":branch==EXPECTED_BRANCH,"head":head==EXPECTED_HEAD,"tracked_preserved":set(tracked)==set(AUTHORITY_HASHES),"staged_zero":not staged,"outside_untracked_preserved":len(outside)==BASE_OUTSIDE_UNTRACKED,"lane_scope":set(lane).issubset(PACKAGE_PATHS),"lane_complete":set(lane)==set(PACKAGE_PATHS) if require_complete else True,"authority":authority_audit()["status"]=="CAD_PASS","parent":parent_audit()["status"]=="CAD_PASS","ignored_zero":not ignored,"cache_forbidden_zero":not forbidden}
 if not all(checks.values()): raise RuntimeError({"guard":checks,"tracked":tracked,"staged":staged,"outside":len(outside),"lane":lane,"ignored":ignored,"forbidden":[str(p) for p in forbidden]})
 return {"root":str(root),"branch":branch,"head":head,"tracked":tracked,"staged":staged,"untracked_total":len(untracked),"outside_untracked":len(outside),"lane_untracked":len(lane),"checks":checks,"status":"CAD_PASS"}

def frame(height:float)->cq.Compound:
 old=height==150.0; top=218.0 if old else 258.0; vertical=110.0 if old else 150.0
 parts=[]
 for y in (-80.5,80.5): parts += [box(442,20,40,0,y,88),box(540,20,20,49,y,top-10)]
 for x in (-211,211): parts.append(box(20,181,20,x,0,78))
 for x in (-211,309): parts.append(box(20,181,20,x,0,top-10))
 for x in (-211,211):
  for y in (-80.5,80.5): parts.append(box(20,20,vertical,x,y,108+vertical/2))
 return compound(parts)
def beam_between(a:tuple[float,float],b:tuple[float,float],y:float)->cq.Workplane:
 dx,dz=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dz); angle=-math.degrees(math.atan2(dz,dx))
 return cq.Workplane("XY").box(length,20,20).rotate((0,0,0),(0,1,0),angle).translate(((a[0]+b[0])/2,y,(a[1]+b[1])/2))
def diagonal_geometry()->cq.Compound:
 # Outer-corner conceptual centres reproduce sqrt(98^2+190^2); not a cut authority.
 return compound([beam_between((221,68),(319,258),y) for y in (-80.5,80.5)]+[box(32,20,20,221,y,68) for y in (-80.5,80.5)]+[box(32,20,20,319,y,258) for y in (-80.5,80.5)])
def source_sprocket()->cq.Workplane:
 embed=SPROCKET["root_radius"]-SPROCKET["embed_depth"]
 ring=cq.Workplane("XY").circle(SPROCKET["root_radius"]).circle(20).extrude(SPROCKET["axial_width"]/2,both=True); body=ring.union(cq.Workplane("XY").circle(18).extrude(22,both=True))
 # Reproduce the protected source's six radial spokes so hub and tooth ring
 # remain a genuine one-piece solid.  The spokes stay inside the root radius.
 for i in range(6):
  spoke=cq.Workplane("XY").box(7.5,12,44).translate((18.75,0,0)).rotate((0,0,0),(0,0,1),i*60)
  body=body.union(spoke)
 pts=[(embed,-6.5),(SPROCKET["root_radius"],-SPROCKET["root_width"]/2),(SPROCKET["tip_radius"],-SPROCKET["tip_width"]/2),(SPROCKET["tip_radius"],SPROCKET["tip_width"]/2),(SPROCKET["root_radius"],SPROCKET["root_width"]/2),(embed,6.5)]
 tooth=cq.Workplane("XY").polyline(pts).close().extrude(22,both=True)
 for i in range(12): body=body.union(tooth.rotate((0,0,0),(0,0,1),15+i*30))
 return body.clean()
def reaction_key(clearance:float=0.2)->cq.Workplane:
 w=4.2+clearance
 return box(7,w,3.4,11.5,0,20.5).union(box(w,7,3.4,0,11.5,20.5)).union(box(4,w+10,3.4,10,7,20.5)).union(box(w+10,4,3.4,7,10,20.5)).clean()
def collar_with_screws()->cq.Compound:
 collar=cq.Workplane("XY").circle(COLLAR["od"]/2).circle(COLLAR["id"]/2).extrude(3).translate((0,0,19))
 sx=cyl_axis(1.9,4.0,(5.05,0,20.5),(1,0,0)); sy=cyl_axis(1.9,4.0,(0,5.05,20.5),(0,1,0)); return compound([collar,sx,sy])
def h25()->dict[str,Any]:
 source=source_sprocket(); body=source.cut(cq.Workplane("XY").circle(10.3/2).extrude(60,both=True)).cut(cq.Workplane("XY").circle(16.2/2).extrude(3.4).translate((0,0,18.8)))
 key=reaction_key(); body=body.cut(key); cover=cq.Workplane("XY").circle(18).circle(10.8/2).extrude(2.5).translate((0,0,22)); collar=collar_with_screws(); assembly=compound([body,collar,key,cover])
 outer_tool=cq.Workplane("XY").circle(40).circle(SPROCKET["root_radius"]).extrude(60,both=True); delta=body.intersect(outer_tool).val().Volume()-source.intersect(outer_tool).val().Volume()
 return {"source":source,"body":body,"collar":collar,"key":key,"cover":cover,"assembly":assembly,"outer_delta":delta}
def collar_coupon()->cq.Workplane:
 p=box(72,25,6,0,0,3)
 for x,d in zip((-24,0,24),(16.0,16.1,16.2)): p=p.cut(cq.Workplane("XY").center(x,0).circle(d/2).extrude(8))
 return p.clean()
def reaction_coupon()->cq.Workplane:
 p=box(72,28,6,0,0,3)
 for x,w in zip((-24,0,24),(4.1,4.2,4.3)): p=p.cut(box(w,18,8,x,5,4))
 return p.clean()
def battery()->cq.Workplane: return box(BATTERY["x"],BATTERY["y"],BATTERY["body_z"],0,0,BATTERY["body_z"]/2)
def bbox_parts()->dict[str,Any]:
 # Scenario-A absolute Z is used only to place the reference; datum remains HOLD.
 base=107.3; main=box(BBOX["x"],BBOX["y"],BBOX["main_z"],BBOX["center_x"],0,base+BBOX["main_z"]/2); dome=box(80,BBOX["local_top_y"],BBOX["local_top_z"],BBOX["center_x"],0,base+BBOX["main_z"]+BBOX["local_top_z"]/2)
 rails=compound([box(BBOX["x"],10,6,BBOX["center_x"],y,base-3) for y in (-62,62)])
 sweep=compound([box(380,BBOX["y"],BBOX["main_z"],-200,0,base+BBOX["main_z"]/2),box(380,BBOX["local_top_y"],BBOX["local_top_z"],-200,0,base+BBOX["main_z"]+BBOX["local_top_z"]/2)])
 return {"candidate":compound([main,dome]),"rails":rails,"sweep":sweep,"base":base}
def cbox_parts()->dict[str,Any]:
 candidate=box(CBOX["x"],CBOX["y"],CBOX["z"],CBOX["center_x"],0,180.5); support=compound([box(CBOX["x"],10,6,CBOX["center_x"],y,155) for y in (-52,52)]+[box(10,140,8,x,0,154) for x in (15,185)])
 return {"candidate":candidate,"support":support}
def integration()->cq.Compound:
 f=frame(190); d=diagonal_geometry(); hp=h25(); bp=bbox_parts(); cp=cbox_parts(); parts=[f,d,bp["candidate"],bp["rails"],cp["candidate"],cp["support"]]
 # Actual battery body in Layout A; terminal plane only, because terminal geometry is unmeasured.
 parts += [battery().translate((BBOX["center_x"],0,bp["base"])),box(60,80,.5,BBOX["center_x"],0,225)]
 for y in (-117.3,117.3):
  for x in (-150,-50,50,150): parts += [cyl_axis(25,44,(x,y-22,25),(0,1,0)),box(67,17,35,x,y-(8.5 if y>0 else -8.5),43.5)]
 # Upper drivetrain reservation and 20:20 PTO reference; transforms remain HOLD.
 parts += [box(500,100,35,49,0,230.5),cyl_axis(5,140,(270,-70,218),(0,1,0)),cyl_axis(5,140,(235,-70,218),(0,1,0)),cyl_axis(18,15,(270,-7.5,218),(0,1,0)),cyl_axis(18,15,(235,-7.5,218),(0,1,0)),box(45,40,40,190,0,218),box(35,20,35,220,0,218),box(20,30,30,250,0,245)]
 parts.append(hp["assembly"].rotate((0,0,0),(1,0,0),90).translate((-190,117.3,40)))
 return compound(parts)

def dimensions_data()->dict[str,Any]:
 return {"version":VERSION,"classification":CLASSIFICATION,"old_frame":OLD_FRAME,"new_frame":NEW_FRAME,"z_datum":Z_DATUM,"diagonal":DIAGONAL,"kp000":KP000,"bearing_6000":BEARING,"collar":COLLAR,"set_screws":SET_SCREWS,"sprocket_12t":SPROCKET,"battery":BATTERY,"bbox":BBOX,"cbox":CBOX,"layout":LAYOUT}
def interfaces_data()->dict[str,Any]:
 return {"pto":{"driver_teeth":20,"driven_teeth":20,"ratio":1.0,"axis":"Y","support":"METAL_PLATE_KP000_SHAFT_KP000_METAL_PLATE","cantilever":"PROHIBITED","transform":"HOLD"},"h25a1_2s":{"load_path":"SHAFT_TWO_M4_SET_SCREWS_METAL_COLLAR_DUAL_REACTION_KEY_PETG_HUB_INTEGRAL_12T","cover_primary_torque":False,"radial_tooth_root_access":False},"bbox":{"load_path":"FRAME_DEDICATED_RAIL_SKID_BBOX","idler_support":False,"retention":["REAR_HARD_STOP","PRIMARY_LOCK","INDEPENDENT_SAFETY_PIN"],"connector":"HIGH_MANUAL_WATERPROOF_HOLD"},"cbox":{"load_path":"FRAME_INDEPENDENT_SUPPORT_CBOX","loads_bbox":False},"service":{"bbox_axis":"-X","layout":LAYOUT["selected"]}}
def coordinate_data()->dict[str,Any]: return {"unit":"mm","angle":"degree","+X":"front","+Y":"left","+Z":"up","ground_z":0,"waterline_z":150,"absolute_frame_top":"HOLD_DATUM_CONFLICT"}
def hardware_data()->dict[str,Any]: return {"pivot":{"nominal_envelope":[32,20,20],"slot":6,"fastener":"M6","actual_rotation_center":"HOLD"},"kp000":KP000,"collar":COLLAR,"set_screws":SET_SCREWS,"cover":{"candidates":["M4x16","M4x20","M4x25"],"first":"M4x20","final":"HOLD_STACK","compression_sleeve":"STRONGLY_RECOMMENDED"},"reaction_slots":[4.1,4.2,4.3],"collar_pockets":[16.0,16.1,16.2]}
def test_limits_data()->dict[str,Any]: return {"h25a1_2s":{"forward_turns":20,"reverse_turns":20,"torque_nm":[0.25,0.5,0.75],"hold_hours":24,"fail":["SHAFT_SLIP","COLLAR_ROTATION","SCREW_LOOSENING","KEY_CRUSH","PETG_DAMAGE","HARDWARE_INTERFERENCE"]},"bbox":{"dry_cycles":20,"lock_cycles":20,"pin_cycles":20,"dummy_mass_kg":1.2,"water_tests":["EMPTY","WEIGHTED","PARTIAL_SUBMERSION","TEMPORARY_FULL_SUBMERSION"]},"side_hardware":{"preferred_max":3.0,"conditional_max":4.0,"over_4":"BLOCK"}}
def geometry_data()->dict[str,Any]:
 h=h25(); f150=frame(150).BoundingBox(); f190=frame(190).BoundingBox(); buoy=[180*114*42.7/1e6,180*114*48.7/1e6]
 return {"schema":"paddy_swarm.common_rover.integration.v0.9.4.1","classification":CLASSIFICATION,"release":RELEASE,"frame_bounds":{"150":{"x":f150.xlen,"y":f150.ylen,"z":f150.zlen,"zmin":f150.zmin,"zmax":f150.zmax},"190":{"x":f190.xlen,"y":f190.ylen,"z":f190.zlen,"zmin":f190.zmin,"zmax":f190.zmax}},"diagonal":DIAGONAL,"h25a1_2s":{"external_12t_volume_delta":h["outer_delta"],"body_solid_count":len(h["body"].solids().vals()),"radial_tooth_root_access":False,"reaction_key":"A2_DUAL_REPLACEABLE_REACTION_KEY","reaction_slot_candidates":[4.1,4.2,4.3],"collar_pocket_candidates":[16.0,16.1,16.2]},"layout":LAYOUT,"bbox":{"geometry":"STEPPED_REFERENCE_ENVELOPE_NOT_WATERPROOF_SHELL","clearance_x_each":(400-BBOX["x"]-CBOX["x"]-20)/2,"battery_margin_x_total":BBOX["x"]-BATTERY["x"],"battery_margin_y_total":BBOX["y"]-BATTERY["y"],"terminal_overhead_clearance":Z_DATUM["terminal_overhead_clearance_range"]},"cbox":{"geometry":"UNIVERSAL_ELECTRONICS_ENVELOPE","electronics":"HOLD"},"buoyancy":{"partial_displacement_l_range":buoy,"buoyant_force_n_range":[x*9.80665 for x in buoy],"net_downward_kgf_excluding_bbox_mass_range":[BATTERY["mass_kg"]-max(buoy),BATTERY["mass_kg"]-min(buoy)],"bbox_mass":"HOLD"},"cg_sensitivity":{"known_battery_mass_kg":1.2,"layout_a_battery_center_x":-100.0,"battery_center_z_range":[147.55,153.55],"known_battery_x_moment_kg_mm":-120.0,"upper_unknown_masses_vertical_shift":40.0,"total_rover_cg":"HOLD_UNKNOWN_COMPONENT_MASSES"},"parent_audit":parent_audit()}
def validation_data()->dict[str,Any]:
 checks={"FRAME_190_CAD":"CAD_PASS","FRAME_Z_ABSOLUTE_DATUM":"HOLD","DIAGONAL_GEOMETRY":"CAD_PASS_REFERENCE","DIAGONAL_CUT_LENGTH":"HOLD_PIVOT_GEOMETRY","PTO":"CONDITIONAL_PASS_TRANSFORM_HOLD","H2.5-A1-2S":"CAD_PASS_PHYSICAL_REQUIRED","BBOX":"CONDITIONAL_PASS_ENVELOPE_WATERPROOF_REQUIRED","CBOX":"CAD_PASS_ENVELOPE_ELECTRONICS_HOLD","BBOX_REMOVAL":"CAD_PASS_REFERENCE_LAYOUT_A","BBOX_CBOX_X_SERIAL":"CAD_PASS_REFERENCE_LAYOUT_A","DRIVETRAIN_CLEARANCE":"HOLD_EXACT_TRANSFORMS","POWERED_ROTATION":"NOT_APPROVED","FIELD":"NOT_APPROVED"}
 interference={"BBOX_vs_frame":"CONDITIONAL_PASS_STEPPED_TOP_AND_DATUM_HOLD","BBOX_vs_battery_body":"CAD_PASS_ENVELOPE","BBOX_terminal_vs_lid":"HOLD_ONLY_7_TO_13_MM_BEFORE_LID_WIRE_ALLOWANCES","BBOX_removal_vs_CBOX":"CAD_PASS_LAYOUT_A_REFERENCE","BBOX_removal_vs_frame_pillars":"CAD_PASS_13_MM_NOMINAL_LATERAL_EACH","BBOX_removal_vs_crawler_idler_KP000":"HOLD_ACTUAL_TRANSFORMS","CBOX_vs_frame":"CAD_PASS_ENVELOPE_3_MM_NOMINAL_Y_EACH","CBOX_vs_drivetrain":"HOLD_ACTUAL_MOTOR_CLUTCH_BELT_TRANSFORMS","H25A1_vs_link_guide_bearing_hardware":"HOLD_DYNAMIC_AND_STACK_ENVELOPES","diagonal_vs_PTO":"HOLD_PIVOT_AND_PTO_TRANSFORMS"}
 missing=["FRAME_Z_DATUM_RECONCILIATION","PIVOT_ROTATION_CENTERS","PIVOT_EXTRUSION_END_OFFSETS","DIAGONAL_FINAL_CUT_LENGTH","BATTERY_TERMINAL_XYZ_ENVELOPE","BBOX_GASKET_MATERIAL","BBOX_GASKET_COMPRESSION","BBOX_LID_STACK","BBOX_MASS","CONNECTOR_MODEL","CBOX_ELECTRONICS_ENVELOPE","EXACT_MOTOR_CLUTCH_BELT_PTO_TRANSFORMS","TRACK_LATERAL_MOVEMENT","SET_SCREW_PITCH","REACTION_KEY_PHYSICAL_FIT"]
 return {"version":VERSION,"classification":CLASSIFICATION,"release":RELEASE,"checks":checks,"interference":interference,"missing_measurements":missing,"powered_rotation_approved":False,"field_deployment_approved":False,"physical_pass":False,"final_status":FINAL_STATUS}

def head()->str: return f"# Common Rover 190 mm / H2.5-A1-2S Integration v{VERSION}\n\nClassification: `{CLASSIFICATION}`  \nRelease: `{RELEASE}`  \nStatus: `{FINAL_STATUS}`\n"
def docs(d:dict[str,Any],g:dict[str,Any],v:dict[str,Any])->dict[str,str]:
 H=head(); out={}
 out["README.md"]=H+"\nParent v0.9.4.0 remains read-only. This lane evaluates the adopted 190 mm structural-height candidate, dual-M4 reaction-key hub, measured battery, and X-serial boxes. CAD_PASS never means PHYSICAL_PASS.\n"
 out["PHYSICAL_FRAME_150_REFERENCE.md"]=H+"\nProtected physical reference: outer upper 540×181, lower 442×181, structural height 150±1, clear 500×100 and 400×140, vertical 2020=110, effective internal Z=90.7 MEASURED. It is retained as `PHYSICAL_REFERENCE_150MM`.\n"
 out["FRAME_190_REVISION.md"]=H+"\nPrimary candidate: structural height 190, +40, vertical 2020=150×4. X/Y are unchanged. 180 mm is `SUPERSEDED_COMPARISON`. The STEP uses Scenario-A Z solely as a drawing reference; absolute ground height remains HOLD.\n"
 out["FRAME_Z_DATUM_CONFLICT.md"]=H+"\nTwo physical datums conflict by 6 mm. A: bottom 68 + structural 150 = old top218 and new top258. B: reported old top≈212 and new top≈252. Likely differences include aluminum outer face, crawler bottom, floor contact and measurement reference surface. New upper-inside plane is 232–238. Ground-to-new-top is HOLD until the same tool/setup measures crawler-bottom, lower outer face and upper outer face in one setup.\n"
 out["DIAGONAL_BEAM_DERIVATION.md"]=H+f"\nConcept only: `sqrt(98²+190²)={DIAGONAL['concept_center_distance']:.3f} mm`. This is not extrusion cut length. Final cut requires measured upper/lower pivot rotation centres plus insertion/end offsets. `DIAGONAL_2020_FINAL_CUT_LENGTH = HOLD`; no aluminum cutting is approved.\n"
 out["PIVOT_INTERFACE.md"]=H+"\nUSER_REPORTED nominal uxcell envelope 32×20×20, 2020, 6 mm slot, M6. Actual rotation centre, insertion offset and travel are missing. Pivot friction may set angle but cannot be the sole PTO reaction lock; metal gusset/stop, anti-slip and witness marks remain candidates.\n"
 out["PTO_20T20T.md"]=H+"\n`COMMON_PTO_HS_1TO1`: 20T→20T, 1:1, shaft candidate along Y. Metal plate→KP000→shaft→KP000→metal plate; permanent cantilever prohibited. Exact transform and powered operation remain HOLD/NOT_APPROVED.\n"
 out["KP000_INTERFACE.md"]=H+"\nPhysical precedence adds mounting-hole centre distance 53.0 MEASURED to the existing 67×17×35, axis18.5±0.5, bore10 and one-side protrusion6 reference. Crawler8 + PTO/related4 =12. Opposite protrusion and final plate holes remain HOLD.\n"
 out["BEARING_6000_UPDATE.md"]=H+"\nOD25.9 MEASURED, PETG seat26.0 TARGET (+0.1 diametral), centre clearance12.0 UNCHANGED. Updated external-only STL is not promoted into source authority. Physical fit remains PENDING; roller exterior and 12T teeth are protected.\n"
 out["H25A1_2S_DESIGN.md"]=H+"\n`H25A1_2S_DUAL_SET_SCREW_REACTION_KEY`: φ10 shaft→two M4 screws→metal collar→dual replaceable key→PETG hub→one-piece 12T. Cover bolts are not torque path. No radial tooth/root access; external protected volume delta is 0. Metal compression sleeves are STRONGLY_RECOMMENDED.\n"
 out["H25A1_2S_COLLAR_MEASUREMENTS.md"]=H+"\nCollar OD15.9, ID10.1, W3.0. Two M4 set screws at90°, measured major OD≈3.8, length4.0, tightened projection1.0. Pitch is HOLD. Collar coupon bores:16.00/16.10/16.20.\n"
 out["H25A1_2S_REACTION_KEY.md"]=H+"\nSelected `A2_DUAL_REPLACEABLE_REACTION_KEY`. It positively receives both 90° screw features while remaining inside the protected root. Slot coupons4.1/4.2/4.3; final slot, shear, crushing and removal fit are PHYSICAL_TEST_REQUIRED. Circular friction-only capture is REJECT.\n"
 out["H25A1_2S_TEST_PLAN.md"]=H+"\nCoupon→collar/shaft/two-screw assembly→witness mark→cover→hand rotation→20 forward/reverse turns→0.25/0.50/0.75 N·m staged static torque→24 h witness recheck. Any slip, collar rotation, screw loosening, key crush, PETG whitening/crack or interference is FAIL.\n"
 out["BATTERY_MEASUREMENT.md"]=H+"\nGOLDENMATE LiFePO4 12.8V 10Ah 128Wh; 150.9×99.4×92.5 body; mass1.2kg MEASURED. Label IP67 is a manufacturer claim and does not waive BBOX waterproofing. Terminal top≈Z225 USER_REPORTED; terminal footprint, connector and wire bend are HOLD.\n"
 out["BBOX_ARCHITECTURE.md"]=H+"\nSealed removable cassette, low/inside frame, shell contact with water ALLOWED and internal contact NOT_ALLOWED. Dedicated frame rails/skids only; idler-shaft support REJECT. Retention requires hard stop + primary lock + independent pin. Manual high connector; no blind mate.\n"
 out["BBOX_CASSETTE.md"]=H+"\nStudy envelope: X180, lower Y114, total available Z130.7 with a Y94 local top zone. Battery body margins are X29.1 total and Y14.6 total. The stepped upper zone is not a final terminal dome or waterproof shell. Only 7–13 mm remains above the reported terminal before lid, insulation, vibration and cable bend; final shell is HOLD. Bambu A1 waterproof-shell printability is not approved until gasket face, unsupported roof, bridge, seam and bed-slinger orientation are resolved.\n"
 out["BBOX_BUOYANCY.md"]=H+f"\nAt Z150 and the two support datums, the 180×114 candidate displaces {g['buoyancy']['partial_displacement_l_range'][0]:.3f}–{g['buoyancy']['partial_displacement_l_range'][1]:.3f} L ({g['buoyancy']['buoyant_force_n_range'][0]:.2f}–{g['buoyancy']['buoyant_force_n_range'][1]:.2f} N). With the 1.2kg battery and excluding unknown BBOX mass, apparent downward load is {g['buoyancy']['net_downward_kgf_excluding_bbox_mass_range'][0]:.3f}–{g['buoyancy']['net_downward_kgf_excluding_bbox_mass_range'][1]:.3f} kgf plus BBOX mass. DERIVED only; water test required.\n"
 out["BBOX_TEST_PLAN.md"]=H+"\nDry fit, insertion/removal×20, lock×20, safety pin×20, dummy1.2kg, empty waterproof, weighted waterproof, partial and temporary full submersion. Real battery installation only after empty/weighted waterproof PHYSICAL_PASS.\n"
 out["CBOX_ARCHITECTURE.md"]=H+"\nFixed 180×94×45 universal electronics envelope in the front half, independently supported by frame. It does not load or move with BBOX. Electronics, penetrations, thermal layout and final waterproof body remain HOLD.\n"
 out["BBOX_CBOX_X_SERIAL_LAYOUT.md"]=H+"\nLAYOUT_A selected: rear BBOX X[-190,-10], 20mm middle gap, front CBOX X[10,190], 10mm end clearance each. BBOX withdraws −X away from the front drivetrain/PTO. LAYOUT_B puts BBOX/removal at the front and is rejected for drivetrain/diagonal/service congestion. X-serial is baseline; vertical stacking is false.\n"
 out["INTERFERENCE_REPORT.md"]=H+"\n"+"\n".join(f"- {k}: `{val}`" for k,val in v["interference"].items())+"\n\nUnknown transforms are HOLD, never zero-interference results.\n"
 out["SERVICEABILITY_REPORT.md"]=H+"\nBBOX reference sweep clears CBOX and has nominal 13mm lateral clearance per side in lower clear width; actual crawler/idler/KP000 and hand envelopes remain HOLD. H2.5 service is axial: cover, M4 access, key, collar, shaft, bearing; no radial tooth/root tool path. CBOX remains fixed during battery service. Known-mass-only battery CG is Z147.55–153.55 at X−100 with −120kg·mm X moment. Raising unknown upper drivetrain masses by40mm is adverse, but whole-rover CG is HOLD because their masses are unknown.\n"
 out["MISSING_MEASUREMENTS.md"]=H+"\n"+"\n".join(f"- `{x}`: HOLD" for x in v["missing_measurements"])+"\n"
 out["DESIGN_GATE.md"]=H+"\n"+"\n".join(f"- `{k}`: `{val}`" for k,val in v["checks"].items())+"\n\nManufacturing, cutting, waterproof release, powered rotation and field deployment are not approved.\n"
 return out

def svg(title:str,body:str)->str: return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 500"><style>text{{font-family:Arial;fill:#17212b}}.f{{fill:none;stroke:#334e68;stroke-width:2}}.n{{fill:#d9eafd;stroke:#245b8a}}.o{{fill:#ddd;stroke:#666}}.h{{fill:#fbd5d5;stroke:#a33}}.w{{stroke:#168aad;stroke-width:3;stroke-dasharray:10 7}}.a{{stroke:#c44;stroke-width:5}}</style><rect width="100%" height="100%" fill="#fbfcfe"/><text x="24" y="34" font-size="22">{title}</text>{body}<text x="24" y="480" font-size="13">v0.9.4.1 · PHYSICAL_INTEGRATION_REVISION · HOLD · NOT_FOR_MANUFACTURING</text></svg>'
def create_drawings()->None:
 values={
 "top_view.svg":'<rect class="n" x="230" y="125" width="540" height="181"/><rect class="h" x="310" y="160" width="180" height="114"/><rect class="n" x="510" y="170" width="180" height="94"/><text x="330" y="220">BBOX rear</text><text x="545" y="220">CBOX front</text><path class="a" d="M310 290H100"/><text x="90" y="315">−X removal</text>',
 "front_view.svg":'<line class="w" x1="100" y1="270" x2="900" y2="270"/><rect class="n" x="410" y="90" width="181" height="190"/><rect class="h" x="444" y="150" width="114" height="120"/><text x="610" y="100">new structural 190</text><text x="610" y="270">water Z150</text>',
 "side_view.svg":'<line class="w" x1="60" y1="270" x2="940" y2="270"/><rect class="n" x="230" y="80" width="540" height="190" fill-opacity=".25"/><rect class="h" x="310" y="145" width="180" height="125"/><rect class="n" x="510" y="185" width="180" height="45"/><line class="a" x1="721" y1="270" x2="770" y2="80"/><text x="70" y="263">water Z150</text><text x="310" y="140">BBOX stepped top</text><text x="520" y="180">CBOX</text>',
 "frame_150_vs_190.svg":'<rect class="o" x="180" y="180" width="300" height="150"/><rect class="n" x="520" y="140" width="300" height="190"/><path class="a" d="M520 180H820"/><text x="250" y="170">150 reference</text><text x="610" y="130">190 candidate</text><text x="610" y="175">+40 zone</text>',
 "waterline_190.svg":'<line class="w" x1="80" y1="260" x2="920" y2="260"/><line class="f" x1="100" y1="400" x2="900" y2="400"/><rect class="n" x="250" y="90" width="500" height="190"/><line class="h" x1="250" y1="96" x2="750" y2="96"/><line class="h" x1="250" y1="102" x2="750" y2="102"/><text x="100" y="390">ground Z0</text><text x="100" y="250">water Z150</text><text x="760" y="100">top Z252 / 258 conflict</text>',
 "diagonal_geometry.svg":f'<path class="a" d="M250 380L650 80"/><path class="f" d="M250 380H650V80"/><text x="390" y="410">ΔX 98</text><text x="665" y="235">ΔZ 190</text><text x="380" y="210">concept {DIAGONAL["concept_center_distance"]:.3f}</text>',
 "diagonal_cut_drawing.svg":'<path class="a" d="M220 360L720 100"/><rect class="h" x="190" y="340" width="64" height="40"/><rect class="h" x="690" y="80" width="64" height="40"/><text x="250" y="400">pivot rotation centres / end offsets unmeasured</text><text x="340" y="160">FINAL CUT LENGTH = HOLD</text>',
 "h25a1_2s_section.svg":'<circle class="n" cx="330" cy="250" r="130"/><circle class="o" cx="330" cy="250" r="34"/><path class="a" d="M364 250H430M330 216V150"/><path class="h" d="M425 235H455V265H425M315 155V125H345V155"/><text x="500" y="190">2×M4, 90°, projection1.0</text><text x="500" y="230">dual replaceable reaction key</text><text x="500" y="270">external 12T delta=0</text><text x="500" y="310">no radial tooth/root access</text>',
 "bbox_section.svg":'<rect class="h" x="260" y="180" width="360" height="210"/><rect class="h" x="400" y="120" width="120" height="60"/><rect class="n" x="310" y="220" width="270" height="150"/><line class="w" x1="100" y1="300" x2="900" y2="300"/><text x="325" y="215">battery body 150.9×99.4×92.5</text><text x="535" y="145">local top zone</text><text x="650" y="295">water Z150</text>',
 "bbox_removal_sequence.svg":'<rect class="h" x="520" y="170" width="220" height="130"/><rect class="n" x="750" y="180" width="170" height="110"/><path class="a" d="M520 235H130"/><text x="520" y="155">BBOX rear</text><text x="780" y="155">CBOX fixed</text><text x="160" y="220">disconnect → pin → lock → withdraw −X</text>',
 "bbox_cbox_x_serial.svg":'<rect class="h" x="150" y="170" width="360" height="140"/><rect class="n" x="550" y="180" width="360" height="120"/><text x="265" y="245">BBOX X180</text><text x="660" y="245">CBOX X180</text><text x="510" y="150">gap20</text><text x="215" y="330">LAYOUT A rear</text><text x="680" y="330">front drivetrain side</text>'}
 for name,body in values.items(): write(LANE/"drawings"/name,svg(name.replace("_"," ").upper(),body))

def build()->dict[str,Any]:
 before=repository_guard(False); f150=frame(150); f190=frame(190); diag=diagonal_geometry(); hp=h25(); bp=bbox_parts(); cp=cbox_parts(); integ=integration(); bat=battery(); cc=collar_coupon(); rc=reaction_coupon()
 jobs=[(f150,CAD[0]),(f190,CAD[1]),(f190,CAD[2]),(diag,CAD[3]),(hp["assembly"],CAD[4]),(hp["body"],CAD[5]),(hp["cover"],CAD[6]),(hp["collar"],CAD[7]),(cc,CAD[8]),(rc,CAD[9]),(hp["key"],CAD[10]),(bat,CAD[11]),(bp["candidate"],CAD[12]),(bp["sweep"],CAD[13]),(bp["rails"],CAD[14]),(cp["candidate"],CAD[15]),(cp["support"],CAD[16]),(integ,CAD[17]),(integ,CAD[18])]
 for shape,rel in jobs: export(shape,LANE/rel)
 create_drawings(); dims=dimensions_data(); interfaces=interfaces_data(); coord=coordinate_data(); hardware=hardware_data(); limits=test_limits_data(); geom=geometry_data(); valid=validation_data()
 for name,data in [("dimensions.json",dims),("interfaces.json",interfaces),("coordinate_system.json",coord),("hardware.json",hardware),("test_limits.json",limits),("geometry_manifest.json",geom),("validation_report.json",valid)]: write_json(LANE/name,data)
 for name,text in docs(dims,geom,valid).items(): write(LANE/name,text)
 write(LANE/"COMMIT_PATHS.txt","\n".join(f"{LANE_REL}/{p}" for p in PACKAGE_PATHS)); write(LANE/"MANIFEST.txt","\n".join(PACKAGE_PATHS)); write(LANE/"BUILD_LOG.txt",f"BUILD PASS\nversion={VERSION}\nCadQuery={cq.__version__}\nPython={sys.version.split()[0]}\npreflight_untracked={before['untracked_total']}\nparent=CAD_PASS"); write(LANE/"TEST_LOG.txt","PENDING_TEST_EXECUTION")
 hashed=[p for p in PACKAGE_PATHS if p!="SHA256SUMS.txt"]; write(LANE/"SHA256SUMS.txt","\n".join(f"{sha(LANE/p)}  {p}" for p in hashed))
 test=subprocess.run([sys.executable,"-B",str(LANE/"tests/test_common_rover_190mm_integration_v0941.py")],cwd=REPO_ROOT,text=True,encoding="utf-8",stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if test.returncode: raise RuntimeError(test.stdout)
 write(LANE/"TEST_LOG.txt",test.stdout); write(LANE/"SHA256SUMS.txt","\n".join(f"{sha(LANE/p)}  {p}" for p in hashed)); after=repository_guard(True)
 return {"status":"CAD_PASS","guard":after,"validation":valid}
def verify_files()->dict[str,Any]:
 missing=[p for p in PACKAGE_PATHS if not (LANE/p).is_file()]; extras=sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.relative_to(LANE).as_posix() not in PACKAGE_PATHS); manifest=(LANE/"MANIFEST.txt").read_text(encoding="utf-8").splitlines(); hashes={}
 for line in (LANE/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines(): digest,rel=line.split("  ",1); hashes[rel]=digest
 bad=[p for p,digest in hashes.items() if sha(LANE/p)!=digest]; d=json.loads((LANE/"dimensions.json").read_text(encoding="utf-8")); g=json.loads((LANE/"geometry_manifest.json").read_text(encoding="utf-8")); v=json.loads((LANE/"validation_report.json").read_text(encoding="utf-8"))
 checks={"package":not missing and not extras and manifest==PACKAGE_PATHS,"hashes":not bad,"frame":d["new_frame"]["height"]==190 and d["new_frame"]["increment"]==40,"battery":d["battery"]["x"]==150.9 and d["battery"]["mass_kg"]==1.2,"h25":d["set_screws"]["quantity"]==2 and d["set_screws"]["angle"]==90,"external":abs(g["h25a1_2s"]["external_12t_volume_delta"])<1e-6 and g["h25a1_2s"]["body_solid_count"]==1 and not g["h25a1_2s"]["radial_tooth_root_access"],"layout":g["layout"]["x_serial"] and not g["layout"]["vertical_stacking"],"release":not v["powered_rotation_approved"] and not v["field_deployment_approved"] and not v["physical_pass"]}
 if not all(checks.values()): raise RuntimeError({"checks":checks,"missing":missing,"extras":extras,"bad":bad})
 return {"status":"CAD_PASS","file_count":len(PACKAGE_PATHS),"checks":checks,"bad_hashes":bad}
def standalone_rebuild()->dict[str,Any]:
 with tempfile.TemporaryDirectory(prefix="ps_cr_v0941_") as td:
  out=Path(td); jobs=[(frame(150),"f150.step"),(frame(190),"f190.step"),(frame(190),"f190.stl"),(diagonal_geometry(),"diag.step"),(h25()["assembly"],"h25.step"),(collar_coupon(),"collar.stl"),(reaction_coupon(),"reaction.stl"),(battery(),"battery.step"),(bbox_parts()["candidate"],"bbox.step"),(cbox_parts()["candidate"],"cbox.step"),(integration(),"integration.step"),(integration(),"integration.stl")]
  for shape,name in jobs: export(shape,out/name)
  b=frame(190).BoundingBox(); checks={"outputs":len(list(out.iterdir()))==len(jobs),"x":abs(b.xlen-540)<1e-6,"y":abs(b.ylen-181)<1e-6,"z":abs(b.zlen-190)<1e-6,"nonempty":all((out/n).stat().st_size>0 for _,n in jobs)}
  if not all(checks.values()): raise RuntimeError(checks)
  return {"status":"CAD_PASS","output_count":len(jobs),"checks":checks}
def create_zip()->tuple[Path,str]:
 target=DOWNLOADS/f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
 if target.exists(): raise FileExistsError(target)
 with zipfile.ZipFile(target,"x",zipfile.ZIP_DEFLATED) as z:
  for rel in PACKAGE_PATHS: z.write(LANE/rel,rel)
 with zipfile.ZipFile(target) as z:
  names=z.namelist(); bad=[n for n in names if PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts]
  if z.testzip() or len(names)!=len(set(names)) or bad or sorted(names)!=PACKAGE_PATHS: raise RuntimeError("ZIP contract")
 return target,sha(target)
def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument("--build",action="store_true"); ap.add_argument("--verify",action="store_true"); ap.add_argument("--standalone-verify",action="store_true"); ap.add_argument("--standalone-rebuild",action="store_true"); ap.add_argument("--zip",action="store_true"); a=ap.parse_args(); result={}
 if not any(vars(a).values()): a.build=a.verify=True
 if a.build: result["build"]=build()
 if a.verify or a.standalone_verify:
  if a.verify: result["guard"]=repository_guard(True)
  result["verify"]=verify_files()
 if a.standalone_verify or a.standalone_rebuild: result["standalone_rebuild"]=standalone_rebuild()
 if a.zip:
  p,d=create_zip(); result["zip"]={"path":str(p),"sha256":d}
 print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
