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

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const WebSocket = require('ws');

/**
 * SVGX Element interface
 */
class SVGXElement {
    constructor(id, type, properties = {}, position = null, children = []) {
        this.id = id;
        this.type = type;
        this.properties = properties;
        this.position = position;
        this.children = children;
    }
}

/**
 * SVGX Simulation interface
 */
class SVGXSimulation {
    constructor(id, type, parameters = {}) {
        this.id = id;
        this.type = type;
        this.parameters = parameters;
        this.status = 'idle';
        this.results = null;
    }
}

/**
 * SVGX Validation Result interface
 */
class SVGXValidationResult {
    constructor(valid = true, errors = [], warnings = []) {
        this.valid = valid;
        this.errors = errors;
        this.warnings = warnings;
    }
}

/**
 * SVGX Language Client for server communication
 */
class SVGXLanguageClient {
    constructor() {
        const config = vscode.workspace.getConfiguration('svgx');
        this.serverUrl = config.get('server.url', 'http://localhost:8000');
        this.apiKey = config.get('server.apiKey', '');
        this.wsConnection = null;
    }

    async validateFile(content) {
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
            return new SVGXValidationResult(false, [{
                line: 1,
                column: 1,
                message: 'Failed to connect to SVGX Engine server',
                severity: 'error'
            }], []);
        }
    }

    async parseFile(content) {
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

    async runSimulation(simulationType, elements) {
        try {
            const response = await axios.post(`${this.serverUrl}/simulate`, {
                type: simulationType,
                elements: elements
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data;
        } catch (error) {
            console.error('Simulation request failed:', error);
            throw new Error(`Simulation failed: ${error.message}`);
        }
    }

    async compileToSVG(elements) {
        try {
            const response = await axios.post(`${this.serverUrl}/compile/svg`, {
                elements: elements
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data.svg;
        } catch (error) {
            console.error('SVG compilation failed:', error);
            throw new Error(`SVG compilation failed: ${error.message}`);
        }
    }

    async compileToJSON(elements) {
        try {
            const response = await axios.post(`${this.serverUrl}/compile/json`, {
                elements: elements
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            });

            return response.data;
        } catch (error) {
            console.error('JSON compilation failed:', error);
            throw new Error(`JSON compilation failed: ${error.message}`);
        }
    }

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                const wsUrl = this.serverUrl.replace('http', 'ws') + '/ws';
                this.wsConnection = new WebSocket(wsUrl);

                this.wsConnection.on('open', () => {
                    console.log('WebSocket connected to SVGX Engine');
                    resolve();
                });

                this.wsConnection.on('message', (data) => {
                    this.handleWebSocketMessage(JSON.parse(data.toString()));
                });

                this.wsConnection.on('error', (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                });

                this.wsConnection.on('close', () => {
                    console.log('WebSocket disconnected from SVGX Engine');
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    handleWebSocketMessage(message) {
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
            default:
                console.log('Unknown WebSocket message type:', message.type);
        }
    }

    handleSimulationUpdate(message) {
        vscode.window.showInformationMessage(`Simulation ${message.simulationId}: ${message.status}`);
    }

    handleValidationResult(message) {
        // Update diagnostics
        if (this.diagnosticsProvider) {
            this.diagnosticsProvider.updateDiagnosticsFromServer(message);
        }
    }

    handlePreviewUpdate(message) {
        // Update preview panel
        if (this.previewProvider) {
            this.previewProvider.updatePreview(message);
        }
    }

    disconnect() {
        if (this.wsConnection) {
            this.wsConnection.close();
            this.wsConnection = null;
        }
    }
}

/**
 * SVGX Preview Provider for live preview
 */
class SVGXPreviewProvider {
    static register(context) {
        const provider = new SVGXPreviewProvider(context);
        const providerRegistration = vscode.window.registerCustomEditorProvider('svgx.preview', provider);
        context.subscriptions.push(providerRegistration);
        return provider;
    }

    constructor(context) {
        this.context = context;
    }

    async resolveCustomTextEditor(document, webviewPanel, token) {
        webviewPanel.webview.options = {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.file(path.join(this.context.extensionPath, 'media'))]
        };

        const updateWebview = () => {
            webviewPanel.webview.html = this.getHtmlForWebview(webviewPanel.webview, document);
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

    getHtmlForWebview(webview, document) {
        const content = document.getText();
        
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
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: #1e1e1e;
                        color: #ffffff;
                    }
                    .preview-container {
                        background: #2d2d30;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 20px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                    }
                    .preview-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                        padding-bottom: 10px;
                        border-bottom: 1px solid #3e3e42;
                    }
                    .preview-title {
                        font-size: 18px;
                        font-weight: 600;
                        color: #007acc;
                    }
                    .preview-status {
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: 500;
                        background: #007acc;
                        color: white;
                    }
                    .svgx-content {
                        background: #1e1e1e;
                        border: 1px solid #3e3e42;
                        border-radius: 4px;
                        padding: 15px;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 14px;
                        line-height: 1.5;
                        color: #d4d4d4;
                        white-space: pre-wrap;
                        overflow-x: auto;
                        max-height: 400px;
                        overflow-y: auto;
                    }
                    .svgx-element {
                        color: #569cd6;
                    }
                    .svgx-attribute {
                        color: #9cdcfe;
                    }
                    .svgx-value {
                        color: #ce9178;
                    }
                    .svgx-comment {
                        color: #6a9955;
                    }
                    .controls {
                        display: flex;
                        gap: 10px;
                        margin-top: 15px;
                    }
                    .control-btn {
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        background: #007acc;
                        color: white;
                        cursor: pointer;
                        font-size: 14px;
                        transition: background 0.2s;
                    }
                    .control-btn:hover {
                        background: #005a9e;
                    }
                    .control-btn.secondary {
                        background: #3e3e42;
                    }
                    .control-btn.secondary:hover {
                        background: #5a5a5a;
                    }
                    .error {
                        color: #f48771;
                        background: #2d2d30;
                        padding: 10px;
                        border-radius: 4px;
                        margin-top: 10px;
                        border-left: 4px solid #f48771;
                    }
                    .warning {
                        color: #ffcc02;
                        background: #2d2d30;
                        padding: 10px;
                        border-radius: 4px;
                        margin-top: 10px;
                        border-left: 4px solid #ffcc02;
                    }
                </style>
            </head>
            <body>
                <div class="preview-container">
                    <div class="preview-header">
                        <div class="preview-title">SVGX Preview</div>
                        <div class="preview-status">Live</div>
                    </div>
                    
                    <div class="svgx-content" id="svgx-content">
                        ${this.highlightSVGX(content)}
                    </div>
                    
                    <div class="controls">
                        <button class="control-btn" onclick="validateContent()">Validate</button>
                        <button class="control-btn" onclick="compileSVG()">Compile SVG</button>
                        <button class="control-btn secondary" onclick="runSimulation()">Run Simulation</button>
                        <button class="control-btn secondary" onclick="debugContent()">Debug</button>
                    </div>
                    
                    <div id="messages"></div>
                </div>
                
                <script>
                    const vscode = acquireVsCodeApi();
                    
                    function validateContent() {
                        vscode.postMessage({
                            command: 'validate',
                            content: document.getElementById('svgx-content').textContent
                        });
                    }
                    
                    function compileSVG() {
                        vscode.postMessage({
                            command: 'compile',
                            type: 'svg',
                            content: document.getElementById('svgx-content').textContent
                        });
                    }
                    
                    function runSimulation() {
                        vscode.postMessage({
                            command: 'simulate',
                            content: document.getElementById('svgx-content').textContent
                        });
                    }
                    
                    function debugContent() {
                        vscode.postMessage({
                            command: 'debug',
                            content: document.getElementById('svgx-content').textContent
                        });
                    }
                    
                    function showMessage(message, type) {
                        const messagesDiv = document.getElementById('messages');
                        const messageDiv = document.createElement('div');
                        messageDiv.className = type;
                        messageDiv.textContent = message;
                        messagesDiv.appendChild(messageDiv);
                        
                        setTimeout(() => {
                            messageDiv.remove();
                        }, 5000);
                    }
                    
                    window.addEventListener('message', event => {
                        const message = event.data;
                        switch (message.command) {
                            case 'validationResult':
                                showMessage(message.message, message.valid ? 'success' : 'error');
                                break;
                            case 'compilationResult':
                                showMessage(message.message, 'success');
                                break;
                            case 'simulationResult':
                                showMessage(message.message, 'success');
                                break;
                        }
                    });
                </script>
            </body>
            </html>
        `;
    }

    highlightSVGX(content) {
        // Simple syntax highlighting for SVGX
        return content
            .replace(/<(\w+)/g, '<span class="svgx-element">$1</span>')
            .replace(/(\w+)="([^"]*)"/g, '<span class="svgx-attribute">$1</span>="<span class="svgx-value">$2</span>"')
            .replace(/<!--([^>]*)-->/g, '<span class="svgx-comment"><!--$1--></span>');
    }
}

/**
 * SVGX Diagnostics Provider for error reporting
 */
class SVGXDiagnosticsProvider {
    constructor() {
        this.diagnosticsCollection = vscode.languages.createDiagnosticCollection('svgx');
    }

    async updateDiagnostics(document) {
        if (document.languageId !== 'svgx') {
            return;
        }

        const content = document.getText();
        const diagnostics = [];

        // Basic validation
        const lines = content.split('\n');
        lines.forEach((line, index) => {
            const lineNumber = index + 1;
            
            // Check for unclosed tags
            const openTags = (line.match(/<(\w+)/g) || []).length;
            const closeTags = (line.match(/<\/(\w+)>/g) || []).length;
            
            if (openTags > closeTags) {
                diagnostics.push(new vscode.Diagnostic(
                    new vscode.Range(lineNumber - 1, 0, lineNumber - 1, line.length),
                    'Unclosed tag detected',
                    vscode.DiagnosticSeverity.Warning
                ));
            }
            
            // Check for invalid attributes
            const invalidAttributes = line.match(/(\w+)="[^"]*"/g);
            if (invalidAttributes) {
                invalidAttributes.forEach(attr => {
                    const attrName = attr.split('=')[0];
                    if (!this.isValidAttribute(attrName)) {
                        diagnostics.push(new vscode.Diagnostic(
                            new vscode.Range(lineNumber - 1, line.indexOf(attr), lineNumber - 1, line.indexOf(attr) + attrName.length),
                            `Invalid attribute: ${attrName}`,
                            vscode.DiagnosticSeverity.Error
                        ));
                    }
                });
            }
        });

        this.diagnosticsCollection.set(document.uri, diagnostics);
    }

    isValidAttribute(attrName) {
        const validAttributes = [
            'id', 'type', 'x', 'y', 'z', 'width', 'height', 'depth',
            'color', 'fill', 'stroke', 'stroke-width', 'opacity',
            'transform', 'rotation', 'scale', 'position',
            'constraint', 'parameter', 'simulation', 'physics'
        ];
        return validAttributes.includes(attrName);
    }

    clearDiagnostics() {
        this.diagnosticsCollection.clear();
    }
}

/**
 * SVGX Completion Provider for IntelliSense
 */
class SVGXCompletionProvider {
    provideCompletionItems(document, position, token, context) {
        const completions = [];
        const linePrefix = document.lineAt(position).text.substr(0, position.character);
        
        // Element completions
        const elements = [
            'building', 'floor', 'room', 'wall', 'door', 'window',
            'equipment', 'piping', 'electrical', 'hvac', 'lighting',
            'furniture', 'fixture', 'sensor', 'controller', 'network'
        ];
        
        elements.forEach(element => {
            completions.push(new vscode.CompletionItem(element, vscode.CompletionItemKind.Class));
        });
        
        // Attribute completions
        const attributes = [
            'id', 'type', 'x', 'y', 'z', 'width', 'height', 'depth',
            'color', 'fill', 'stroke', 'stroke-width', 'opacity',
            'transform', 'rotation', 'scale', 'position',
            'constraint', 'parameter', 'simulation', 'physics'
        ];
        
        attributes.forEach(attr => {
            completions.push(new vscode.CompletionItem(attr, vscode.CompletionItemKind.Property));
        });
        
        // Simulation types
        const simulationTypes = [
            'structural', 'fluid_dynamics', 'heat_transfer', 'electrical', 'rf_propagation'
        ];
        
        simulationTypes.forEach(type => {
            completions.push(new vscode.CompletionItem(type, vscode.CompletionItemKind.Value));
        });
        
        return completions;
    }
}

/**
 * Main extension activation function
 */
function activate(context) {
    console.log('SVGX Engine extension is now active!');

    // Initialize services
    const languageClient = new SVGXLanguageClient();
    const diagnosticsProvider = new SVGXDiagnosticsProvider();
    const previewProvider = SVGXPreviewProvider.register(context);
    const completionProvider = vscode.languages.registerCompletionItemProvider(
        { language: 'svgx' },
        new SVGXCompletionProvider()
    );

    // Register commands
    const validateCommand = vscode.commands.registerCommand('svgx.validate', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'svgx') {
            vscode.window.showWarningMessage('Please open an SVGX file to validate.');
            return;
        }

        try {
            vscode.window.showInformationMessage('Validating SVGX file...');
            const content = editor.document.getText();
            const result = await languageClient.validateFile(content);
            
            if (result.valid) {
                vscode.window.showInformationMessage('SVGX file is valid!');
            } else {
                vscode.window.showErrorMessage(`Validation failed: ${result.errors.length} errors found.`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Validation error: ${error.message}`);
        }
    });

    const previewCommand = vscode.commands.registerCommand('svgx.preview', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'svgx') {
            vscode.window.showWarningMessage('Please open an SVGX file to preview.');
            return;
        }

        const document = editor.document;
        const panel = vscode.window.createWebviewPanel(
            'svgxPreview',
            'SVGX Preview',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'media'))]
            }
        );

        panel.webview.html = previewProvider.getHtmlForWebview(panel.webview, document);
    });

    const simulateCommand = vscode.commands.registerCommand('svgx.simulate', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'svgx') {
            vscode.window.showWarningMessage('Please open an SVGX file to simulate.');
            return;
        }

        try {
            const simulationType = await vscode.window.showQuickPick([
                'structural', 'fluid_dynamics', 'heat_transfer', 'electrical', 'rf_propagation'
            ], {
                placeHolder: 'Select simulation type'
            });

            if (!simulationType) {
                return;
            }

            vscode.window.showInformationMessage(`Running ${simulationType} simulation...`);
            const content = editor.document.getText();
            const elements = await languageClient.parseFile(content);
            const result = await languageClient.runSimulation(simulationType, elements);
            
            vscode.window.showInformationMessage(`Simulation completed: ${result.status}`);
        } catch (error) {
            vscode.window.showErrorMessage(`Simulation error: ${error.message}`);
        }
    });

    const debugCommand = vscode.commands.registerCommand('svgx.debug', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'svgx') {
            vscode.window.showWarningMessage('Please open an SVGX file to debug.');
            return;
        }

        vscode.window.showInformationMessage('Starting SVGX debug session...');
        
        // Create debug configuration
        const debugConfig = {
            name: 'SVGX Debug',
            type: 'node',
            request: 'launch',
            program: '${workspaceFolder}/svgx_engine/debug/svgx_debugger.js',
            args: [editor.document.uri.fsPath],
            console: 'integratedTerminal'
        };

        await vscode.debug.startDebugging(vscode.workspace.workspaceFolders[0], debugConfig);
    });

    const compileCommand = vscode.commands.registerCommand('svgx.compile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'svgx') {
            vscode.window.showWarningMessage('Please open an SVGX file to compile.');
            return;
        }

        try {
            vscode.window.showInformationMessage('Compiling to SVG...');
            const content = editor.document.getText();
            const elements = await languageClient.parseFile(content);
            const svg = await languageClient.compileToSVG(elements);
            
            // Create new document with SVG content
            const svgDocument = await vscode.workspace.openTextDocument({
                content: svg,
                language: 'xml'
            });
            
            await vscode.window.showTextDocument(svgDocument, vscode.ViewColumn.Beside);
            vscode.window.showInformationMessage('SVG compilation completed!');
        } catch (error) {
            vscode.window.showErrorMessage(`Compilation error: ${error.message}`);
        }
    });

    const compileJsonCommand = vscode.commands.registerCommand('svgx.compile.json', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'svgx') {
            vscode.window.showWarningMessage('Please open an SVGX file to compile.');
            return;
        }

        try {
            vscode.window.showInformationMessage('Compiling to JSON...');
            const content = editor.document.getText();
            const elements = await languageClient.parseFile(content);
            const json = await languageClient.compileToJSON(elements);
            
            // Create new document with JSON content
            const jsonDocument = await vscode.workspace.openTextDocument({
                content: JSON.stringify(json, null, 2),
                language: 'json'
            });
            
            await vscode.window.showTextDocument(jsonDocument, vscode.ViewColumn.Beside);
            vscode.window.showInformationMessage('JSON compilation completed!');
        } catch (error) {
            vscode.window.showErrorMessage(`Compilation error: ${error.message}`);
        }
    });

    // Register document change listener for diagnostics
    const changeDocumentListener = vscode.workspace.onDidChangeTextDocument(event => {
        diagnosticsProvider.updateDiagnostics(event.document);
    });

    // Register document open listener
    const openDocumentListener = vscode.workspace.onDidOpenTextDocument(document => {
        diagnosticsProvider.updateDiagnostics(document);
    });

    // Connect to WebSocket
    languageClient.connectWebSocket().catch(error => {
        console.error('Failed to connect to WebSocket:', error);
    });

    // Add subscriptions to context
    context.subscriptions.push(
        validateCommand,
        previewCommand,
        simulateCommand,
        debugCommand,
        compileCommand,
        compileJsonCommand,
        completionProvider,
        changeDocumentListener,
        openDocumentListener
    );

    // Store references for cleanup
    context.globalState.update('svgx.languageClient', languageClient);
    context.globalState.update('svgx.diagnosticsProvider', diagnosticsProvider);
}

/**
 * Extension deactivation function
 */
function deactivate() {
    console.log('SVGX Engine extension is now deactivated!');
}

module.exports = {
    activate,
    deactivate
}; 