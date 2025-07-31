import React from 'react'
import { 
  Box, 
  Paper, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText,
  Typography,
  Divider
} from '@mui/material'
import {
  Folder as FolderIcon,
  Description as FileIcon,
  Code as CodeIcon,
  Settings as SettingsIcon
} from '@mui/icons-material'

interface SidebarProps {
  activeFile: string | null
  onFileSelect: (file: string) => void
}

export const Sidebar: React.FC<SidebarProps> = ({ activeFile, onFileSelect }) => {
  const mockFiles = [
    { name: 'main.svgx', type: 'svgx', path: '/src/main.svgx' },
    { name: 'building.svgx', type: 'svgx', path: '/src/building.svgx' },
    { name: 'components.svgx', type: 'svgx', path: '/src/components.svgx' },
    { name: 'config.json', type: 'json', path: '/config.json' }
  ]

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'svgx':
        return <CodeIcon />
      default:
        return <FileIcon />
    }
  }

  return (
    <Paper 
      sx={{ 
        width: 250, 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        borderRadius: 0
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6" component="h2">
          Project
        </Typography>
      </Box>
      
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <List dense>
          <ListItem>
            <ListItemIcon>
              <FolderIcon />
            </ListItemIcon>
            <ListItemText primary="src" />
          </ListItem>
          
          <Divider />
          
          {mockFiles.map((file) => (
            <ListItem
              key={file.path}
              button
              selected={activeFile === file.path}
              onClick={() => onFileSelect(file.path)}
              sx={{ pl: 4 }}
            >
              <ListItemIcon>
                {getFileIcon(file.type)}
              </ListItemIcon>
              <ListItemText primary={file.name} />
            </ListItem>
          ))}
        </List>
      </Box>
      
      <Divider />
      
      <List dense>
        <ListItem button>
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText primary="Settings" />
        </ListItem>
      </List>
    </Paper>
  )
} 