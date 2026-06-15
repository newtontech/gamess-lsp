#!/usr/bin/env python3
"""Regenerate raw/assets/manifest.json checksums and entry metadata.

Pipeline: official-docs -> raw/assets -> wiki -> schema/rules -> provenance.
Run from repo root: python3 scripts/refresh_provenance_manifest.py
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS = REPO_ROOT / "raw" / "assets"
MANIFEST_PATH = ASSETS / "manifest.json"

OFFICIAL_ANCHORS = [
    {
        "name": "GAMESS input documentation",
        "type": "official_docs",
        "url": "https://www.msg.chem.iastate.edu/gamess/documentation.html",
        "retrieval_date": "2026-06-15",
        "software_version": "GAMESS (US) 2024 R1",
        "license": "academic use",
        "notes": "Primary keyword and $GROUP reference",
    }
]

ROLE_BY_NAME = {
    "DIAGNOSTIC_ENGINE_V1.md": "architecture_doc",
    "OPENQC_ALIGNMENT.md": "integration_contract",
    "agent-verification-loop.md": "quality_doc",
    "README.md": "overview",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def stable_id(rel: str) -> str:
    stem = rel.replace("/", "-").replace(".", "-").lower()
    return f"gamess-{stem}-v1"


def build_entries() -> list[dict]:
    entries: list[dict] = []
    for path in sorted(ASSETS.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        rel = path.relative_to(ASSETS).as_posix()
        entries.append(
            {
                "path": rel,
                "source_type": "official_docs" if rel.startswith("examples/") else "internal_doc",
                "source_url": OFFICIAL_ANCHORS[0]["url"] if rel.startswith("examples/") else None,
                "retrieval_date": "2026-06-15",
                "software_version": OFFICIAL_ANCHORS[0]["software_version"],
                "license": "MIT" if rel.startswith("examples/") else "internal",
                "checksum_sha256": sha256(path),
                "stable_id": stable_id(rel),
                "role": ROLE_BY_NAME.get(path.name, "examples" if rel.startswith("examples/") else "reference"),
                "wiki_links": [],
            }
        )
    return entries


def main() -> None:
    manifest = {
        "manifest_version": "1.0.0",
        "schema_version": "provenance-manifest-v1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repository": "newtontech/gamess-lsp",
        "pipeline": (
            "official-docs -> raw/assets -> wiki/entities+concepts+synthesis -> "
            "versioned schema/rules -> provenance -> fixtures/eval -> LSP runtime/OpenQC integration"
        ),
        "official_source_anchors": OFFICIAL_ANCHORS,
        "entries": build_entries(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH} ({len(manifest['entries'])} entries)")


if __name__ == "__main__":
    main()
