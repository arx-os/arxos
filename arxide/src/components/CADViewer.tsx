import React, { useEffect, useRef, useState, useCallback } from 'react'
import { Box, Paper, Typography, IconButton, Tooltip } from '@mui/material'
import { PlayArrow, Stop, Save, Upload, Download } from '@mui/icons-material'

interface CADViewerProps {
  svgxCode?: string
  onCodeChange?: (code: string) => void
  sessionId?: string
  clientId?: string
}

interface DrawingOperation {
  type: string
  data: any
  timestamp: number
}

export const CADViewer: React.FC<CADViewerProps> = ({
  svgxCode = '',
  onCodeChange,
  sessionId,
  clientId
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [currentTool, setCurrentTool] = useState('select')
  const [precision, setPrecision] = useState(0.001)
  const [isConnected, setIsConnected] = useState(false)
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)
  const [drawingOperations, setDrawingOperations] = useState<DrawingOperation[]>([])

  // Canvas state
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null)
  const [currentPoint, setCurrentPoint] = useState<{ x: number; y: number } | null>(null)

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width
      canvas.height = rect.height
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Draw grid
    drawGrid(ctx)

    return () => {
      window.removeEventListener('resize', resizeCanvas)
    }
  }, [])

  // Connect to WebSocket for real-time collaboration
  useEffect(() => {
    if (!sessionId || !clientId) return

    const ws = new WebSocket(`ws://localhost:8000/api/v1/svgx/ws/${sessionId}/${clientId}`)

    ws.onopen = () => {
      console.log('Connected to CAD collaboration')
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }

    ws.onclose = () => {
      console.log('Disconnected from CAD collaboration')
      setIsConnected(false)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    setWebsocket(ws)

    return () => {
      ws.close()
    }
  }, [sessionId, clientId])

  const drawGrid = (ctx: CanvasRenderingContext2D) => {
    const canvas = ctx.canvas
    const gridSize = 20
    const gridColor = '#e0e0e0'

    ctx.strokeStyle = gridColor
    ctx.lineWidth = 0.5

    // Draw vertical lines
    for (let x = 0; x <= canvas.width; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, canvas.height)
      ctx.stroke()
    }

    // Draw horizontal lines
    for (let y = 0; y <= canvas.height; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(canvas.width, y)
      ctx.stroke()
    }
  }

  const getCanvasPoint = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return null

    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Snap to grid
    const gridSize = 20
    const snappedX = Math.round(x / gridSize) * gridSize
    const snappedY = Math.round(y / gridSize) * gridSize

    return { x: snappedX, y: snappedY }
  }

  const handleMouseDown = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const point = getCanvasPoint(event)
    if (!point) return

    setStartPoint(point)
    setCurrentPoint(point)
    setIsDrawing(true)

    if (currentTool !== 'select') {
      // Start drawing operation
      const operation: DrawingOperation = {
        type: 'start_drawing',
        data: { tool: currentTool, startPoint: point },
        timestamp: Date.now()
      }
      setDrawingOperations(prev => [...prev, operation])
      sendDrawingOperation(operation)
    }
  }, [currentTool])

  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return

    const point = getCanvasPoint(event)
    if (!point) return

    setCurrentPoint(point)

    if (currentTool !== 'select' && startPoint) {
      // Update drawing preview
      const canvas = canvasRef.current
      const ctx = canvas?.getContext('2d')
      if (!ctx) return

      // Clear and redraw
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      drawGrid(ctx)
      drawAllOperations(ctx)

      // Draw current preview
      drawPreview(ctx, startPoint, point)
    }
  }, [isDrawing, currentTool, startPoint])

  const handleMouseUp = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return

    const point = getCanvasPoint(event)
    if (!point || !startPoint) return

    setIsDrawing(false)

    if (currentTool !== 'select') {
      // Finish drawing operation
      const operation: DrawingOperation = {
        type: 'finish_drawing',
        data: { tool: currentTool, startPoint, endPoint: point },
        timestamp: Date.now()
      }
      setDrawingOperations(prev => [...prev, operation])
      sendDrawingOperation(operation)

      // Update SVGX code
      updateSVGXCode(operation)
    }

    setStartPoint(null)
    setCurrentPoint(null)
  }, [isDrawing, currentTool, startPoint])

  const drawPreview = (ctx: CanvasRenderingContext2D, start: { x: number; y: number }, end: { x: number; y: number }) => {
    ctx.strokeStyle = '#2196f3'
    ctx.lineWidth = 2
    ctx.setLineDash([5, 5])

    switch (currentTool) {
      case 'line':
        ctx.beginPath()
        ctx.moveTo(start.x, start.y)
        ctx.lineTo(end.x, end.y)
        ctx.stroke()
        break

      case 'rectangle':
        const width = end.x - start.x
        const height = end.y - start.y
        ctx.strokeRect(start.x, start.y, width, height)
        break

      case 'circle':
        const radius = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2))
        ctx.beginPath()
        ctx.arc(start.x, start.y, radius, 0, 2 * Math.PI)
        ctx.stroke()
        break
    }

    ctx.setLineDash([])
  }

  const drawAllOperations = (ctx: CanvasRenderingContext2D) => {
    ctx.strokeStyle = '#000000'
    ctx.lineWidth = 2
    ctx.setLineDash([])

    drawingOperations.forEach(operation => {
      if (operation.type === 'finish_drawing') {
        const { tool, startPoint, endPoint } = operation.data

        switch (tool) {
          case 'line':
            ctx.beginPath()
            ctx.moveTo(startPoint.x, startPoint.y)
            ctx.lineTo(endPoint.x, endPoint.y)
            ctx.stroke()
            break

          case 'rectangle':
            const width = endPoint.x - startPoint.x
            const height = endPoint.y - startPoint.y
            ctx.strokeRect(startPoint.x, startPoint.y, width, height)
            break

          case 'circle':
            const radius = Math.sqrt(Math.pow(endPoint.x - startPoint.x, 2) + Math.pow(endPoint.y - startPoint.y, 2))
            ctx.beginPath()
            ctx.arc(startPoint.x, startPoint.y, radius, 0, 2 * Math.PI)
            ctx.stroke()
            break
        }
      }
    })
  }

  const sendDrawingOperation = (operation: DrawingOperation) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'drawing_operation',
        sessionId,
        clientId,
        operation
      }
      websocket.send(JSON.stringify(message))
    }
  }

  const handleWebSocketMessage = (message: any) => {
    if (message.type === 'drawing_operation' && message.clientId !== clientId) {
      // Handle drawing operation from other client
      setDrawingOperations(prev => [...prev, message.operation])
      
      // Redraw canvas
      const canvas = canvasRef.current
      const ctx = canvas?.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        drawGrid(ctx)
        drawAllOperations(ctx)
      }
    }
  }

  const updateSVGXCode = (operation: DrawingOperation) => {
    if (!onCodeChange) return

    const { tool, startPoint, endPoint } = operation.data
    let newCode = svgxCode

    switch (tool) {
      case 'line':
        newCode += `\n<line x1="${startPoint.x}" y1="${startPoint.y}" x2="${endPoint.x}" y2="${endPoint.y}" stroke="black" stroke-width="2"/>`
        break

      case 'rectangle':
        const width = endPoint.x - startPoint.x
        const height = endPoint.y - startPoint.y
        newCode += `\n<rect x="${startPoint.x}" y="${startPoint.y}" width="${width}" height="${height}" stroke="black" stroke-width="2" fill="none"/>`
        break

      case 'circle':
        const radius = Math.sqrt(Math.pow(endPoint.x - startPoint.x, 2) + Math.pow(endPoint.y - startPoint.y, 2))
        newCode += `\n<circle cx="${startPoint.x}" cy="${startPoint.y}" r="${radius}" stroke="black" stroke-width="2" fill="none"/>`
        break
    }

    onCodeChange(newCode)
  }

  const handleToolChange = (tool: string) => {
    setCurrentTool(tool)
  }

  const handlePrecisionChange = (newPrecision: number) => {
    setPrecision(newPrecision)
  }

  const handleSave = () => {
    // Save drawing to SVGX format
    const svgxData = {
      version: '1.0.0',
      precision: precision,
      operations: drawingOperations,
      code: svgxCode
    }
    
    const blob = new Blob([JSON.stringify(svgxData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'drawing.svgx'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleLoad = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.svgx,.json'
    input.onchange = (event) => {
      const file = (event.target as HTMLInputElement).files?.[0]
      if (file) {
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            const data = JSON.parse(e.target?.result as string)
            setDrawingOperations(data.operations || [])
            setPrecision(data.precision || 0.001)
            if (onCodeChange) {
              onCodeChange(data.code || '')
            }
          } catch (error) {
            console.error('Failed to load SVGX file:', error)
          }
        }
        reader.readAsText(file)
      }
    }
    input.click()
  }

  return (
    <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* CAD Toolbar */}
      <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="h6" sx={{ mr: 2 }}>
          CAD Viewer
        </Typography>
        
        {/* Drawing Tools */}
        <Tooltip title="Select">
          <IconButton
            size="small"
            color={currentTool === 'select' ? 'primary' : 'default'}
            onClick={() => handleToolChange('select')}
          >
            <PlayArrow />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Line">
          <IconButton
            size="small"
            color={currentTool === 'line' ? 'primary' : 'default'}
            onClick={() => handleToolChange('line')}
          >
            <PlayArrow />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Rectangle">
          <IconButton
            size="small"
            color={currentTool === 'rectangle' ? 'primary' : 'default'}
            onClick={() => handleToolChange('rectangle')}
          >
            <PlayArrow />
          </IconButton>
        </Tooltip>
        
        <Tooltip title="Circle">
          <IconButton
            size="small"
            color={currentTool === 'circle' ? 'primary' : 'default'}
            onClick={() => handleToolChange('circle')}
          >
            <PlayArrow />
          </IconButton>
        </Tooltip>

        {/* Precision Control */}
        <Typography variant="body2" sx={{ ml: 2 }}>
          Precision:
        </Typography>
        <select
          value={precision}
          onChange={(e) => handlePrecisionChange(Number(e.target.value))}
          style={{ marginLeft: 8 }}
        >
          <option value={0.001}>0.001"</option>
          <option value={0.01}>0.01"</option>
          <option value={0.1}>0.1"</option>
          <option value={1}>1"</option>
        </select>

        {/* File Operations */}
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          <Tooltip title="Save Drawing">
            <IconButton size="small" onClick={handleSave}>
              <Save />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Load Drawing">
            <IconButton size="small" onClick={handleLoad}>
              <Upload />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Export SVGX">
            <IconButton size="small">
              <Download />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Connection Status */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              bgcolor: isConnected ? 'success.main' : 'error.main'
            }}
          />
          <Typography variant="caption">
            {isConnected ? 'Connected' : 'Disconnected'}
          </Typography>
        </Box>
      </Box>

      {/* Canvas */}
      <Box sx={{ flex: 1, position: 'relative' }}>
        <canvas
          ref={canvasRef}
          style={{
            width: '100%',
            height: '100%',
            cursor: isDrawing ? 'crosshair' : 'default'
          }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
        />
      </Box>
    </Paper>
  )
} 