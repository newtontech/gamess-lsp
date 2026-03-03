# VS Code Extension for GAMESS-LSP

This is the VS Code extension for GAMESS Language Server Protocol support.

## Features

- Syntax highlighting for GAMESS input files
- Auto-completion for $GROUPs and parameters
- Hover documentation
- Real-time diagnostics
- Code folding for $GROUP sections
- Code snippets for common calculations

## Installation

### From VS Code Marketplace (when published)

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "GAMESS Language Support"
4. Click Install

### From Source

1. Clone this repository
2. Run `npm install`
3. Run `npm run compile`
4. Press F5 to open a new Extension Development Host window

## Requirements

- VS Code 1.74.0 or higher
- gamess-lsp installed (`pip install gamess-lsp`)

## Configuration

Add to your VS Code settings (`settings.json`):

```json
{
  "gamess-lsp.serverPath": "gamess-lsp",
  "gamess-lsp.logLevel": "info"
}
```

## Development

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch for changes
npm run watch

# Package extension
npm run package
```

## License

MIT
