import React from 'react'
import { Box, Paper, Typography } from '@mui/material'
import MonacoEditor from 'react-monaco-editor'

interface EditorPanelProps {
  code: string
  onCodeChange: (code: string) => void
}

export const EditorPanel: React.FC<EditorPanelProps> = ({ code, onCodeChange }) => {
  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      onCodeChange(value)
    }
  }

  const editorOptions = {
    selectOnLineNumbers: true,
    roundedSelection: false,
    readOnly: false,
    cursorStyle: 'line',
    automaticLayout: true,
    theme: 'vs-dark',
    fontSize: 14,
    minimap: {
      enabled: true
    }
  }

  return (
    <Paper 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        borderRadius: 0
      }}
    >
      <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="subtitle2" color="text.secondary">
          SVGX Editor
        </Typography>
      </Box>
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <MonacoEditor
          height="100%"
          language="svgx"
          value={code}
          options={editorOptions}
          onChange={handleEditorChange}
        />
      </Box>
    </Paper>
  )
} 