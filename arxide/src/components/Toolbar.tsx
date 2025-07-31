import React from 'react'
import { 
  AppBar, 
  Toolbar as MuiToolbar, 
  IconButton, 
  Button,
  Box,
  Divider
} from '@mui/material'
import {
  PlayArrow as RunIcon,
  Save as SaveIcon,
  FolderOpen as OpenIcon,
  Build as BuildIcon,
  ViewInAr as View3DIcon,
  Code as CodeIcon
} from '@mui/icons-material'

export const Toolbar: React.FC = () => {
  const handleRun = () => {
    console.log('Running SVGX code...')
  }

  const handleSave = () => {
    console.log('Saving file...')
  }

  const handleOpen = () => {
    console.log('Opening file...')
  }

  const handleBuild = () => {
    console.log('Building project...')
  }

  return (
    <AppBar 
      position="static" 
      sx={{ 
        backgroundColor: 'background.paper',
        color: 'text.primary',
        borderBottom: 1,
        borderColor: 'divider'
      }}
    >
      <MuiToolbar variant="dense">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<OpenIcon />}
            onClick={handleOpen}
          >
            Open
          </Button>
          
          <Button
            variant="outlined"
            size="small"
            startIcon={<SaveIcon />}
            onClick={handleSave}
          >
            Save
          </Button>
        </Box>

        <Divider orientation="vertical" flexItem sx={{ mx: 2 }} />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button
            variant="contained"
            size="small"
            startIcon={<RunIcon />}
            onClick={handleRun}
          >
            Run
          </Button>
          
          <Button
            variant="outlined"
            size="small"
            startIcon={<BuildIcon />}
            onClick={handleBuild}
          >
            Build
          </Button>
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton size="small" title="Code View">
            <CodeIcon />
          </IconButton>
          
          <IconButton size="small" title="3D View">
            <View3DIcon />
          </IconButton>
        </Box>
      </MuiToolbar>
    </AppBar>
  )
} 