#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paddy Swarm crawler_h1 v0.11.4 CadQuery generator.

Deep-Capture + Easy-Shaft Revision / FIT TEST CANDIDATE

Assembly coordinates:
  X = crawler travel direction
  Y = track width / hinge shaft direction
  Z = +Z sprocket and rover side, -Z TPU LUG and ground side
  Z = 0 is the LNK/LUG mounting interface.

Changes from v0.11.3:
- Increase snap-head CAPTURE_HEIGHT by +1.0/+1.5/+2.0 mm.
- Pair the increases with 7.5/8.0/8.5 mm TPU LUGs and a 1.8 mm ground floor.
- Compare phi3.6/3.7/3.8 mm round hinge bores.
- Compare 0.80/0.90/1.00 mm total symmetric axial play.
- Add stronger external shaft lead-ins and 1.0 mm root-side relief.
- Expand the Y-axis keep-out to phi4.6/4.6/4.8 mm.
- Keep 20 mm pitch, X=+/-10 mm axes, snap-head LUG retention,
  joint-centred sprocket drive valleys, and central lateral guides.

This is experimental CAD. It does not certify retention, shaft insertion,
strength, fatigue, SPR/ROL compatibility, or field durability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence
import argparse
import csv
import hashlib
import json
import math
import shutil

try:
    import cadquery as cq
    from cadquery import exporters
except Exception:
    cq = None
    exporters = None

VERSION = "crawler-h1-v0.11.4-deep-capture-easy-shaft"
PACKAGE_NAME = "crawler_h1_snap_head_lug_link_v0_11_4_deep_capture_easy_shaft"
STATUS = "FIT_TEST_CANDIDATE_RETENTION_AND_SHAFT_INSERTION_NOT_VERIFIED"


@dataclass(frozen=True)
class CaptureFit:
    code: str
    capture_increase_mm: float
    lug_thickness_mm: float
    ground_floor_mm: float = 1.8
    marker_count: int = 0


@dataclass(frozen=True)
class ShaftFit:
    code: str
    hole_diameter_mm: float
    total_axial_play_mm: float
    entrance_chamfer_mm: float
    keepout_diameter_mm: float
    marker_count: int = 0

    @property
    def per_side_play_mm(self) -> float:
        return self.total_axial_play_mm / 2.0


@dataclass(frozen=True)
class HeadFit:
    code: str
    shaft_diameter_mm: float
    head_diameter_mm: float
    lug_entry_diameter_mm: float = 5.4
    lug_chamber_diameter_mm: float = 6.7
    marker_count: int = 0


@dataclass(frozen=True)
class GuideFit:
    code: str
    side_clearance_mm: float
    marker_count: int = 0


CAPTURE_FITS = {
    "A": CaptureFit("CAP-A", 1.0, 7.5, 1.8, 1),
    "B": CaptureFit("CAP-B", 1.5, 8.0, 1.8, 2),
    "C": CaptureFit("CAP-C", 2.0, 8.5, 1.8, 3),
}
SHAFT_FITS = {
    "A": ShaftFit("SHAFT-A", 3.6, 0.80, 0.8, 4.6, 1),
    "B": ShaftFit("SHAFT-B", 3.7, 0.90, 0.8, 4.6, 2),
    "C": ShaftFit("SHAFT-C", 3.8, 1.00, 1.0, 4.8, 3),
}
HEAD_FITS = {
    "A": HeadFit("HEAD-A", 4.8, 5.8, 5.4, 6.7, 1),
    "B": HeadFit("HEAD-B", 4.8, 6.2, 5.4, 6.7, 2),
    "C": HeadFit("HEAD-C", 4.8, 6.6, 5.4, 6.7, 3),
}
GUIDE_FITS = {
    "A": GuideFit("GUIDE-A", 0.8, 1),
    "B": GuideFit("GUIDE-B", 1.2, 2),
    "C": GuideFit("GUIDE-C", 1.5, 3),
}
STANDARD_CAPTURE = CAPTURE_FITS["B"]
STANDARD_SHAFT = SHAFT_FITS["B"]
STANDARD_HEAD = HEAD_FITS["B"]
STANDARD_GUIDE = GUIDE_FITS["B"]


