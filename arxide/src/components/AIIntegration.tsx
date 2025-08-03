import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  CardActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Badge,
} from '@mui/material';
import {
  SmartToy as AIIcon,
  Lightbulb as SuggestionIcon,
  AutoFixHigh as AutoFixIcon,
  Psychology as PsychologyIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Send as SendIcon,
  History as HistoryIcon,
  Star as StarIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';

interface AISuggestion {
  id: string;
  type: 'design' | 'optimization' | 'analysis' | 'generation' | 'correction';
  title: string;
  description: string;
  confidence: number;
  status: 'pending' | 'applied' | 'rejected' | 'error';
  timestamp: Date;
  metadata?: {
    category?: string;
    priority?: number;
    tags?: string[];
    parameters?: any;
  };
}

interface AIConversation {
  id: string;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    metadata?: any;
  }>;
  createdAt: Date;
  updatedAt: Date;
}

interface AIIntegrationProps {
  onSuggestionApply?: (suggestion: AISuggestion) => void;
  onSuggestionReject?: (suggestionId: string) => void;
  onConversationStart?: (prompt: string) => void;
  onAutoComplete?: (partial: string) => Promise<string>;
  onDesignAnalysis?: (design: any) => Promise<any>;
  onOptimization?: (parameters: any) => Promise<any>;
}

// AI Suggestion Component
const AISuggestionCard: React.FC<{
  suggestion: AISuggestion;
  onApply: (suggestion: AISuggestion) => void;
  onReject: (suggestionId: string) => void;
  onFeedback: (suggestionId: string, feedback: 'positive' | 'negative') => void;
}> = ({ suggestion, onApply, onReject, onFeedback }) => {
  const getStatusColor = (status: AISuggestion['status']) => {
    switch (status) {
      case 'applied': return 'success';
      case 'rejected': return 'error';
      case 'error': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: AISuggestion['status']) => {
    switch (status) {
      case 'applied': return <SuccessIcon />;
      case 'rejected': return <ErrorIcon />;
      case 'error': return <ErrorIcon />;
      case 'pending': return <WarningIcon />;
      default: return <InfoIcon />;
    }
  };

  const getTypeIcon = (type: AISuggestion['type']) => {
    switch (type) {
      case 'design': return <AIIcon />;
      case 'optimization': return <AutoFixIcon />;
      case 'analysis': return <PsychologyIcon />;
      case 'generation': return <CodeIcon />;
      case 'correction': return <AutoFixIcon />;
      default: return <AIIcon />;
    }
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getTypeIcon(suggestion.type)}
            <Typography variant="h6" component="div">
              {suggestion.title}
            </Typography>
          </Box>
          <Chip
            icon={getStatusIcon(suggestion.status)}
            label={suggestion.status}
            color={getStatusColor(suggestion.status) as any}
            size="small"
          />
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {suggestion.description}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Confidence: {suggestion.confidence}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={suggestion.confidence}
            sx={{ flex: 1, ml: 1 }}
          />
        </Box>

        {suggestion.metadata?.tags && (
          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
            {suggestion.metadata.tags.map((tag, index) => (
              <Chip key={index} label={tag} size="small" variant="outlined" />
            ))}
          </Box>
        )}

        <Typography variant="caption" color="text.secondary">
          {suggestion.timestamp.toLocaleString()}
        </Typography>
      </CardContent>

      <CardActions>
        {suggestion.status === 'pending' && (
          <>
            <Button
              size="small"
              variant="contained"
              onClick={() => onApply(suggestion)}
            >
              Apply
            </Button>
            <Button
              size="small"
              color="error"
              onClick={() => onReject(suggestion.id)}
            >
              Reject
            </Button>
          </>
        )}
        <Box sx={{ flex: 1 }} />
        <Tooltip title="Helpful">
          <IconButton
            size="small"
            onClick={() => onFeedback(suggestion.id, 'positive')}
          >
            <ThumbUpIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Not helpful">
          <IconButton
            size="small"
            onClick={() => onFeedback(suggestion.id, 'negative')}
          >
            <ThumbDownIcon />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  );
};

