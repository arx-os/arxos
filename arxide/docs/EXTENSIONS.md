# ArxIDE Extension Development Guide

## 🏗️ Overview

ArxIDE's extension system allows developers to create custom CAD functionality, system-specific tools, and specialized building analysis capabilities. This guide provides everything needed to develop, test, and deploy extensions for ArxIDE.

## 🎯 Extension Architecture

### Core Concepts

```typescript
// Extension Lifecycle
interface ExtensionLifecycle {
  activate: (context: ExtensionContext) => Promise<void>
  deactivate: () => Promise<void>
  dispose: () => Promise<void>
}

// Extension Context
interface ExtensionContext {
  subscriptions: Disposable[]
  workspaceState: Memento
  globalState: Memento
  extensionPath: string
  extensionUri: URI
  environmentVariableCollection: EnvironmentVariableCollection
  storagePath: string
  globalStoragePath: string
  logPath: string
  extensionMode: ExtensionMode
}
```

### Extension Structure

```
extension/
├── package.json          # Extension manifest
├── src/
│   ├── extension.ts      # Main extension entry point
│   ├── commands/         # Command implementations
│   ├── providers/        # Language providers, etc.
│   ├── views/           # UI components
│   └── utils/           # Utility functions
├── resources/           # Static resources
├── README.md           # Extension documentation
└── CHANGELOG.md        # Version history
```

## 📦 Extension Manifest

### package.json Structure

```json
{
  "name": "arxide-electrical-extension",
  "displayName": "Electrical CAD Tools",
  "description": "Advanced electrical design and analysis tools for ArxIDE",
  "version": "1.0.0",
  "publisher": "arxos",
  "engines": {
    "arxide": "^1.0.0"
  },
  "categories": ["CAD", "Electrical", "Analysis"],
  "keywords": ["electrical", "circuit", "panel", "wiring"],
  "main": "./dist/extension.js",
  "activationEvents": [
    "onCommand:electrical.createPanel",
    "onCommand:electrical.analyzeCircuit",
    "onLanguage:svgx"
  ],
  "contributes": {
    "commands": [
      {
        "command": "electrical.createPanel",
        "title": "Create Electrical Panel",
        "category": "Electrical"
      },
      {
        "command": "electrical.analyzeCircuit",
        "title": "Analyze Circuit",
        "category": "Electrical"
      }
    ],
    "menus": {
      "commandPalette": [
        {
          "command": "electrical.createPanel",
          "when": "resourceExtname == .svgx"
        }
      ],
      "editor/context": [
        {
          "command": "electrical.analyzeCircuit",
          "when": "resourceExtname == .svgx"
        }
      ]
    },
    "views": {
      "explorer": [
        {
          "id": "electricalExplorer",
          "name": "Electrical Components"
        }
      ]
    },
    "viewsContainers": {
      "activitybar": [
        {
          "id": "electrical",
          "title": "Electrical",
          "icon": "resources/electrical-icon.svg"
        }
      ]
    },
    "configuration": {
      "title": "Electrical Extension",
      "properties": {
        "electrical.defaultVoltage": {
          "type": "number",
          "default": 120,
          "description": "Default voltage for new electrical components"
        },
        "electrical.safetyFactor": {
          "type": "number",
          "default": 1.25,
          "description": "Safety factor for electrical calculations"
        }
      }
    }
  },
  "scripts": {
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./",
    "test": "jest",
    "package": "arxide-extension-manager package"
  },
  "devDependencies": {
    "@types/node": "^16.0.0",
    "@types/arxide": "^1.0.0",
    "typescript": "^4.5.0"
  }
}
```

## 🔧 Extension API

### Command Registration

```typescript
// Command Implementation
export function activate(context: ExtensionContext) {
  // Register commands
  const createPanelCommand = arxide.commands.registerCommand(
    'electrical.createPanel',
    createElectricalPanel
  )

  const analyzeCircuitCommand = arxide.commands.registerCommand(
    'electrical.analyzeCircuit',
    analyzeCircuit
  )

  context.subscriptions.push(createPanelCommand, analyzeCircuitCommand)
}

// Command Functions
async function createElectricalPanel() {
  const panel = await arxide.window.showInputBox({
    prompt: 'Enter panel name',
    placeHolder: 'Main Panel'
  })

  if (panel) {
    const svgxCode = generatePanelSVGX(panel)
    const document = await arxide.workspace.openTextDocument({
      content: svgxCode,
      language: 'svgx'
    })

    await arxide.window.showTextDocument(document)
  }
}

async function analyzeCircuit() {
  const editor = arxide.window.activeTextEditor
  if (!editor) {
    arxide.window.showErrorMessage('No active editor')
    return
  }

  const svgxCode = editor.document.getText()
  const analysis = await analyzeElectricalCircuit(svgxCode)

  // Show results in a new panel
  const panel = arxide.window.createWebviewPanel(
    'circuitAnalysis',
    'Circuit Analysis',
    arxide.ViewColumn.Beside,
    {}
  )

  panel.webview.html = generateAnalysisHTML(analysis)
}
```