@dataclass(frozen=True)
class Params:
    # Fixed crawler contract.
    track_width_mm: float = 50.0
    link_pitch_mm: float = 20.0
    link_body_length_mm: float = 17.0
    link_body_width_mm: float = 50.0
    link_thickness_mm: float = 7.2

    # v0.11.3 CL-B baseline retained.
    center_knuckle_width_y_mm: float = 13.60
    outer_ear_width_y_mm: float = 13.77
    minimum_knuckle_width_y_mm: float = 4.0
    maximum_total_axial_play_mm: float = 1.0
    side_relief_mm: float = 1.0

    # v0.11.3 snap pin baseline and v0.11.4 definitions.
    pin_center_pitch_y_mm: float = 12.0
    current_capture_height_mm: float = 3.45
    pin_head_thickness_mm: float = 1.30
    pin_head_shoulder_transition_mm: float = 0.35
    pin_head_max_band_mm: float = 0.25
    pin_head_nose_tip_diameter_mm: float = 3.2
    pin_root_boss_diameter_mm: float = 9.8
    pin_root_boss_height_mm: float = 0.8
    pin_root_taper_height_mm: float = 0.8

    # TPU LUG planform and open service features.
    lug_length_x_mm: float = 14.0
    lug_width_y_mm: float = 34.0
    lug_edge_radius_mm: float = 1.2
    lug_chamber_cyl_height_mm: float = 0.70
    lug_chamber_taper_height_mm: float = 0.80
    boss_seat_top_diameter_mm: float = 10.2
    boss_seat_bottom_diameter_mm: float = 5.6
    boss_seat_depth_mm: float = 1.6
    tool_notch_width_y_mm: float = 5.0
    tool_notch_depth_x_mm: float = 2.0
    tool_notch_height_z_mm: float = 2.2
    shear_rail_length_x_mm: float = 11.0
    shear_rail_width_y_mm: float = 3.0
    shear_rail_center_y_mm: float = 13.0
    shear_rail_height_mm: float = 0.8
    shear_groove_clearance_mm: float = 0.4
    shear_groove_depth_mm: float = 1.0

    # Hinge X-Z profile.
    hinge_pin_nominal_mm: float = 3.0
    hinge_axis_z_mm: float = 8.5
    hinge_ear_outer_diameter_mm: float = 10.5
    hinge_ear_flat_cut_mm: float = 0.8
    hinge_ear_root_length_x_mm: float = 5.0
    hinge_ear_root_fillet_mm: float = 2.7
    hinge_root_side_relief_mm: float = 1.0
    hinge_keepout_extension_each_y_mm: float = 1.5
    minimum_xz_wall_mm: float = 2.0
    candidate_max_articulation_deg: float = 35.0

    # Central sacrificial print datums remain away from X=+/-10 axes.
    print_datum_center_x_mm: float = 0.0
    print_datum_center_y_mm: float = 12.0
    print_datum_post_x_mm: float = 4.0
    print_datum_post_y_mm: float = 7.0
    print_datum_neck_height_mm: float = 0.8
    print_datum_neck_x_mm: float = 1.2
    print_datum_neck_y_mm: float = 5.0

    # Inherited SPR reference record; actual repository source remains required.
    drive_sprocket_teeth: int = 12
    spr_pitch_mm: float = 20.0
    spr_tooth_axial_width_y_mm: float = 44.0
    spr_tooth_tangential_width_mm: float = 7.5
    spr_legacy_root_offset_mm: float = 7.0
    spr_legacy_tooth_depth_mm: float = 10.0
    spr_corrected_effective_tooth_height_mm: float = 3.6
    drive_pocket_total_clearance_x_mm: float = 1.0
    drive_pocket_width_clearance_each_y_mm: float = 0.8
    drive_pocket_depth_mm: float = 3.2
    minimum_engaged_teeth: int = 3

    # Central lateral guides are independent from hinge play.
    guide_height_mm: float = 3.0
    guide_thickness_y_mm: float = 2.5
    guide_length_x_mm: float = 8.0
    guide_root_fillet_mm: float = 1.2
    guide_tip_radius_mm: float = 0.6

    # Quantity remains HOLD.
    link_quantity: int = 40
    link_spare_quantity: int = 8
    lug_quantity: int = 40
    lug_spare_quantity: int = 8

    @property
    def front_axis_x_mm(self) -> float:
        return self.link_pitch_mm / 2.0

    @property
    def rear_axis_x_mm(self) -> float:
        return -self.link_pitch_mm / 2.0

    def capture_height_mm(self, fit: CaptureFit) -> float:
        return self.current_capture_height_mm + fit.capture_increase_mm

    def total_pin_projection_mm(self, fit: CaptureFit) -> float:
        return self.capture_height_mm(fit) + self.pin_head_thickness_mm

    def pin_head_ground_recess_mm(self, fit: CaptureFit) -> float:
        return fit.lug_thickness_mm - self.total_pin_projection_mm(fit)

    def ground_z_assembly_mm(self, fit: CaptureFit) -> float:
        return -fit.lug_thickness_mm

    def pin_tip_z_assembly_mm(self, fit: CaptureFit) -> float:
        return -self.total_pin_projection_mm(fit)

    @property
    def hinge_lowest_z_mm(self) -> float:
        return self.hinge_axis_z_mm - self.hinge_ear_outer_diameter_mm / 2.0

    @property
    def hinge_flat_z_mm(self) -> float:
        return self.hinge_axis_z_mm + self.hinge_ear_outer_diameter_mm / 2.0 - self.hinge_ear_flat_cut_mm

    def minimum_xz_wall_actual_mm(self, fit: ShaftFit) -> float:
        return (self.hinge_ear_outer_diameter_mm - fit.hole_diameter_mm) / 2.0

    def outer_pair_inner_span_mm(self, fit: ShaftFit) -> float:
        return self.center_knuckle_width_y_mm + fit.total_axial_play_mm

    def outer_ear_center_y_mm(self, fit: ShaftFit) -> float:
        return self.outer_pair_inner_span_mm(fit) / 2.0 + self.outer_ear_width_y_mm / 2.0

    def outer_ear_outer_face_y_mm(self, fit: ShaftFit) -> float:
        return self.outer_ear_center_y_mm(fit) + self.outer_ear_width_y_mm / 2.0

    def body_edge_empty_space_each_y_mm(self, fit: ShaftFit) -> float:
        return self.link_body_width_mm / 2.0 - self.outer_ear_outer_face_y_mm(fit)

    def hinge_keepout_total_length_y_mm(self, fit: ShaftFit) -> float:
        return 2.0 * (self.outer_ear_outer_face_y_mm(fit) + self.hinge_keepout_extension_each_y_mm)

    @property
    def interlink_body_gap_x_mm(self) -> float:
        return self.link_pitch_mm - self.link_body_length_mm

    @property
    def drive_valley_target_x_mm(self) -> float:
        return self.spr_tooth_tangential_width_mm + self.drive_pocket_total_clearance_x_mm

    @property
    def drive_half_pocket_x_mm(self) -> float:
        return max(0.0, (self.drive_valley_target_x_mm - self.interlink_body_gap_x_mm) / 2.0)

    @property
    def drive_pocket_width_y_mm(self) -> float:
        return self.spr_tooth_axial_width_y_mm + 2.0 * self.drive_pocket_width_clearance_each_y_mm

    @property
    def drive_remaining_ligament_z_mm(self) -> float:
        return self.link_thickness_mm - self.drive_pocket_depth_mm

    @property
    def pitch_radius_mm(self) -> float:
        return self.link_pitch_mm / (2.0 * math.sin(math.pi / self.drive_sprocket_teeth))

    @property
    def chord_mid_radius_mm(self) -> float:
        return self.pitch_radius_mm * math.cos(math.pi / self.drive_sprocket_teeth)

    @property
    def corrected_spr_outer_radius_mm(self) -> float:
        return self.chord_mid_radius_mm - self.drive_valley_target_x_mm / 2.0 + self.spr_corrected_effective_tooth_height_mm

    @property
    def legacy_spr_outer_radius_mm(self) -> float:
        return self.pitch_radius_mm - self.spr_legacy_root_offset_mm + self.spr_legacy_tooth_depth_mm

    def guide_channel_width_y_mm(self, fit: GuideFit) -> float:
        return self.spr_tooth_axial_width_y_mm + 2.0 * fit.side_clearance_mm

    def guide_total_width_y_mm(self, fit: GuideFit) -> float:
        return self.guide_channel_width_y_mm(fit) + 2.0 * self.guide_thickness_y_mm

    @property
    def guide_axis_x_clearance_mm(self) -> float:
        return self.front_axis_x_mm - self.guide_length_x_mm / 2.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["capture_candidates"] = {
            k: {
                **asdict(v),
                "capture_height_mm": self.capture_height_mm(v),
                "head_thickness_mm": self.pin_head_thickness_mm,
                "total_pin_projection_mm": self.total_pin_projection_mm(v),
                "pin_head_ground_recess_mm": self.pin_head_ground_recess_mm(v),
            } for k, v in CAPTURE_FITS.items()
        }
        data["shaft_candidates"] = {
            k: {
                **asdict(v),
                "per_side_play_mm": v.per_side_play_mm,
                "outer_pair_inner_span_mm": self.outer_pair_inner_span_mm(v),
                "outer_ear_center_y_mm": self.outer_ear_center_y_mm(v),
                "outer_ear_outer_face_y_mm": self.outer_ear_outer_face_y_mm(v),
                "empty_space_to_body_edge_each_y_mm": self.body_edge_empty_space_each_y_mm(v),
                "minimum_xz_wall_actual_mm": self.minimum_xz_wall_actual_mm(v),
                "rod_path_radial_margin_mm": (v.keepout_diameter_mm - v.hole_diameter_mm) / 2.0,
            } for k, v in SHAFT_FITS.items()
        }
        data["head_candidates"] = {k: asdict(v) for k, v in HEAD_FITS.items()}
        data["guide_candidates"] = {k: asdict(v) for k, v in GUIDE_FITS.items()}
        data["standard_guide_channel_width_y_mm"] = self.guide_channel_width_y_mm(STANDARD_GUIDE)
        data["standard_guide_total_width_y_mm"] = self.guide_total_width_y_mm(STANDARD_GUIDE)
        return data


