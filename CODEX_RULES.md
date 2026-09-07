# Codex Compatibility

Canonical project instructions are in [AGENTS.md](AGENTS.md). Read and apply that contract and its linked safety boundary.
Engineering truth is not stored here; read [CHATGPT_PROJECT_INDEX.md](CHATGPT_PROJECT_INDEX.md) for current authority navigation.

Codex-specific behavior must not silently override the project safety or authority boundaries in AGENTS.md.
Task-specific user instructions may narrow the work scope. Exact runtime/system permissions, sandboxing, and approval enforcement remain governed by Codex itself; this file grants no additional permissions.

When using GPT-6 Astra, also read the [Astra operating profile](docs/agent/ASTRA_OPERATING_PROFILE.md) for behavior tuning only.
Keep permanent shared rules in the canonical files, not in this compatibility shim.

Codex discovers project guidance through AGENTS files; this compatibility filename does not itself guarantee automatic loading.
An existing `AGENTS.override.md` can replace the AGENTS file at the same directory level during discovery, so keep its use temporary/local and retain the canonical references described in AGENTS.md.
See [official Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md#how-codex-discovers-guidance).
