# Mavis / MiniMax Code integration

Registers `agent-guard` as a global `PreToolUse` hook that runs on every `bash` tool call.

## Install (hardened — recommended)

Run the installer. It copies the guard out of this repo into a read-only, immutable location
the agent does not work in, pins the rule-set hash, and prints the exact hook command:

```bash
./scripts/install.sh
```

Paste the `mavis hook create …` command it prints. That command pins:
- the **rules path** and **rules sha256** (`AGENT_GUARD_RULES_SHA256`) → fail-safe on tamper
- the **interpreter** to an absolute `/usr/bin/python3` → no PATH hijack
- the guard path under `~/.agent-guard` (immutable via `chflags uchg`)

> For a stronger install, place the files under a **root-owned** path
> (`/usr/local/lib/agent-guard`, `root:wheel`, `0644`) so the agent — running as you —
> cannot modify them at all. See [`../../docs/THREAT_MODEL.md`](../../docs/THREAT_MODEL.md).

## Verify

```bash
# Should ABORT
mavis hook test agent-guard \
  --input '{"toolName":"bash","toolArgs":{"command":"security find-internet-password -s github.com -w"}}' \
  --output '{}'

# Should PASS
mavis hook test agent-guard \
  --input '{"toolName":"bash","toolArgs":{"command":"git status"}}' \
  --output '{}'
```

## Notes
- Hooks take effect in the next session — no daemon restart needed.
- The guard is fail-open by default (malformed payloads pass), and fail-safe when
  integrity checking is enabled — it never silently breaks the agent.
- Updating rules is a deliberate human action: edit the source, re-run `scripts/install.sh`
  (re-pins the hash), then `mavis hook update agent-guard --body …` with the new sha.
