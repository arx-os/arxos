import { app, BrowserWindow, ipcMain } from 'electron'
import { ArxIDEApplication } from './ArxIDEApplication'
import path from 'path'

class ArxIDEMain {
  private mainWindow: BrowserWindow | null = null
  private arxIDE: ArxIDEApplication | null = null

  constructor() {
    this.setupAppEvents()
    this.setupIPCHandlers()
  }

  private setupAppEvents(): void {
    app.whenReady().then(() => {
      this.createWindow()
    })

    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        app.quit()
      }
    })

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        this.createWindow()
      }
    })
  }

  private async createWindow(): Promise<void> {
    this.mainWindow = new BrowserWindow({
      width: 1920,
      height: 1080,
      minWidth: 1200,
      minHeight: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        enableRemoteModule: false,
        preload: path.join(__dirname, 'preload.js')
      },
      titleBarStyle: 'default',
      show: false
    })

    // Load the renderer process
    if (process.env.NODE_ENV === 'development') {
      await this.mainWindow.loadURL('http://localhost:3000')
      this.mainWindow.webContents.openDevTools()
    } else {
      await this.mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
    }

    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show()
    })

    this.arxIDE = new ArxIDEApplication(this.mainWindow)
  }

  private setupIPCHandlers(): void {
    // File operations
    ipcMain.handle('file:open', async (_, filePath: string) => {
      try {
        return await this.arxIDE?.openFile(filePath)
      } catch (error) {
        console.error('Error opening file:', error)
        throw error
      }
    })

    ipcMain.handle('file:save', async (_, filePath: string, content: string) => {
      try {
        return await this.arxIDE?.saveFile(filePath, content)
      } catch (error) {
        console.error('Error saving file:', error)
        throw error
      }
    })

    // SVGX operations
    ipcMain.handle('svgx:validate', async (_, code: string) => {
      try {
        return await this.arxIDE?.validateSVGX(code)
      } catch (error) {
        console.error('Error validating SVGX:', error)
        throw error
      }
    })

    ipcMain.handle('svgx:compile', async (_, code: string) => {
      try {
        return await this.arxIDE?.compileSVGX(code)
      } catch (error) {
        console.error('Error compiling SVGX:', error)
        throw error
      }
    })

    // 3D operations
    ipcMain.handle('3d:render', async (_, modelData: any) => {
      try {
        return await this.arxIDE?.render3DModel(modelData)
      } catch (error) {
        console.error('Error rendering 3D model:', error)
        throw error
      }
    })

    // AI operations
    ipcMain.handle('ai:process-command', async (_, command: string) => {
      try {
        return await this.arxIDE?.processAICommand(command)
      } catch (error) {
        console.error('Error processing AI command:', error)
        throw error
      }
    })
  }
}

// Initialize the application
new ArxIDEMain() 