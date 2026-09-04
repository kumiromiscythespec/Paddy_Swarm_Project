"""Contract tests for PTO_SERVO_SLIDING_IDLER_CLUTCH_V001."""
import importlib.util,json
from pathlib import Path
from cadquery import importers

LANE=Path(__file__).resolve().parents[1];bp=LANE/"build_pto_servo_sliding_idler_clutch_v001.py"
s=importlib.util.spec_from_file_location("b",bp);assert s and s.loader;b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
n=0
def ck(x,label):
 global n;n+=1
 if not x:raise AssertionError(label)
repo=b.repository_guard(True);p=json.loads((LANE/"design_parameters.json").read_text());v=json.loads((LANE/"validation_report.json").read_text())
for key in ("repository","branch","head","staged_zero","dirty_preserved","outside_preserved","authority_4","protected_9","scope","complete"):ck(repo["checks"][key],key)
ck(p["hardware"]["frame_outer_width_mm"]==205,"frame")
ck(p["hardware"]["pto_motor_shafts"]=={"count":2,"diameter_mm":6},"motor shafts")
ck(p["hardware"]["pto_output_shafts"]=={"count":2,"diameter_mm":10},"output shafts")
ck(p["transmission"]["motor_pulley_teeth"]==20 and p["transmission"]["output_pulley_teeth"]==20,"20/20")
ck(p["transmission"]["ratio"]==1.0,"ratio")
ck(p["transmission"]["shaft_diameter_adapter"]=="NOT_REQUIRED","adapter")
ck(p["architecture"]["motor_fixed"] and p["architecture"]["output_shaft_fixed"],"fixed")
ck(p["architecture"]["moving_parts"]==["IDLER_CARRIAGE","SERVO_LINK"],"moving")
ck(p["architecture"]["first_build"]=="ONE_SIDE_ONLY","one side")
ck(p["study"]["stroke_candidates_mm"]==[6.0,8.0,10.0,12.0],"strokes")
ck(p["study"]["permanent_notch_ids"]=={"10":3,"12":4,"6":1,"8":2},"notches")
ck(p["study"]["servo_sweep_candidates_deg"]==[45.0,60.0,75.0],"sweeps")
ck(p["study"]["over_center_candidates_deg"]==[0.0,3.0,5.0],"over center")
ck(len(p["study"]["kinematics"])==12,"kinematic rows")
for r in p["study"]["kinematics"]:ck(r["required_horn_radius_mm"]>0,"radius")
ck(p["study"]["winner"]=="HOLD_PHYSICAL_BELT_TEST","no false winner")
ck(p["guide"]["on_hard_stop"] and p["guide"]["off_hard_stop"],"stops")
ck(p["guide"]["servo_continuous_belt_load_path"] is False,"servo load")
ck(p["guide"]["switch_pads"]==["ON_SWITCH_RESERVED_PAD","OFF_SWITCH_RESERVED_PAD"],"switch pads")
ck(p["output"]["double_supported"],"double support")
ck(p["output"]["future_dual_total_width_candidate_mm"]==[265,285],"width")
ck(max(p["output"]["future_dual_total_width_candidate_mm"])<=290,"target")
ck(max(p["output"]["future_dual_total_width_candidate_mm"])<300,"ceiling")
ck(p["idler"]["route"]=="SMOOTH_ROLLER_ON_BELT_BACKSIDE","idler route")
ck("REJECTED" in p["idler"]["repository_inventory"],"inventory firewall")
ck(p["hardware"]["horn"]["hole_radii"]=="PHYSICAL_HOLD","horn hold")
ck(p["electrical"]["servo_supply"]=="DEDICATED_BEC_NOT_ESP32_5V","BEC")
ck(p["electrical"]["common_ground"],"ground")
ck(p["operation"][0]=="PTO_MOTOR_STOP" and p["operation"][-1]=="ENABLE_PTO_MOTOR","sequence")
ck(len(b.EXPECTED)==39,"paths")
ck(len((LANE/"COMMIT_PATHS.txt").read_text().splitlines())==39,"commit paths")
ck(len(b.STEPS)==7 and len(b.STLS)==4 and len(b.SVGS)==9,"counts")
for rel in b.STEPS:
 sh=importers.importStep(str(LANE/rel));ck(sh.val().isValid(),rel);ck(len(sh.solids().vals())>0,rel+" solids")
for rel in b.STLS:
 a=b.stl_audit(LANE/rel);ck(a["watertight"] and a["manifold"],rel);ck(a["bad_edges"]==0 and a["degenerate_triangles"]==0,rel+" quality")
for rel in b.SVGS:
 text=(LANE/rel).read_text(encoding="utf-8");ck(text.startswith("<svg"),rel);ck(b.VERSION in text,rel+" version")
for stroke,rel in zip(b.STROKES,b.STEPS[2:6]):
 bb=importers.importStep(str(LANE/rel)).val().BoundingBox();ck(round(bb.ylen,3)==b.STOP_SPAN-stroke,"slider length")
ck(round(importers.importStep(str(LANE/b.STEPS[0])).val().BoundingBox().xlen,3)==245.0,"one-side width 245")
fixture_mesh=b.stl_audit(LANE/b.STLS[3]);ck(fixture_mesh["watertight"],"fixture final mesh")
ck(b.FIXTURE_DIMS==[160.0,130.0,26.0],"fixture dimensions authority")
fixture_bb=b.fixture().val().BoundingBox();ck([round(fixture_bb.xlen,3),round(fixture_bb.ylen,3),round(fixture_bb.zlen,3)]==b.FIXTURE_DIMS,"fixture generated dimensions")
assembly=importers.importStep(str(LANE/b.STEPS[6]));ck(len(assembly.solids().vals())>=12,"belt reference solids present")
ck(v["pass_count"]==v["check_count"],"validation")
ck(v["reproducibility"]["status"]=="PASS","repro")
ck(all(x["valid"] for x in v["steps"]),"steps")
ck(all(x["watertight"] for x in v["stls"].values()),"stls")
ck("ONE_SIDE_PHYSICAL_VALIDATION_PENDING" in v["status"],"status")
print(f"AUTOMATED_TESTS={n}/{n} PASS")
print("STEP_RELOAD=7/7 PASS")
print("STL_WATERTIGHT_MANIFOLD=4/4 PASS")
print("PROTECTED_TREES=9/9 UNCHANGED")
print("FINAL=PASS")
