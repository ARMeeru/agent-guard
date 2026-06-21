# Threat Model

agent-guard is **defense-in-depth, not a sandbox.** This document states plainly what it
does and does not protect against, so you never mistake it for confinement.

## What agent-guard is

A `PreToolUse` hook that inspects the shell command an agent is *about to run* and aborts
the ones matching a rule set (credential exfiltration, destructive ops, risky egress, and
attempts to disable the guard itself). It is a **speed bump and an audit point** in the
command path — valuable, but in-band with the thing it polices.

## What it protects against

- An agent (or a careless automation) running a *recognized* dangerous command via the
  **bash tool** — e.g. harvesting a keychain credential, `rm -rf ~/`, `curl … | bash`.
- Low-effort tampering with the guard's files, when those files are installed read-only /
  immutable (see Hardening).

## What it does NOT protect against

| Gap | Why | Mitigation |
|-----|-----|------------|
| **File-write tools bypass the bash hook** | The guard only sees `bash`. An agent's Write/Edit tool can alter files without triggering it. | Install the guard **immutable** (`chflags uchg`) so the OS blocks writes from *any* tool; clearing the flag is a bash command the guard blocks (`self-protection`). |
| **The guard can be neutralized if writable** | If the agent can edit `cred_guard.py` / `rules.json`, it can disable the control. | Install **root-owned, read-only**, outside the agent's workspace. Enable the **integrity check** (`AGENT_GUARD_RULES_SHA256`). |
| **Regex evasion / obfuscation** | Rules are pattern-based. Base64, env indirection, or novel phrasings can slip past. | Treat coverage as best-effort; layer with scoped credentials and review. Contribute rules for gaps you find. |
| **Non-bash exfiltration** | A credential read inside a Python tool call, MCP server, or compiled binary never hits the bash hook. | Out-of-band sandboxing is the only real answer here. |
| **Fail-open by default** | Malformed payloads pass through so the guard can't wedge the agent. | Enable integrity mode for fail-safe behavior on rule-set problems. |

## The honest ceiling

**Any in-band guard can be defeated by something with enough access to the guard.** True
enforcement must live *out of band* relative to the agent:

- macOS `sandbox-exec` / Seatbelt profiles
- a container with a read-only FS and no credential mounts
- running the agent as a **separate, low-privilege user** that cannot read your keychain,
  SSH keys, or token files in the first place

agent-guard reduces the blast radius of routine mistakes and provides an audit trail. It is
**one layer**. Use it alongside least-privilege credentials, scoped tokens, and human review
— never as a substitute for them.

## Hardening checklist

1. Install **outside** any directory the agent works in (not the source repo).
2. Install **root-owned, read-only**, or at minimum `chmod 0444` + `chflags uchg` (immutable).
3. Pin the rule-set hash: set `AGENT_GUARD_RULES_SHA256` in the hook (fail-safe on tamper).
4. Pin the interpreter to an absolute path (`/usr/bin/python3`), not a PATH lookup.
5. Keep the guard dependency-free (stdlib only) to shrink its own supply-chain surface.

See [`scripts/install.sh`](../scripts/install.sh) for an install that applies items 2–4.
