import React, { useState } from 'react'
import { Box, Grid, Paper } from '@mui/material'
import { EditorPanel } from './EditorPanel'
import { ThreeDViewer } from './ThreeDViewer'
import { Sidebar } from './Sidebar'
import { Toolbar } from './Toolbar'
import { StatusBar } from './StatusBar'

export const ArxIDEApplication: React.FC = () => {
  const [activeFile, setActiveFile] = useState<string | null>(null)
  const [svgxCode, setSvgxCode] = useState<string>('')

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
            <Grid item xs={6}>
              <EditorPanel 
                code={svgxCode}
                onCodeChange={setSvgxCode}
              />
            </Grid>
            
            {/* 3D Viewer Panel */}
            <Grid item xs={6}>
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