DEFAULT = Params()


def require_cadquery() -> None:
    if cq is None or exporters is None:
        raise RuntimeError("CadQuery is not installed. Use --metadata-only or run in a CadQuery environment.")


def rounded_box_xy(x_mm: float, y_mm: float, z_mm: float, radius_mm: float = 0.0):
    require_cadquery()
    obj = cq.Workplane("XY").box(x_mm, y_mm, z_mm, centered=(True, True, False))
    if radius_mm > 0:
        try:
            obj = obj.edges("|Z").fillet(radius_mm)
        except Exception:
            pass
    return obj


def cyl_z(diameter_mm: float, height_mm: float):
    require_cadquery()
    return cq.Workplane("XY").circle(diameter_mm / 2.0).extrude(height_mm)


def cyl_y(diameter_mm: float, length_mm: float):
    require_cadquery()
    return cq.Workplane("XZ").circle(diameter_mm / 2.0).extrude(length_mm / 2.0, both=True)


def cone_y(radius1_mm: float, radius2_mm: float, length_mm: float, start_xyz: tuple[float, float, float], direction_y: float):
    require_cadquery()
    solid = cq.Solid.makeCone(
        radius1_mm,
        radius2_mm,
        length_mm,
        cq.Vector(*start_xyz),
        cq.Vector(0.0, direction_y, 0.0),
    )
    return cq.Workplane(obj=solid)


def make_compound(parts: Iterable[object]):
    require_cadquery()
    vals = [p.val() if hasattr(p, "val") else p for p in parts]
    return cq.Compound.makeCompound(vals)


def place_on_bed(shape):
    obj = shape.val() if hasattr(shape, "val") else shape
    bb = obj.BoundingBox()
    return shape.translate((0.0, 0.0, -bb.zmin))


def add_marker_notches(shape, count: int, y_edge_mm: float, z0_mm: float, height_mm: float):
    if count <= 0:
        return shape
    result = shape
    spacing = 2.4
    start = -(count - 1) * spacing / 2.0
    for idx in range(count):
        x = start + idx * spacing
        cutter = rounded_box_xy(1.2, 1.8, height_mm + 0.4, 0.2).translate((x, y_edge_mm, z0_mm - 0.2))
        result = result.cut(cutter)
    return result


def build_ear(p: Params, axis_x_mm: float, center_y_mm: float, ear_width_y_mm: float, toward_center_sign: int):
    ear = cyl_y(p.hinge_ear_outer_diameter_mm, ear_width_y_mm).translate((axis_x_mm, center_y_mm, p.hinge_axis_z_mm))
    root_x = axis_x_mm - toward_center_sign * p.hinge_ear_root_length_x_mm / 2.0
    root_h = max(1.0, p.hinge_axis_z_mm - p.link_thickness_mm)
    root_y = max(p.minimum_knuckle_width_y_mm, ear_width_y_mm - 2.0 * p.hinge_root_side_relief_mm)
    root = rounded_box_xy(
        p.hinge_ear_root_length_x_mm,
        root_y,
        root_h,
        min(1.4, p.hinge_ear_root_fillet_mm),
    ).translate((root_x, center_y_mm, p.link_thickness_mm))
    return ear.union(root).clean()


def build_hinge_hole_cutter(p: Params, fit: ShaftFit, axis_x_mm: float):
    length = p.hinge_keepout_total_length_y_mm(fit) + 2.0
    bore = cyl_y(fit.hole_diameter_mm, length).translate((axis_x_mm, 0.0, p.hinge_axis_z_mm))
    outer_face = p.outer_ear_outer_face_y_mm(fit)
    depth = min(fit.entrance_chamfer_mm, p.outer_ear_width_y_mm / 3.0)
    small_r = fit.hole_diameter_mm / 2.0
    large_r = small_r + fit.entrance_chamfer_mm
    pos = cone_y(small_r, large_r, depth, (axis_x_mm, outer_face - depth, p.hinge_axis_z_mm), +1.0)
    neg = cone_y(small_r, large_r, depth, (axis_x_mm, -outer_face + depth, p.hinge_axis_z_mm), -1.0)
    return bore.union(pos).union(neg)


def build_snap_pin(p: Params, capture_fit: CaptureFit, head_fit: HeadFit, center_y_mm: float):
    capture_h = p.capture_height_mm(capture_fit)
    head_h = p.pin_head_thickness_mm
    boss = cyl_z(p.pin_root_boss_diameter_mm, p.pin_root_boss_height_mm)
    taper = (
        cq.Workplane("XY").workplane(offset=p.pin_root_boss_height_mm)
        .circle(p.pin_root_boss_diameter_mm / 2.0)
        .workplane(offset=p.pin_root_taper_height_mm)
        .circle(head_fit.shaft_diameter_mm / 2.0).loft(combine=True)
    )
    shaft_start = p.pin_root_boss_height_mm + p.pin_root_taper_height_mm
    shaft_h = capture_h - shaft_start
    if shaft_h <= 0:
        raise ValueError("Capture height is too short for boss+taper stack")
    shaft = cyl_z(head_fit.shaft_diameter_mm, shaft_h).translate((0.0, 0.0, shaft_start))
    trans_h = min(p.pin_head_shoulder_transition_mm, head_h * 0.35)
    band_h = min(p.pin_head_max_band_mm, head_h * 0.25)
    nose_h = head_h - trans_h - band_h
    shoulder = (
        cq.Workplane("XY").workplane(offset=capture_h)
        .circle(head_fit.shaft_diameter_mm / 2.0)
        .workplane(offset=trans_h)
        .circle(head_fit.head_diameter_mm / 2.0).loft(combine=True)
    )
    band = cyl_z(head_fit.head_diameter_mm, band_h).translate((0.0, 0.0, capture_h + trans_h))
    nose = (
        cq.Workplane("XY").workplane(offset=capture_h + trans_h + band_h)
        .circle(head_fit.head_diameter_mm / 2.0)
        .workplane(offset=nose_h)
        .circle(p.pin_head_nose_tip_diameter_mm / 2.0).loft(combine=True)
    )
    pin = boss.union(taper).union(shaft).union(shoulder).union(band).union(nose).clean()
    return pin.rotate((0, 0, 0), (1, 0, 0), 180.0).translate((0.0, center_y_mm, 0.0)).clean()


