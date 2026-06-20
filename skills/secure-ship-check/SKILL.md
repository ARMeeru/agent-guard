---
name: secure-ship-check
description: "Security-focused pre-delivery gate. Trigger when the user says 'secure ship check', 'security check', 'sec check', or asks to verify a change is safe to ship/commit/push. Runs build, tests, then a security pass (secret scan, dependency audit, SAST, risky-pattern grep) and a threat readout. Use before delivering any code that touches auth, input handling, network, or secrets."
---

# Secure Ship Check

A security-weighted delivery gate. Run every step in order. Report each as ✅ / ❌ /
⏭️ (skipped, with reason). Never claim a step passed without showing its output.

## Steps
1. **Scope** — restate what changed and list files touched. Flag anything touching auth,
   input parsing, network calls, file I/O, or secrets.
2. **Build + tests** — run the project's build and test suite (pnpm/`uv run pytest`/`go test`).
3. **Secret scan** — `gitleaks detect` or grep the diff for `password|secret|api[_-]?key|token|bearer|BEGIN .*PRIVATE KEY`. Report any hit.
4. **Dependency audit** — `pnpm audit` / `pip-audit` / `govulncheck`. Report NEW advisories only.
5. **SAST** — `semgrep --config auto` if available; else review the diff for the OWASP basics:
   injection (SQL/command), unsafe deserialization, path traversal, SSRF, missing authz,
   hardcoded creds.
6. **Risky-pattern check** — scan for `eval`, `exec`, `subprocess(... shell=True)`,
   `child_process.exec`, unparameterized queries, `# nosec`/`// nolint` suppressions.
7. **Threat readout** — 2–3 sentences: what's the attack surface this change adds, what's
   the worst case, and what you'd monitor after shipping.

## Rules
- If a tool isn't installed (no gitleaks/semgrep), mark it ⏭️ with the reason and fall back
  to the manual diff review — don't fake it.
- For authorized offensive/security tooling, this gate still applies to *your own* code
  (don't ship a scanner with a hardcoded key or a command-injection hole).
- End with a one-line verdict: **SHIP** / **HOLD** + the single biggest security reason.
