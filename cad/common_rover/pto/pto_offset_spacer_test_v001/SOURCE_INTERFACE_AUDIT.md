# Source / interface audit

Exact second attachment face and current installed transform are NOT PROVEN.

Read-only evidence:

1. `cad/common_rover/frame/front_interface_dual_pto_20t_v002/DESIGN_AUTHORITY.md`: architecture candidate uses a400 mm beam,
   support plates, bearings at Y50/100, pulley Y130, all physical validation pending.
2. `cad/common_rover/frame/front_interface_dual_pto_20t_v001/build_front_interface_dual_pto_20t_v001.py`: reference rail end is
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
