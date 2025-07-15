import * as vscode from 'vscode';
import * as chokidar from 'chokidar';
import { ApiClient } from './apiClient';

export class ContextCapture {
    private context: vscode.ExtensionContext;
    private apiClient: ApiClient;
    private isCapturing = false;
    private sessionId: string;
    private fileWatcher?: chokidar.FSWatcher;
    private disposables: vscode.Disposable[] = [];

    constructor(context: vscode.ExtensionContext, apiClient: ApiClient) {
        this.context = context;
        this.apiClient = apiClient;
        this.sessionId = this.generateSessionId();
    }

    public start(): void {
        if (this.isCapturing) return;

        this.isCapturing = true;
        console.log(`Starting context capture for session: ${this.sessionId}`);

        this.startFileWatcher();
        this.startEditorListeners();
        this.startTerminalListeners();
        this.startGitListeners();

        // Send session start event
        this.sendContextEvent('session', 'start', {
            sessionId: this.sessionId,
            workspace: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
            timestamp: new Date().toISOString()
        });
    }

    public stop(): void {
        if (!this.isCapturing) return;

        this.isCapturing = false;
        console.log(`Stopping context capture for session: ${this.sessionId}`);

        // Clean up watchers and listeners
        this.fileWatcher?.close();
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];

        // Send session end event
        this.sendContextEvent('session', 'end', {
            sessionId: this.sessionId,
            timestamp: new Date().toISOString()
        });
    }

    private startFileWatcher(): void {
        const config = vscode.workspace.getConfiguration('pulsedev');
        if (!config.get<boolean>('enableFileWatcher', true)) return;

        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspaceRoot) return;

        this.fileWatcher = chokidar.watch(workspaceRoot, {
            ignored: /(^|[\/\\])(\.|node_modules|\.git)/,
            persistent: true,
            ignoreInitial: true
        });

        this.fileWatcher
            .on('add', path => this.sendContextEvent('file', 'created', { path }))
            .on('change', path => this.sendContextEvent('file', 'modified', { path }))
            .on('unlink', path => this.sendContextEvent('file', 'deleted', { path }));
    }

    private startEditorListeners(): void {
        // Track active editor changes
        this.disposables.push(
            vscode.window.onDidChangeActiveTextEditor(editor => {
                if (editor) {
                    this.sendContextEvent('editor', 'focus', {
                        file: editor.document.fileName,
                        language: editor.document.languageId,
                        lineCount: editor.document.lineCount
                    });
                }
            })
        );

        // Track text changes
        this.disposables.push(
            vscode.workspace.onDidChangeTextDocument(event => {
                this.sendContextEvent('editor', 'edit', {
                    file: event.document.fileName,
                    changes: event.contentChanges.length,
                    language: event.document.languageId
                });
            })
        );

        // Track saves
        this.disposables.push(
            vscode.workspace.onDidSaveTextDocument(document => {
                this.sendContextEvent('editor', 'save', {
                    file: document.fileName,
                    language: document.languageId,
                    lineCount: document.lineCount
                });
            })
        );

        // Track cursor position changes
        this.disposables.push(
            vscode.window.onDidChangeTextEditorSelection(event => {
                const selection = event.selections[0];
                this.sendContextEvent('editor', 'cursor', {
                    file: event.textEditor.document.fileName,
                    line: selection.start.line,
                    character: selection.start.character
                });
            })
        );
    }

    private startTerminalListeners(): void {
        const config = vscode.workspace.getConfiguration('pulsedev');
        if (!config.get<boolean>('enableTerminalCapture', true)) return;

        this.disposables.push(
            vscode.window.onDidOpenTerminal(terminal => {
                this.sendContextEvent('terminal', 'opened', {
                    name: terminal.name,
                    processId: terminal.processId
                });
            })
        );

        this.disposables.push(
            vscode.window.onDidCloseTerminal(terminal => {
                this.sendContextEvent('terminal', 'closed', {
                    name: terminal.name,
                    processId: terminal.processId
                });
            })
        );
    }

    private startGitListeners(): void {
        // Monitor git status changes
        this.disposables.push(
            vscode.workspace.onDidSaveTextDocument(async (document) => {
                try {
                    const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
                    if (gitExtension) {
                        const git = gitExtension.getAPI(1);
                        const repo = git.repositories[0];
                        
                        if (repo) {
                            const status = await repo.getStatus();
                            this.sendContextEvent('git', 'status_change', {
                                branch: repo.state.HEAD?.name,
                                changes: status.length,
                                modifiedFiles: status.map((s: any) => s.uri.fsPath)
                            });
                        }
                    }
                } catch (error) {
                    console.error('Git status capture error:', error);
                }
            })
        );
    }

    private async sendContextEvent(agent: string, type: string, payload: any): Promise<void> {
        if (!this.isCapturing) return;

        try {
            await this.apiClient.sendContextEvent({
                sessionId: this.sessionId,
                agent,
                type,
                payload,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('Failed to send context event:', error);
        }
    }

    private generateSessionId(): string {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}