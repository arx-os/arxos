import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Slider,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Settings as SettingsIcon,
  AutoFixHigh as OptimizeIcon,
  Warning as WarningIcon,
  CheckCircle as ValidIcon,
  Error as InvalidIcon,
} from '@mui/icons-material';

interface Constraint {
  id: string;
  type: 'distance' | 'angle' | 'parallel' | 'perpendicular' | 'coincident' | 'tangent' | 'horizontal' | 'vertical' | 'parametric' | 'dynamic';
  objects: string[];
  parameters: {
    value?: number;
    expression?: string;
    tolerance?: number;
    units?: string;
  };
  status: 'valid' | 'invalid' | 'warning' | 'pending';
  metadata?: {
    description?: string;
    category?: string;
    priority?: number;
    autoSolve?: boolean;
  };
}

interface AdvancedConstraintsProps {
  constraints: Constraint[];
  objects: any[];
  onConstraintAdd: (constraint: Constraint) => void;
  onConstraintUpdate: (constraintId: string, updates: Partial<Constraint>) => void;
  onConstraintDelete: (constraintId: string) => void;
  onConstraintsOptimize: () => void;
  onConstraintSolve: (constraintId: string) => void;
  precision: number;
}

// Constraint Type Definitions
const CONSTRAINT_TYPES = {
  distance: {
    label: 'Distance',
    description: 'Set exact distance between objects',
    parameters: ['value', 'tolerance'],
    units: ['inches', 'mm', 'cm', 'feet'],
  },
  angle: {
    label: 'Angle',
    description: 'Set angle between objects',
    parameters: ['value', 'tolerance'],
    units: ['degrees', 'radians'],
  },
  parallel: {
    label: 'Parallel',
    description: 'Make objects parallel',
    parameters: ['tolerance'],
    units: ['degrees'],
  },
  perpendicular: {
    label: 'Perpendicular',
    description: 'Make objects perpendicular',
    parameters: ['tolerance'],
    units: ['degrees'],
  },
  coincident: {
    label: 'Coincident',
    description: 'Make objects share a point',
    parameters: ['tolerance'],
    units: ['inches', 'mm'],
  },
  tangent: {
    label: 'Tangent',
    description: 'Make objects tangent',
    parameters: ['tolerance'],
    units: ['inches', 'mm'],
  },
  horizontal: {
    label: 'Horizontal',
    description: 'Make object horizontal',
    parameters: ['tolerance'],
    units: ['degrees'],
  },
  vertical: {
    label: 'Vertical',
    description: 'Make object vertical',
    parameters: ['tolerance'],
    units: ['degrees'],
  },
  parametric: {
    label: 'Parametric',
    description: 'Define constraint with mathematical expression',
    parameters: ['expression', 'tolerance'],
    units: ['custom'],
  },
  dynamic: {
    label: 'Dynamic',
    description: 'Constraint that changes based on other constraints',
    parameters: ['expression', 'tolerance'],
    units: ['custom'],
  },
};

