import * as vscode from 'vscode';
import { ContextCapture } from './contextCapture';
import { ApiClient } from './apiClient';

let contextCapture: ContextCapture;

export function activate(context: vscode.ExtensionContext) {
    console.log('PulseDev+ CCM is now active');

    const config = vscode.workspace.getConfiguration('pulsedev');
    const apiUrl = config.get<string>('apiUrl', 'http://localhost:8000');
    
    const apiClient = new ApiClient(apiUrl);
    contextCapture = new ContextCapture(context, apiClient);

    // Register commands
    const startCommand = vscode.commands.registerCommand('pulsedev.startContext', () => {
        contextCapture.start();
        vscode.window.showInformationMessage('PulseDev+ context capture started');
    });

    const stopCommand = vscode.commands.registerCommand('pulsedev.stopContext', () => {
        contextCapture.stop();
        vscode.window.showInformationMessage('PulseDev+ context capture stopped');
    });

    const viewCommand = vscode.commands.registerCommand('pulsedev.viewContext', async () => {
        const panel = vscode.window.createWebviewPanel(
            'pulsdevContext',
            'PulseDev+ Context',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );
        
        const contextData = await apiClient.getRecentContext();
        panel.webview.html = getContextWebviewContent(contextData);
    });

    const wipeCommand = vscode.commands.registerCommand('pulsedev.wipeContext', async () => {
        const result = await vscode.window.showWarningMessage(
            'Are you sure you want to wipe all context data?',
            'Yes', 'No'
        );
        
        if (result === 'Yes') {
            await apiClient.wipeContext();
            vscode.window.showInformationMessage('Context data wiped');
        }
    });

    context.subscriptions.push(startCommand, stopCommand, viewCommand, wipeCommand);

    // Auto-start context capture
    contextCapture.start();
}

export function deactivate() {
    if (contextCapture) {
        contextCapture.stop();
    }
}

function getContextWebviewContent(contextData: any): string {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PulseDev+ Context</title>
        <style>
            body { font-family: var(--vscode-font-family); color: var(--vscode-foreground); }
            .event { margin: 10px 0; padding: 10px; border-left: 3px solid var(--vscode-accent); }
            .timestamp { color: var(--vscode-descriptionForeground); font-size: 0.9em; }
            .agent { font-weight: bold; color: var(--vscode-symbolIcon-keywordForeground); }
        </style>
    </head>
    <body>
        <h1>Recent Context Events</h1>
        ${contextData.map((event: any) => `
            <div class="event">
                <div class="timestamp">${new Date(event.timestamp).toLocaleString()}</div>
                <div class="agent">${event.agent}</div>
                <div>${event.type}: ${JSON.stringify(event.payload, null, 2)}</div>
            </div>
        `).join('')}
    </body>
    </html>`;
}