### Language Provider

```typescript
// SVGX Language Provider
class SVGXLanguageProvider implements arxide.DocumentSymbolProvider {
  provideDocumentSymbols(
    document: arxide.TextDocument,
    token: arxide.CancellationToken
  ): arxide.ProviderResult<arxide.SymbolInformation[] | arxide.DocumentSymbol[]> {
    const symbols: arxide.DocumentSymbol[] = []
    const text = document.getText()

    // Parse SVGX code and extract symbols
    const lines = text.split('\n')

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]

      // Match electrical components
      const panelMatch = line.match(/panel\s+(\w+)/)
      if (panelMatch) {
        const symbol = new arxide.DocumentSymbol(
          panelMatch[1],
          'Electrical Panel',
          arxide.SymbolKind.Class,
          new arxide.Range(i, 0, i, line.length),
          new arxide.Range(i, 0, i, line.length)
        )
        symbols.push(symbol)
      }

      // Match circuit definitions
      const circuitMatch = line.match(/circuit\s+(\w+)/)
      if (circuitMatch) {
        const symbol = new arxide.DocumentSymbol(
          circuitMatch[1],
          'Electrical Circuit',
          arxide.SymbolKind.Function,
          new arxide.Range(i, 0, i, line.length),
          new arxide.Range(i, 0, i, line.length)
        )
        symbols.push(symbol)
      }
    }

    return symbols
  }
}
```

### Webview Provider

```typescript
// Circuit Analysis Webview
class CircuitAnalysisProvider implements arxide.WebviewViewProvider {
  public static readonly viewType = 'circuitAnalysis'

  constructor(private readonly _extensionUri: arxide.Uri) {}

  public resolveWebviewView(
    webviewView: arxide.WebviewView,
    context: arxide.WebviewViewResolveContext,
    _token: arxide.CancellationToken
  ) {
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri]
    }

    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview)

    // Handle messages from webview
    webviewView.webview.onDidReceiveMessage(
      message => {
        switch (message.command) {
          case 'analyzeCircuit':
            this.analyzeCircuit(message.circuitData)
            return
        }
      }
    )
  }

  private _getHtmlForWebview(webview: arxide.Webview) {
    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Circuit Analysis</title>
      </head>
      <body>
        <div id="circuit-analysis">
          <h2>Electrical Circuit Analysis</h2>
          <div id="circuit-diagram"></div>
          <div id="analysis-results"></div>
        </div>
        <script>
          // Webview JavaScript
          const arxide = acquireArxIDEApi()

          function analyzeCircuit(circuitData) {
            arxide.postMessage({
              command: 'analyzeCircuit',
              circuitData: circuitData
            })
          }
        </script>
      </body>
      </html>
    `
  }
}
```

## 🎨 UI Components

### Custom Views

```typescript
// Electrical Components Tree View
class ElectricalComponentsProvider implements arxide.TreeDataProvider<ElectricalComponent> {
  private _onDidChangeTreeData: arxide.EventEmitter<ElectricalComponent | undefined | null | undefined> = new arxide.EventEmitter<ElectricalComponent | undefined | null | undefined>()
  readonly onDidChangeTreeData: arxide.Event<ElectricalComponent | undefined | null | undefined> = this._onDidChangeTreeData.event

  constructor(private workspaceRoot: string | undefined) {}

  refresh(): void {
    this._onDidChangeTreeData.fire()
  }

  getTreeItem(element: ElectricalComponent): arxide.TreeItem {
    return element
  }

  getChildren(element?: ElectricalComponent): Thenable<ElectricalComponent[]> {
    if (!this.workspaceRoot) {
      return Promise.resolve([])
    }

    if (element) {
      return Promise.resolve(element.children || [])
    } else {
      return this.getElectricalComponents()
    }
  }

  private async getElectricalComponents(): Promise<ElectricalComponent[]> {
    const components: ElectricalComponent[] = []

    // Scan workspace for SVGX files
    const files = await arxide.workspace.findFiles('**/*.svgx')

    for (const file of files) {
      const document = await arxide.workspace.openTextDocument(file)
      const componentsInFile = this.parseElectricalComponents(document.getText())
      components.push(...componentsInFile)
    }

    return components
  }

