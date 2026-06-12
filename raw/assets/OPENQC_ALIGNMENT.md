# OpenQC Alignment

`gamess-lsp` is the standalone GAMESS (US) language server. `newtontech/OpenQC-VSCode` should expose the same language behavior in VS Code.

## Keep aligned

- File extension handling for `.inp` GAMESS files.
- Diagnostics for unknown groups, unclosed sections, and required keywords.
- Snippet behavior for common GAMESS calculations.
- Completion and hover vocabulary for `$` groups and keywords.
- Minimal parser fixtures used for smoke tests.

## Release check

Before a public OpenQC release, smoke test one valid and one invalid GAMESS input against this server and the extension.
