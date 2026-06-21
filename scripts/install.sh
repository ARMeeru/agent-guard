#!/usr/bin/env bash
#
# Hardened user-level install of agent-guard.
#
# Copies the guard + rules OUT of the source repo into a read-only, immutable
# location the agent does not work in, pins the rule-set hash, and prints the
# exact hook-registration command (Mavis / MiniMax Code) with the interpreter
# pinned to an absolute path.
#
# For a stronger install, place the files under a root-owned path
# (e.g. /usr/local/lib/agent-guard) instead — see docs/THREAT_MODEL.md.
#
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${AGENT_GUARD_HOME:-$HOME/.agent-guard}"
PY="${AGENT_GUARD_PYTHON:-/usr/bin/python3}"

echo "Installing agent-guard"
echo "  source: $SRC"
echo "  dest:   $DEST"
echo "  python: $PY"

# Clear any prior immutable flags so we can refresh.
if [ -d "$DEST" ]; then
  chflags -R nouchg "$DEST" 2>/dev/null || true
fi

mkdir -p "$DEST/guard" "$DEST/rules"
install -m 0444 "$SRC/guard/cred_guard.py" "$DEST/guard/cred_guard.py"
install -m 0444 "$SRC/rules/rules.json"     "$DEST/rules/rules.json"
chmod 0555 "$DEST" "$DEST/guard" "$DEST/rules"

# Make the installed files immutable (OS blocks writes from ANY tool, incl. Write/Edit).
chflags uchg "$DEST/guard/cred_guard.py" "$DEST/rules/rules.json" 2>/dev/null \
  || echo "  (note: chflags unavailable; files are read-only but not immutable)"

SHA="$(shasum -a 256 "$DEST/rules/rules.json" | awk '{print $1}')"

echo
echo "Installed. Rule-set sha256: $SHA"
echo
echo "Register the hook (Mavis / MiniMax Code):"
echo "------------------------------------------------------------------"
cat <<EOF
mavis hook create agent-guard \\
  --event PreToolUse --type script --priority 5 \\
  --matcher '^[Bb]ash\$' --timeout 15000 \\
  --body '\`\`\`bash
AGENT_GUARD_RULES="$DEST/rules/rules.json" AGENT_GUARD_RULES_SHA256="$SHA" "$PY" "$DEST/guard/cred_guard.py"
\`\`\`'
EOF
echo "------------------------------------------------------------------"
echo "To update rules later: edit the source repo, re-run this script (re-pins the hash),"
echo "then 'mavis hook update' the body with the new sha. Guard admin is a human action."