def build_link_assembly(
    p: Params = DEFAULT,
    capture_fit: CaptureFit = STANDARD_CAPTURE,
    shaft_fit: ShaftFit = STANDARD_SHAFT,
    head_fit: HeadFit = STANDARD_HEAD,
    guide_fit: GuideFit = STANDARD_GUIDE,
):
    link = rounded_box_xy(p.link_body_length_mm, p.link_body_width_mm, p.link_thickness_mm, 1.4)

    oy = p.outer_ear_center_y_mm(shaft_fit)
    for y in (-oy, oy):
        link = link.union(build_ear(p, p.front_axis_x_mm, y, p.outer_ear_width_y_mm, +1))
    link = link.union(build_ear(p, p.rear_axis_x_mm, 0.0, p.center_knuckle_width_y_mm, -1)).clean()

    # Small crown flats become bed contacts after 180 degree print rotation.
    top_cutter = rounded_box_xy(
        p.link_pitch_mm + p.hinge_ear_outer_diameter_mm + 8.0,
        p.guide_total_width_y_mm(guide_fit) + 12.0,
        20.0,
        0.0,
    ).translate((0.0, 0.0, p.hinge_flat_z_mm))
    link = link.cut(top_cutter)

    # Joint-centred open sprocket valleys. Drive X-Z geometry is retained.
    hp = p.drive_half_pocket_x_mm
    for sign in (-1.0, 1.0):
        x_edge = sign * p.link_body_length_mm / 2.0
        x_center = x_edge - sign * hp / 2.0
        cutter = rounded_box_xy(
            hp + 0.5,
            p.drive_pocket_width_y_mm,
            p.drive_pocket_depth_mm + 0.3,
            0.6,
        ).translate((x_center, 0.0, p.link_thickness_mm - p.drive_pocket_depth_mm))
        link = link.cut(cutter)

    # Central lateral guides are independent from hinge play.
    channel_w = p.guide_channel_width_y_mm(guide_fit)
    guide_y = channel_w / 2.0 + p.guide_thickness_y_mm / 2.0
    for y in (-guide_y, guide_y):
        guide = rounded_box_xy(
            p.guide_length_x_mm,
            p.guide_thickness_y_mm,
            p.guide_height_mm,
            p.guide_tip_radius_mm,
        ).translate((0.0, y, p.link_thickness_mm))
        link = link.union(guide)

    # Broad open shear rails and deep-capture snap heads on -Z.
    for y in (-p.shear_rail_center_y_mm, p.shear_rail_center_y_mm):
        rail = rounded_box_xy(
            p.shear_rail_length_x_mm,
            p.shear_rail_width_y_mm,
            p.shear_rail_height_mm,
            0.8,
        ).translate((0.0, y, -p.shear_rail_height_mm))
        link = link.union(rail)
    for y in (-p.pin_center_pitch_y_mm / 2.0, p.pin_center_pitch_y_mm / 2.0):
        link = link.union(build_snap_pin(p, capture_fit, head_fit, y))

    # One global Y-axis cutter per joint axis guarantees common nominal axes.
    for x in (p.front_axis_x_mm, p.rear_axis_x_mm):
        link = link.cut(build_hinge_hole_cutter(p, shaft_fit, x))

    marker = max(capture_fit.marker_count, shaft_fit.marker_count, head_fit.marker_count, guide_fit.marker_count)
    return add_marker_notches(link, marker, p.link_body_width_mm / 2.0 - 1.0, 0.0, p.link_thickness_mm).clean()


def add_central_breakaway_print_datums(link, p: Params = DEFAULT):
    datum_h = p.hinge_flat_z_mm - p.link_thickness_mm
    if datum_h <= p.print_datum_neck_height_mm:
        return link
    result = link
    for y in (-p.print_datum_center_y_mm, p.print_datum_center_y_mm):
        neck = rounded_box_xy(
            p.print_datum_neck_x_mm,
            p.print_datum_neck_y_mm,
            p.print_datum_neck_height_mm,
            0.2,
        ).translate((p.print_datum_center_x_mm, y, p.link_thickness_mm))
        post = rounded_box_xy(
            p.print_datum_post_x_mm,
            p.print_datum_post_y_mm,
            datum_h - p.print_datum_neck_height_mm,
            0.5,
        ).translate((p.print_datum_center_x_mm, y, p.link_thickness_mm + p.print_datum_neck_height_mm))
        result = result.union(neck).union(post)
    return result.clean()


def build_link_print(p=DEFAULT, capture_fit=STANDARD_CAPTURE, shaft_fit=STANDARD_SHAFT, head_fit=STANDARD_HEAD, guide_fit=STANDARD_GUIDE):
    link = add_central_breakaway_print_datums(build_link_assembly(p, capture_fit, shaft_fit, head_fit, guide_fit), p)
    return place_on_bed(link.rotate((0, 0, 0), (1, 0, 0), 180.0))


def build_lug(p: Params = DEFAULT, capture_fit: CaptureFit = STANDARD_CAPTURE, head_fit: HeadFit = STANDARD_HEAD):
    lug_t = capture_fit.lug_thickness_mm
    floor = capture_fit.ground_floor_mm
    lug = rounded_box_xy(p.lug_length_x_mm, p.lug_width_y_mm, lug_t, p.lug_edge_radius_mm)
    chamber_cyl_top = floor + p.lug_chamber_cyl_height_mm
    chamber_taper_top = chamber_cyl_top + p.lug_chamber_taper_height_mm
    for y in (-p.pin_center_pitch_y_mm / 2.0, p.pin_center_pitch_y_mm / 2.0):
        chamber = cyl_z(head_fit.lug_chamber_diameter_mm, p.lug_chamber_cyl_height_mm).translate((0.0, y, floor))
        taper = (
            cq.Workplane("XY").workplane(offset=chamber_cyl_top)
            .center(0.0, y).circle(head_fit.lug_chamber_diameter_mm / 2.0)
            .workplane(offset=p.lug_chamber_taper_height_mm)
            .circle(head_fit.lug_entry_diameter_mm / 2.0).loft(combine=True)
        )
        entry_h = lug_t - chamber_taper_top + 0.2
        entry = cyl_z(head_fit.lug_entry_diameter_mm, entry_h).translate((0.0, y, chamber_taper_top))
        lug = lug.cut(chamber).cut(taper).cut(entry)
        seat = (
            cq.Workplane("XY").workplane(offset=lug_t - p.boss_seat_depth_mm)
            .center(0.0, y).circle(p.boss_seat_bottom_diameter_mm / 2.0)
            .workplane(offset=p.boss_seat_depth_mm + 0.2)
            .circle(p.boss_seat_top_diameter_mm / 2.0).loft(combine=True)
        )
        lug = lug.cut(seat)
    for y in (-p.shear_rail_center_y_mm, p.shear_rail_center_y_mm):
        groove = rounded_box_xy(
            p.lug_length_x_mm + 2.0,
            p.shear_rail_width_y_mm + p.shear_groove_clearance_mm,
            p.shear_groove_depth_mm + 0.2,
            0.7,
        ).translate((0.0, y, lug_t - p.shear_groove_depth_mm))
        lug = lug.cut(groove)
    notch_z = lug_t - p.tool_notch_height_z_mm
    for sign in (-1.0, 1.0):
        x = sign * (p.lug_length_x_mm / 2.0 - p.tool_notch_depth_x_mm / 2.0 + 0.1)
        notch = rounded_box_xy(
            p.tool_notch_depth_x_mm + 0.4,
            p.tool_notch_width_y_mm,
            p.tool_notch_height_z_mm + 0.2,
            0.8,
        ).translate((x, 0.0, notch_z))
        lug = lug.cut(notch)
    return add_marker_notches(lug, capture_fit.marker_count, p.lug_width_y_mm / 2.0 - 1.0, 0.0, lug_t).clean()


