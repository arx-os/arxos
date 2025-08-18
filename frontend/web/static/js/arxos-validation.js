/**
 * ArxOS Validation System
 * Handles field validation and confidence improvement
 */

class ValidationManager {
    constructor() {
        this.validationQueue = [];
        this.activeValidation = null;
        this.validationHistory = [];
        this.wsConnection = null;
        this.apiBaseUrl = window.location.origin + '/api/v1';
    }
    
    /**
     * Initialize validation system
     */
    async initialize() {
        // Set up WebSocket for real-time updates
        this.setupWebSocket();
        
        // Load pending validations
        await this.loadPendingValidations();
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    /**
     * Setup WebSocket connection for real-time updates
     */
    setupWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws/validation`;
        this.wsConnection = new WebSocket(wsUrl);
        
        this.wsConnection.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleValidationUpdate(data);
        };
        
        this.wsConnection.onerror = (error) => {
            console.error('WebSocket error:', error);
            // Attempt reconnection after 5 seconds
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }
    
    /**
     * Load pending validations from server
     */
    async loadPendingValidations() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/validations/pending`);
            const data = await response.json();
            this.validationQueue = data.validations || [];
            this.updateValidationUI();
        } catch (error) {
            console.error('Failed to load validations:', error);
        }
    }
    
    /**
     * Flag an object for validation
     */
    async flagForValidation(objectId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/validations/flag`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ object_id: objectId })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Object flagged for validation', 'success');
                this.validationQueue.push(result.validation);
                this.updateValidationUI();
            }
        } catch (error) {
            console.error('Failed to flag for validation:', error);
            this.showNotification('Failed to flag object', 'error');
        }
    }
    
    /**
     * Submit validation data
     */
    async submitValidation(validationData) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/validations/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(validationData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Show impact visualization
                this.visualizeValidationImpact(result.impact);
                
                // Update local state
                this.validationHistory.push(validationData);
                
                // Remove from queue
                this.validationQueue = this.validationQueue.filter(
                    v => v.object_id !== validationData.object_id
                );
                
                // Update UI
                this.updateValidationUI();
                
                // Show success
                this.showNotification(
                    `Validation improved ${result.impact.cascaded_count} objects!`, 
                    'success'
                );
            }
        } catch (error) {
            console.error('Failed to submit validation:', error);
            this.showNotification('Failed to submit validation', 'error');
        }
    }
    
    /**
     * Show validation tasks interface
     */
    showValidationTasks() {
        const modal = this.createValidationModal();
        document.body.appendChild(modal);
        
        // Load first task
        if (this.validationQueue.length > 0) {
            this.loadValidationTask(this.validationQueue[0]);
        }
    }
    
    /**
     * Create validation modal
     */
    createValidationModal() {
        const modal = document.createElement('div');
        modal.id = 'validation-modal';
        modal.className = 'validation-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Validation Tasks</h2>
                    <button class="close-btn" onclick="arxosValidation.closeValidationModal()">×</button>
                </div>
                
                <div class="validation-progress">
                    <div class="progress-info">
                        <span>Task <span id="current-task">1</span> of <span id="total-tasks">${this.validationQueue.length}</span></span>
                        <span class="points-earned">🏆 <span id="points">0</span> points earned</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%;"></div>
                    </div>
                </div>
                
                <div class="validation-content" id="validation-content">
                    <!-- Dynamic content loaded here -->
                </div>
                
                <div class="validation-actions">
                    <button class="btn-skip" onclick="arxosValidation.skipValidation()">
                        Skip
                    </button>
                    <button class="btn-submit" onclick="arxosValidation.submitCurrentValidation()">
                        Submit Validation
                    </button>
                </div>
            </div>
        `;
        
        return modal;
    }
    
    /**
     * Load a validation task
     */
    loadValidationTask(validation) {
        this.activeValidation = validation;
        
        const content = document.getElementById('validation-content');
        if (!content) return;
        
        content.innerHTML = `
            <div class="validation-task">
                <div class="object-info">
                    <h3>${validation.object_type}</h3>
                    <p>ID: ${validation.object_id}</p>
                    <div class="current-confidence">
                        Current Confidence: ${arxosConfidence.createConfidenceBadge(validation.confidence)}
                    </div>
                </div>
                
                <div class="validation-form">
                    ${this.createValidationForm(validation)}
                </div>
                
                <div class="validation-help">
                    <h4>💡 Validation Tips</h4>
                    <ul>
                        ${this.getValidationTips(validation.object_type)}
                    </ul>
                </div>
                
                <div class="similar-objects">
                    <h4>Similar Objects (${validation.similar_count || 0})</h4>
                    <p>Your validation will improve confidence for these similar objects too!</p>
                </div>
            </div>
        `;
        
        // Update progress
        this.updateProgress();
    }
    
    /**
     * Create validation form based on object type
     */
    createValidationForm(validation) {
        const objectType = validation.object_type;
        
        // Type-specific forms
        if (objectType === 'wall') {
            return `
                <div class="form-group">
                    <label>Wall Type</label>
                    <select id="val-wall-type">
                        <option value="">Select...</option>
                        <option value="exterior">Exterior</option>
                        <option value="interior">Interior</option>
                        <option value="partition">Partition</option>
                        <option value="fire">Fire-rated</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Measured Length (meters)</label>
                    <input type="number" id="val-length" step="0.01" placeholder="e.g., 5.25">
                </div>
                
                <div class="form-group">
                    <label>Wall Thickness (cm)</label>
                    <input type="number" id="val-thickness" step="1" placeholder="e.g., 15">
                </div>
                
                <div class="form-group">
                    <label>Material</label>
                    <select id="val-material">
                        <option value="">Select...</option>
                        <option value="drywall">Drywall</option>
                        <option value="concrete">Concrete</option>
                        <option value="brick">Brick</option>
                        <option value="glass">Glass</option>
                    </select>
                </div>
            `;
        } else if (objectType === 'door') {
            return `
                <div class="form-group">
                    <label>Door Type</label>
                    <select id="val-door-type">
                        <option value="">Select...</option>
                        <option value="single">Single</option>
                        <option value="double">Double</option>
                        <option value="sliding">Sliding</option>
                        <option value="revolving">Revolving</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Width (cm)</label>
                    <input type="number" id="val-width" step="1" placeholder="e.g., 90">
                </div>
                
                <div class="form-group">
                    <label>Fire Rating</label>
                    <select id="val-fire-rating">
                        <option value="">None</option>
                        <option value="20min">20 minutes</option>
                        <option value="1hour">1 hour</option>
                        <option value="2hour">2 hours</option>
                    </select>
                </div>
            `;
        } else if (objectType === 'room') {
            return `
                <div class="form-group">
                    <label>Room Type</label>
                    <select id="val-room-type">
                        <option value="">Select...</option>
                        <option value="office">Office</option>
                        <option value="conference">Conference</option>
                        <option value="restroom">Restroom</option>
                        <option value="kitchen">Kitchen</option>
                        <option value="storage">Storage</option>
                        <option value="mechanical">Mechanical</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Room Number/Name</label>
                    <input type="text" id="val-room-name" placeholder="e.g., 101 or Conference Room A">
                </div>
                
                <div class="form-group">
                    <label>Approximate Area (m²)</label>
                    <input type="number" id="val-area" step="0.1" placeholder="e.g., 25.5">
                </div>
                
                <div class="form-group">
                    <label>Occupancy Capacity</label>
                    <input type="number" id="val-occupancy" step="1" placeholder="e.g., 10">
                </div>
            `;
        } else {
            // Generic validation form
            return `
                <div class="form-group">
                    <label>Is the object type correct?</label>
                    <select id="val-type-correct">
                        <option value="yes">Yes</option>
                        <option value="no">No</option>
                    </select>
                </div>
                
                <div class="form-group" id="correct-type-group" style="display: none;">
                    <label>Correct Type</label>
                    <input type="text" id="val-correct-type" placeholder="Enter correct type">
                </div>
                
                <div class="form-group">
                    <label>Additional Notes</label>
                    <textarea id="val-notes" rows="3" placeholder="Any additional information..."></textarea>
                </div>
            `;
        }
    }
    
    /**
     * Get validation tips for object type
     */
    getValidationTips(objectType) {
        const tips = {
            wall: [
                'Measure from center to center of walls',
                'Check if wall extends to ceiling',
                'Note any openings (doors/windows)',
                'Identify load-bearing walls if possible'
            ],
            door: [
                'Measure clear opening width',
                'Check swing direction',
                'Note if fire-rated or emergency exit',
                'Verify accessibility compliance'
            ],
            room: [
                'Verify room number matches signage',
                'Count electrical outlets',
                'Note HVAC vents/returns',
                'Check for emergency exits'
            ],
            default: [
                'Take a photo for reference',
                'Measure key dimensions',
                'Note material and color',
                'Check connections to other objects'
            ]
        };
        
        const tipList = tips[objectType] || tips.default;
        return tipList.map(tip => `<li>${tip}</li>`).join('');
    }
    
    /**
     * Submit current validation
     */
    submitCurrentValidation() {
        if (!this.activeValidation) return;
        
        // Gather form data
        const formData = this.gatherValidationFormData();
        
        // Create validation submission
        const validationData = {
            object_id: this.activeValidation.object_id,
            validation_type: this.activeValidation.validation_type || 'manual',
            data: formData,
            validator: this.getCurrentUser(),
            confidence: 0.95, // High confidence for human validation
            timestamp: new Date().toISOString()
        };
        
        // Submit to server
        this.submitValidation(validationData);
        
        // Move to next task
        this.nextValidationTask();
    }
    
    /**
     * Gather validation form data
     */
    gatherValidationFormData() {
        const formData = {};
        
        // Get all form inputs
        document.querySelectorAll('#validation-content input, #validation-content select, #validation-content textarea').forEach(input => {
            if (input.id && input.id.startsWith('val-')) {
                const key = input.id.replace('val-', '');
                formData[key] = input.value;
            }
        });
        
        return formData;
    }
    
    /**
     * Skip current validation
     */
    skipValidation() {
        this.nextValidationTask();
    }
    
    /**
     * Move to next validation task
     */
    nextValidationTask() {
        // Remove current from queue
        if (this.activeValidation) {
            this.validationQueue = this.validationQueue.filter(
                v => v.object_id !== this.activeValidation.object_id
            );
        }
        
        // Load next task or close
        if (this.validationQueue.length > 0) {
            this.loadValidationTask(this.validationQueue[0]);
        } else {
            this.showCompletionMessage();
        }
    }
    
    /**
     * Update progress bar
     */
    updateProgress() {
        const total = this.validationQueue.length + this.validationHistory.length;
        const completed = this.validationHistory.length;
        const percentage = total > 0 ? (completed / total) * 100 : 0;
        
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        // Update task numbers
        document.getElementById('current-task').textContent = completed + 1;
        document.getElementById('total-tasks').textContent = total;
    }
    
    /**
     * Visualize validation impact
     */
    visualizeValidationImpact(impact) {
        // Create impact visualization
        const impactViz = document.createElement('div');
        impactViz.className = 'validation-impact';
        impactViz.innerHTML = `
            <div class="impact-animation">
                <div class="impact-center">
                    <div class="validated-object">✓</div>
                </div>
                <div class="impact-ripple"></div>
                <div class="cascaded-objects">
                    ${Array(impact.cascaded_count).fill('').map((_, i) => 
                        `<div class="cascaded-object" style="animation-delay: ${i * 0.1}s;">📦</div>`
                    ).join('')}
                </div>
            </div>
            
            <div class="impact-stats">
                <h3>Validation Impact</h3>
                <div class="stat">
                    <span class="stat-value">+${Math.round(impact.confidence_improvement * 100)}%</span>
                    <span class="stat-label">Confidence Improved</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${impact.cascaded_count}</span>
                    <span class="stat-label">Objects Updated</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${impact.time_saved || 0}</span>
                    <span class="stat-label">Minutes Saved</span>
                </div>
            </div>
        `;
        
        document.body.appendChild(impactViz);
        
        // Remove after animation
        setTimeout(() => {
            impactViz.remove();
        }, 5000);
    }
    
    /**
     * Show completion message
     */
    showCompletionMessage() {
        const content = document.getElementById('validation-content');
        if (!content) return;
        
        const totalValidated = this.validationHistory.length;
        const pointsEarned = totalValidated * 10; // Simple points system
        
        content.innerHTML = `
            <div class="completion-message">
                <div class="celebration">🎉</div>
                <h2>Great Work!</h2>
                <p>You've completed all validation tasks.</p>
                
                <div class="completion-stats">
                    <div class="stat">
                        <span class="stat-value">${totalValidated}</span>
                        <span class="stat-label">Objects Validated</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">${pointsEarned}</span>
                        <span class="stat-label">Points Earned</span>
                    </div>
                </div>
                
                <button class="btn-primary" onclick="arxosValidation.closeValidationModal()">
                    Done
                </button>
            </div>
        `;
    }
    
    /**
     * Close validation modal
     */
    closeValidationModal() {
        const modal = document.getElementById('validation-modal');
        if (modal) {
            modal.remove();
        }
    }
    
    /**
     * Handle real-time validation updates
     */
    handleValidationUpdate(data) {
        if (data.type === 'confidence_update') {
            // Update confidence visualization
            const element = document.querySelector(`[data-arxobject-id="${data.object_id}"]`);
            if (element && arxosConfidence) {
                arxosConfidence.animateConfidenceImprovement(
                    element, 
                    data.old_confidence, 
                    data.new_confidence
                );
            }
        } else if (data.type === 'pattern_learned') {
            this.showNotification(
                `Pattern learned! ${data.objects_improved} objects improved.`,
                'success'
            );
        }
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    /**
     * Get current user
     */
    getCurrentUser() {
        // In production, get from auth system
        return localStorage.getItem('arxos_user') || 'field_validator';
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for validation type changes
        document.addEventListener('change', (e) => {
            if (e.target.id === 'val-type-correct') {
                const correctTypeGroup = document.getElementById('correct-type-group');
                if (correctTypeGroup) {
                    correctTypeGroup.style.display = e.target.value === 'no' ? 'block' : 'none';
                }
            }
        });
    }
    
    /**
     * Export validation data
     */
    async exportValidationData() {
        const data = {
            validations: this.validationHistory,
            timestamp: new Date().toISOString(),
            validator: this.getCurrentUser()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `validations_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Initialize validation manager
const arxosValidation = new ValidationManager();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        arxosValidation.initialize();
    });
} else {
    arxosValidation.initialize();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ValidationManager;
}