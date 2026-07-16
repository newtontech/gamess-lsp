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

has_npm_script() {
  local script="$1"
  [ -f package.json ] || return 1
  node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts[process.argv[1]] ? 0 : 1)" "$script"
}

python_lint_targets() {
  local targets=""
  [ -d src ] && targets="$targets src"
  [ -d tests ] && targets="$targets tests"
  [ -d test ] && targets="$targets test"
  for d in *_lsp cp2k_input_tools mdparser gromacs_lsp; do
    [ -d "$d" ] && targets="$targets $d"
  done
  if [ -z "${targets# }" ]; then
    echo "."
  else
    echo "$targets"
  fi
}

if has_npm_script lint; then
  npm run lint
  ran=1
fi

if [ -f Cargo.toml ]; then
  if command -v cargo-clippy >/dev/null 2>&1; then
    cargo clippy --all-targets --all-features -- -D warnings
  else
    cargo check --all-targets --all-features
  fi
  ran=1
fi

if [ -f pyproject.toml ] || [ -f setup.py ]; then
  if "$python_bin" -m flake8 --version >/dev/null 2>&1; then
    py_targets="$(python_lint_targets)"
    "$python_bin" -m flake8 $py_targets --max-line-length=100 --extend-ignore=E203,W503
    ran=1
  fi
  if "$python_bin" -m bandit --version >/dev/null 2>&1; then
    "$python_bin" -m bandit -q -r src
    ran=1
  fi
fi

if [ "$ran" -eq 0 ]; then
  echo "No linter configured; skipping."
fi