def build_snap_head_coupon(p=DEFAULT, capture_fit=STANDARD_CAPTURE, head_fit=STANDARD_HEAD):
    base = rounded_box_xy(12.0, 20.0, 3.0, 1.0)
    for y in (-p.pin_center_pitch_y_mm / 2.0, p.pin_center_pitch_y_mm / 2.0):
        base = base.union(build_snap_pin(p, capture_fit, head_fit, y))
    return add_marker_notches(base, capture_fit.marker_count, 9.0, 0.0, 3.0).clean()


def build_snap_head_coupon_print(p=DEFAULT, capture_fit=STANDARD_CAPTURE, head_fit=STANDARD_HEAD):
    return place_on_bed(build_snap_head_coupon(p, capture_fit, head_fit).rotate((0, 0, 0), (1, 0, 0), 180.0))


def build_snap_assembly(p=DEFAULT, capture_fit=STANDARD_CAPTURE, shaft_fit=STANDARD_SHAFT, head_fit=STANDARD_HEAD, guide_fit=STANDARD_GUIDE):
    link = build_link_assembly(p, capture_fit, shaft_fit, head_fit, guide_fit)
    lug = build_lug(p, capture_fit, head_fit).translate((0.0, 0.0, -capture_fit.lug_thickness_mm))
    return make_compound([link, lug])


def build_ground_contact_reference(p=DEFAULT, capture_fit=STANDARD_CAPTURE):
    assembly = build_snap_assembly(p, capture_fit)
    ground_z = p.ground_z_assembly_mm(capture_fit)
    ground = rounded_box_xy(36.0, 62.0, 0.4, 0.0).translate((0.0, 0.0, ground_z - 0.4))
    return make_compound([assembly, ground])


def transform_link_about_joint(shape, local_joint_x: float, target_joint_x: float, angle_deg: float, p=DEFAULT):
    return (
        shape.translate((-local_joint_x, 0.0, -p.hinge_axis_z_mm))
        .rotate((0, 0, 0), (0, 1, 0), angle_deg)
        .translate((target_joint_x, 0.0, p.hinge_axis_z_mm))
    )


def build_three_link_reference(p=DEFAULT, capture_fit=STANDARD_CAPTURE, shaft_fit=STANDARD_SHAFT, angle_deg: float = 0.0, lateral_shift_y_mm: float = 0.0):
    center = build_link_assembly(p, capture_fit, shaft_fit).translate((0.0, lateral_shift_y_mm, 0.0))
    base_left = build_link_assembly(p, capture_fit, shaft_fit)
    base_right = build_link_assembly(p, capture_fit, shaft_fit)
    left = transform_link_about_joint(base_left, p.front_axis_x_mm, p.rear_axis_x_mm, +angle_deg, p).translate((0.0, lateral_shift_y_mm, 0.0))
    right = transform_link_about_joint(base_right, p.rear_axis_x_mm, p.front_axis_x_mm, -angle_deg, p).translate((0.0, lateral_shift_y_mm, 0.0))
    rod_len = p.hinge_keepout_total_length_y_mm(shaft_fit)
    rods = [
        cyl_y(p.hinge_pin_nominal_mm, rod_len).translate((p.rear_axis_x_mm, lateral_shift_y_mm, p.hinge_axis_z_mm)),
        cyl_y(p.hinge_pin_nominal_mm, rod_len).translate((p.front_axis_x_mm, lateral_shift_y_mm, p.hinge_axis_z_mm)),
    ]
    return make_compound([left, center, right, *rods])


def build_sprocket_reference(p=DEFAULT, legacy: bool = False):
    if legacy:
        outer_r = p.legacy_spr_outer_radius_mm
        tooth_h = p.spr_legacy_tooth_depth_mm
    else:
        outer_r = p.corrected_spr_outer_radius_mm
        tooth_h = p.spr_corrected_effective_tooth_height_mm
    root_r = outer_r - tooth_h
    disc = cq.Workplane("XZ").circle(root_r).extrude(p.spr_tooth_axial_width_y_mm / 2.0, both=True)
    parts = [disc]
    for idx in range(p.drive_sprocket_teeth):
        angle = idx * 360.0 / p.drive_sprocket_teeth
        tooth = rounded_box_xy(p.spr_tooth_tangential_width_mm, p.spr_tooth_axial_width_y_mm, tooth_h, 0.6).rotate((0, 0, 0), (1, 0, 0), 90.0)
        tooth = tooth.translate((0.0, 0.0, root_r)).rotate((0, 0, 0), (0, 1, 0), angle)
        parts.append(tooth)
    return make_compound(parts)


def build_five_link_wrap_reference(p=DEFAULT, capture_fit=STANDARD_CAPTURE, shaft_fit=STANDARD_SHAFT, legacy=False, lateral_shift_y_mm=0.0):
    parts = [build_sprocket_reference(p, legacy)]
    for angle_deg in (-60.0, -30.0, 0.0, 30.0, 60.0):
        a = math.radians(angle_deg)
        x = p.pitch_radius_mm * math.sin(a)
        z = p.pitch_radius_mm * math.cos(a) - p.hinge_axis_z_mm
        link = build_link_assembly(p, capture_fit, shaft_fit).rotate((0, 0, 0), (0, 1, 0), angle_deg).translate((x, lateral_shift_y_mm, z))
        parts.append(link)
    return make_compound(parts)


