/**
 * ArxOS Confidence Visualization System
 * Provides visual feedback for AI confidence scores
 */

class ConfidenceVisualizer {
    constructor() {
        this.confidenceThresholds = {
            high: 0.85,
            medium: 0.60,
            low: 0.60
        };
        
        this.confidenceColors = {
            high: '#10b981',    // Green
            medium: '#f59e0b',  // Yellow/Amber
            low: '#ef4444',     // Red
            unknown: '#9ca3af'  // Gray
        };
        
        this.confidenceIcons = {
            high: '✓',
            medium: '!',
            low: '?',
            unknown: '◯'
        };
    }
    
    /**
     * Get confidence level from score
     */
    getConfidenceLevel(score) {
        if (score >= this.confidenceThresholds.high) {
            return 'high';
        } else if (score >= this.confidenceThresholds.medium) {
            return 'medium';
        } else if (score > 0) {
            return 'low';
        } else {
            return 'unknown';
        }
    }
    
    /**
     * Get color for confidence score
     */
    getConfidenceColor(score) {
        const level = this.getConfidenceLevel(score);
        return this.confidenceColors[level];
    }
    
    /**
     * Get icon for confidence level
     */
    getConfidenceIcon(score) {
        const level = this.getConfidenceLevel(score);
        return this.confidenceIcons[level];
    }
    
    /**
     * Create confidence badge HTML
     */
    createConfidenceBadge(score, showDetails = false) {
        const level = this.getConfidenceLevel(score);
        const color = this.confidenceColors[level];
        const icon = this.confidenceIcons[level];
        const percentage = Math.round(score * 100);
        
        let badge = `
            <span class="confidence-badge confidence-${level}" 
                  style="background-color: ${color}15; color: ${color}; border: 1px solid ${color};"
                  data-confidence="${score}"
                  title="Confidence: ${percentage}%">
                <span class="confidence-icon">${icon}</span>
                <span class="confidence-value">${percentage}%</span>
            </span>
        `;
        
        if (showDetails) {
            badge += `
                <div class="confidence-details" style="display: none;">
                    <div class="confidence-breakdown">
                        <div>Classification: ${Math.round(score * 100)}%</div>
                        <div>Position: ${Math.round(score * 100)}%</div>
                        <div>Properties: ${Math.round(score * 100)}%</div>
                        <div>Relationships: ${Math.round(score * 100)}%</div>
                    </div>
                </div>
            `;
        }
        
        return badge;
    }
    
    /**
     * Create confidence indicator bar
     */
    createConfidenceBar(score, width = 200) {
        const percentage = Math.round(score * 100);
        const color = this.getConfidenceColor(score);
        
        return `
            <div class="confidence-bar" style="width: ${width}px;">
                <div class="confidence-bar-bg" style="background: #e5e7eb;">
                    <div class="confidence-bar-fill" 
                         style="width: ${percentage}%; background: ${color}; height: 8px; transition: width 0.3s;">
                    </div>
                </div>
                <span class="confidence-bar-label" style="color: ${color};">
                    ${percentage}%
                </span>
            </div>
        `;
    }
    
    /**
     * Apply confidence styling to ArxObject element
     */
    styleArxObjectElement(element, arxObject) {
        if (!arxObject.confidence) {
            return;
        }
        
        const score = arxObject.confidence.overall || 0;
        const color = this.getConfidenceColor(score);
        const level = this.getConfidenceLevel(score);
        
        // Add confidence class
        element.classList.add(`confidence-${level}`);
        
        // Apply visual styling based on confidence
        if (level === 'low') {
            // Low confidence - dashed border, semi-transparent
            element.style.borderStyle = 'dashed';
            element.style.opacity = '0.7';
            element.style.borderColor = color;
        } else if (level === 'medium') {
            // Medium confidence - dotted border
            element.style.borderStyle = 'dotted';
            element.style.opacity = '0.85';
            element.style.borderColor = color;
        } else if (level === 'high') {
            // High confidence - solid border
            element.style.borderStyle = 'solid';
            element.style.opacity = '1';
            element.style.borderColor = color;
        }
        
        // Add data attributes
        element.dataset.confidence = score;
        element.dataset.confidenceLevel = level;
        
        // Add hover effect
        element.addEventListener('mouseenter', () => {
            this.showConfidenceTooltip(element, arxObject);
        });
        
        element.addEventListener('mouseleave', () => {
            this.hideConfidenceTooltip();
        });
    }
    
