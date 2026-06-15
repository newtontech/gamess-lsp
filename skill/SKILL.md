---
name: gamess
description: "GAMESS input preflight for generated .inp job files."
---

# GAMESS LSP Skill

Use this skill when preparing, repairing, or reviewing GAMESS input files before a run. It provides an installable language server and an agent-facing CLI that reports machine-readable diagnostics.

## Scope

- Input patterns: *.inp
- Server command: `gamess-lsp`
- Agent CLI: `gamess-lsp-tool`
- Diagnostic contract: `DiagnosticEnvelope/v1`

## Installing the checker

```bash
pip install gamess-lsp
```

This installs the `gamess-lsp` language server and the `gamess-lsp-tool` agent CLI from the `gamess-lsp` Python package.

## Useful inspection commands

```bash
gamess-lsp-tool capabilities
gamess-lsp-tool skill-spec --format json
gamess-lsp-tool skill-export --output ./skill
gamess-lsp-tool check <input-file-or-dir> --format json
gamess-lsp-tool context <input-file-or-dir> --line 0 --character 0 --format json
gamess-lsp-tool hover <input-file-or-dir> --line 0 --character 0 --format json
gamess-lsp-tool complete <input-file-or-dir> --line 0 --character 0 --format json
gamess-lsp-tool symbols <input-file-or-dir> --format json
gamess-lsp-tool fix <input-file-or-dir> --line 0 --character 0 --format json
```

`fix` is advisory and must be treated as a preview. Do not blindly apply a repair without preserving the user's scientific intent.

## Validation gate

Before saying generated inputs are ready, run:

```bash
gamess-lsp-tool check <input-file-or-dir> --format json --fail-on-blocking
```

Report `commands`, `files_checked`, `tool_available`, `diagnostics`, `blocking_findings`, `readiness`, and `reason`.

## Repair rules

1. Validate first and identify the smallest blocking issue.
2. Fix syntax or schema errors with minimal edits.
3. Preserve scientific settings unless the user explicitly asks to redesign them.
4. Re-run the checker after every edit.
5. Separate syntax, schema, semantic, and runtime-log diagnostics in the final report.
