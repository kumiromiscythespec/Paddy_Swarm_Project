# Protocol v0 Session Negotiation (RC-SN-001)

Status: software-only / deterministic internal model / simulator-first /
real motor output prohibited

## Scope and boundary

This package manages normalized `SESSION_HELLO` candidates,
Controller-to-Rover `SESSION_END`, one-controller ownership, in-process
session-ID reuse protection, rover boot-ID changes, RC-SM-001 runtime
synchronization, and construction or invalidation of the RC-WA-001
`ReceiverContext`.

All names and types are Python fixture contracts only. They are not approved
wire properties. RC-SN-001 does not implement JSON parsing or schema, encoding,
network framing, TCP/UDP, WebSocket, HTTP, Bluetooth, ESP-NOW, authentication,
security tokens, cryptography, persistent storage, NVM, cloud/PWA/ESP32 code,
ID generation, random values, GPIO/PWM, or motor/PTO output.

Session, boot, sender, instance, message, sequence, freshness, time, and request
indices are injected explicitly. The package reads no wall clock and has no
global mutable state.

## Candidate and manager state

`SessionCandidate` is a normalized SESSION_HELLO fixture containing:

- protocol version candidates;
- requested controller or observer role;
- candidate session ID and current rover boot ID;
- sender ID and explicit sender-instance/nonce fixture;
- exact boolean human switch confirmation;
- deterministic request index.

`SessionManagerState` records the current boot ID, optional active
session/controller/instance, selected version, ownership flag, process-local
used-session history, negotiation step, last disposition, session generation,
termination-pending flag, runtime synchronization state, and the last safely
ended controller identity.

The manager emits `SESSION_ACCEPTED`, `SESSION_REJECTED`, `SESSION_ENDED`,
`NO_CHANGE`, or `INTERNAL_ERROR`. A result is an internal equivalent of a
session notification; it is not a wire message, transport acknowledgement,
authentication decision, or production authorization.

## Version, role, and ownership

Candidate version lists must be non-empty tuples of unique non-empty strings.
Selection follows the manager's explicitly injected supported-version
preference. No type conversion or default is performed.

Only the controller role is implemented. Observer candidates are rejected with
`role_unavailable`; observer count, lifecycle, and ownership remain on HOLD.
At most one controller is active. A different controller can be considered
only after the old session safely ended, the runtime is DISARMED with all
outputs zero and no operation or latch, and an exact `true` human switch
confirmation is supplied. The same controller may reconnect only with a new
unused session ID.

## Session acceptance and runtime BOOT

Before dispatching runtime BOOT the manager validates structure, supported
version, boot ID, unused session ID, controller availability, manager/runtime
consistency, safe runtime state, zero output, absent operation, absent safety
latches, and any controller-switch confirmation.

Only a candidate passing all preconditions reaches runner-local
`RuntimeInput.local(Event.BOOT, session_id=<candidate>)`. Manager ownership,
used-session history, generation, and `ReceiverContext` update only if
RC-SM-001 accepts BOOT. Rejection before runtime dispatch leaves the runtime
step index unchanged. Runtime BOOT rejection does not consume the candidate ID
in manager history.

SESSION_ACCEPTED never runs BOOT_COMPLETE, restores communication, asserts
deadman, ARM, MOVE, PTO_START, restores an operation, or clears a safety latch.
BOOT_COMPLETE and other receiver-local events remain separate calls.

The runtime needs an explicitly injected bootstrap session in
`RuntimeConfig`; it is not exposed as an adapter active session. Before
negotiation and after session termination, manager `receiver_context` is
`None`, so COMMAND adaptation cannot use a fabricated session or owner.

## Session ID and SESSION_END

Accepted and ended IDs remain in process-local `used_session_ids` and cannot be
accepted again. The manager also checks RC-SM-001 used-session history before
dispatching BOOT. Reconnect therefore requires an explicitly supplied new ID;
sequence, ARM, deadman, output, and operation state are never restored.

Controller-to-Rover SESSION_END is first normalized through the unchanged
RC-WA-001 adapter and then dispatched to RC-SM-001. The manager clears its
session and owner only after runtime acceptance and confirmation that armed,
deadman, drive/PTO output, and operation are all inactive. The ended ID remains
used and `ReceiverContext` becomes `None`.

An active/armed SESSION_END can correctly leave RC-SM-001 in
`COMM_LOSS_LATCHED`. Because its formal reset event remains undefined, this
manager does not invent one and cannot use a new session or BOOT to bypass the
latch. A DISARMED safe session can end and later negotiate a new session.
Rover-to-Client SESSION_END is notification output and is not reinjected as a
runtime command by this manager.

## Boot ID changes

A changed boot ID invalidates manager session, owner, selected version, and
adapter context while preserving used-session history. If the existing runtime
is armed or active, the manager first applies the existing receiver-local
communication-loss safety event. A boot-ID update never clears a safety latch.
Commands from the old boot/session cannot be adapted after context
invalidation, and a new negotiation is required.

Actual ESP32 reboot behavior, cross-process session history, NVM persistence,
and physical input revalidation remain on HOLD.

## Deterministic virtual bridge

`VirtualSessionBridge` records negotiation, adapter, and runtime results in
separate fields and renders stable UTF-8 JSON with one trailing LF. Reports
contain no wall-clock timestamp, random value, absolute path, username,
hostname, opaque wire payload, or hardware action. Real motor output is always
reported as `false`.

## Remaining HOLD

Observer management, production controller switching, authentication,
pairing/encryption, persistent used-session storage, sequence collision cache,
final gap policy, COMM_LOSS reset event, actual power-cycle latch persistence,
hardware/runtime contracts, ESP32 integration, motor connection, and
water/mud/paddy-field testing remain unresolved and unapproved.
