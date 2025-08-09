import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Badge,
  LinearProgress,
} from '@mui/material';
import {
  Extension as ExtensionIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Code as CodeIcon,
  Build as BuildIcon,
  Store as StoreIcon,
  Security as SecurityIcon,
  Update as UpdateIcon,
  CheckCircle as ValidIcon,
  Error as InvalidIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface Plugin {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  category: 'tool' | 'constraint' | 'export' | 'import' | 'utility' | 'visualization';
  status: 'active' | 'inactive' | 'error' | 'loading';
  enabled: boolean;
  settings: Record<string, any>;
  dependencies: string[];
  permissions: string[];
  metadata: {
    icon?: string;
    homepage?: string;
    repository?: string;
    license?: string;
    tags?: string[];
    size?: number;
    downloads?: number;
    rating?: number;
    lastUpdated?: string;
  };
}

interface PluginSystemProps {
  plugins: Plugin[];
  onPluginInstall: (pluginId: string) => void;
  onPluginUninstall: (pluginId: string) => void;
  onPluginEnable: (pluginId: string) => void;
  onPluginDisable: (pluginId: string) => void;
  onPluginUpdate: (pluginId: string, settings: Record<string, any>) => void;
  onPluginExecute: (pluginId: string, parameters?: any) => void;
  availablePlugins?: Plugin[];
  onPluginSearch?: (query: string) => void;
  onPluginDownload?: (pluginId: string) => void;
}

// Plugin Card Component
const PluginCard: React.FC<{
  plugin: Plugin;
  onEnable: (pluginId: string) => void;
  onDisable: (pluginId: string) => void;
  onUninstall: (pluginId: string) => void;
  onExecute: (pluginId: string) => void;
  onSettings: (pluginId: string) => void;
}> = ({ plugin, onEnable, onDisable, onUninstall, onExecute, onSettings }) => {
  const getStatusColor = (status: Plugin['status']) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'error': return 'error';
      case 'loading': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: Plugin['status']) => {
    switch (status) {
      case 'active': return <ValidIcon />;
      case 'inactive': return <InfoIcon />;
      case 'error': return <InvalidIcon />;
      case 'loading': return <WarningIcon />;
      default: return <InfoIcon />;
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Typography variant="h6" component="div">
            {plugin.name}
          </Typography>
          <Chip
            icon={getStatusIcon(plugin.status)}
            label={plugin.status}
            color={getStatusColor(plugin.status) as any}
            size="small"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {plugin.description}
        </Typography>

        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
          <Chip label={plugin.category} size="small" variant="outlined" />
          <Chip label={`v${plugin.version}`} size="small" variant="outlined" />
          {plugin.metadata.tags?.map((tag) => (
            <Chip key={tag} label={tag} size="small" variant="outlined" />
          ))}
        </Box>

        <Typography variant="caption" color="text.secondary">
          by {plugin.author}
        </Typography>

        {plugin.metadata.rating && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Rating: {plugin.metadata.rating}/5
            </Typography>
          </Box>
        )}
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="Execute Plugin">
            <IconButton
              size="small"
              onClick={() => onExecute(plugin.id)}
              disabled={!plugin.enabled}
            >
              <PlayIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Plugin Settings">
            <IconButton
              size="small"
              onClick={() => onSettings(plugin.id)}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>

        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {plugin.enabled ? (
            <Tooltip title="Disable Plugin">
              <IconButton
                size="small"
                onClick={() => onDisable(plugin.id)}
                color="warning"
              >
                <StopIcon />
              </IconButton>
            </Tooltip>
          ) : (
            <Tooltip title="Enable Plugin">
              <IconButton
                size="small"
                onClick={() => onEnable(plugin.id)}
                color="success"
              >
                <PlayIcon />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Uninstall Plugin">
            <IconButton
              size="small"
              onClick={() => onUninstall(plugin.id)}
              color="error"
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </CardActions>
    </Card>
  );
};

// Plugin Settings Dialog
const PluginSettingsDialog: React.FC<{
  plugin: Plugin;
  open: boolean;
  onClose: () => void;
  onSave: (pluginId: string, settings: Record<string, any>) => void;
}> = ({ plugin, open, onClose, onSave }) => {
  const [settings, setSettings] = useState(plugin.settings);

  const handleSave = () => {
    onSave(plugin.id, settings);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Settings - {plugin.name}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {Object.entries(settings).map(([key, value]) => (
            <TextField
              key={key}
              label={key}
              value={value}
              onChange={(e) => setSettings({ ...settings, [key]: e.target.value })}
              fullWidth
            />
          ))}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} variant="contained">
          Save Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Plugin Marketplace Component
const PluginMarketplace: React.FC<{
  availablePlugins: Plugin[];
  onInstall: (pluginId: string) => void;
  onDownload: (pluginId: string) => void;
  onSearch: (query: string) => void;
}> = ({ availablePlugins, onInstall, onDownload, onSearch }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = ['all', 'tool', 'constraint', 'export', 'import', 'utility', 'visualization'];

  const filteredPlugins = useMemo(() => {
    return availablePlugins.filter(plugin => {
      const matchesSearch = plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          plugin.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || plugin.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [availablePlugins, searchQuery, selectedCategory]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    onSearch(query);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Plugin Marketplace
      </Typography>

      {/* Search and Filter */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField
          fullWidth
          label="Search plugins..."
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          size="small"
        />
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Category</InputLabel>
          <Select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            label="Category"
          >
            {categories.map((category) => (
              <MenuItem key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {/* Plugin Grid */}
      <Grid container spacing={2}>
        {filteredPlugins.map((plugin) => (
          <Grid item xs={12} sm={6} md={4} key={plugin.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" component="div">
                  {plugin.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {plugin.description}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
                  <Chip label={plugin.category} size="small" variant="outlined" />
                  <Chip label={`v${plugin.version}`} size="small" variant="outlined" />
                  {plugin.metadata.rating && (
                    <Chip label={`★ ${plugin.metadata.rating}`} size="small" color="primary" />
                  )}
                </Box>
                <Typography variant="caption" color="text.secondary">
                  by {plugin.author}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  startIcon={<DownloadIcon />}
                  onClick={() => onDownload(plugin.id)}
                >
                  Download
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => onInstall(plugin.id)}
                >
                  Install
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

// Main Plugin System Component
export const PluginSystem: React.FC<PluginSystemProps> = ({
  plugins,
  onPluginInstall,
  onPluginUninstall,
  onPluginEnable,
  onPluginDisable,
  onPluginUpdate,
  onPluginExecute,
  availablePlugins = [],
  onPluginSearch,
  onPluginDownload,
}) => {
  const [activeTab, setActiveTab] = useState<'installed' | 'marketplace' | 'development'>('installed');
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Statistics
  const stats = useMemo(() => {
    const total = plugins.length;
    const active = plugins.filter(p => p.status === 'active').length;
    const enabled = plugins.filter(p => p.enabled).length;
    const errors = plugins.filter(p => p.status === 'error').length;

    return { total, active, enabled, errors };
  }, [plugins]);

  // Handle plugin actions
  const handlePluginEnable = (pluginId: string) => {
    onPluginEnable(pluginId);
  };

  const handlePluginDisable = (pluginId: string) => {
    onPluginDisable(pluginId);
  };

  const handlePluginUninstall = (pluginId: string) => {
    if (window.confirm('Are you sure you want to uninstall this plugin?')) {
      onPluginUninstall(pluginId);
    }
  };

  const handlePluginExecute = (pluginId: string) => {
    onPluginExecute(pluginId);
  };

  const handlePluginSettings = (pluginId: string) => {
    const plugin = plugins.find(p => p.id === pluginId);
    if (plugin) {
      setSelectedPlugin(plugin);
      setShowSettings(true);
    }
  };

  const handleSettingsSave = (pluginId: string, settings: Record<string, any>) => {
    onPluginUpdate(pluginId, settings);
  };

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6">Plugin System</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant={activeTab === 'installed' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setActiveTab('installed')}
            >
              Installed ({stats.total})
            </Button>
            <Button
              variant={activeTab === 'marketplace' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setActiveTab('marketplace')}
              startIcon={<StoreIcon />}
            >
              Marketplace
            </Button>
            <Button
              variant={activeTab === 'development' ? 'contained' : 'outlined'}
              size="small"
              onClick={() => setActiveTab('development')}
              startIcon={<CodeIcon />}
            >
              Development
            </Button>
          </Box>
        </Box>

        {/* Statistics */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label={`Total: ${stats.total}`} size="small" />
          <Chip label={`Active: ${stats.active}`} color="success" size="small" />
          <Chip label={`Enabled: ${stats.enabled}`} color="primary" size="small" />
          <Chip label={`Errors: ${stats.errors}`} color="error" size="small" />
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {activeTab === 'installed' && (
          <>
            {plugins.length === 0 ? (
              <Alert severity="info">
                No plugins installed. Visit the marketplace to find and install plugins.
              </Alert>
            ) : (
              <Grid container spacing={2}>
                {plugins.map((plugin) => (
                  <Grid item xs={12} sm={6} md={4} key={plugin.id}>
                    <PluginCard
                      plugin={plugin}
                      onEnable={handlePluginEnable}
                      onDisable={handlePluginDisable}
                      onUninstall={handlePluginUninstall}
                      onExecute={handlePluginExecute}
                      onSettings={handlePluginSettings}
                    />
                  </Grid>
                ))}
              </Grid>
            )}
          </>
        )}

        {activeTab === 'marketplace' && (
          <PluginMarketplace
            availablePlugins={availablePlugins}
            onInstall={onPluginInstall}
            onDownload={onPluginDownload || (() => {})}
            onSearch={onPluginSearch || (() => {})}
          />
        )}

        {activeTab === 'development' && (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Plugin Development
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Plugin development tools and documentation will be available here.
            </Alert>
            <List>
              <ListItem>
                <ListItemIcon>
                  <CodeIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Plugin SDK"
                  secondary="Download the ArxIDE Plugin SDK for development"
                />
                <ListItemSecondaryAction>
                  <Button size="small" startIcon={<DownloadIcon />}>
                    Download SDK
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <BuildIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Plugin Builder"
                  secondary="Create and test plugins in the integrated builder"
                />
                <ListItemSecondaryAction>
                  <Button size="small" startIcon={<BuildIcon />}>
                    Open Builder
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemIcon>
                  <SecurityIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Security Guidelines"
                  secondary="Learn about plugin security and best practices"
                />
                <ListItemSecondaryAction>
                  <Button size="small">
                    View Guidelines
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Box>
        )}
      </Box>

      {/* Plugin Settings Dialog */}
      {selectedPlugin && showSettings && (
        <PluginSettingsDialog
          plugin={selectedPlugin}
          open={showSettings}
          onClose={() => {
            setShowSettings(false);
            setSelectedPlugin(null);
          }}
          onSave={handleSettingsSave}
        />
      )}
    </Box>
  );
};
