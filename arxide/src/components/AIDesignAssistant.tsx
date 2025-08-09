import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Box, Typography, Paper, Grid, TextField, Button,
         List, ListItem, ListItemText, ListItemIcon, ListItemSecondaryAction,
         Dialog, DialogTitle, DialogContent, DialogActions,
         IconButton, Tooltip, Chip, Alert, CircularProgress,
         Accordion, AccordionSummary, AccordionDetails,
         FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import {
  SmartToy, AutoFixHigh, Lightbulb, TrendingUp,
  Psychology, Code, Build, Analytics,
  Send, Mic, MicOff, History, Refresh,
  ExpandMore, CheckCircle, Warning, Error,
  PlayArrow, Pause, Stop, Settings
} from '@mui/icons-material';

interface AISuggestion {
  id: string;
  type: 'optimization' | 'design' | 'constraint' | 'analysis' | 'automation';
  title: string;
  description: string;
  confidence: number;
  impact: 'high' | 'medium' | 'low';
  category: string;
  timestamp: Date;
  status: 'pending' | 'applied' | 'rejected' | 'in_progress';
  parameters?: any;
  estimatedTime?: number;
  costSavings?: number;
}

interface DesignAnalysis {
  id: string;
  type: 'structural' | 'electrical' | 'mechanical' | 'plumbing' | 'general';
  title: string;
  summary: string;
  details: string[];
  recommendations: string[];
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  timestamp: Date;
}

interface ConversationMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  metadata?: any;
}

interface AIDesignAssistantProps {
  onSuggestionApply: (suggestion: AISuggestion) => void;
  onSuggestionReject: (suggestionId: string) => void;
  onConversationStart: (prompt: string) => void;
  onAutoComplete: (partial: string) => Promise<string>;
  onDesignAnalysis: (design: any) => Promise<DesignAnalysis>;
  onOptimization: (parameters: any) => Promise<any>;
  onAutomationExecute: (automation: any) => Promise<any>;
}

