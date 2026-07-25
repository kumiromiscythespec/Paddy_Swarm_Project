"""Single-source interface dimensions for dummy panicle head v0.1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StemInterface:
    """STEM-NOMINAL-4 shaft/socket interface dimensions in mm."""

    name: str = "STEM-NOMINAL-4"
    nominal_diameter: float = 4.0
    receiver_diameter: float = 4.3
    insertion_depth: float = 20.0
    entry_chamfer: float = 0.8
    clamp_screw_clearance_diameter: float = 3.4
    clamp_screw_offset: float = 10.0

    @property
    def diametral_clearance(self) -> float:
        """Return receiver minus shaft diameter."""

        return self.receiver_diameter - self.nominal_diameter


@dataclass(frozen=True)
class PanicleTabInterface:
    """PANICLE-TAB-V001 flexible tab and rigid slot dimensions in mm."""

    name: str = "PANICLE-TAB-V001"
    tab_width: float = 8.0
    tab_thickness: float = 2.0
    tab_length: float = 14.0
    slot_width: float = 8.4
    slot_thickness: float = 2.4
    insertion_depth: float = 12.0


@dataclass(frozen=True)
class PanicleHeadInterface:
    """Shared uncalibrated panicle-head targets in mm, degrees, and grams."""

    reference_length: float = 200.0
    target_mass_min_g: float = 4.0
    target_mass_reference_g: float = 5.0
    target_mass_max_g: float = 6.0
    standard_droop_angle_degrees: float = 20.0
    branch_panel_count: int = 4
    branch_print_quantity: int = 6
    calibration_status: str = "CALIBRATION_PENDING"


@dataclass(frozen=True)
class CartridgeInterface:
    """Replaceable cartridge and holder-face safety dimensions in mm."""

    cartridge_length: float = 170.0
    cuttable_length: float = 80.0
    holder_length: float = 25.0
    tube_outer_diameter: float = 4.0
    tube_inner_diameter: float = 2.5
    holder_insertion_depth: float = 15.0
    fiber_channel_diameter: float = 2.0
    holder_face_safety_distance: float = 30.0

    @property
    def cartridge_end_exclusion_length(self) -> float:
        """Return insertion plus safety distance at each cartridge end."""

        return self.holder_insertion_depth + self.holder_face_safety_distance

    @property
    def required_cartridge_length(self) -> float:
        """Return length required by both insertions, safety zones, and cut zone."""

        return (
            2.0 * self.holder_insertion_depth
            + 2.0 * self.holder_face_safety_distance
            + self.cuttable_length
        )

    @property
    def derived_cuttable_length(self) -> float:
        """Return the central nominal zone implied by the corrected datums."""

        return self.cartridge_length - 2.0 * self.cartridge_end_exclusion_length


STEM = StemInterface()
PANICLE_TAB = PanicleTabInterface()
PANICLE_HEAD = PanicleHeadInterface()
CARTRIDGE = CartridgeInterface()

M4_CLEARANCE_DIAMETER = 4.5


def validate_interfaces() -> None:
    """Raise ``ValueError`` when a shared interface is internally inconsistent."""

    if STEM.nominal_diameter <= 0.0:
        raise ValueError("STEM-NOMINAL-4 shaft diameter must be positive")
    if STEM.receiver_diameter <= STEM.nominal_diameter:
        raise ValueError("STEM-NOMINAL-4 receiver must be larger than the shaft")
    if abs(STEM.diametral_clearance - 0.30) > 1.0e-9:
        raise ValueError("STEM-NOMINAL-4 diametral clearance must be 0.30 mm")

    if PANICLE_TAB.slot_width <= PANICLE_TAB.tab_width:
        raise ValueError("PANICLE-TAB-V001 slot width must exceed tab width")
    if PANICLE_TAB.slot_thickness <= PANICLE_TAB.tab_thickness:
        raise ValueError("PANICLE-TAB-V001 slot thickness must exceed tab thickness")
    if PANICLE_TAB.insertion_depth > PANICLE_TAB.tab_length:
        raise ValueError("PANICLE-TAB-V001 insertion depth exceeds tab length")

    if CARTRIDGE.fiber_channel_diameter >= CARTRIDGE.tube_inner_diameter:
        raise ValueError("fiber channel must fit inside the cartridge tube")
    if CARTRIDGE.holder_insertion_depth >= CARTRIDGE.holder_length:
        raise ValueError("holder insertion depth must be shorter than holder length")
    if abs(CARTRIDGE.cartridge_length - CARTRIDGE.required_cartridge_length) > 1.0e-9:
        raise ValueError(
            "cartridge length must equal two insertions, two holder-face safety "
            "distances, and the cuttable length"
        )
    if abs(CARTRIDGE.derived_cuttable_length - CARTRIDGE.cuttable_length) > 1.0e-9:
        raise ValueError("cartridge dimensions do not produce the specified cuttable length")


validate_interfaces()
