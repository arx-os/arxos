import React, { useState } from 'react'
import { Box, Grid, Paper } from '@mui/material'
import { EditorPanel } from './EditorPanel'
import { ThreeDViewer } from './ThreeDViewer'
import { CADViewer } from './CADViewer'
import { Sidebar } from './Sidebar'
import { Toolbar } from './Toolbar'
import { StatusBar } from './StatusBar'

export const ArxIDEApplication: React.FC = () => {
  const [activeFile, setActiveFile] = useState<string | null>(null)
  const [svgxCode, setSvgxCode] = useState<string>('')
  const [sessionId, setSessionId] = useState<string>('test-session-123')
  const [clientId, setClientId] = useState<string>('client-' + Math.random().toString(36).substr(2, 9))

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Toolbar */}
      <Toolbar />
      
      {/* Main Content Area */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Left Sidebar */}
        <Sidebar 
          activeFile={activeFile}
          onFileSelect={setActiveFile}
        />
        
        {/* Center Content */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <Grid container sx={{ flex: 1, height: '100%' }}>
            {/* Editor Panel */}
            <Grid item xs={4}>
              <EditorPanel 
                code={svgxCode}
                onCodeChange={setSvgxCode}
              />
            </Grid>
            
            {/* CAD Viewer Panel */}
            <Grid item xs={4}>
              <CADViewer 
                svgxCode={svgxCode}
                onCodeChange={setSvgxCode}
                sessionId={sessionId}
                clientId={clientId}
              />
            </Grid>
            
            {/* 3D Viewer Panel */}
            <Grid item xs={4}>
              <ThreeDViewer 
                svgxCode={svgxCode}
              />
            </Grid>
          </Grid>
        </Box>
      </Box>
      
      {/* Bottom Status Bar */}
      <StatusBar />
    </Box>
  )
} 