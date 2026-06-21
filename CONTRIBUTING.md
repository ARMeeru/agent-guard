# Contributing to agent-guard

Thanks for helping harden the guard. agent-guard is a regex-based PreToolUse
guard for AI coding agents — **defense-in-depth, not a sandbox.** Rules are
data, not code: this repo's job is to keep the rule set in
[`rules/rules.json`](rules/rules.json) accurate, well-tested, and tight enough
not to block normal developer workflows. See
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for what the guard does and
does not protect against.

---

## The golden rule

> **Every new or changed rule must come with BOTH a `BLOCK` test AND a
> near-miss `ALLOW` test.** Pull requests without both will not be accepted.

The number-one risk in this codebase is **false positives** that block normal
commands — they make the guard a nuisance and push people to disable it. The
number-two risk is **false negatives** that miss real attacks. Precision beats
quantity every time. One well-scoped, well-tested rule beats ten vague ones.

When you add a rule, prove two things:

1. **It fires on the bad command.** Add a representative attack string to
   `BLOCK` in [`tests/test_guard.py`](tests/test_guard.py).
2. **It does NOT fire on the obvious near-miss.** Add at least one
   intentionally similar but legitimate command to `ALLOW`, with a comment
   explaining what it's guarding against. This is your regression net.

If you cannot think of a near-miss, your rule is probably too broad — narrow
it until you can.

---

## `rules.json` schema

The rule file is plain JSON. The shape is:

```jsonc
{
  "version": "0.2.0",
  "categories": {
    "<category-name>": {
      "summary": "One-line human description of the threat class.",
      "rules": [
        {
          "id": "<kebab-case-unique-id>",
          "pattern": "<Python regex, matched case-insensitive, anywhere in the command>",
          "label": "Short human label surfaced in the abort reason."
        }
      ]
    }
  }
}
```

Rules:

- **`id`** — unique within the whole file. Use a kebab-case name that
  describes *what's blocked*, not the category (e.g. `aws-credentials`,
  not `cred-rule-3`).
- **`pattern`** — a Python `re` regex (POSIX-ish; no lookbehind in some
  Python versions, but standard character classes work). The engine compiles
  every pattern with `re.IGNORECASE` and matches against the *entire* shell
  command string with `re.search`. So your pattern must be specific enough
  not to over-match anywhere in a longer command.
- **`label`** — appears verbatim in the abort reason. Make it actionable
  ("SSH private key read" is good; "bad" is not).
- **Categories** — group rules by threat class. Existing categories:
  `credential-exfil`, `destructive-ops`, `network-egress`,
  `data-exfiltration`, `self-protection`. Add a new category only when a
  threat doesn't fit any of these, and give it a one-line `summary`.

### How to add a rule

1. Identify the threat and the near-miss. If you can't name a near-miss,
   stop and re-scope.
2. Pick or create a category. Update its `summary` if the new rule changes
   the threat's framing.
3. Append the rule to that category's `rules` array. Keep IDs unique.
4. Bump `version` in `rules.json` (the project follows semver-ish versioning
   on the rule set; any new rule is a minor bump).
5. Add a `BLOCK` and an `ALLOW` entry in
   [`tests/test_guard.py`](tests/test_guard.py) with comments explaining
   each.
6. Run `python3 tests/test_guard.py` locally — both lists must pass cleanly.
7. Open a PR (see workflow below). PR description must list each new rule
   and the BLOCK/ALLOW pair you added for it.

### Pattern-crafting tips

- **Anchor where you can.** Use `\b` at word boundaries (`\b169\.254\.169\.254\b`)
  so a partial match inside an unrelated URL doesn't fire.
- **Prefer precise literals to broad classes.** `\.aws/credentials\b` is
  better than `\.aws/.*` — the former won't false-positive on
  `cat ~/.aws/config`, which only contains region and profile metadata, not
  secrets.
- **Read-tool files narrowly.** For credentials reached via `cat`/`less`/
  `head`/`tail`/`grep`, follow the existing `.netrc` shape:
  `(^|\s)(cat|less|head|tail|grep)\s+[^\n|]*<path-token>\b`. Don't try to
  cover `dd`, `base64`, or `python -c "open(...)..."` — those have unbounded
  attack surface and belong in a future "exfiltration toolchain" category.
- **Beware partial overlaps.** A metadata-IP rule and a curl-pipe-shell
  rule may both fire on the same command; that's fine. But two rules in
  the same category that fire on the same near-miss usually mean one of
  them is too broad.
- **Don't weaken, broaden, or remove an existing rule.** That's a separate,
  explicitly-justified PR. Existing `BLOCK`/`ALLOW` tests must keep
  passing unchanged.

---

## Engine changes

`guard/cred_guard.py` is intentionally small. The detection power lives in
the rule data; the engine just loads JSON, compiles regexes, and aborts on
the first match.

**Do not modify the engine in a rule-change PR.** If you genuinely believe
the engine needs a change (a new payload field, a category-level
override, a deny-list escape hatch), **stop and explain in the PR
description** instead of doing it. Engine changes are a different review
class and ship on their own.

---

## Honest framing

agent-guard is **best-effort defense-in-depth**, not a sandbox:

- Patterns are case-insensitive regex against a single string. A
  sufficiently obfuscated command can evade them.
- The guard is fail-OPEN by default — a malformed rule set or payload
  prints `{}` instead of blocking, so a bug never wedges the agent.
- An attacker with write access to the guard's own files can disable it
  (which is why there's a `self-protection` category).

Read [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) before proposing
changes. Use this guard alongside least-privilege credentials, scoped
tokens, OS sandboxing, and human review — never as a guarantee on its
own.

---

## Development workflow

1. **Branch off `develop`.** Conventional-Commits-style branch name:
   `feat/...`, `fix/...`, `docs/...`, `ci/...`.
2. Make your changes. Keep the diff minimal and in-scope.
3. Run the test suite: `python3 tests/test_guard.py` (works on the macOS
   system Python 3.9 — that's a hard support target). CI also runs on
   Python 3.9 / 3.11 / 3.12 / 3.13 across all four jobs in
   `.github/workflows/ci.yml`.
4. Commit with [Conventional Commits](https://www.conventionalcommits.org/).
   No AI / "generated by" / `Co-Authored-By` trailer.
5. Push your branch and open a PR into `develop`. Stop at the PR — the
   reviewer merges.

---

## Integrity hash re-pin (operators)

`rules/rules.json` is data, so any change to it changes its sha256. The
guard supports an opt-in **integrity mode**: set the environment variable
`AGENT_GUARD_RULES_SHA256` to the pinned sha256 of the rule file, and the
guard will **fail safe** (block the tool call) on any hash mismatch or
unreadable rule set.

If you operate the guard with integrity mode enabled (see
[`integrations/mavis/`](integrations/mavis/) and
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for the hardening recipe):

1. After pulling a new `rules.json`, recompute the hash:
   ```sh
   shasum -a 256 rules/rules.json
   ```
2. Re-pin your `AGENT_GUARD_RULES_SHA256` to the new value.
3. Restart the hook.

Skipping this step after a rule update will cause the guard to start
blocking everything, which is the safe-but-noisy failure mode.

---

## License

By contributing, you agree your contributions are licensed under the MIT
license that covers this repository. See [`LICENSE`](LICENSE).