  private parseElectricalComponents(svgxCode: string): ElectricalComponent[] {
    const components: ElectricalComponent[] = []
    const lines = svgxCode.split('\n')

    for (const line of lines) {
      // Parse electrical components from SVGX code
      const panelMatch = line.match(/panel\s+(\w+)/)
      if (panelMatch) {
        components.push(new ElectricalComponent(
          panelMatch[1],
          'panel',
          arxide.TreeItemCollapsibleState.Collapsed
        ))
      }

      const circuitMatch = line.match(/circuit\s+(\w+)/)
      if (circuitMatch) {
        components.push(new ElectricalComponent(
          circuitMatch[1],
          'circuit',
          arxide.TreeItemCollapsibleState.None
        ))
      }
    }

    return components
  }
}

class ElectricalComponent extends arxide.TreeItem {
  constructor(
    public readonly label: string,
    public readonly type: string,
    public readonly collapsibleState: arxide.TreeItemCollapsibleState,
    public readonly children?: ElectricalComponent[]
  ) {
    super(label, collapsibleState)

    this.tooltip = `${this.type}: ${this.label}`
    this.description = this.type

    // Set icon based on type
    this.iconPath = {
      light: arxide.Uri.file(path.join(__filename, '..', '..', 'resources', 'light', `${this.type}.svg`)),
      dark: arxide.Uri.file(path.join(__filename, '..', '..', 'resources', 'dark', `${this.type}.svg`))
    }
  }
}
```

### Status Bar Items

```typescript
// Electrical Status Bar
class ElectricalStatusBar {
  private statusBarItem: arxide.StatusBarItem

  constructor() {
    this.statusBarItem = arxide.window.createStatusBarItem(
      arxide.StatusBarAlignment.Right,
      100
    )
    this.statusBarItem.command = 'electrical.showStatus'
    this.updateStatus()
  }

  updateStatus() {
    const editor = arxide.window.activeTextEditor
    if (editor && editor.document.languageId === 'svgx') {
      const text = editor.document.getText()
      const componentCount = this.countElectricalComponents(text)

      this.statusBarItem.text = `$(circuit-board) ${componentCount} Electrical Components`
      this.statusBarItem.show()
    } else {
      this.statusBarItem.hide()
    }
  }

  private countElectricalComponents(svgxCode: string): number {
    const panelMatches = svgxCode.match(/panel\s+\w+/g) || []
    const circuitMatches = svgxCode.match(/circuit\s+\w+/g) || []
    return panelMatches.length + circuitMatches.length
  }

  dispose() {
    this.statusBarItem.dispose()
  }
}
```

## 🔍 Testing Extensions

### Unit Testing

```typescript
// extension.test.ts
import * as assert from 'assert'
import * as arxide from 'arxide'
import * as path from 'path'

suite('Electrical Extension Test Suite', () => {
  arxide.window.showInformationMessage('Start all tests.')

  test('Should create electrical panel', async () => {
    // Test panel creation
    const panelName = 'TestPanel'
    const svgxCode = generatePanelSVGX(panelName)

    assert.strictEqual(svgxCode.includes(`panel ${panelName}`), true)
    assert.strictEqual(svgxCode.includes('voltage: 120'), true)
  })

  test('Should analyze circuit', async () => {
    // Test circuit analysis
    const svgxCode = `
      panel MainPanel {
        voltage: 120
        circuits: [
          circuit Lighting {
            load: 15
            type: "lighting"
          }
        ]
      }
    `

    const analysis = await analyzeElectricalCircuit(svgxCode)

    assert.strictEqual(analysis.totalLoad, 15)
    assert.strictEqual(analysis.panels.length, 1)
    assert.strictEqual(analysis.circuits.length, 1)
  })

  test('Should validate electrical code', async () => {
    // Test validation
    const svgxCode = `
      panel MainPanel {
        voltage: 120
        circuits: [
          circuit Lighting {
            load: 15
            type: "lighting"
          }
        ]
      }
    `

    const validation = await validateElectricalCode(svgxCode)

    assert.strictEqual(validation.isValid, true)
    assert.strictEqual(validation.errors.length, 0)
  })
})
```

### Integration Testing

```typescript
// integration.test.ts
import * as assert from 'assert'
import * as arxide from 'arxide'

