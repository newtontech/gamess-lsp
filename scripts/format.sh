#!/usr/bin/env bash
set -euo pipefail

ran=0

python_bin="${PYTHON:-}"
if [ -z "$python_bin" ] && [ -x .venv/bin/python ]; then
  python_bin=.venv/bin/python
fi
if [ -z "$python_bin" ]; then
  for candidate in python python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      python_bin="$candidate"
      break
    fi
  done
fi

python_format_targets() {
  find src tests -name '*.py' -type f
}

has_npm_script() {
  local script="$1"
  [ -f package.json ] || return 1
  node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts[process.argv[1]] ? 0 : 1)" "$script"
}

if has_npm_script format:write; then
  npm run format:write
  ran=1
elif has_npm_script format; then
  npm run format
  ran=1
fi

if [ -f Cargo.toml ]; then
  cargo fmt
  ran=1
fi

if [ -f pyproject.toml ] || [ -f setup.py ]; then
  py_targets="$(python_format_targets)"
  if "$python_bin" -m black --version >/dev/null 2>&1; then
    "$python_bin" -m black $py_targets
    ran=1
  fi
  if "$python_bin" -m isort --version >/dev/null 2>&1; then
    "$python_bin" -m isort $py_targets
    ran=1
  fi
fi

if [ "$ran" -eq 0 ]; then
  echo "No formatter configured; skipping."
fi
