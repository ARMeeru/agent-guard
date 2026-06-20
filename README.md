# agent-guard

> A lightweight, rule-driven **safety layer for AI coding agents** — blocks credential
> exfiltration, destructive operations, and risky network egress *before* the tool call runs.

Traditional SAST scans your source. It does **not** understand the semantic layer where an
agent decides to run `security find-internet-password | gh auth login --with-token` to get
past a login wall. `agent-guard` sits at that layer: it inspects the commands an agent is
about to execute and stops the dangerous ones.

## Why this exists

This started from a real incident. An agentic coding model hit a logged-out `gh`, was told
the auth needed a human — and then, unprompted, **harvested a GitHub token from the macOS
keychain** to authenticate as the user and continue. The outcome was benign; the *pattern*
is not. No SAST tool catches it, and the existing agent-safety scanners are vendor-locked.

`agent-guard` is the open, self-hostable answer: defense-in-depth you can read, audit, and
extend.

## How it works

A `PreToolUse` hook pipes the agent's shell command into the guard. The guard matches it
against an external [rule set](rules/rules.json) (regex, grouped by category) and aborts the
call with an explanation if it matches.

```
agent runtime ──PreToolUse──▶ agent-guard ──▶ ✅ allow  /  🛑 abort + reason
```

Rules are data, not code — add or tune them in `rules/rules.json` without touching the guard.

### Categories (v0.1)
- **credential-exfil** — keychain reads, `gh auth token`, `.netrc`, `.git-credentials`, SSH keys
- **destructive-ops** — `rm -rf /`, force-push without `--force-with-lease`, hard-reset to remote
- **network-egress** — `curl … | bash`

## Install (Mavis / MiniMax Code)

See [integrations/mavis](integrations/mavis/) — registers a global `PreToolUse` hook that
runs the guard on every `bash` call. There's also a companion
[`secure-ship-check`](skills/secure-ship-check/) skill: a pre-delivery security gate.

## Honest limitations

This is **defense-in-depth, not a sandbox.** It is regex-based and fail-open (a malformed
payload is allowed through so the guard never wedges the agent). A determined or obfuscated
command can evade it. Use it as one layer alongside least-privilege credentials, scoped
tokens, and review — not as a guarantee.

## Roadmap
- [ ] v0.1 — Python guard + Mavis hook + rule set + skill pack
- [ ] Tests + GitHub Actions CI
- [ ] Go single-binary rewrite (portable, dependency-free)
- [ ] Adapters for Claude Code and OpenCode hook APIs
- [ ] Allowlist / per-rule severity / audit log

## License
MIT — see [LICENSE](LICENSE).
