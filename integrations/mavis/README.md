# Mavis / MiniMax Code integration

Registers `agent-guard` as a global `PreToolUse` hook that runs on every `bash` tool call.

## Install

```bash
# 1. Point the guard at this repo's rules (or copy rules.json wherever you like)
export GUARD_DIR="$HOME/Development/AIPlayground/agent-guard"

# 2. Register the hook (global; matcher targets the bash tool)
mavis hook create agent-guard \
  --event PreToolUse \
  --type script \
  --priority 5 \
  --matcher '^[Bb]ash$' \
  --timeout 15000 \
  --body '```bash
python3 '"$GUARD_DIR"'/guard/cred_guard.py
```'
```

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
- Built-in hooks can't be overridden, but this is a user hook, so it coexists with them.
- The guard is fail-open: malformed payloads pass through, so it can never wedge the agent.
