#!/usr/bin/env python3
"""agent-guard — PreToolUse guard for agent runtimes.

Reads a tool-call payload on stdin, checks the shell command against an external
rule set (rules/rules.json), and aborts the call if it matches a dangerous pattern.

Protocol (Mavis PreToolUse): stdin is {"input":.., "output":..}; print a JSON object
to stdout that is merged into `output`. Emitting {"_abort": {"reason": ...}} aborts
the tool call.

Failure modes:
  * Integrity DISABLED (default): any parse/load error is fail-OPEN (prints {}), so the
    guard never wedges the agent on malformed input. It is defense-in-depth, not a sandbox.
  * Integrity ENABLED (set AGENT_GUARD_RULES_SHA256 to the pinned sha256 of rules.json):
    a hash mismatch or unreadable rule set is fail-SAFE (aborts), on the assumption that a
    changed rule set may be tampering. Recompute and re-pin the sha after any legit edit:
        shasum -a 256 rules/rules.json
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

RULES_PATH = os.environ.get(
    "AGENT_GUARD_RULES",
    os.path.join(os.path.dirname(__file__), "..", "rules", "rules.json"),
)
EXPECTED_SHA = os.environ.get("AGENT_GUARD_RULES_SHA256", "").strip().lower()


def _abort(reason: str) -> None:
    print(json.dumps({"_abort": {"reason": reason}}))


def load_rules() -> list[tuple[re.Pattern[str], str, str]]:
    with open(RULES_PATH, "rb") as fh:
        raw = fh.read()
    if EXPECTED_SHA:
        actual = hashlib.sha256(raw).hexdigest()
        if actual != EXPECTED_SHA:
            raise IntegrityError(
                f"rule set integrity check FAILED (expected {EXPECTED_SHA[:12]}…, "
                f"got {actual[:12]}…). The guard's rules may have been tampered with. "
                f"If you changed them on purpose, re-pin: shasum -a 256 {RULES_PATH}"
            )
    data = json.loads(raw)
    compiled: list[tuple[re.Pattern[str], str, str]] = []
    for cat_name, cat in (data.get("categories") or {}).items():
        for rule in cat.get("rules", []):
            compiled.append(
                (re.compile(rule["pattern"], re.IGNORECASE), cat_name, rule["label"])
            )
    return compiled


class IntegrityError(Exception):
    """Raised when the rule set fails its pinned-hash check."""


def extract_command(payload: dict) -> str:
    inp = payload.get("input") or {}
    args = inp.get("toolArgs") or {}
    if isinstance(args, dict):
        return args.get("command", "") or ""
    return ""


def evaluate(command: str, rules) -> str | None:
    for pattern, category, label in rules:
        if pattern.search(command):
            return (
                f"Blocked by agent-guard [{category}]: command appears to "
                f"perform a disallowed action ({label}). Surface the exact command "
                f"for the user to run and wait for explicit approval — do not route "
                f"around the boundary."
            )
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        rules = load_rules()
    except IntegrityError as exc:
        # Integrity is opt-in; if it's on and fails, fail SAFE (block).
        _abort(str(exc))
        return
    except Exception:
        if EXPECTED_SHA:
            # Integrity requested but rules unreadable → fail safe.
            _abort(
                "agent-guard could not load its rule set while integrity checking is "
                "enabled. Blocking until the guard is restored."
            )
        else:
            print("{}")  # fail-open
        return

    reason = evaluate(extract_command(payload), rules)
    if reason:
        _abort(reason)
    else:
        print("{}")


if __name__ == "__main__":
    main()
