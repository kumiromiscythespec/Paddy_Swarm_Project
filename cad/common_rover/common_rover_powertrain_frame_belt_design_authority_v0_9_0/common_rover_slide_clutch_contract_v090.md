# Common Rover v0.9.0 slide-clutch contract

`CLUTCH_GEOMETRY = PARAMETRIC_CANDIDATE`  
`CLUTCH_MANUFACTURING = HOLD`

Each side has a motor input shaft, rotationally locked sliding sleeve, DRIVE dog
hub, PTO dog hub, mandatory NEUTRAL gap, shift fork, actuator reservation,
position-sensor reservation, axial stops and full-stroke envelope.

The mechanical stroke cannot engage DRIVE and PTO together. Non-selected
pulley paths are disconnected or free-running. Switching is allowed only after
motor command and rotation reach zero. Loss of power or unknown position
selects motor-zero and NEUTRAL/human-intervention behavior.

Unknown measurements: stroke, engagement depth, tooth count, shaft spline,
fork thickness and actuator force. Final dog torque members remain metal
candidates. PETG-only final torque transmission is prohibited.