    /**
     * Show confidence tooltip on hover
     */
    showConfidenceTooltip(element, arxObject) {
        // Remove existing tooltip
        this.hideConfidenceTooltip();
        
        const conf = arxObject.confidence;
        const tooltip = document.createElement('div');
        tooltip.id = 'confidence-tooltip';
        tooltip.className = 'confidence-tooltip';
        tooltip.innerHTML = `
            <div class="tooltip-header">
                <strong>${arxObject.type}</strong>
                ${this.createConfidenceBadge(conf.overall)}
            </div>
            <div class="tooltip-body">
                <div class="confidence-metric">
                    <span>Classification:</span>
                    ${this.createConfidenceBar(conf.classification, 100)}
                </div>
                <div class="confidence-metric">
                    <span>Position:</span>
                    ${this.createConfidenceBar(conf.position, 100)}
                </div>
                <div class="confidence-metric">
                    <span>Properties:</span>
                    ${this.createConfidenceBar(conf.properties, 100)}
                </div>
                <div class="confidence-metric">
                    <span>Relationships:</span>
                    ${this.createConfidenceBar(conf.relationships, 100)}
                </div>
            </div>
            ${conf.overall < 0.6 ? `
                <div class="tooltip-action">
                    <button onclick="arxosValidation.flagForValidation('${arxObject.id}')">
                        🎯 Validate This Object
                    </button>
                </div>
            ` : ''}
        `;
        
        // Position tooltip near element
        const rect = element.getBoundingClientRect();
        tooltip.style.position = 'fixed';
        tooltip.style.left = `${rect.right + 10}px`;
        tooltip.style.top = `${rect.top}px`;
        tooltip.style.zIndex = '10000';
        
        document.body.appendChild(tooltip);
    }
    
