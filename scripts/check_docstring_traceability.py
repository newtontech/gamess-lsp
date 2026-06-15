#!/usr/bin/env python3
"""Generate the OpenQC v1 docstring/wiki/raw traceability report for GAMESS."""

from __future__ import annotations

import argparse
import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = REPO_ROOT / "reports" / "docstring-wiki-raw-traceability.json"
SCHEMA_VERSION = "openqc.lsp.traceability.v1"
SERVER_ID = "gamess-lsp"
REPOSITORY = "newtontech/gamess-lsp"
LANGUAGE_ID = "gamess"

WIKI_RE = re.compile(r"wiki/(?:concepts|entities|synthesis)/[\w./-]+\.md")
RAW_RE = re.compile(r"raw/assets/[\w./-]+")

RULE_IDS: tuple[dict[str, str], ...] = (
    {"code": "GAMESS-INPUT-STRUCTURE-001", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-STRUCTURE-002", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-SCHEMA-001", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-SCHEMA-002", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-SCHEMA-003", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-SCHEMA-004", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-SCHEMA-005", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-BESTPRAC-001", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-BESTPRAC-002", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-INPUT-BESTPRAC-003", "sourcePath": "src/gamess_lsp/features/lint.py"},
    {"code": "GAMESS-DIAG-SYNTAX-001", "sourcePath": "src/gamess_lsp/features/diagnostic.py"},
    {"code": "GAMESS-DIAG-SEMANTIC-001", "sourcePath": "src/gamess_lsp/features/diagnostic.py"},
    {"code": "GAMESS-DIAG-TYPECHECK-001", "sourcePath": "src/gamess_lsp/features/typecheck.py"},
    {"code": "GAMESS-OUTPUT-RUNTIME-001", "sourcePath": "src/gamess_lsp/output_parser.py"},
    {"code": "GAMESS-PREFLIGHT-ENVELOPE-001", "sourcePath": "src/gamess_lsp/preflight.py"},
)


def repo_relative(path: Path) -> str:
    """Return a repository-relative path."""
    return str(path.relative_to(REPO_ROOT))


def module_docstring(path: Path) -> str:
    """Return a Python module docstring, or an empty string if parsing fails."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return ""
    return ast.get_docstring(tree) or ""


def collect_docstrings() -> tuple[list[dict[str, str]], int, int, int]:
    """Collect module docstring -> wiki links."""
    entries: list[dict[str, str]] = []
    total = 0
    linked = 0
    broken = 0
    for path in sorted((REPO_ROOT / "src" / "gamess_lsp").rglob("*.py")):
        doc = module_docstring(path)
        if not doc:
            continue
        total += 1
        wiki_paths = sorted(set(WIKI_RE.findall(doc)))
        if wiki_paths:
            linked += 1
        for wiki_path in wiki_paths:
            if not (REPO_ROOT / wiki_path).is_file():
                broken += 1
            entries.append(
                {
                    "path": repo_relative(path),
                    "symbol": path.stem,
                    "wikiPath": wiki_path,
                }
            )
    return entries, total, linked, broken


def collect_wiki_sources() -> tuple[list[dict[str, str]], int]:
    """Collect wiki page -> raw evidence links."""
    entries: list[dict[str, str]] = []
    missing_raw = 0
    for path in sorted((REPO_ROOT / "wiki").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        raw_paths = sorted(set(RAW_RE.findall(text)))
        if not raw_paths:
            missing_raw += 1
            continue
        for raw_path in raw_paths:
            entries.append(
                {
                    "wikiPath": repo_relative(path),
                    "rawPath": raw_path,
                    "sourceUrl": f"https://github.com/{REPOSITORY}/blob/main/{raw_path}",
                }
            )
    return entries, missing_raw


def collect_source_urls() -> list[dict[str, str]]:
    """Collect GitHub URLs for raw evidence assets."""
    entries: list[dict[str, str]] = []
    for path in sorted((REPO_ROOT / "raw" / "assets").rglob("*")):
        if path.is_file():
            raw_path = repo_relative(path)
            entries.append(
                {
                    "rawPath": raw_path,
                    "url": f"https://github.com/{REPOSITORY}/blob/main/{raw_path}",
                }
            )
    return entries


def raw_manifest_descriptor() -> dict[str, object]:
    """Return the canonical raw manifest descriptor consumed by OpenQC."""
    path = REPO_ROOT / "raw" / "assets" / "manifest.json"
    return {
        "path": repo_relative(path),
        "ok": path.is_file() and path.stat().st_size > 0,
    }


def generate_report() -> dict[str, Any]:
    """Generate the full traceability report."""
    docstrings, total_docstrings, linked_docstrings, broken_wiki_links = collect_docstrings()
    wiki_sources, wiki_sources_without_raw = collect_wiki_sources()
    source_urls = collect_source_urls()
    raw_manifest = raw_manifest_descriptor()
    rule_ids = list(RULE_IDS)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "serverId": SERVER_ID,
        "repository": REPOSITORY,
        "languageId": LANGUAGE_ID,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "docstringsTotal": total_docstrings,
            "docstringsLinked": linked_docstrings,
            "brokenWikiLinks": broken_wiki_links,
            "wikiSourcesWithoutRaw": wiki_sources_without_raw,
            "rawManifestFailures": 0 if raw_manifest["ok"] else 1,
            "ruleIdsTotal": len(rule_ids),
            "sourceUrlsTotal": len(source_urls),
            "wikiSourcesTotal": len(wiki_sources),
        },
        "docstrings": docstrings,
        "wikiSources": wiki_sources,
        "ruleIds": rule_ids,
        "sourceUrls": source_urls,
        "rawManifest": raw_manifest,
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    """Validate the report against the OpenQC checker contract."""
    errors: list[str] = []
    for field in [
        "schemaVersion",
        "serverId",
        "repository",
        "languageId",
        "generatedAt",
        "summary",
        "docstrings",
        "wikiSources",
        "ruleIds",
        "sourceUrls",
        "rawManifest",
    ]:
        if field not in report:
            errors.append(f"missing top-level field: {field}")
    if errors:
        return errors
    if report["schemaVersion"] != SCHEMA_VERSION:
        errors.append("wrong schemaVersion")
    summary = report["summary"]
    for field in [
        "docstringsTotal",
        "docstringsLinked",
        "brokenWikiLinks",
        "wikiSourcesWithoutRaw",
        "rawManifestFailures",
    ]:
        if not isinstance(summary.get(field), int) or summary[field] < 0:
            errors.append(f"summary.{field} must be a non-negative integer")
    if summary.get("docstringsLinked") != summary.get("docstringsTotal"):
        errors.append("not all module docstrings link to wiki pages")
    if summary.get("brokenWikiLinks") != 0:
        errors.append("broken wiki links found")
    if summary.get("wikiSourcesWithoutRaw") != 0:
        errors.append("wiki pages without raw evidence found")
    if summary.get("rawManifestFailures") != 0:
        errors.append("raw manifest failure found")
    rule_pattern = re.compile(r"^[A-Z]+-[A-Z]+-[A-Z]+-\d{3}$")
    for item in report["ruleIds"]:
        if not rule_pattern.fullmatch(item.get("code", "")):
            errors.append(f"bad rule id: {item.get('code')}")
    raw_manifest = report["rawManifest"]
    if not isinstance(raw_manifest, dict):
        errors.append("rawManifest must be an object")
    elif not isinstance(raw_manifest.get("path"), str) or not isinstance(
        raw_manifest.get("ok"), bool
    ):
        errors.append("rawManifest must contain path and ok")
    return errors


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = generate_report()
    errors = validate_report(report)
    if args.write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Report written to {REPORT_PATH}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1 if args.strict else 0
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
