"""Tests for the OpenQC v1 docstring/wiki/raw traceability report."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "reports" / "docstring-wiki-raw-traceability.json"
CHECKER = REPO_ROOT / "scripts" / "check_docstring_traceability.py"


def load_report() -> dict[str, Any]:
    """Load the committed traceability report."""
    return cast(dict[str, Any], json.loads(REPORT_PATH.read_text(encoding="utf-8")))


def test_traceability_report_schema_contract() -> None:
    report = load_report()
    assert report["schemaVersion"] == "openqc.lsp.traceability.v1"
    assert report["serverId"] == "gamess-lsp"
    assert report["repository"] == "newtontech/gamess-lsp"
    assert report["languageId"] == "gamess"
    for field in ["summary", "docstrings", "wikiSources", "ruleIds", "sourceUrls", "rawManifest"]:
        assert field in report


def test_summary_has_zero_failures() -> None:
    summary = load_report()["summary"]
    assert summary["docstringsTotal"] == summary["docstringsLinked"]
    assert summary["brokenWikiLinks"] == 0
    assert summary["wikiSourcesWithoutRaw"] == 0
    assert summary["rawManifestFailures"] == 0


def test_docstring_links_exist() -> None:
    for entry in load_report()["docstrings"]:
        assert (REPO_ROOT / entry["path"]).is_file()
        assert (REPO_ROOT / entry["wikiPath"]).is_file()
        assert entry["wikiPath"].startswith("wiki/")


def test_wiki_sources_link_to_raw_assets() -> None:
    for entry in load_report()["wikiSources"]:
        assert (REPO_ROOT / entry["wikiPath"]).is_file()
        assert (REPO_ROOT / entry["rawPath"]).exists()
        assert entry["sourceUrl"].startswith("https://github.com/newtontech/gamess-lsp/")


def test_rule_ids_match_openqc_pattern() -> None:
    pattern = re.compile(r"^[A-Z]+-[A-Z]+-[A-Z]+-\d{3}$")
    for entry in load_report()["ruleIds"]:
        assert pattern.fullmatch(entry["code"])
        assert (REPO_ROOT / entry["sourcePath"]).is_file()


def test_source_urls_are_repo_relative_raw_links() -> None:
    for entry in load_report()["sourceUrls"]:
        assert entry["rawPath"].startswith("raw/assets/")
        assert (REPO_ROOT / entry["rawPath"]).is_file()
        assert entry["url"].startswith("https://github.com/newtontech/gamess-lsp/")


def test_raw_manifest_descriptor() -> None:
    raw_manifest = load_report()["rawManifest"]
    assert raw_manifest == {"path": "raw/assets/manifest.json", "ok": True}
    assert (REPO_ROOT / raw_manifest["path"]).is_file()


def test_checker_regenerates_report() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--write-report", "--strict"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