export const AIDesignAssistant: React.FC<AIDesignAssistantProps> = ({
  onSuggestionApply,
  onSuggestionReject,
  onConversationStart,
  onAutoComplete,
  onDesignAnalysis,
  onOptimization,
  onAutomationExecute
}) => {
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [analysis, setAnalysis] = useState<DesignAnalysis[]>([]);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'suggestions' | 'analysis' | 'automation'>('chat');
  const [selectedSuggestion, setSelectedSuggestion] = useState<AISuggestion | null>(null);
  const [showSuggestionDialog, setShowSuggestionDialog] = useState(false);
  const [autoCompleteEnabled, setAutoCompleteEnabled] = useState(true);
  const [aiModel, setAiModel] = useState('gpt-4');
  const [temperature, setTemperature] = useState(0.7);

  const inputRef = useRef<HTMLInputElement>(null);
  const conversationRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize speech recognition
  useEffect(() => {
    initializeSpeechRecognition();
  }, []);

  // Auto-scroll conversation
  useEffect(() => {
    if (conversationRef.current) {
      conversationRef.current.scrollTop = conversationRef.current.scrollHeight;
    }
  }, [conversation]);

  // Generate AI suggestions
  useEffect(() => {
    generateSuggestions();
  }, []);

  const generateSuggestions = async () => {
    const mockSuggestions: AISuggestion[] = [
      {
        id: 'suggestion_1',
        type: 'optimization',
        title: 'Optimize Wall Thickness',
        description: 'Reduce wall thickness by 15% while maintaining structural integrity',
        confidence: 0.92,
        impact: 'high',
        category: 'structural',
        timestamp: new Date(),
        status: 'pending',
        estimatedTime: 300,
        costSavings: 2500
      },
      {
        id: 'suggestion_2',
        type: 'design',
        title: 'Improve Electrical Layout',
        description: 'Reorganize electrical components for better efficiency and safety',
        confidence: 0.87,
        impact: 'medium',
        category: 'electrical',
        timestamp: new Date(),
        status: 'pending',
        estimatedTime: 180,
        costSavings: 1200
      },
      {
        id: 'suggestion_3',
        type: 'constraint',
        title: 'Add Geometric Constraints',
        description: 'Apply parallel and perpendicular constraints to improve design accuracy',
        confidence: 0.95,
        impact: 'high',
        category: 'geometric',
        timestamp: new Date(),
        status: 'pending',
        estimatedTime: 120,
        costSavings: 800
      }
    ];

    setSuggestions(mockSuggestions);
  };

  const handleSendMessage = async () => {
    if (!userInput.trim()) return;

    const userMessage: ConversationMessage = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: userInput,
      timestamp: new Date()
    };

    setConversation(prev => [...prev, userMessage]);
    setUserInput('');
    setIsProcessing(true);

    try {
      // Simulate AI response
      await new Promise(resolve => setTimeout(resolve, 1000));

      const aiResponse: ConversationMessage = {
        id: `ai_${Date.now()}`,
        type: 'ai',
        content: `I understand you're asking about "${userMessage.content}". Let me analyze your design and provide some suggestions.`,
        timestamp: new Date()
      };

      setConversation(prev => [...prev, aiResponse]);
      onConversationStart(userMessage.content);

      // Generate new suggestions based on conversation
      const newSuggestion: AISuggestion = {
        id: `suggestion_${Date.now()}`,
        type: 'analysis',
        title: 'Design Analysis Based on Query',
        description: `Analysis of your design based on: "${userMessage.content}"`,
        confidence: 0.85,
        impact: 'medium',
        category: 'analysis',
        timestamp: new Date(),
        status: 'pending'
      };

      setSuggestions(prev => [newSuggestion, ...prev]);

    } catch (error) {
      console.error('Failed to process message:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceInput = (transcript: string) => {
    setUserInput(transcript);
    setIsListening(false);
  };

  const handleSuggestionApply = async (suggestion: AISuggestion) => {
    setSelectedSuggestion(suggestion);
    setShowSuggestionDialog(true);
  };

  const confirmSuggestionApply = async () => {
    if (!selectedSuggestion) return;

    try {
      setIsProcessing(true);

      // Simulate applying suggestion
      await new Promise(resolve => setTimeout(resolve, 2000));

      setSuggestions(prev => prev.map(s =>
        s.id === selectedSuggestion.id
          ? { ...s, status: 'applied' as const }
          : s
      ));

      onSuggestionApply(selectedSuggestion);
      setShowSuggestionDialog(false);
      setSelectedSuggestion(null);

    } catch (error) {
      console.error('Failed to apply suggestion:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSuggestionReject = (suggestionId: string) => {
    setSuggestions(prev => prev.map(s =>
      s.id === suggestionId
        ? { ...s, status: 'rejected' as const }
        : s
    ));
    onSuggestionReject(suggestionId);
  };

  const runDesignAnalysis = async () => {
    try {
      setIsProcessing(true);

      const analysisResult = await onDesignAnalysis({});
      setAnalysis(prev => [analysisResult, ...prev]);

    } catch (error) {
      console.error('Failed to run design analysis:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'success';
    if (confidence >= 0.7) return 'warning';
    return 'error';
  };

  const initializeSpeechRecognition = () => {
    try {
      // Add proper type declarations for Speech Recognition API
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          const transcript = Array.from(event.results)
            .map((result: any) => result[0].transcript)
            .join('');

          if (event.results[0].isFinal) {
            handleVoiceInput(transcript);
          }
        };

        recognition.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
        };

        recognitionRef.current = recognition;
      } else {
        console.warn('Speech Recognition API not supported in this browser');
      }
    } catch (error) {
      console.error('Failed to initialize speech recognition:', error);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SmartToy color="primary" />
              AI Design Assistant
            </Typography>
            <Chip
              label={isProcessing ? 'Processing...' : 'Ready'}
              color={isProcessing ? 'warning' : 'success'}
              size="small"
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>AI Model</InputLabel>
              <Select
                value={aiModel}
                onChange={(e) => setAiModel(e.target.value)}
                label="AI Model"
              >
                <MenuItem value="gpt-4">GPT-4</MenuItem>
                <MenuItem value="gpt-3.5">GPT-3.5</MenuItem>
                <MenuItem value="claude">Claude</MenuItem>
              </Select>
            </FormControl>

            <TextField
              size="small"
              label="Temperature"
              type="number"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              inputProps={{ min: 0, max: 1, step: 0.1 }}
              sx={{ width: 100 }}
            />
          </Box>
        </Box>
      </Paper>

      {/* Content */}
      <Box sx={{ flex: 1, display: 'flex', gap: 2, overflow: 'hidden' }}>
        {/* Main AI Interface */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Tab Navigation */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant={activeTab === 'chat' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('chat')}
                startIcon={<Psychology />}
              >
                Chat
              </Button>
              <Button
                variant={activeTab === 'suggestions' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('suggestions')}
                startIcon={<Lightbulb />}
              >
                Suggestions
              </Button>
              <Button
                variant={activeTab === 'analysis' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('analysis')}
                startIcon={<Analytics />}
              >
                Analysis
              </Button>
              <Button
                variant={activeTab === 'automation' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('automation')}
                startIcon={<AutoFixHigh />}
              >
                Automation
              </Button>
            </Box>
          </Box>

          {/* Tab Content */}
          {activeTab === 'chat' && (
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* Conversation */}
              <Paper sx={{ p: 2, mb: 2, flex: 1, overflow: 'auto' }} ref={conversationRef}>
                <Typography variant="h6" gutterBottom>
                  AI Conversation
                </Typography>

                <List>
                  {conversation.map((message) => (
                    <ListItem key={message.id} sx={{
                      flexDirection: 'column',
                      alignItems: message.type === 'user' ? 'flex-end' : 'flex-start'
                    }}>
                      <Paper sx={{
                        p: 2,
                        maxWidth: '80%',
                        backgroundColor: message.type === 'user' ? 'primary.main' : 'grey.100',
                        color: message.type === 'user' ? 'white' : 'text.primary'
                      }}>
                        <Typography variant="body1">
                          {message.content}
                        </Typography>
                        <Typography variant="caption" sx={{ opacity: 0.7 }}>
                          {message.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Paper>
                    </ListItem>
                  ))}
                </List>

                {isProcessing && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
                    <CircularProgress size={20} />
                    <Typography variant="body2">AI is thinking...</Typography>
                  </Box>
                )}
              </Paper>

              {/* Input */}
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    ref={inputRef}
                    fullWidth
                    placeholder="Ask AI about your design..."
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    disabled={isProcessing}
                  />
                  <Tooltip title="Voice Input">
                    <IconButton
                      onClick={() => {
                        if (recognitionRef.current) {
                          recognitionRef.current.start();
                          setIsListening(true);
                        }
                      }}
                      color={isListening ? 'error' : 'primary'}
                    >
                      {isListening ? <MicOff /> : <Mic />}
                    </IconButton>
                  </Tooltip>
                  <Button
                    variant="contained"
                    onClick={handleSendMessage}
                    disabled={!userInput.trim() || isProcessing}
                    startIcon={<Send />}
                  >
                    Send
                  </Button>
                </Box>
              </Paper>
            </Box>
          )}

          {activeTab === 'suggestions' && (
            <Paper sx={{ p: 2, flex: 1, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                AI Suggestions
              </Typography>

              <List>
                {suggestions.map((suggestion) => (
                  <ListItem key={suggestion.id} sx={{ mb: 2 }}>
                    <Paper sx={{ p: 2, width: '100%' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="h6">
                          {suggestion.title}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Chip
                            label={suggestion.impact}
                            color={getImpactColor(suggestion.impact) as any}
                            size="small"
                          />
                          <Chip
                            label={`${(suggestion.confidence * 100).toFixed(0)}%`}
                            color={getConfidenceColor(suggestion.confidence) as any}
                            size="small"
                          />
                        </Box>
                      </Box>

                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {suggestion.description}
                      </Typography>

                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Chip label={suggestion.category} size="small" />
                          {suggestion.estimatedTime && (
                            <Chip label={`${suggestion.estimatedTime}s`} size="small" />
                          )}
                          {suggestion.costSavings && (
                            <Chip label={`$${suggestion.costSavings}`} size="small" color="success" />
                          )}
                        </Box>

                        <Box sx={{ display: 'flex', gap: 1 }}>
                          {suggestion.status === 'pending' && (
                            <>
                              <Button
                                size="small"
                                variant="contained"
                                onClick={() => handleSuggestionApply(suggestion)}
                                startIcon={<CheckCircle />}
                              >
                                Apply
                              </Button>
                              <Button
                                size="small"
                                variant="outlined"
                                onClick={() => handleSuggestionReject(suggestion.id)}
                                startIcon={<Error />}
                              >
                                Reject
                              </Button>
                            </>
                          )}
                          {suggestion.status === 'applied' && (
                            <Chip label="Applied" color="success" size="small" />
                          )}
                          {suggestion.status === 'rejected' && (
                            <Chip label="Rejected" color="error" size="small" />
                          )}
                        </Box>
                      </Box>
                    </Paper>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          {activeTab === 'analysis' && (
            <Paper sx={{ p: 2, flex: 1, overflow: 'auto' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Design Analysis
                </Typography>
                <Button
                  variant="contained"
                  onClick={runDesignAnalysis}
                  disabled={isProcessing}
                  startIcon={<Analytics />}
                >
                  Run Analysis
                </Button>
              </Box>

              <List>
                {analysis.map((item) => (
                  <ListItem key={item.id} sx={{ mb: 2 }}>
                    <Paper sx={{ p: 2, width: '100%' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                        <Typography variant="h6">
                          {item.title}
                        </Typography>
                        <Chip
                          label={item.riskLevel}
                          color={item.riskLevel === 'critical' ? 'error' :
                                 item.riskLevel === 'high' ? 'warning' : 'success'}
                          size="small"
                        />
                      </Box>

                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {item.summary}
                      </Typography>

                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Typography variant="subtitle2">Details & Recommendations</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Box>
                            <Typography variant="subtitle2" gutterBottom>Details:</Typography>
                            <List dense>
                              {item.details.map((detail, index) => (
                                <ListItem key={index}>
                                  <ListItemText primary={detail} />
                                </ListItem>
                              ))}
                            </List>

                            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                              Recommendations:
                            </Typography>
                            <List dense>
                              {item.recommendations.map((rec, index) => (
                                <ListItem key={index}>
                                  <ListItemText primary={rec} />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    </Paper>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}

          {activeTab === 'automation' && (
            <Paper sx={{ p: 2, flex: 1, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                AI Automation
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Design Optimization
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Automatically optimize your design for cost, performance, and manufacturability
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      startIcon={<TrendingUp />}
                    >
                      Run Optimization
                    </Button>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Constraint Generation
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Automatically generate geometric and dimensional constraints
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      startIcon={<Build />}
                    >
                      Generate Constraints
                    </Button>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Code Generation
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Generate code for automation and integration
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      startIcon={<Code />}
                    >
                      Generate Code
                    </Button>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      Documentation
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Automatically generate design documentation and reports
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      startIcon={<Settings />}
                    >
                      Generate Docs
                    </Button>
                  </Paper>
                </Grid>
              </Grid>
            </Paper>
          )}
        </Box>
      </Box>

      {/* Suggestion Dialog */}
      <Dialog
        open={showSuggestionDialog}
        onClose={() => setShowSuggestionDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Apply AI Suggestion
        </DialogTitle>
        <DialogContent>
          {selectedSuggestion && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedSuggestion.title}
              </Typography>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedSuggestion.description}
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Confidence</Typography>
                  <Typography variant="body2">
                    {(selectedSuggestion.confidence * 100).toFixed(1)}%
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Impact</Typography>
                  <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                    {selectedSuggestion.impact}
                  </Typography>
                </Grid>
                {selectedSuggestion.estimatedTime && (
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Estimated Time</Typography>
                    <Typography variant="body2">
                      {selectedSuggestion.estimatedTime} seconds
                    </Typography>
                  </Grid>
                )}
                {selectedSuggestion.costSavings && (
                  <Grid item xs={6}>
                    <Typography variant="subtitle2">Cost Savings</Typography>
                    <Typography variant="body2" color="success.main">
                      ${selectedSuggestion.costSavings}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSuggestionDialog(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={confirmSuggestionApply}
            disabled={isProcessing}
            startIcon={isProcessing ? <CircularProgress size={20} /> : <CheckCircle />}
          >
            {isProcessing ? 'Applying...' : 'Apply Suggestion'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
