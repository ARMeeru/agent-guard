#!/usr/bin/env python3
"""agent-guard — PreToolUse guard for agent runtimes.

Reads a tool-call payload on stdin, checks the shell command against an external
rule set (rules/rules.json), and aborts the call if it matches a dangerous pattern.

Protocol (Mavis PreToolUse): stdin is {"input":.., "output":..}; print a JSON object
to stdout that is merged into `output`. Emitting {"_abort": {"reason": ...}} aborts
the tool call. Any parse failure is fail-open (prints {}) so the guard never wedges
the agent on malformed input — it is defense-in-depth, not a hard sandbox.
"""
from __future__ import annotations

import json
import os
import re
import sys

RULES_PATH = os.environ.get(
    "AGENT_GUARD_RULES",
    os.path.join(os.path.dirname(__file__), "..", "rules", "rules.json"),
)


def load_rules() -> list[tuple[re.Pattern[str], str, str]]:
    with open(RULES_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    compiled: list[tuple[re.Pattern[str], str, str]] = []
    for cat_name, cat in (data.get("categories") or {}).items():
        for rule in cat.get("rules", []):
            compiled.append(
                (re.compile(rule["pattern"], re.IGNORECASE), cat_name, rule["label"])
            )
    return compiled


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
    except Exception:
        print("{}")  # fail-open
        return

    reason = evaluate(extract_command(payload), rules)
    if reason:
        print(json.dumps({"_abort": {"reason": reason}}))
    else:
        print("{}")


if __name__ == "__main__":
    main()