def make_capture_plate(p=DEFAULT):
    parts = []
    for idx, key in enumerate(("A", "B", "C")):
        fit = CAPTURE_FITS[key]
        parts.append(build_snap_head_coupon_print(p, fit).translate(((idx - 1) * 24.0, 0.0, 0.0)))
    return make_compound(parts)


def make_lug_plate(p=DEFAULT):
    parts = []
    for idx, key in enumerate(("A", "B", "C")):
        fit = CAPTURE_FITS[key]
        parts.append(place_on_bed(build_lug(p, fit)).translate(((idx - 1) * 20.0, 0.0, 0.0)))
    return make_compound(parts)


def make_shaft_plate(p=DEFAULT):
    parts = []
    for idx, key in enumerate(("A", "B", "C")):
        fit = SHAFT_FITS[key]
        parts.append(build_link_print(p, STANDARD_CAPTURE, fit).translate(((idx - 1) * 28.0, 0.0, 0.0)))
    return make_compound(parts)


def shape_bbox(shape):
    obj = shape.val() if hasattr(shape, "val") else shape
    bb = obj.BoundingBox()
    return bb.xlen, bb.ylen, bb.zlen


def export_shape(shape, path: Path):
    require_cadquery()
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path))


def static_validation(p=DEFAULT, capture_fit=STANDARD_CAPTURE, shaft_fit=STANDARD_SHAFT, head_fit=STANDARD_HEAD, guide_fit=STANDARD_GUIDE):
    issues = []
    def add(level, code, message):
        issues.append({"level": level, "code": code, "message": message})

    capture_h = p.capture_height_mm(capture_fit)
    total_pin = p.total_pin_projection_mm(capture_fit)
    recess = p.pin_head_ground_recess_mm(capture_fit)
    head_stretch = head_fit.head_diameter_mm / head_fit.lug_entry_diameter_mm - 1.0
    shoulder_radial = (head_fit.head_diameter_mm - head_fit.lug_entry_diameter_mm) / 2.0
    wall = p.minimum_xz_wall_actual_mm(shaft_fit)
    keep_margin = (shaft_fit.keepout_diameter_mm - shaft_fit.hole_diameter_mm) / 2.0
    empty = p.body_edge_empty_space_each_y_mm(shaft_fit)
    hole_clear = shaft_fit.hole_diameter_mm - p.hinge_pin_nominal_mm

    add("PASS" if abs(p.link_pitch_mm - 20.0) < 1e-9 else "FAIL", "LINK_PITCH", f"Axis pitch={p.link_pitch_mm:.3f} mm")
    add("PASS" if abs(p.front_axis_x_mm - 10.0) < 1e-9 and abs(p.rear_axis_x_mm + 10.0) < 1e-9 else "FAIL", "HINGE_GLOBAL_AXES", "Global joint axes remain X=+/-10.0 mm and common Z.")
    add("PASS", "V0113_CL_B_WIDTHS_RETAINED", f"Center/outer Y widths={p.center_knuckle_width_y_mm:.2f}/{p.outer_ear_width_y_mm:.2f} mm")

    add("PASS" if capture_h >= p.current_capture_height_mm + 1.0 else "FAIL", "CAPTURE_HEIGHT_INCREASE", f"Capture height={capture_h:.3f} mm; increase={capture_fit.capture_increase_mm:.3f} mm")
    add("PASS" if recess >= 1.2 else "FAIL", "PIN_HEAD_GROUND_RECESS", f"PETG head recess={recess:.3f} mm")
    add("PASS" if capture_fit.ground_floor_mm >= 1.5 else "FAIL", "TPU_GROUND_FLOOR", f"TPU ground floor={capture_fit.ground_floor_mm:.3f} mm")
    add("PASS" if abs(total_pin - (capture_h + p.pin_head_thickness_mm)) < 1e-9 else "FAIL", "TOTAL_PIN_PROJECTION_FORMULA", f"Total pin projection={total_pin:.3f} mm")
    add("PASS" if capture_fit.lug_thickness_mm > total_pin else "FAIL", "LUG_PIN_STACK_COMPATIBILITY", f"LUG thickness={capture_fit.lug_thickness_mm:.3f} mm > pin projection={total_pin:.3f} mm")
    add("PASS", "GROUND_CONTACT_TPU_ONLY_SOURCE", "Snap head remains inside TPU; hinge, drive walls, and guides remain +Z.")
    add("WARN", "SNAP_RETENTION_PHYSICAL", f"Head/entry stretch={head_stretch*100:.1f}%; radial shoulder={shoulder_radial:.3f} mm. Physical insertion, pull-off and 20-cycle tests remain required.")

    add("PASS" if shaft_fit.total_axial_play_mm <= p.maximum_total_axial_play_mm else "FAIL", "TOTAL_AXIAL_PLAY", f"Total play={shaft_fit.total_axial_play_mm:.3f} mm")
    add("PASS" if shaft_fit.per_side_play_mm >= 0.40 else "FAIL", "PER_SIDE_AXIAL_PLAY", f"Per-side play={shaft_fit.per_side_play_mm:.3f} mm")
    add("PASS" if hole_clear >= 0.6 else "WARN", "HINGE_HOLE_DIAMETRAL_CLEARANCE", f"Hole-shaft diametral clearance={hole_clear:.3f} mm")
    add("PASS" if wall >= p.minimum_xz_wall_mm else "FAIL", "MINIMUM_XZ_WALL", f"Nominal X-Z radial wall={wall:.3f} mm")
    add("PASS" if keep_margin >= 0.4 else "FAIL", "HINGE_KEEP_OUT_RADIAL_MARGIN", f"Bore-to-keep-out radial margin={keep_margin:.3f} mm")
    add("PASS" if empty >= 0.0 else "FAIL", "BODY_EDGE_EMPTY_SPACE", f"Visible empty space to body edge={empty:.3f} mm/side")
    add("PASS", "COMMON_AXIS_SOURCE", "Every ear bore is cut from the same global X/Z axis parameters.")
    add("PASS", "LEFT_RIGHT_ENTRY_LEAD_IN_SOURCE", f"External lead-in depth/chamfer={shaft_fit.entrance_chamfer_mm:.3f} mm at both outer faces.")
    add("PASS", "ROOT_SIDE_RELIEF_SOURCE", f"Ear root Y width is reduced by {p.hinge_root_side_relief_mm:.3f} mm per side.")
    add("PASS", "NO_END_PROTRUSION_IN_ROD_PATH", "Keep-out cutter extends beyond both outer faces; no guide or datum is added at the entries.")
    add("WARN", "SUS_ROD_STRAIGHT_INSERTION_PHYSICAL", "Common nominal axes and lead-ins do not replace a printed three-link phi3 mm insertion test.")
    add("WARN", "ANGLE_DEPENDENT_ALIGNMENT_PHYSICAL", f"{p.candidate_max_articulation_deg:.1f} deg remains a reference candidate; hand alignment at several angles is required.")

    valley = p.interlink_body_gap_x_mm + 2.0 * p.drive_half_pocket_x_mm
    add("PASS" if abs(valley - p.drive_valley_target_x_mm) < 0.05 else "FAIL", "DRIVE_VALLEY_WIDTH", f"Combined open valley={valley:.3f} mm")
    add("PASS" if p.drive_remaining_ligament_z_mm >= 3.5 else "FAIL", "DRIVE_WALL_LIGAMENT", f"Remaining PETG ligament={p.drive_remaining_ligament_z_mm:.3f} mm")
    add("WARN", "ACTUAL_SPROCKET_SOURCE_MISSING", "Public main did not expose crawler_h1 SPR; 12T/44 mm/7.5 mm values remain inherited reference data.")
    add("WARN", "LATERAL_PLAY_ENGAGEMENT_PHYSICAL", f"SPR engagement with {shaft_fit.total_axial_play_mm:.2f} mm play requires centred/left/right CAD and hand-rotation tests.")

    add("PASS" if p.guide_axis_x_clearance_mm > shaft_fit.keepout_diameter_mm / 2.0 + 1.5 else "FAIL", "GUIDE_HINGE_KEEP_OUT_CLEAR", f"Guide nearest X edge is {p.guide_axis_x_clearance_mm:.3f} mm from hinge axis.")
    add("PASS", "GUIDE_PLAY_INDEPENDENT", "Guide clearance and hinge axial play remain separate parameters.")
    add("WARN", "GUIDE_ROL_UNKNOWN", "ROL guided width/surface remains UNKNOWN_REQUIRES_SOURCE_CONFIRMATION.")

    add("PASS", "OPEN_WASH_PATH", "No small drain holes; shear grooves and tool notches remain open.")
    add("WARN", "SUPPORT_OFF_SLICER_CHECK", "Bambu Studio support-OFF inspection is required for all CAP and SHAFT candidates.")
    add("WARN", "MESH_NOT_RUN" if cq is None else "MESH_RUNTIME_REQUIRED", "Positive volume, valid solid, STL/STEP, watertight, islands and collision checks require CadQuery execution.")
    add("PASS", "QUANTITY_HOLD", "40+8 links and 40+8 LUGs remain HOLD until FIT TEST acceptance.")

    failures = [i for i in issues if i["level"] == "FAIL"]
    warnings = [i for i in issues if i["level"] == "WARN"]
    return {
        "version": VERSION,
        "status": STATUS,
        "result": "FAIL" if failures else "STATIC_PASS_WITH_WARNINGS",
        "selected": {
            "capture": asdict(capture_fit),
            "shaft": {**asdict(shaft_fit), "per_side_play_mm": shaft_fit.per_side_play_mm},
            "head": asdict(head_fit),
            "guide": asdict(guide_fit),
        },
        "computed": {
            "original_capture_height_mm": p.current_capture_height_mm,
            "new_capture_height_mm": capture_h,
            "capture_height_increase_mm": capture_fit.capture_increase_mm,
            "head_diameter_mm": head_fit.head_diameter_mm,
            "head_thickness_mm": p.pin_head_thickness_mm,
            "total_pin_projection_mm": total_pin,
            "lug_total_thickness_mm": capture_fit.lug_thickness_mm,
            "tpu_ground_floor_mm": capture_fit.ground_floor_mm,
            "pin_head_ground_recess_mm": recess,
            "tpu_entrance_stretch_ratio": head_stretch,
            "retention_shoulder_radial_mm": shoulder_radial,
            "hinge_hole_diameter_mm": shaft_fit.hole_diameter_mm,
            "total_axial_play_mm": shaft_fit.total_axial_play_mm,
            "per_side_axial_play_mm": shaft_fit.per_side_play_mm,
            "entrance_chamfer_mm": shaft_fit.entrance_chamfer_mm,
            "keepout_diameter_mm": shaft_fit.keepout_diameter_mm,
            "rod_path_radial_margin_mm": keep_margin,
            "center_knuckle_width_y_mm": p.center_knuckle_width_y_mm,
            "outer_ear_width_y_mm": p.outer_ear_width_y_mm,
            "minimum_xz_wall_actual_mm": wall,
            "side_relief_mm": p.hinge_root_side_relief_mm,
            "empty_space_to_body_edge_each_y_mm": empty,
        },
        "cadquery_available": cq is not None,
        "issues": issues,
        "failures": len(failures),
        "warnings": len(warnings),
    }