// Constraint Editor Component
const ConstraintEditor: React.FC<{
  constraint?: Constraint;
  objects: any[];
  onSave: (constraint: Constraint) => void;
  onCancel: () => void;
}> = ({ constraint, objects, onSave, onCancel }) => {
  const [type, setType] = useState<Constraint['type']>(constraint?.type || 'distance');
  const [selectedObjects, setSelectedObjects] = useState<string[]>(constraint?.objects || []);
  const [value, setValue] = useState(constraint?.parameters.value || 0);
  const [expression, setExpression] = useState(constraint?.parameters.expression || '');
  const [tolerance, setTolerance] = useState(constraint?.parameters.tolerance || 0.001);
  const [units, setUnits] = useState(constraint?.parameters.units || 'inches');
  const [description, setDescription] = useState(constraint?.metadata?.description || '');
  const [autoSolve, setAutoSolve] = useState<boolean>(constraint?.metadata?.autoSolve ?? true);

  const constraintType = CONSTRAINT_TYPES[type as keyof typeof CONSTRAINT_TYPES];

  const handleSave = () => {
    const newConstraint: Constraint = {
      id: constraint?.id || `constraint_${Date.now()}`,
      type: type as Constraint['type'],
      objects: selectedObjects,
      parameters: {
        value: type !== 'parametric' && type !== 'dynamic' ? value : undefined,
        expression: type === 'parametric' || type === 'dynamic' ? expression : undefined,
        tolerance,
        units,
      },
      status: 'pending',
      metadata: {
        description,
        autoSolve,
        priority: 1,
      },
    };

    onSave(newConstraint);
  };

  return (
    <Dialog open={true} onClose={onCancel} maxWidth="md" fullWidth>
      <DialogTitle>
        {constraint ? 'Edit Constraint' : 'Add New Constraint'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {/* Constraint Type */}
          <FormControl fullWidth>
            <InputLabel>Constraint Type</InputLabel>
            <Select
              value={type}
              onChange={(e) => setType(e.target.value as Constraint['type'])}
              label="Constraint Type"
            >
              {Object.entries(CONSTRAINT_TYPES).map(([key, config]) => (
                <MenuItem key={key} value={key}>
                  {config.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Description */}
          <TextField
            fullWidth
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe this constraint..."
          />

          {/* Object Selection */}
          <FormControl fullWidth>
            <InputLabel>Objects</InputLabel>
            <Select
              multiple
              value={selectedObjects}
              onChange={(e) => setSelectedObjects(e.target.value as string[])}
              label="Objects"
            >
              {objects.map((obj) => (
                <MenuItem key={obj.id} value={obj.id}>
                  {obj.name || obj.id}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Parameters based on type */}
          {type !== 'parametric' && type !== 'dynamic' && (
            <TextField
              fullWidth
              label="Value"
              type="number"
              value={value}
              onChange={(e) => setValue(Number(e.target.value))}
              inputProps={{ step: 0.001 }}
            />
          )}

          {(type === 'parametric' || type === 'dynamic') && (
            <TextField
              fullWidth
              label="Expression"
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              placeholder="e.g., 2 * distance(obj1, obj2) + 5"
              multiline
              rows={3}
            />
          )}

          {/* Tolerance */}
          <TextField
            fullWidth
            label="Tolerance"
            type="number"
            value={tolerance}
            onChange={(e) => setTolerance(Number(e.target.value))}
            inputProps={{ step: 0.0001 }}
          />

          {/* Units */}
          <FormControl fullWidth>
            <InputLabel>Units</InputLabel>
            <Select
              value={units}
              onChange={(e) => setUnits(e.target.value)}
              label="Units"
            >
              {constraintType.units.map((unit) => (
                <MenuItem key={unit} value={unit}>
                  {unit}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Auto-solve */}
          <FormControlLabel
            control={
              <Switch
                checked={autoSolve}
                onChange={(e) => setAutoSolve(e.target.checked)}
              />
            }
            label="Auto-solve constraint"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          {constraint ? 'Update' : 'Add'} Constraint
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Constraint Status Component
const ConstraintStatus: React.FC<{ status: Constraint['status'] }> = ({ status }) => {
  const statusConfig = {
    valid: { icon: <ValidIcon />, color: 'success', label: 'Valid' },
    invalid: { icon: <InvalidIcon />, color: 'error', label: 'Invalid' },
    warning: { icon: <WarningIcon />, color: 'warning', label: 'Warning' },
    pending: { icon: <WarningIcon />, color: 'info', label: 'Pending' },
  };

  const config = statusConfig[status];

  return (
    <Chip
      icon={config.icon}
      label={config.label}
      color={config.color as any}
      size="small"
    />
  );
};

// Main Advanced Constraints Component
export const AdvancedConstraints: React.FC<AdvancedConstraintsProps> = ({
  constraints,
  objects,
  onConstraintAdd,
  onConstraintUpdate,
  onConstraintDelete,
  onConstraintsOptimize,
  onConstraintSolve,
  precision,
}) => {
  const [showEditor, setShowEditor] = useState(false);
  const [editingConstraint, setEditingConstraint] = useState<Constraint | undefined>();
  const [expandedConstraint, setExpandedConstraint] = useState<string | false>(false);

  // Statistics
  const stats = useMemo(() => {
    const total = constraints.length;
    const valid = constraints.filter(c => c.status === 'valid').length;
    const invalid = constraints.filter(c => c.status === 'invalid').length;
    const warning = constraints.filter(c => c.status === 'warning').length;
    const pending = constraints.filter(c => c.status === 'pending').length;

    return { total, valid, invalid, warning, pending };
  }, [constraints]);

  // Handle constraint editing
  const handleEditConstraint = (constraint: Constraint) => {
    setEditingConstraint(constraint);
    setShowEditor(true);
  };

  // Handle constraint saving
  const handleSaveConstraint = (constraint: Constraint) => {
    if (editingConstraint) {
      onConstraintUpdate(editingConstraint.id, constraint);
    } else {
      onConstraintAdd(constraint);
    }
    setShowEditor(false);
    setEditingConstraint(undefined);
  };

  // Handle constraint deletion
  const handleDeleteConstraint = (constraintId: string) => {
    if (window.confirm('Are you sure you want to delete this constraint?')) {
      onConstraintDelete(constraintId);
    }
  };

  // Handle constraint solving
  const handleSolveConstraint = (constraintId: string) => {
    onConstraintSolve(constraintId);
  };

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6">Advanced Constraints</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Add Constraint">
              <IconButton
                size="small"
                onClick={() => setShowEditor(true)}
                color="primary"
              >
                <AddIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Optimize Constraints">
              <IconButton
                size="small"
                onClick={onConstraintsOptimize}
                color="secondary"
              >
                <OptimizeIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Statistics */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label={`Total: ${stats.total}`} size="small" />
          <Chip label={`Valid: ${stats.valid}`} color="success" size="small" />
          <Chip label={`Invalid: ${stats.invalid}`} color="error" size="small" />
          <Chip label={`Warning: ${stats.warning}`} color="warning" size="small" />
          <Chip label={`Pending: ${stats.pending}`} color="info" size="small" />
        </Box>
      </Box>

      {/* Constraints List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        {constraints.length === 0 ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            No constraints defined. Click the + button to add a constraint.
          </Alert>
        ) : (
          constraints.map((constraint) => (
            <Accordion
              key={constraint.id}
              expanded={expandedConstraint === constraint.id}
              onChange={(_: React.SyntheticEvent, isExpanded: boolean) => setExpandedConstraint(isExpanded ? constraint.id : false)}
              sx={{ mb: 1 }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                  <ConstraintStatus status={constraint.status} />
                  <Typography variant="subtitle2">
                    {CONSTRAINT_TYPES[constraint.type]?.label || constraint.type}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ({constraint.objects.length} objects)
                  </Typography>
                  {constraint.metadata?.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                      - {constraint.metadata.description}
                    </Typography>
                  )}
                </Box>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <Tooltip title="Edit Constraint">
                    <IconButton
                      size="small"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        handleEditConstraint(constraint);
                      }}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Solve Constraint">
                    <IconButton
                      size="small"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        handleSolveConstraint(constraint.id);
                      }}
                    >
                      <SettingsIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete Constraint">
                    <IconButton
                      size="small"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        handleDeleteConstraint(constraint.id);
                      }}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {/* Objects */}
                  <Typography variant="subtitle2">Objects:</Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {constraint.objects.map((objId) => {
                      const obj = objects.find(o => o.id === objId);
                      return (
                        <Chip
                          key={objId}
                          label={obj?.name || objId}
                          size="small"
                          variant="outlined"
                        />
                      );
                    })}
                  </Box>

                  {/* Parameters */}
                  <Typography variant="subtitle2">Parameters:</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    {constraint.parameters.value !== undefined && (
                      <Typography variant="body2">
                        Value: {constraint.parameters.value} {constraint.parameters.units}
                      </Typography>
                    )}
                    {constraint.parameters.expression && (
                      <Typography variant="body2">
                        Expression: {constraint.parameters.expression}
                      </Typography>
                    )}
                    <Typography variant="body2">
                      Tolerance: {constraint.parameters.tolerance} {constraint.parameters.units}
                    </Typography>
                  </Box>

                  {/* Metadata */}
                  {constraint.metadata && (
                    <>
                      <Typography variant="subtitle2">Metadata:</Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        {constraint.metadata.description && (
                          <Typography variant="body2">
                            Description: {constraint.metadata.description}
                          </Typography>
                        )}
                        {constraint.metadata.category && (
                          <Typography variant="body2">
                            Category: {constraint.metadata.category}
                          </Typography>
                        )}
                        {constraint.metadata.priority && (
                          <Typography variant="body2">
                            Priority: {constraint.metadata.priority}
                          </Typography>
                        )}
                        <Typography variant="body2">
                          Auto-solve: {constraint.metadata.autoSolve ? 'Yes' : 'No'}
                        </Typography>
                      </Box>
                    </>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          ))
        )}
      </Box>

      {/* Constraint Editor Dialog */}
      {showEditor && (
        <ConstraintEditor
          constraint={editingConstraint}
          objects={objects}
          onSave={handleSaveConstraint}
          onCancel={() => {
            setShowEditor(false);
            setEditingConstraint(undefined);
          }}
        />
      )}
    </Box>
  );
};
