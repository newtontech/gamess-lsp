#!/usr/bin/env python3
"""Verify that all GAMESS-LSP release metadata agrees with the pushed tag."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _project_version() -> str:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    if match is None:
        raise RuntimeError("project.version is missing from pyproject.toml")
    return match.group(1)


def _versions() -> dict[str, str]:
    capabilities = json.loads((ROOT / "lsp-capabilities.json").read_text(encoding="utf-8"))
    init_text = (ROOT / "src/gamess_lsp/__init__.py").read_text(encoding="utf-8")
    init_match = re.search(r'__version__ = "([^"]+)"', init_text)
    if init_match is None:
        raise RuntimeError("runtime version metadata is missing")
    uv_lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    uv_lock_match = re.search(r'\[\[package\]\]\nname = "gamess-lsp"\nversion = "([^"]+)"', uv_lock)
    if uv_lock_match is None:
        raise RuntimeError("gamess-lsp version is missing from uv.lock")
    return {
        "pyproject.toml": _project_version(),
        "uv.lock": uv_lock_match.group(1),
        "VERSION": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "gamess_lsp runtime": init_match.group(1),
        "lsp-capabilities.json": capabilities["releaseVersion"],
    }


def verify(tag: str) -> str:
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError(f"release tag must use vMAJOR.MINOR.PATCH, got {tag!r}")
    expected = tag.removeprefix("v")
    mismatches = {name: value for name, value in _versions().items() if value != expected}
    if mismatches:
        details = ", ".join(f"{name}={value}" for name, value in sorted(mismatches.items()))
        raise ValueError(f"release metadata does not match {tag}: {details}")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{expected}]" not in changelog:
        raise ValueError(f"CHANGELOG.md has no {expected} release entry")
    return expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True, help="Release tag, for example v0.1.1")
    args = parser.parse_args()
    version = verify(args.tag)
    print(f"release metadata verified for {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