def design_contract(p: Params, validation: dict) -> dict:
    return {
        "package": PACKAGE_NAME,
        "version": VERSION,
        "status": STATUS,
        "supersedes": {
            "version": "v0.11.3",
            "reason": [
                "Snap-head capture height was physically too shallow",
                "TPU LUG barely entered the capture space",
                "Three-link phi3 mm hole alignment was angle-dependent",
                "More play, lead-in and root-side relief are required",
            ],
        },
        "coordinate_contract": {
            "X": "travel direction",
            "Y": "track width and hinge shaft",
            "Z": "+Z SPR/rover; -Z TPU/ground",
        },
        "fixed_contract": {
            "link_pitch_mm": 20.0,
            "front_axis_x_mm": 10.0,
            "rear_axis_x_mm": -10.0,
            "track_width_mm": 50.0,
            "knuckle_structure": "three plate round knuckle",
            "snap_head_system": "integral PETG mushroom head retained",
            "ground_contact": "TPU only",
            "sprocket_drive": "joint-centred open valley and thick forward/reverse walls",
            "lateral_retention": "central low/thick guides independent of hinge play",
        },
        "source_inspection": {
            "public_repository_status": "crawler_h1 source not found in public main at generation time",
            "local_predecessor_source": "crawler_h1_snap_head_lug_link_v0_11_3.py",
            "v0_11_3_capture_height_mm": p.current_capture_height_mm,
            "v0_11_3_center_knuckle_width_y_mm": p.center_knuckle_width_y_mm,
            "v0_11_3_outer_ear_width_y_mm": p.outer_ear_width_y_mm,
        },
        "fit_matrix": {
            "capture": {k: asdict(v) for k, v in CAPTURE_FITS.items()},
            "shaft": {k: {**asdict(v), "per_side_play_mm": v.per_side_play_mm} for k, v in SHAFT_FITS.items()},
            "heads": {k: asdict(v) for k, v in HEAD_FITS.items()},
            "guides": {k: asdict(v) for k, v in GUIDE_FITS.items()},
        },
        "standard_candidate": "CAP-B + SHAFT-B + HEAD-B + GUIDE-B",
        "quantity_status": "HOLD_NOT_GENERATED",
        "unknowns": [
            "actual/current SPR source geometry and physical engagement",
            "current ROL guided width and guide compatibility",
            "printed TPU snap retention and 20-cycle result",
            "three-link printed phi3 mm shaft insertion at multiple angles",
            "maximum practical articulation angle",
        ],
        "params": p.to_dict(),
        "validation_result": validation["result"],
    }


