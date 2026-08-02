# Individual Isolation and Reconnection

## Isolation sequence

1. `CLOSE_UPPER_SUPPLY`
2. `WAIT_FOR_TOWER_DRAIN_TO_LOCAL_SUMP`
3. `CONFIRM_LOCAL_LEVEL_STABLE`
4. `CLOSE_EQUALIZATION_VALVE`
5. `DISCONNECT_OR_SERVICE_TOWER_AND_SUMP`

Closing the equalization valve first while upper supply continues is
prohibited. The HIGH overflow remains available throughout isolation and
routes only to the non-circulating emergency receiver.

Record tower ID, time, reason, local level, EC, pH, visual disease status and
both valve states. Mark the isolated branch physically at both valves.

## Reconnection sequence

1. `VERIFY_SUMP_CLEAN`
2. `VERIFY_EC_AND_PH_COMPATIBLE`
3. `MATCH_LOCAL_WATER_LEVEL_TO_ZONE`
4. `OPEN_EQUALIZATION_VALVE_SLOWLY`
5. `CHECK_FOR_LEAKS`
6. `OPEN_UPPER_SUPPLY`
7. `CONFIRM_RETURN_FLOW`

Do not reconnect disease-suspect solution. Replace or sanitize affected hose,
bulkhead, valve and sump surfaces according to the cleaning plan. Reconnection
of one branch does not authorize a whole-zone disease-clear status.
