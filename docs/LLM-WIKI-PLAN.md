# GAMESS LLM Wiki Plan

This repository follows the OpenQC LSP family wiki layout. Keep raw source provenance in `raw/assets/`, distilled entities in `wiki/entities/`, concepts in `wiki/concepts/`, and agent-facing synthesis in `wiki/synthesis/`.

## Sources

- Official documentation links are tracked in `lsp-capabilities.json` under `sourceProvenance`.
- Do not copy large upstream documents into this repository; preserve links, versions, and retrieval dates.

## Agent Contract

The wiki should feed diagnostics, hover, completion, next-token guidance, and repair-plan hints exposed through `gamess-lsp-tool` and OpenQC `DSLAuthoringContext`.