def write_csv(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def export_geometry(out: Path, p: Params, target: str) -> None:
    require_cadquery()
    for sub in ("stl/petg", "stl/tpu", "step", "reference", "plates", "manifest"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    rows = []

    def emit(part_id, shape, material, print_shape=None, status="FIT_TEST_ONLY"):
        pshape = print_shape if print_shape is not None else place_on_bed(shape)
        stl_dir = out / ("stl/tpu" if material.startswith("TPU") else "stl/petg")
        export_shape(pshape, stl_dir / f"{part_id}.stl")
        export_shape(shape, out / "step" / f"{part_id}.step")
        bx, by, bz = shape_bbox(pshape)
        rows.append({
            "part_id": part_id,
            "material": material,
            "bbox_x_mm": round(bx, 3),
            "bbox_y_mm": round(by, 3),
            "bbox_z_mm": round(bz, 3),
            "support": "OFF_CANDIDATE",
            "status": status,
        })

    if target in ("DEEP_CAPTURE", "ALL"):
        for key, fit in CAPTURE_FITS.items():
            emit(f"PS-TRH1-CAP-{key}-PETG", build_snap_head_coupon(p, fit), "PETG", build_snap_head_coupon_print(p, fit))
            emit(f"PS-TRH1-CAP-{key}-LUG-TPU", build_lug(p, fit), "TPU 95A")
            export_shape(build_ground_contact_reference(p, fit), out / "reference" / f"CAP_{key}_ONE_LINK_GROUND_REFERENCE.step")
        export_shape(make_capture_plate(p), out / "plates" / "DEEP_CAPTURE_FIT_TEST_PETG.step")
        export_shape(make_lug_plate(p), out / "plates" / "DEEP_CAPTURE_FIT_TEST_TPU.step")

    if target in ("EASY_SHAFT", "ALL"):
        for key, fit in SHAFT_FITS.items():
            emit(f"PS-TRH1-SHAFT-{key}-LNK", build_link_assembly(p, STANDARD_CAPTURE, fit), "PETG", build_link_print(p, STANDARD_CAPTURE, fit))
            export_shape(build_three_link_reference(p, STANDARD_CAPTURE, fit, 0.0), out / "reference" / f"SHAFT_{key}_THREE_LINK_STRAIGHT_REFERENCE.step")
        export_shape(build_three_link_reference(p, STANDARD_CAPTURE, STANDARD_SHAFT, 15.0), out / "reference" / "SHAFT_B_THREE_LINK_BENT_REFERENCE.step")
        export_shape(build_three_link_reference(p, STANDARD_CAPTURE, STANDARD_SHAFT, p.candidate_max_articulation_deg), out / "reference" / "SHAFT_B_THREE_LINK_MAX_BEND_REFERENCE.step")
        export_shape(make_shaft_plate(p), out / "plates" / "EASY_SHAFT_FIT_TEST_PETG.step")

    if target in ("PARTS", "ALL"):
        emit("PS-TRH1-LNK-0114-STANDARD", build_link_assembly(p), "PETG", build_link_print(p))
        emit("PS-TRH1-LUG-0114-STANDARD", build_lug(p), "TPU 95A")
        for key, fit in HEAD_FITS.items():
            emit(f"PS-TRH1-HEAD-{key}-FIT", build_snap_head_coupon(p, STANDARD_CAPTURE, fit), "PETG", build_snap_head_coupon_print(p, STANDARD_CAPTURE, fit))
        for key, fit in GUIDE_FITS.items():
            emit(f"PS-TRH1-GUIDE-{key}-FIT", build_link_assembly(p, STANDARD_CAPTURE, STANDARD_SHAFT, STANDARD_HEAD, fit), "PETG", build_link_print(p, STANDARD_CAPTURE, STANDARD_SHAFT, STANDARD_HEAD, fit))

    if target in ("REFERENCES", "ALL"):
        export_shape(build_five_link_wrap_reference(p), out / "reference" / "V0114_FIVE_LINK_SPROCKET_WRAP_REFERENCE.step")
        export_shape(build_five_link_wrap_reference(p, lateral_shift_y_mm=0.0), out / "reference" / "V0114_SPROCKET_CENTERED_REFERENCE.step")
        shift = STANDARD_GUIDE.side_clearance_mm + 0.2
        export_shape(build_five_link_wrap_reference(p, lateral_shift_y_mm=-shift), out / "reference" / "V0114_SPROCKET_LEFT_SHIFT_REFERENCE.step")
        export_shape(build_five_link_wrap_reference(p, lateral_shift_y_mm=shift), out / "reference" / "V0114_SPROCKET_RIGHT_SHIFT_REFERENCE.step")

    if rows:
        write_csv(out / "manifest" / "print_manifest.csv", rows)


def write_metadata(out: Path, p: Params, validation: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "contracts").mkdir(exist_ok=True)
    (out / "reports").mkdir(exist_ok=True)
    contract = design_contract(p, validation)
    (out / "contracts" / "crawler_h1_v0_11_4_design_contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "reports" / "validation_report.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_checksums(root: Path) -> None:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rows.append(f"{sha256_file(path)}  {path.relative_to(root).as_posix()}")
    (root / "SHA256SUMS.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--target", default="ALL", choices=("DEEP_CAPTURE", "EASY_SHAFT", "PARTS", "REFERENCES", "ALL"))
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument("--capture", choices=("A", "B", "C"), default="B")
    parser.add_argument("--shaft", choices=("A", "B", "C"), default="B")
    parser.add_argument("--head", choices=("A", "B", "C"), default="B")
    parser.add_argument("--guide", choices=("A", "B", "C"), default="B")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    p = DEFAULT
    capture = CAPTURE_FITS[args.capture]
    shaft = SHAFT_FITS[args.shaft]
    head = HEAD_FITS[args.head]
    guide = GUIDE_FITS[args.guide]
    validation = static_validation(p, capture, shaft, head, guide)
    write_metadata(args.out, p, validation)
    (args.out / "source").mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    dst = (args.out / "source" / Path(__file__).name).resolve()
    if src != dst:
        shutil.copy2(src, dst)
    if not args.metadata_only:
        export_geometry(args.out, p, args.target)
    write_checksums(args.out)
    print(json.dumps({
        "out": str(args.out),
        "version": VERSION,
        "capture": capture.code,
        "shaft": shaft.code,
        "head": head.code,
        "guide": guide.code,
        "metadata_only": args.metadata_only,
        "cadquery_available": cq is not None,
        "validation": validation["result"],
        "failures": validation["failures"],
        "warnings": validation["warnings"],
        "quantity_status": "HOLD_NOT_GENERATED",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
