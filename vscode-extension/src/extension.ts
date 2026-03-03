import * as path from 'path';
import { workspace, ExtensionContext } from 'vscode';
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
  // Get the server path from configuration or use default
  const config = workspace.getConfiguration('gamess-lsp');
  const serverPath = config.get<string>('serverPath', 'gamess-lsp');

  // Server options
  const serverOptions: ServerOptions = {
    command: serverPath,
    args: ['server', '--stdio'],
    options: {
      env: process.env,
    },
  };

  // Client options
  const clientOptions: LanguageClientOptions = {
    documentSelector: [
      { scheme: 'file', language: 'gamess' },
      { scheme: 'file', pattern: '**/*.inp' },
    ],
    synchronize: {
      fileEvents: workspace.createFileSystemWatcher('**/*.inp'),
    },
  };

  // Create and start the client
  client = new LanguageClient(
    'gamess-lsp',
    'GAMESS Language Server',
    serverOptions,
    clientOptions
  );

  // Start the client
  client.start();
}

export function deactivate(): Thenable<void> | undefined {
  if (!client) {
    return undefined;
  }
  return client.stop();
}
