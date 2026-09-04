# Architecture decision

## Decision

`TOP_SERVICE_MANUAL_SWAP + AUTONOMOUS_CONTACT_CHARGING` is the current Common Rover battery-operation baseline.

Normal operation keeps the battery installed and uses autonomous station contact charging. Manual cassette exchange is a human service action through the BBOX top after stop, motor-power isolation, and CBOX movement to a mechanically locked service position.

## Reasons

1. Avoid a permanently large BBOX side/rear battery opening.
2. Simplify the waterproof boundary.
3. Avoid a repeated seal on mud-, straw-, sand-, and water-exposed side surfaces.
4. Remove automatic battery exchange from the initial MVP.
5. Make routine operation viable through autonomous contact charging.
6. Retain manual top exchange for busy season and maintenance.
7. Keep the Battery Transporter useful as logistics transport rather than a precision insertion robot.

The rear-slide automatic-swap and large rear waterproof-door research is `SUPERSEDED_AS_PRIMARY_ARCHITECTURE` and `PRESERVED_FOR_FUTURE_AUTOMATIC_SWAP_RESEARCH`.
