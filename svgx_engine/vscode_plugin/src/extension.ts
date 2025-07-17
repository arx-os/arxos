/**
 * SVGX Engine VS Code Extension
 * 
 * Provides comprehensive support for SVGX files including:
 * - Syntax highlighting
 * - IntelliSense and autocompletion
 * - Live preview integration
 * - Error reporting and validation
 * - Debugging support
 * 
 * CTO Directives:
 * - Standard development practices
 * - Performance monitoring
 * - Real-time validation
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';
import WebSocket from 'ws';

interface SVGXElement {
    id: string;
    type: string;
    properties: Record<string, any>;
    position?: { x: number; y: number; z?: number };
    children?: SVGXElement[];
}

interface SVGXSimulation {
    id: string;
    type: 'structural' | 'fluid_dynamics' | 'heat_transfer' | 'electrical' | 'rf_propagation';
    parameters: Record<string, any>;
    status: 'idle' | 'running' | 'completed' | 'error';
    results?: any;
}

interface SVGXValidationResult {
    valid: boolean;
    errors: Array<{
        line: number;
        column: number;
        message: string;
        severity: 'error' | 'warning';
    }>;
    warnings: Array<{
        line: number;
        column: number;
        message: string;
    }>;
}

class SVGXLanguageClient {
    private serverUrl: string;
    private apiKey: string;
    private wsConnection?: WebSocket;

    constructor() {
        const config = vscode.workspace.getConfiguration('svgx');
        this.serverUrl = config.get('server.url', 'http://localhost:8000');
        this.apiKey = config.get('server.apiKey', '');
    }

    async validateFile(content: string): Promise<SVGXValidationResult> {
        try {
            const response = await axios.post(`${this.serverUrl}/validate`, {
                content: content
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data;
        } catch (error) {
            console.error('Validation request failed:', error);
            return {
                valid: false,
                errors: [{
                    line: 1,
                    column: 1,
                    message: 'Failed to connect to SVGX Engine server',
                    severity: 'error'
                }],
                warnings: []
            };
        }
    }

    async parseFile(content: string): Promise<SVGXElement[]> {
        try {
            const response = await axios.post(`${this.serverUrl}/parse`, {
                content: content
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data.elements || [];
        } catch (error) {
            console.error('Parse request failed:', error);
            return [];
        }
    }

    async runSimulation(simulationType: string, elements: SVGXElement[]): Promise<any> {
        try {
            const response = await axios.post(`${this.serverUrl}/simulate`, {
                simulation_type: simulationType,
                data: {
                    elements: elements
                }
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data;
        } catch (error) {
            console.error('Simulation request failed:', error);
            throw new Error('Failed to run simulation');
        }
    }

    async compileToSVG(elements: SVGXElement[]): Promise<string> {
        try {
            const response = await axios.post(`${this.serverUrl}/compile`, {
                target: 'svg',
                elements: elements
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data.svg_content;
        } catch (error) {
            console.error('Compilation request failed:', error);
            throw new Error('Failed to compile to SVG');
        }
    }

    async compileToJSON(elements: SVGXElement[]): Promise<any> {
        try {
            const response = await axios.post(`${this.serverUrl}/compile`, {
                target: 'json',
                elements: elements
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data.json_content;
        } catch (error) {
            console.error('Compilation request failed:', error);
            throw new Error('Failed to compile to JSON');
        }
    }

    connectWebSocket(): Promise<void> {
        return new Promise((resolve, reject) => {
            const wsUrl = this.serverUrl.replace('http', 'ws') + '/ws';
            this.wsConnection = new WebSocket(wsUrl);

            this.wsConnection.on('open', () => {
                console.log('WebSocket connected to SVGX Engine');
                resolve();
            });

            this.wsConnection.on('error', (error) => {
                console.error('WebSocket connection failed:', error);
                reject(error);
            });

            this.wsConnection.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            });
        });
    }

    private handleWebSocketMessage(message: any) {
        switch (message.type) {
            case 'simulation_update':
                this.handleSimulationUpdate(message);
                break;
            case 'validation_result':
                this.handleValidationResult(message);
                break;
            case 'preview_update':
                this.handlePreviewUpdate(message);
                break;
        }
    }

    private handleSimulationUpdate(message: any) {
        // Update simulation status in the UI
        vscode.commands.executeCommand('svgx.updateSimulationStatus', message);
    }

    private handleValidationResult(message: any) {
        // Update validation results in the UI
        vscode.commands.executeCommand('svgx.updateValidationResult', message);
    }

    private handlePreviewUpdate(message: any) {
        // Update live preview
        vscode.commands.executeCommand('svgx.updatePreview', message);
    }

    disconnect() {
        if (this.wsConnection) {
            this.wsConnection.close();
            this.wsConnection = undefined;
        }
    }
}

class SVGXPreviewProvider implements vscode.CustomTextEditorProvider {
    public static register(context: vscode.ExtensionContext): vscode.Disposable {
        return vscode.window.registerCustomEditorProvider('svgx.preview', new SVGXPreviewProvider(context));
    }

    constructor(private readonly context: vscode.ExtensionContext) {}

    async resolveCustomTextEditor(
        document: vscode.TextDocument,
        webviewPanel: vscode.WebviewPanel,
        _token: vscode.CancellationToken
    ): Promise<void> {
        webviewPanel.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.joinPath(this.context.extensionUri, 'media')
            ]
        };

        webviewPanel.webview.html = this.getHtmlForWebview(webviewPanel.webview);

        const updateWebview = () => {
            webviewPanel.webview.postMessage({
                type: 'update',
                content: document.getText()
            });
        };

        const changeDocumentSubscription = vscode.workspace.onDidChangeTextDocument(e => {
            if (e.document.uri.toString() === document.uri.toString()) {
                updateWebview();
            }
        });

        webviewPanel.onDidDispose(() => {
            changeDocumentSubscription.dispose();
        });

        updateWebview();
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>SVGX Preview</title>
                <style>
                    body {
                        margin: 0;
                        padding: 20px;
                        font-family: Arial, sans-serif;
                        background-color: #1e1e1e;
                        color: #ffffff;
                    }
                    .preview-container {
                        width: 100%;
                        height: calc(100vh - 40px);
                        border: 1px solid #3c3c3c;
                        border-radius: 4px;
                        overflow: hidden;
                    }
                    .svgx-viewer {
                        width: 100%;
                        height: 100%;
                        background-color: #2d2d2d;
                    }
                    .loading {
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100%;
                        font-size: 16px;
                        color: #cccccc;
                    }
                    .error {
                        color: #ff6b6b;
                        padding: 20px;
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <div class="preview-container">
                    <div id="svgx-viewer" class="svgx-viewer">
                        <div class="loading">Loading SVGX preview...</div>
                    </div>
                </div>
                <script>
                    const vscode = acquireVsCodeApi();
                    const viewer = document.getElementById('svgx-viewer');
                    
                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.type) {
                            case 'update':
                                updatePreview(message.content);
                                break;
                        }
                    });
                    
                    function updatePreview(content) {
                        try {
                            // Parse SVGX content and render
                            const elements = parseSVGX(content);
                            renderElements(elements);
                        } catch (error) {
                            viewer.innerHTML = '<div class="error">Error parsing SVGX: ' + error.message + '</div>';
                        }
                    }
                    
                    function parseSVGX(content) {
                        // Simplified SVGX parser
                        const lines = content.split('\\n');
                        const elements = [];
                        
                        for (let i = 0; i < lines.length; i++) {
                            const line = lines[i].trim();
                            if (line.startsWith('element')) {
                                const element = parseElement(line, i + 1);
                                if (element) {
                                    elements.push(element);
                                }
                            }
                        }
                        
                        return elements;
                    }
                    
                    function parseElement(line, lineNumber) {
                        try {
                            const match = line.match(/element\\s+(\\w+)\\s+(\\w+)\\s*\\(([^)]*)\\)/);
                            if (match) {
                                return {
                                    id: match[1],
                                    type: match[2],
                                    properties: parseProperties(match[3]),
                                    line: lineNumber
                                };
                            }
                        } catch (error) {
                            console.error('Error parsing element:', error);
                        }
                        return null;
                    }
                    
                    function parseProperties(propsString) {
                        const properties = {};
                        if (propsString) {
                            const pairs = propsString.split(',');
                            for (const pair of pairs) {
                                const [key, value] = pair.split('=').map(s => s.trim());
                                if (key && value) {
                                    properties[key] = value;
                                }
                            }
                        }
                        return properties;
                    }
                    
                    function renderElements(elements) {
                        if (elements.length === 0) {
                            viewer.innerHTML = '<div class="loading">No elements to display</div>';
                            return;
                        }
                        
                        let svgContent = '<svg width="100%" height="100%" viewBox="0 0 800 600">';
                        svgContent += '<rect width="100%" height="100%" fill="#2d2d2d"/>';
                        
                        for (const element of elements) {
                            svgContent += renderElement(element);
                        }
                        
                        svgContent += '</svg>';
                        viewer.innerHTML = svgContent;
                    }
                    
                    function renderElement(element) {
                        const x = parseFloat(element.properties.x) || 100;
                        const y = parseFloat(element.properties.y) || 100;
                        const width = parseFloat(element.properties.width) || 50;
                        const height = parseFloat(element.properties.height) || 50;
                        
                        switch (element.type) {
                            case 'rectangle':
                                return \`<rect x="\${x}" y="\${y}" width="\${width}" height="\${height}" fill="#4a9eff" stroke="#ffffff" stroke-width="2"/>\`;
                            case 'circle':
                                const radius = parseFloat(element.properties.radius) || 25;
                                return \`<circle cx="\${x}" cy="\${y}" r="\${radius}" fill="#4a9eff" stroke="#ffffff" stroke-width="2"/>\`;
                            case 'line':
                                const x2 = parseFloat(element.properties.x2) || x + 100;
                                const y2 = parseFloat(element.properties.y2) || y;
                                return \`<line x1="\${x}" y1="\${y}" x2="\${x2}" y2="\${y2}" stroke="#ffffff" stroke-width="3"/>\`;
                            default:
                                return \`<rect x="\${x}" y="\${y}" width="\${width}" height="\${height}" fill="#666666" stroke="#ffffff" stroke-width="1"/>\`;
                        }
                    }
                </script>
            </body>
            </html>
        `;
    }
}

class SVGXDiagnosticsProvider {
    private diagnosticsCollection: vscode.DiagnosticCollection;

    constructor() {
        this.diagnosticsCollection = vscode.languages.createDiagnosticCollection('svgx');
    }

    async updateDiagnostics(document: vscode.TextDocument): Promise<void> {
        if (document.languageId !== 'svgx') {
            return;
        }

        const client = new SVGXLanguageClient();
        const validationResult = await client.validateFile(document.getText());

        const diagnostics: vscode.Diagnostic[] = [];

        // Add errors
        for (const error of validationResult.errors) {
            const range = new vscode.Range(
                error.line - 1,
                error.column - 1,
                error.line - 1,
                error.column
            );
            
            const diagnostic = new vscode.Diagnostic(
                range,
                error.message,
                vscode.DiagnosticSeverity.Error
            );
            
            diagnostics.push(diagnostic);
        }

        // Add warnings
        for (const warning of validationResult.warnings) {
            const range = new vscode.Range(
                warning.line - 1,
                warning.column - 1,
                warning.line - 1,
                warning.column
            );
            
            const diagnostic = new vscode.Diagnostic(
                range,
                warning.message,
                vscode.DiagnosticSeverity.Warning
            );
            
            diagnostics.push(diagnostic);
        }

        this.diagnosticsCollection.set(document.uri, diagnostics);
    }

    clearDiagnostics(): void {
        this.diagnosticsCollection.clear();
    }
}

class SVGXCompletionProvider implements vscode.CompletionItemProvider {
    provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): vscode.ProviderResult<vscode.CompletionItem[] | vscode.CompletionList<vscode.CompletionItem>> {
        const items: vscode.CompletionItem[] = [];

        // Element types
        const elementTypes = [
            'rectangle', 'circle', 'line', 'polygon', 'text',
            'beam', 'column', 'wall', 'floor', 'roof',
            'pipe', 'valve', 'pump', 'tank', 'pump',
            'wire', 'resistor', 'capacitor', 'inductor', 'voltage_source'
        ];

        for (const type of elementTypes) {
            const item = new vscode.CompletionItem(type, vscode.CompletionItemKind.Class);
            item.detail = `SVGX Element Type`;
            item.documentation = `Create a ${type} element`;
            item.insertText = `element ${type}(id="", x=0, y=0)`;
            items.push(item);
        }

        // Properties
        const properties = [
            'id', 'x', 'y', 'z', 'width', 'height', 'radius',
            'length', 'thickness', 'material', 'color',
            'position', 'rotation', 'scale'
        ];

        for (const prop of properties) {
            const item = new vscode.CompletionItem(prop, vscode.CompletionItemKind.Property);
            item.detail = `SVGX Property`;
            item.documentation = `Property: ${prop}`;
            item.insertText = `${prop}=`;
            items.push(item);
        }

        // Simulation types
        const simulationTypes = [
            'structural', 'fluid_dynamics', 'heat_transfer', 'electrical', 'rf_propagation'
        ];

        for (const simType of simulationTypes) {
            const item = new vscode.CompletionItem(simType, vscode.CompletionItemKind.Function);
            item.detail = `SVGX Simulation Type`;
            item.documentation = `Run ${simType} simulation`;
            item.insertText = simType;
            items.push(item);
        }

        return new vscode.CompletionList(items);
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('SVGX Engine extension is now active!');

    const languageClient = new SVGXLanguageClient();
    const diagnosticsProvider = new SVGXDiagnosticsProvider();

    // Register commands
    let previewCommand = vscode.commands.registerCommand('svgx.preview', async () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'svgx') {
            const uri = editor.document.uri;
            await vscode.commands.executeCommand('vscode.openWith', uri, 'svgx.preview');
        } else {
            vscode.window.showWarningMessage('Please open an SVGX file to preview.');
        }
    });

    let validateCommand = vscode.commands.registerCommand('svgx.validate', async () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'svgx') {
            try {
                const validationResult = await languageClient.validateFile(editor.document.getText());
                
                if (validationResult.valid) {
                    vscode.window.showInformationMessage('SVGX file is valid!');
                } else {
                    vscode.window.showErrorMessage(`SVGX file has ${validationResult.errors.length} errors.`);
                }
                
                await diagnosticsProvider.updateDiagnostics(editor.document);
            } catch (error) {
                vscode.window.showErrorMessage(`Validation failed: ${error.message}`);
            }
        } else {
            vscode.window.showWarningMessage('Please open an SVGX file to validate.');
        }
    });

    let simulateCommand = vscode.commands.registerCommand('svgx.simulate', async () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'svgx') {
            try {
                const elements = await languageClient.parseFile(editor.document.getText());
                
                if (elements.length === 0) {
                    vscode.window.showWarningMessage('No elements found to simulate.');
                    return;
                }

                const simulationType = await vscode.window.showQuickPick([
                    'structural',
                    'fluid_dynamics', 
                    'heat_transfer',
                    'electrical',
                    'rf_propagation'
                ], {
                    placeHolder: 'Select simulation type'
                });

                if (simulationType) {
                    vscode.window.showInformationMessage(`Running ${simulationType} simulation...`);
                    
                    const result = await languageClient.runSimulation(simulationType, elements);
                    
                    vscode.window.showInformationMessage(`Simulation completed successfully!`);
                    
                    // Show results in a new document
                    const resultsDoc = await vscode.workspace.openTextDocument({
                        content: JSON.stringify(result, null, 2),
                        language: 'json'
                    });
                    await vscode.window.showTextDocument(resultsDoc);
                }
            } catch (error) {
                vscode.window.showErrorMessage(`Simulation failed: ${error.message}`);
            }
        } else {
            vscode.window.showWarningMessage('Please open an SVGX file to simulate.');
        }
    });

    let compileCommand = vscode.commands.registerCommand('svgx.compile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'svgx') {
            try {
                const elements = await languageClient.parseFile(editor.document.getText());
                
                if (elements.length === 0) {
                    vscode.window.showWarningMessage('No elements found to compile.');
                    return;
                }

                const svgContent = await languageClient.compileToSVG(elements);
                
                // Create new SVG file
                const svgUri = editor.document.uri.with({ path: editor.document.uri.path.replace('.svgx', '.svg') });
                const svgDoc = await vscode.workspace.openTextDocument({
                    uri: svgUri,
                    content: svgContent
                });
                await vscode.window.showTextDocument(svgDoc);
                
                vscode.window.showInformationMessage('SVGX compiled to SVG successfully!');
            } catch (error) {
                vscode.window.showErrorMessage(`Compilation failed: ${error.message}`);
            }
        } else {
            vscode.window.showWarningMessage('Please open an SVGX file to compile.');
        }
    });

    let compileJsonCommand = vscode.commands.registerCommand('svgx.compile.json', async () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'svgx') {
            try {
                const elements = await languageClient.parseFile(editor.document.getText());
                
                if (elements.length === 0) {
                    vscode.window.showWarningMessage('No elements found to compile.');
                    return;
                }

                const jsonContent = await languageClient.compileToJSON(elements);
                
                // Create new JSON file
                const jsonUri = editor.document.uri.with({ path: editor.document.uri.path.replace('.svgx', '.json') });
                const jsonDoc = await vscode.workspace.openTextDocument({
                    uri: jsonUri,
                    content: JSON.stringify(jsonContent, null, 2)
                });
                await vscode.window.showTextDocument(jsonDoc);
                
                vscode.window.showInformationMessage('SVGX compiled to JSON successfully!');
            } catch (error) {
                vscode.window.showErrorMessage(`Compilation failed: ${error.message}`);
            }
        } else {
            vscode.window.showWarningMessage('Please open an SVGX file to compile.');
        }
    });

    let debugCommand = vscode.commands.registerCommand('svgx.debug', async () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'svgx') {
            try {
                // Start debugging session
                vscode.window.showInformationMessage('Starting SVGX debugging session...');
                
                // Connect to WebSocket for real-time debugging
                await languageClient.connectWebSocket();
                
                // Create debug console
                const debugConsole = vscode.window.createOutputChannel('SVGX Debug');
                debugConsole.show();
                debugConsole.appendLine('SVGX Debug Console');
                debugConsole.appendLine('Connected to SVGX Engine server');
                
            } catch (error) {
                vscode.window.showErrorMessage(`Debug session failed: ${error.message}`);
            }
        } else {
            vscode.window.showWarningMessage('Please open an SVGX file to debug.');
        }
    });

    // Register completion provider
    let completionProvider = vscode.languages.registerCompletionItemProvider(
        { language: 'svgx' },
        new SVGXCompletionProvider()
    );

    // Register custom editor provider
    let previewProvider = SVGXPreviewProvider.register(context);

    // Register diagnostics provider
    let diagnosticsUpdate = vscode.workspace.onDidChangeTextDocument(async (event) => {
        if (event.document.languageId === 'svgx') {
            await diagnosticsProvider.updateDiagnostics(event.document);
        }
    });

    // Register document open handler
    let documentOpen = vscode.workspace.onDidOpenTextDocument(async (document) => {
        if (document.languageId === 'svgx') {
            await diagnosticsProvider.updateDiagnostics(document);
        }
    });

    // Register document close handler
    let documentClose = vscode.workspace.onDidCloseTextDocument((document) => {
        if (document.languageId === 'svgx') {
            diagnosticsProvider.clearDiagnostics();
        }
    });

    // Add to subscriptions
    context.subscriptions.push(
        previewCommand,
        validateCommand,
        simulateCommand,
        compileCommand,
        compileJsonCommand,
        debugCommand,
        completionProvider,
        previewProvider,
        diagnosticsUpdate,
        documentOpen,
        documentClose
    );
}

export function deactivate() {
    console.log('SVGX Engine extension is now deactivated!');
} 