suite('Electrical Extension Integration Tests', () => {
  test('Should register commands', async () => {
    // Test command registration
    const commands = await arxide.commands.getCommands()

    assert.strictEqual(commands.includes('electrical.createPanel'), true)
    assert.strictEqual(commands.includes('electrical.analyzeCircuit'), true)
  })

  test('Should show electrical components in explorer', async () => {
    // Test tree view
    const treeDataProvider = new ElectricalComponentsProvider(arxide.workspace.rootPath)
    const components = await treeDataProvider.getChildren()

    assert.strictEqual(components.length > 0, true)
  })

  test('Should update status bar', async () => {
    // Test status bar
    const statusBar = new ElectricalStatusBar()

    // Create test document
    const document = await arxide.workspace.openTextDocument({
      content: `
        panel MainPanel {
          voltage: 120
          circuits: [
            circuit Lighting {
              load: 15
              type: "lighting"
            }
          ]
        }
      `,
      language: 'svgx'
    })

    await arxide.window.showTextDocument(document)
    statusBar.updateStatus()

    // Verify status bar shows component count
    assert.strictEqual(statusBar.statusBarItem.text.includes('2'), true)
  })
})
```

## 📦 Packaging & Distribution

### Extension Packaging

```json
// package.json scripts
{
  "scripts": {
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./",
    "test": "jest",
    "package": "arxide-extension-manager package",
    "publish": "arxide-extension-manager publish"
  }
}
```

### Extension Marketplace

```json
// package.json marketplace configuration
{
  "publisher": "arxos",
  "repository": {
    "type": "git",
    "url": "https://github.com/arxos/arxide-electrical-extension.git"
  },
  "bugs": {
    "url": "https://github.com/arxos/arxide-electrical-extension/issues"
  },
  "homepage": "https://github.com/arxos/arxide-electrical-extension#readme",
  "license": "MIT",
  "galleryBanner": {
    "color": "#C80000",
    "theme": "dark"
  },
  "badges": [
    {
      "url": "https://img.shields.io/badge/ArxIDE-Electrical-red.svg",
      "description": "Electrical CAD Tools"
    }
  ]
}
```

## 🔧 Development Tools

### Extension Development Host

```typescript
// Extension development utilities
class ExtensionDevTools {
  static async createTestWorkspace(): Promise<arxide.WorkspaceFolder> {
    const testWorkspacePath = path.join(__dirname, 'test-workspace')

    // Create test workspace with sample SVGX files
    await fs.mkdir(testWorkspacePath, { recursive: true })

    const sampleFile = path.join(testWorkspacePath, 'sample.svgx')
    await fs.writeFile(sampleFile, `
      panel MainPanel {
        voltage: 120
        circuits: [
          circuit Lighting {
            load: 15
            type: "lighting"
          },
          circuit Outlets {
            load: 20
            type: "power"
          }
        ]
      }
    `)

    return arxide.workspace.addWorkspaceFolder(testWorkspacePath)
  }

  static async cleanupTestWorkspace(): Promise<void> {
    const testWorkspacePath = path.join(__dirname, 'test-workspace')
    await fs.rm(testWorkspacePath, { recursive: true, force: true })
  }
}
```

### Debug Configuration

```json
// .arxide/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}"
      ],
      "outFiles": [
        "${workspaceFolder}/dist/**/*.js"
      ],
      "preLaunchTask": "npm: compile"
    },
    {
      "name": "Extension Tests",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}",
        "--extensionTestsPath=${workspaceFolder}/out/test/suite/index"
      ],
      "outFiles": [
        "${workspaceFolder}/out/test/**/*.js"
      ],
      "preLaunchTask": "npm: compile"
    }
  ]
}
```

## 📚 Best Practices

### Code Organization

1. **Modular Design**: Separate concerns into different modules
2. **Type Safety**: Use TypeScript for better type checking
3. **Error Handling**: Implement comprehensive error handling
4. **Documentation**: Document all public APIs and functions
5. **Testing**: Write unit and integration tests

### Performance

1. **Lazy Loading**: Load resources only when needed
2. **Caching**: Cache frequently accessed data
3. **Async Operations**: Use async/await for non-blocking operations
4. **Optimization**: Continuous performance optimization

### Security

1. **Input Validation**: Validate all user inputs
2. **Sandboxing**: Run extensions in isolated environments
3. **Permission Model**: Implement least-privilege access
4. **Audit Logging**: Log security-relevant events

### User Experience

1. **Intuitive Commands**: Use clear, descriptive command names
2. **Progressive Disclosure**: Show advanced features only when needed
3. **Feedback**: Provide clear feedback for user actions
4. **Accessibility**: Ensure extensions are accessible to all users

This extension development guide provides a comprehensive foundation for creating powerful, secure, and user-friendly extensions for ArxIDE. Follow these guidelines to build extensions that integrate seamlessly with the Arxos ecosystem.
