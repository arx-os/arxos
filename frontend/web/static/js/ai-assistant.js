/**
 * Arxos AI Assistant - GUS Integration
 * Handles natural language CAD commands and intelligent building design
 *
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class AiAssistant {
    constructor() {
        this.isInitialized = false;
        this.conversationHistory = [];
        this.currentContext = null;

        // AI capabilities
        this.capabilities = {
            createObjects: true,
            modifyObjects: true,
            analyzeDesign: true,
            suggestImprovements: true,
            codeCompliance: true,
            optimization: true
        };

        // Command patterns
        this.commandPatterns = {
            create: /create|add|draw|place|insert/i,
            modify: /modify|change|update|edit|move|resize/i,
            delete: /delete|remove|erase/i,
            analyze: /analyze|check|verify|validate/i,
            suggest: /suggest|recommend|improve|optimize/i
        };

        // Object types mapping
        this.objectTypes = {
            room: ['room', 'space', 'area', 'chamber'],
            wall: ['wall', 'partition', 'divider'],
            door: ['door', 'entrance', 'exit', 'opening'],
            window: ['window', 'opening', 'glazing'],
            electrical_outlet: ['outlet', 'socket', 'plug', 'receptacle'],
            light_fixture: ['light', 'fixture', 'lamp', 'luminaire'],
            hvac_register: ['register', 'vent', 'duct', 'hvac'],
            plumbing_fixture: ['fixture', 'sink', 'toilet', 'shower']
        };

        // Initialize AI assistant
        this.initialize();
    }

    /**
     * Initialize AI assistant
     */
    async initialize() {
        try {
            console.log('Initializing Arxos AI Assistant...');

            // Initialize conversation history
            this.conversationHistory = [];

            // Set initial context
            this.currentContext = {
                project: 'Arxos Building Project',
                user: 'Building Designer',
                mode: 'design',
                focus: 'general'
            };

            this.isInitialized = true;
            console.log('Arxos AI Assistant initialized successfully');

        } catch (error) {
            console.error('Failed to initialize AI Assistant:', error);
            throw error;
        }
    }

    /**
     * Process user message
     */
    async processMessage(message, arxObjectSystem) {
        try {
            console.log('Processing AI message:', message);

            // Add to conversation history
            this.conversationHistory.push({
                role: 'user',
                content: message,
                timestamp: Date.now()
            });

            // Parse message intent
            const intent = this.parseIntent(message);

            // Generate response based on intent
            let response;
            switch (intent.type) {
                case 'create':
                    response = await this.handleCreateCommand(message, intent, arxObjectSystem);
                    break;
                case 'modify':
                    response = await this.handleModifyCommand(message, intent, arxObjectSystem);
                    break;
                case 'delete':
                    response = await this.handleDeleteCommand(message, intent, arxObjectSystem);
                    break;
                case 'analyze':
                    response = await this.handleAnalyzeCommand(message, intent, arxObjectSystem);
                    break;
                case 'suggest':
                    response = await this.handleSuggestCommand(message, intent, arxObjectSystem);
                    break;
                case 'query':
                    response = await this.handleQueryCommand(message, intent, arxObjectSystem);
                    break;
                default:
                    response = await this.handleGeneralCommand(message, arxObjectSystem);
            }

            // Add response to conversation history
            this.conversationHistory.push({
                role: 'assistant',
                content: response,
                timestamp: Date.now()
            });

            return response;

        } catch (error) {
            console.error('Error processing AI message:', error);
            return 'I encountered an error processing your request. Please try again.';
        }
    }

    /**
     * Parse message intent
     */
    parseIntent(message) {
        const lowerMessage = message.toLowerCase();

        // Check for command patterns
        for (const [command, pattern] of Object.entries(this.commandPatterns)) {
            if (pattern.test(lowerMessage)) {
                return {
                    type: command,
                    confidence: 0.8,
                    message: lowerMessage
                };
            }
        }

        // Check for object types
        for (const [objectType, keywords] of Object.entries(this.objectTypes)) {
            for (const keyword of keywords) {
                if (lowerMessage.includes(keyword)) {
                    return {
                        type: 'create',
                        objectType: objectType,
                        confidence: 0.7,
                        message: lowerMessage
                    };
                }
            }
        }

        // Default to query
        return {
            type: 'query',
            confidence: 0.5,
            message: lowerMessage
        };
    }

    /**
     * Handle create commands
     */
    async handleCreateCommand(message, intent, arxObjectSystem) {
        const objectType = intent.objectType || this.extractObjectType(message);

        if (!objectType) {
            return "I'm not sure what type of object you want to create. Please specify (e.g., 'create a room', 'add a door', 'place a window').";
        }

        // Extract dimensions from message
        const dimensions = this.extractDimensions(message);

        // Extract properties from message
        const properties = this.extractProperties(message, objectType);

        // Create ArxObject
        const geometry = this.generateGeometry(objectType, dimensions);
        const arxObject = arxObjectSystem.createArxObject(objectType, geometry, properties);

        return `I've created a ${objectType} with the specified properties. The object has been added to your drawing with ID: ${arxObject.id}`;
    }

    /**
     * Handle modify commands
     */
    async handleModifyCommand(message, intent, arxObjectSystem) {
        // Extract object identifier
        const objectId = this.extractObjectId(message);

        if (!objectId) {
            return "I need to know which object you want to modify. Please select an object or specify its ID.";
        }

        // Extract new properties
        const newProperties = this.extractProperties(message);

        // Update ArxObject
        const arxObject = arxObjectSystem.getArxObject(objectId);
        if (!arxObject) {
            return "I couldn't find the specified object. Please check the object ID and try again.";
        }

        arxObjectSystem.updateArxObject(objectId, { properties: newProperties });

        return `I've updated the ${arxObject.type} with the new properties.`;
    }

    /**
     * Handle delete commands
     */
    async handleDeleteCommand(message, intent, arxObjectSystem) {
        // Extract object identifier
        const objectId = this.extractObjectId(message);

        if (!objectId) {
            return "I need to know which object you want to delete. Please select an object or specify its ID.";
        }

        // Delete ArxObject
        const arxObject = arxObjectSystem.getArxObject(objectId);
        if (!arxObject) {
            return "I couldn't find the specified object. Please check the object ID and try again.";
        }

        arxObjectSystem.deleteArxObject(objectId);

        return `I've deleted the ${arxObject.type} from your drawing.`;
    }

    /**
     * Handle analyze commands
     */
    async handleAnalyzeCommand(message, intent, arxObjectSystem) {
        const analysis = this.analyzeDesign(arxObjectSystem);

        let response = "Here's my analysis of your current design:\n\n";

        // Add statistics
        const stats = arxObjectSystem.getStatistics();
        response += `📊 **Design Statistics:**\n`;
        response += `- Total Objects: ${stats.totalObjects}\n`;
        response += `- Total Area: ${(stats.totalArea / 144).toFixed(1)} sq ft\n`;
        response += `- Total Volume: ${(stats.totalVolume / 1728).toFixed(1)} cu ft\n\n`;

        // Add object breakdown
        response += `🏗️ **Object Breakdown:**\n`;
        for (const [type, count] of Object.entries(stats.objectsByType)) {
            response += `- ${type}: ${count}\n`;
        }

        // Add recommendations
        if (analysis.recommendations.length > 0) {
            response += `\n💡 **Recommendations:**\n`;
            for (const recommendation of analysis.recommendations) {
                response += `- ${recommendation}\n`;
            }
        }

        return response;
    }

    /**
     * Handle suggest commands
     */
    async handleSuggestCommand(message, intent, arxObjectSystem) {
        const suggestions = this.generateSuggestions(arxObjectSystem);

        let response = "Here are my suggestions for improving your design:\n\n";

        for (const suggestion of suggestions) {
            response += `💡 ${suggestion}\n`;
        }

        return response;
    }

    /**
     * Handle query commands
     */
    async handleQueryCommand(message, intent, arxObjectSystem) {
        // Handle general questions about the design
        if (message.toLowerCase().includes('how many')) {
            return this.answerQuantityQuery(message, arxObjectSystem);
        } else if (message.toLowerCase().includes('what is') || message.toLowerCase().includes('tell me about')) {
            return this.answerInformationQuery(message, arxObjectSystem);
        } else {
            return this.answerGeneralQuery(message, arxObjectSystem);
        }
    }

    /**
     * Handle general commands
     */
    async handleGeneralCommand(message, arxObjectSystem) {
        return "I'm here to help you with your building design! You can ask me to:\n\n" +
               "• Create objects (e.g., 'create a 20x30 room')\n" +
               "• Modify objects (e.g., 'make the door wider')\n" +
               "• Analyze your design (e.g., 'analyze the current design')\n" +
               "• Get suggestions (e.g., 'suggest improvements')\n" +
               "• Ask questions (e.g., 'how many doors are there?')\n\n" +
               "What would you like to do?";
    }

    /**
     * Extract object type from message
     */
    extractObjectType(message) {
        const lowerMessage = message.toLowerCase();

        for (const [objectType, keywords] of Object.entries(this.objectTypes)) {
            for (const keyword of keywords) {
                if (lowerMessage.includes(keyword)) {
                    return objectType;
                }
            }
        }

        return null;
    }

    /**
     * Extract dimensions from message
     */
    extractDimensions(message) {
        const dimensions = {};

        // Extract width x height patterns
        const widthHeightPattern = /(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)/i;
        const match = message.match(widthHeightPattern);
        if (match) {
            dimensions.width = parseFloat(match[1]);
            dimensions.height = parseFloat(match[2]);
        }

        // Extract individual dimensions
        const widthPattern = /(\d+(?:\.\d+)?)\s*(?:inch|in|")?\s*(?:wide|width)/i;
        const widthMatch = message.match(widthPattern);
        if (widthMatch) {
            dimensions.width = parseFloat(widthMatch[1]);
        }

        const heightPattern = /(\d+(?:\.\d+)?)\s*(?:inch|in|")?\s*(?:tall|height|high)/i;
        const heightMatch = message.match(heightPattern);
        if (heightMatch) {
            dimensions.height = parseFloat(heightMatch[1]);
        }

        const lengthPattern = /(\d+(?:\.\d+)?)\s*(?:inch|in|")?\s*(?:long|length)/i;
        const lengthMatch = message.match(lengthPattern);
        if (lengthMatch) {
            dimensions.length = parseFloat(lengthMatch[1]);
        }

        return dimensions;
    }

    /**
     * Extract properties from message
     */
    extractProperties(message, objectType = null) {
        const properties = {};
        const lowerMessage = message.toLowerCase();

        // Extract material
        const materialPattern = /(wood|metal|plastic|glass|concrete|drywall|steel|aluminum)/i;
        const materialMatch = message.match(materialPattern);
        if (materialMatch) {
            properties.material = materialMatch[1].toLowerCase();
        }

        // Extract type
        const typePattern = /(swing|sliding|pocket|folding|fixed|operable)/i;
        const typeMatch = message.match(typePattern);
        if (typeMatch) {
            properties.type = typeMatch[1].toLowerCase();
        }

        // Extract color
        const colorPattern = /(white|black|gray|brown|blue|red|green|yellow)/i;
        const colorMatch = message.match(colorPattern);
        if (colorMatch) {
            properties.color = colorMatch[1].toLowerCase();
        }

        // Extract voltage for electrical
        if (objectType === 'electrical_outlet') {
            const voltagePattern = /(\d+)\s*volt/i;
            const voltageMatch = message.match(voltagePattern);
            if (voltageMatch) {
                properties.voltage = parseInt(voltageMatch[1]);
            }
        }

        return properties;
    }

    /**
     * Extract object ID from message
     */
    extractObjectId(message) {
        // Look for ArxObject ID pattern
        const idPattern = /arx_[a-zA-Z0-9_]+/;
        const match = message.match(idPattern);
        return match ? match[0] : null;
    }

    /**
     * Generate geometry for object type
     */
    generateGeometry(objectType, dimensions) {
        const defaultDimensions = {
            room: { width: 240, height: 180 }, // 20' x 15'
            wall: { length: 120, height: 96 }, // 10' x 8'
            door: { width: 36, height: 80 }, // 3' x 6'8"
            window: { width: 36, height: 48 }, // 3' x 4'
            electrical_outlet: { width: 4, height: 4 },
            light_fixture: { width: 12, height: 12 }
        };

        const dims = { ...defaultDimensions[objectType], ...dimensions };

        switch (objectType) {
            case 'room':
            case 'wall':
            case 'door':
            case 'window':
                return {
                    type: 'rectangle',
                    startPoint: { x: 0, y: 0 },
                    endPoint: { x: dims.width, y: dims.height }
                };

            case 'electrical_outlet':
            case 'light_fixture':
                return {
                    type: 'circle',
                    center: { x: 0, y: 0 },
                    radius: dims.width / 2
                };

            default:
                return {
                    type: 'rectangle',
                    startPoint: { x: 0, y: 0 },
                    endPoint: { x: 100, y: 100 }
                };
        }
    }

    /**
     * Analyze design
     */
    analyzeDesign(arxObjectSystem) {
        const analysis = {
            statistics: arxObjectSystem.getStatistics(),
            recommendations: [],
            issues: [],
            strengths: []
        };

        const stats = analysis.statistics;

        // Check for common issues
        if (stats.totalObjects === 0) {
            analysis.recommendations.push("Start by creating some basic building elements like walls and rooms.");
        }

        if (stats.objectsByType.room && stats.objectsByType.room < 2) {
            analysis.recommendations.push("Consider adding more rooms to create a functional layout.");
        }

        if (stats.objectsByType.door && stats.objectsByType.door < 1) {
            analysis.recommendations.push("Add doors to provide access between rooms.");
        }

        if (stats.objectsByType.window && stats.objectsByType.window < 1) {
            analysis.recommendations.push("Consider adding windows for natural light and ventilation.");
        }

        // Check for strengths
        if (stats.totalArea > 1000) {
            analysis.strengths.push("Good use of space with substantial area coverage.");
        }

        if (stats.objectsByType.electrical_outlet && stats.objectsByType.electrical_outlet > 2) {
            analysis.strengths.push("Good electrical outlet distribution.");
        }

        return analysis;
    }

    /**
     * Generate suggestions
     */
    generateSuggestions(arxObjectSystem) {
        const suggestions = [];
        const stats = arxObjectSystem.getStatistics();

        // Space optimization suggestions
        if (stats.totalArea < 500) {
            suggestions.push("Consider expanding the design to create more functional spaces.");
        }

        // Accessibility suggestions
        if (!stats.objectsByType.door || stats.objectsByType.door < 2) {
            suggestions.push("Add more doors to improve accessibility and flow between spaces.");
        }

        // Lighting suggestions
        if (!stats.objectsByType.light_fixture || stats.objectsByType.light_fixture < 3) {
            suggestions.push("Add more lighting fixtures to ensure adequate illumination throughout the space.");
        }

        // Electrical suggestions
        if (!stats.objectsByType.electrical_outlet || stats.objectsByType.electrical_outlet < 4) {
            suggestions.push("Add more electrical outlets to meet modern power requirements.");
        }

        // HVAC suggestions
        if (!stats.objectsByType.hvac_register) {
            suggestions.push("Consider adding HVAC registers for proper climate control.");
        }

        return suggestions;
    }

    /**
     * Answer quantity queries
     */
    answerQuantityQuery(message, arxObjectSystem) {
        const stats = arxObjectSystem.getStatistics();
        const lowerMessage = message.toLowerCase();

        if (lowerMessage.includes('room')) {
            return `There are ${stats.objectsByType.room || 0} rooms in the design.`;
        } else if (lowerMessage.includes('door')) {
            return `There are ${stats.objectsByType.door || 0} doors in the design.`;
        } else if (lowerMessage.includes('window')) {
            return `There are ${stats.objectsByType.window || 0} windows in the design.`;
        } else if (lowerMessage.includes('outlet')) {
            return `There are ${stats.objectsByType.electrical_outlet || 0} electrical outlets in the design.`;
        } else if (lowerMessage.includes('light')) {
            return `There are ${stats.objectsByType.light_fixture || 0} light fixtures in the design.`;
        } else {
            return `There are ${stats.totalObjects} total objects in the design.`;
        }
    }

    /**
     * Answer information queries
     */
    answerInformationQuery(message, arxObjectSystem) {
        const lowerMessage = message.toLowerCase();

        if (lowerMessage.includes('area')) {
            const stats = arxObjectSystem.getStatistics();
            return `The total area is ${(stats.totalArea / 144).toFixed(1)} square feet.`;
        } else if (lowerMessage.includes('volume')) {
            const stats = arxObjectSystem.getStatistics();
            return `The total volume is ${(stats.totalVolume / 1728).toFixed(1)} cubic feet.`;
        } else {
            return "I can provide information about area, volume, object counts, and design statistics. What specific information would you like to know?";
        }
    }

    /**
     * Answer general queries
     */
    answerGeneralQuery(message, arxObjectSystem) {
        return "I'm here to help you with your building design! You can ask me about object counts, areas, volumes, or request design analysis and suggestions.";
    }

    /**
     * Get conversation history
     */
    getConversationHistory() {
        return this.conversationHistory;
    }

    /**
     * Clear conversation history
     */
    clearConversationHistory() {
        this.conversationHistory = [];
    }

    /**
     * Update context
     */
    updateContext(newContext) {
        this.currentContext = { ...this.currentContext, ...newContext };
    }
}

// Export for global use
window.AiAssistant = AiAssistant;
