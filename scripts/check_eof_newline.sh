#!/usr/bin/env bash
# Verbatim mirror of the CI step's bash, used locally to verify the check
# actually catches a violation before opening the PR.
set -u
offenders=()
while IFS= read -r f; do
  [ -f "$f" ] || continue
  [ -s "$f" ] || continue
  # skip binary files (NUL byte in the first 8 KiB).
  # Use od + grep instead of `grep -q $'\x00'` directly: BSD grep
  # on macOS treats the NUL pattern as a match for every input,
  # which would silently skip every file and break detection.
  if head -c 8192 "$f" | LC_ALL=C od -An -c | grep -q '\\0'; then
    continue
  fi
  last=$(tail -c 1 "$f" | od -An -c | tr -d ' \n')
  if [ "$last" != "\n" ]; then
    offenders+=("$f")
  fi
done < <(git ls-files)

if [ "${#offenders[@]}" -gt 0 ]; then
  echo "::error::The following tracked text files are missing a final newline:"
  for f in "${offenders[@]}"; do
    echo "::error file=$f::missing final newline"
  done
  exit 1
fi
echo "all tracked text files end with a newline"