// AI Chat Component
const AIChat: React.FC<{
  conversations: AIConversation[];
  currentConversation?: AIConversation;
  onSendMessage: (message: string) => void;
  onNewConversation: () => void;
  onLoadConversation: (conversationId: string) => void;
}> = ({ conversations, currentConversation, onSendMessage, onNewConversation, onLoadConversation }) => {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = () => {
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
      setIsTyping(true);
      // Simulate AI response
      setTimeout(() => setIsTyping(false), 2000);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">AI Assistant</Typography>
          <Button
            size="small"
            startIcon={<AIIcon />}
            onClick={onNewConversation}
          >
            New Chat
          </Button>
        </Box>
      </Box>

      {/* Conversations List */}
      <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Recent Conversations
        </Typography>
        <List dense>
          {conversations.map((conv) => (
            <ListItem
              key={conv.id}
              button
              selected={currentConversation?.id === conv.id}
              onClick={() => onLoadConversation(conv.id)}
            >
              <ListItemIcon>
                <AIIcon />
              </ListItemIcon>
              <ListItemText
                primary={conv.messages[0]?.content.substring(0, 50) + '...'}
                secondary={conv.updatedAt.toLocaleString()}
              />
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Chat Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {currentConversation?.messages.map((msg) => (
          <Box
            key={msg.id}
            sx={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              mb: 2,
            }}
          >
            <Box
              sx={{
                maxWidth: '70%',
                p: 1.5,
                borderRadius: 2,
                backgroundColor: msg.role === 'user' ? 'primary.main' : 'grey.100',
                color: msg.role === 'user' ? 'white' : 'text.primary',
              }}
            >
              <Typography variant="body2">{msg.content}</Typography>
              <Typography variant="caption" sx={{ opacity: 0.7 }}>
                {msg.timestamp.toLocaleTimeString()}
              </Typography>
            </Box>
          </Box>
        ))}

        {isTyping && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                backgroundColor: 'grey.100',
              }}
            >
              <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                AI is typing...
              </Typography>
            </Box>
          </Box>
        )}
      </Box>

      {/* Message Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            placeholder="Ask AI for help with your design..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            disabled={isTyping}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={!message.trim() || isTyping}
          >
            <SendIcon />
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

// AI Analysis Component
const AIAnalysis: React.FC<{
  analysisResults: any[];
  onRunAnalysis: (type: string) => void;
  onExportResults: (results: any[]) => void;
}> = ({ analysisResults, onRunAnalysis, onExportResults }) => {
  const analysisTypes = [
    { id: 'design', name: 'Design Analysis', description: 'Analyze design patterns and best practices' },
    { id: 'performance', name: 'Performance Analysis', description: 'Analyze performance and optimization opportunities' },
    { id: 'sustainability', name: 'Sustainability Analysis', description: 'Analyze environmental impact and sustainability' },
    { id: 'cost', name: 'Cost Analysis', description: 'Analyze material and manufacturing costs' },
  ];

  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>
        AI Analysis
      </Typography>

      {/* Analysis Types */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          Available Analyses
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {analysisTypes.map((type) => (
            <Card key={type.id} sx={{ minWidth: 200 }}>
              <CardContent>
                <Typography variant="h6" component="div">
                  {type.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {type.description}
                </Typography>
                <Button
                  size="small"
                  variant="contained"
                  onClick={() => onRunAnalysis(type.id)}
                >
                  Run Analysis
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Box>

      {/* Analysis Results */}
      {analysisResults.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1">
              Analysis Results
            </Typography>
            <Button
              size="small"
              startIcon={<DownloadIcon />}
              onClick={() => onExportResults(analysisResults)}
            >
              Export Results
            </Button>
          </Box>
          <List>
            {analysisResults.map((result, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText
                  primary={result.title}
                  secondary={result.description}
                />
                <ListItemSecondaryAction>
                  <Chip
                    label={result.severity}
                    color={result.severity === 'high' ? 'error' : result.severity === 'medium' ? 'warning' : 'success'}
                    size="small"
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Box>
  );
};

// Main AI Integration Component
export const AIIntegration: React.FC<AIIntegrationProps> = ({
  onSuggestionApply,
  onSuggestionReject,
  onConversationStart,
  onAutoComplete,
  onDesignAnalysis,
  onOptimization,
}) => {
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<AIConversation | undefined>();
  const [analysisResults, setAnalysisResults] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'suggestions' | 'chat' | 'analysis' | 'settings'>('suggestions');
  const [aiEnabled, setAiEnabled] = useState(true);
  const [autoSuggestions, setAutoSuggestions] = useState(true);

  // Mock AI suggestions
  useEffect(() => {
    const mockSuggestions: AISuggestion[] = [
      {
        id: 'suggestion_1',
        type: 'optimization',
        title: 'Optimize Wall Thickness',
        description: 'Reduce wall thickness from 0.25" to 0.2" to save 20% material while maintaining structural integrity.',
        confidence: 85,
        status: 'pending',
        timestamp: new Date(),
        metadata: {
          category: 'material-optimization',
          priority: 1,
          tags: ['optimization', 'material', 'cost'],
        },
      },
      {
        id: 'suggestion_2',
        type: 'design',
        title: 'Add Reinforcement',
        description: 'Add corner reinforcements to improve structural stability and load-bearing capacity.',
        confidence: 92,
        status: 'pending',
        timestamp: new Date(),
        metadata: {
          category: 'structural-improvement',
          priority: 2,
          tags: ['structural', 'safety', 'reinforcement'],
        },
      },
      {
        id: 'suggestion_3',
        type: 'analysis',
        title: 'Thermal Analysis',
        description: 'Perform thermal analysis to identify potential heat transfer issues in the design.',
        confidence: 78,
        status: 'applied',
        timestamp: new Date(Date.now() - 3600000),
        metadata: {
          category: 'thermal-analysis',
          priority: 3,
          tags: ['thermal', 'analysis', 'heat'],
        },
      },
    ];

    setSuggestions(mockSuggestions);
  }, []);

  // Mock conversations
  useEffect(() => {
    const mockConversations: AIConversation[] = [
      {
        id: 'conv_1',
        messages: [
          {
            id: 'msg_1',
            role: 'user',
            content: 'How can I optimize this design for 3D printing?',
            timestamp: new Date(Date.now() - 7200000),
          },
          {
            id: 'msg_2',
            role: 'assistant',
            content: 'I can help you optimize your design for 3D printing. Consider reducing overhangs, adding support structures, and optimizing wall thickness. Would you like me to analyze your current design?',
            timestamp: new Date(Date.now() - 7000000),
          },
        ],
        createdAt: new Date(Date.now() - 7200000),
        updatedAt: new Date(Date.now() - 7000000),
      },
    ];

    setConversations(mockConversations);
    setCurrentConversation(mockConversations[0]);
  }, []);

  // Handle suggestion apply
  const handleSuggestionApply = useCallback((suggestion: AISuggestion) => {
    setSuggestions(prev =>
      prev.map(s => s.id === suggestion.id ? { ...s, status: 'applied' } : s)
    );
    onSuggestionApply?.(suggestion);
  }, [onSuggestionApply]);

  // Handle suggestion reject
  const handleSuggestionReject = useCallback((suggestionId: string) => {
    setSuggestions(prev =>
      prev.map(s => s.id === suggestionId ? { ...s, status: 'rejected' } : s)
    );
    onSuggestionReject?.(suggestionId);
  }, [onSuggestionReject]);

  // Handle suggestion feedback
  const handleSuggestionFeedback = useCallback((suggestionId: string, feedback: 'positive' | 'negative') => {
    console.log('AI feedback:', suggestionId, feedback);
    // Send feedback to AI system for learning
  }, []);

  // Handle send message
  const handleSendMessage = useCallback((message: string) => {
    if (!currentConversation) return;

    const newMessage = {
      id: `msg_${Date.now()}`,
      role: 'user' as const,
      content: message,
      timestamp: new Date(),
    };

    const updatedConversation = {
      ...currentConversation,
      messages: [...currentConversation.messages, newMessage],
      updatedAt: new Date(),
    };

    setCurrentConversation(updatedConversation);
    setConversations(prev =>
      prev.map(c => c.id === currentConversation.id ? updatedConversation : c)
    );

    onConversationStart?.(message);
  }, [currentConversation, onConversationStart]);

  // Handle new conversation
  const handleNewConversation = useCallback(() => {
    const newConversation: AIConversation = {
      id: `conv_${Date.now()}`,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    setConversations(prev => [newConversation, ...prev]);
    setCurrentConversation(newConversation);
  }, []);

  // Handle load conversation
  const handleLoadConversation = useCallback((conversationId: string) => {
    const conversation = conversations.find(c => c.id === conversationId);
    setCurrentConversation(conversation);
  }, [conversations]);

  // Handle run analysis
  const handleRunAnalysis = useCallback((type: string) => {
    const mockResults = [
      {
        title: `${type.charAt(0).toUpperCase() + type.slice(1)} Complete`,
        description: `Analysis completed successfully. Found 3 optimization opportunities.`,
        severity: 'medium',
      },
    ];

    setAnalysisResults(prev => [...mockResults, ...prev]);
    onDesignAnalysis?.({ type });
  }, [onDesignAnalysis]);

  // Handle export results
  const handleExportResults = useCallback((results: any[]) => {
    console.log('Exporting analysis results:', results);
    onExportResults?.(results);
  }, [onExportResults]);

  return (
    <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6">
            AI Integration
            <Chip
              label={aiEnabled ? 'Enabled' : 'Disabled'}
              color={aiEnabled ? 'success' : 'error'}
              size="small"
              sx={{ ml: 1 }}
            />
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={aiEnabled}
                  onChange={(e) => setAiEnabled(e.target.checked)}
                />
              }
              label="AI Enabled"
            />
            <Tooltip title="AI Settings">
              <IconButton
                size="small"
                onClick={() => setActiveTab('settings')}
              >
                <SettingsIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Tab Navigation */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant={activeTab === 'suggestions' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('suggestions')}
            startIcon={<SuggestionIcon />}
          >
            Suggestions ({suggestions.filter(s => s.status === 'pending').length})
          </Button>
          <Button
            variant={activeTab === 'chat' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('chat')}
            startIcon={<AIIcon />}
          >
            AI Chat
          </Button>
          <Button
            variant={activeTab === 'analysis' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setActiveTab('analysis')}
            startIcon={<PsychologyIcon />}
          >
            Analysis
          </Button>
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {activeTab === 'suggestions' && (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              AI Suggestions
            </Typography>
            {suggestions.map((suggestion) => (
              <AISuggestionCard
                key={suggestion.id}
                suggestion={suggestion}
                onApply={handleSuggestionApply}
                onReject={handleSuggestionReject}
                onFeedback={handleSuggestionFeedback}
              />
            ))}
          </Box>
        )}

        {activeTab === 'chat' && (
          <AIChat
            conversations={conversations}
            currentConversation={currentConversation}
            onSendMessage={handleSendMessage}
            onNewConversation={handleNewConversation}
            onLoadConversation={handleLoadConversation}
          />
        )}

        {activeTab === 'analysis' && (
          <AIAnalysis
            analysisResults={analysisResults}
            onRunAnalysis={handleRunAnalysis}
            onExportResults={handleExportResults}
          />
        )}

        {activeTab === 'settings' && (
          <Box>
            <Typography variant="h6" sx={{ mb: 2 }}>
              AI Settings
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={autoSuggestions}
                  onChange={(e) => setAutoSuggestions(e.target.checked)}
                />
              }
              label="Auto-suggestions"
            />
            <Alert severity="info" sx={{ mt: 2 }}>
              Additional AI settings will be implemented here.
            </Alert>
          </Box>
        )}
      </Box>
    </Box>
  );
}; 