    /**
     * Hide confidence tooltip
     */
    hideConfidenceTooltip() {
        const tooltip = document.getElementById('confidence-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }
    
    /**
     * Create confidence legend
     */
    createConfidenceLegend() {
        return `
            <div class="confidence-legend">
                <h4>Confidence Levels</h4>
                <div class="legend-item">
                    <span class="legend-color" style="background: ${this.confidenceColors.high};"></span>
                    <span>High (≥85%)</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background: ${this.confidenceColors.medium};"></span>
                    <span>Medium (60-84%)</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background: ${this.confidenceColors.low};"></span>
                    <span>Low (<60%)</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Render confidence overview panel
     */
    renderConfidenceOverview(arxObjects) {
        const stats = this.calculateConfidenceStats(arxObjects);
        
        return `
            <div class="confidence-overview">
                <h3>Extraction Confidence</h3>
                <div class="overall-confidence">
                    <div class="big-number" style="color: ${this.getConfidenceColor(stats.overall)};">
                        ${Math.round(stats.overall * 100)}%
                    </div>
                    <div class="label">Overall Confidence</div>
                </div>
                
                <div class="confidence-distribution">
                    <div class="dist-bar">
                        <div class="dist-segment high" 
                             style="width: ${stats.distribution.high}%; background: ${this.confidenceColors.high};"
                             title="${stats.counts.high} objects">
                        </div>
                        <div class="dist-segment medium" 
                             style="width: ${stats.distribution.medium}%; background: ${this.confidenceColors.medium};"
                             title="${stats.counts.medium} objects">
                        </div>
                        <div class="dist-segment low" 
                             style="width: ${stats.distribution.low}%; background: ${this.confidenceColors.low};"
                             title="${stats.counts.low} objects">
                        </div>
                    </div>
                </div>
                
                <div class="confidence-stats">
                    <div class="stat">
                        <span class="stat-value">${stats.counts.high}</span>
                        <span class="stat-label">High Confidence</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">${stats.counts.medium}</span>
                        <span class="stat-label">Medium Confidence</span>
                    </div>
                    <div class="stat">
                        <span class="stat-value">${stats.counts.low}</span>
                        <span class="stat-label">Need Validation</span>
                    </div>
                </div>
                
                ${stats.counts.low > 0 ? `
                    <div class="validation-prompt">
                        <p>📍 ${stats.counts.low} objects need validation</p>
                        <button onclick="arxosValidation.showValidationTasks()">
                            Start Validation
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Calculate confidence statistics
     */
    calculateConfidenceStats(arxObjects) {
        let counts = { high: 0, medium: 0, low: 0, unknown: 0 };
        let totalConfidence = 0;
        let validObjects = 0;
        
        arxObjects.forEach(obj => {
            if (obj.confidence && obj.confidence.overall !== undefined) {
                const level = this.getConfidenceLevel(obj.confidence.overall);
                counts[level]++;
                totalConfidence += obj.confidence.overall;
                validObjects++;
            } else {
                counts.unknown++;
            }
        });
        
        const total = arxObjects.length;
        
        return {
            overall: validObjects > 0 ? totalConfidence / validObjects : 0,
            counts: counts,
            distribution: {
                high: total > 0 ? (counts.high / total) * 100 : 0,
                medium: total > 0 ? (counts.medium / total) * 100 : 0,
                low: total > 0 ? (counts.low / total) * 100 : 0,
                unknown: total > 0 ? (counts.unknown / total) * 100 : 0
            },
            total: total,
            needsValidation: counts.low + counts.unknown
        };
    }
    
    /**
     * Animate confidence improvement
     */
    animateConfidenceImprovement(element, oldScore, newScore) {
        const startColor = this.getConfidenceColor(oldScore);
        const endColor = this.getConfidenceColor(newScore);
        
        // Create improvement indicator
        const indicator = document.createElement('div');
        indicator.className = 'confidence-improvement';
        indicator.innerHTML = `
            <span class="improvement-value">
                +${Math.round((newScore - oldScore) * 100)}%
            </span>
        `;
        indicator.style.color = endColor;
        
        element.appendChild(indicator);
        
        // Animate the improvement
        element.style.transition = 'all 0.5s ease';
        element.style.borderColor = endColor;
        
        // Update confidence attributes
        element.dataset.confidence = newScore;
        element.dataset.confidenceLevel = this.getConfidenceLevel(newScore);
        
        // Remove indicator after animation
        setTimeout(() => {
            indicator.remove();
        }, 2000);
    }
    
    /**
     * Highlight low confidence objects
     */
    highlightLowConfidence(arxObjects) {
        const lowConfidenceObjects = arxObjects.filter(obj => 
            obj.confidence && obj.confidence.overall < this.confidenceThresholds.medium
        );
        
        lowConfidenceObjects.forEach(obj => {
            const element = document.querySelector(`[data-arxobject-id="${obj.id}"]`);
            if (element) {
                element.classList.add('needs-validation');
                element.style.animation = 'pulse 2s infinite';
            }
        });
        
        return lowConfidenceObjects;
    }
    
    /**
     * Create confidence filter controls
     */
    createConfidenceFilter() {
        return `
            <div class="confidence-filter">
                <label>Show Objects:</label>
                <div class="filter-options">
                    <label>
                        <input type="checkbox" name="confidence-filter" value="high" checked>
                        <span style="color: ${this.confidenceColors.high};">High</span>
                    </label>
                    <label>
                        <input type="checkbox" name="confidence-filter" value="medium" checked>
                        <span style="color: ${this.confidenceColors.medium};">Medium</span>
                    </label>
                    <label>
                        <input type="checkbox" name="confidence-filter" value="low" checked>
                        <span style="color: ${this.confidenceColors.low};">Low</span>
                    </label>
                </div>
            </div>
        `;
    }
    
    /**
     * Apply confidence filter
     */
    applyConfidenceFilter(selectedLevels) {
        document.querySelectorAll('[data-confidence-level]').forEach(element => {
            const level = element.dataset.confidenceLevel;
            if (selectedLevels.includes(level)) {
                element.style.display = '';
            } else {
                element.style.display = 'none';
            }
        });
    }
}

// Initialize confidence visualizer
const arxosConfidence = new ConfidenceVisualizer();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConfidenceVisualizer;
}