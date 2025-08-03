/**
 * Hover Module
 * Handles hover effects, tooltips, and visual feedback
 */

export class Hover {
    constructor(viewportManager, options = {}) {
        this.viewportManager = viewportManager;
        
        // Hover state
        this.hoveredObject = null;
        this.hoverTimeout = null;
        this.hoverDelay = options.hoverDelay || 200; // ms before showing tooltip
        
        // Tooltip
        this.tooltip = null;
        this.tooltipEnabled = options.tooltipEnabled !== false;
        this.tooltipContent = null;
        
        // Hover effects
        this.hoverEffectsEnabled = options.hoverEffectsEnabled !== false;
        this.hoverHighlightClass = options.hoverHighlightClass || 'hover-highlight';
        
        // Performance optimizations
        this.hoverThrottleDelay = options.hoverThrottleDelay || 16; // ~60fps
        this.lastHoverUpdate = 0;
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.createTooltip();
    }

    setupEventListeners() {
        if (!this.viewportManager || !this.viewportManager.svg) return;
        
        const svg = this.viewportManager.svg;
        
        // Mouse events for hover
        svg.addEventListener('mouseover', (e) => this.handleMouseOver(e));
        svg.addEventListener('mouseout', (e) => this.handleMouseOut(e));
        svg.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        
        // Global mouse events
        document.addEventListener('mouseover', (e) => this.handleGlobalMouseOver(e));
        document.addEventListener('mouseout', (e) => this.handleGlobalMouseOut(e));
    }

    handleMouseOver(event) {
        const target = this.findHoverableObject(event.target);
        if (!target) return;
        
        this.startHover(target, event);
    }

    handleMouseOut(event) {
        const target = this.findHoverableObject(event.target);
        if (!target) return;
        
        this.endHover(target, event);
    }

    handleMouseMove(event) {
        if (!this.hoveredObject) return;
        
        // Throttle hover updates for performance
        const currentTime = performance.now();
        if (currentTime - this.lastHoverUpdate < this.hoverThrottleDelay) {
            return;
        }
        
        this.lastHoverUpdate = currentTime;
        this.updateTooltipPosition(event);
    }

    handleGlobalMouseOver(event) {
        // Handle hover for elements outside the SVG
        const target = this.findHoverableObject(event.target);
        if (target && target !== this.hoveredObject) {
            this.startHover(target, event);
        }
    }

    handleGlobalMouseOut(event) {
        // Handle mouse out for elements outside the SVG
        const target = this.findHoverableObject(event.target);
        if (target && target === this.hoveredObject) {
            this.endHover(target, event);
        }
    }

    // Hover control methods
    startHover(target, event) {
        if (this.hoveredObject === target) return;
        
        // End previous hover
        if (this.hoveredObject) {
            this.endHover(this.hoveredObject, event);
        }
        
        this.hoveredObject = target;
        
        // Add hover visual effects
        this.addHoverEffects(target);
        
        // Show tooltip after delay
        if (this.tooltipEnabled) {
            this.scheduleTooltip(target, event);
        }
        
        this.triggerEvent('hoverStarted', { target, event });
    }

    endHover(target, event) {
        if (this.hoveredObject !== target) return;
        
        this.hoveredObject = null;
        
        // Remove hover visual effects
        this.removeHoverEffects(target);
        
        // Hide tooltip
        this.hideTooltip();
        
        // Clear hover timeout
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
            this.hoverTimeout = null;
        }
        
        this.triggerEvent('hoverEnded', { target, event });
    }

    // Tooltip methods
    scheduleTooltip(target, event) {
        // Clear existing timeout
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
        }
        
        // Schedule new tooltip
        this.hoverTimeout = setTimeout(() => {
            this.showTooltip(target, event);
        }, this.hoverDelay);
    }

    showTooltip(target, event) {
        if (!this.tooltip || !this.tooltipEnabled) return;
        
        const tooltipContent = this.getTooltipContent(target);
        if (!tooltipContent) return;
        
        this.tooltip.innerHTML = tooltipContent;
        this.tooltip.style.display = 'block';
        
        this.updateTooltipPosition(event);
        
        this.triggerEvent('tooltipShown', { target, content: tooltipContent });
    }

    hideTooltip() {
        if (!this.tooltip) return;
        
        this.tooltip.style.display = 'none';
        this.triggerEvent('tooltipHidden');
    }

    updateTooltipPosition(event) {
        if (!this.tooltip || this.tooltip.style.display === 'none') return;
        
        const offset = 10; // pixels from cursor
        const x = event.clientX + offset;
        const y = event.clientY + offset;
        
        // Ensure tooltip stays within viewport
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let finalX = x;
        let finalY = y;
        
        // Adjust horizontal position if tooltip would go off-screen
        if (x + tooltipRect.width > viewportWidth) {
            finalX = event.clientX - tooltipRect.width - offset;
        }
        
        // Adjust vertical position if tooltip would go off-screen
        if (y + tooltipRect.height > viewportHeight) {
            finalY = event.clientY - tooltipRect.height - offset;
        }
        
        this.tooltip.style.left = `${finalX}px`;
        this.tooltip.style.top = `${finalY}px`;
    }

    getTooltipContent(target) {
        if (!target) return null;
        
        // Get tooltip content from data attributes
        const tooltipText = target.getAttribute('data-tooltip');
        if (tooltipText) {
            return tooltipText;
        }
        
        // Generate tooltip content based on object type
        const objectType = target.getAttribute('data-type') || target.className.baseVal;
        const objectId = target.id || target.getAttribute('data-id');
        const objectName = target.getAttribute('data-name') || 'Object';
        
        let content = `<div class="tooltip-title">${objectName}</div>`;
        
        if (objectType) {
            content += `<div class="tooltip-type">Type: ${objectType}</div>`;
        }
        
        if (objectId) {
            content += `<div class="tooltip-id">ID: ${objectId}</div>`;
        }
        
        // Add position information
        const position = this.getObjectPosition(target);
        if (position) {
            content += `<div class="tooltip-position">Position: (${Math.round(position.x)}, ${Math.round(position.y)})</div>`;
        }
        
        return content;
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'hover-tooltip';
        this.tooltip.style.cssText = `
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 10000;
            display: none;
            max-width: 200px;
            white-space: nowrap;
        `;
        
        document.body.appendChild(this.tooltip);
    }

    // Hover effects methods
    addHoverEffects(target) {
        if (!this.hoverEffectsEnabled || !target) return;
        
        target.classList.add(this.hoverHighlightClass);
        target.style.cursor = 'pointer';
        
        // Add data attribute to track hover state
        target.setAttribute('data-hovered', 'true');
        
        this.triggerEvent('hoverEffectsAdded', { target });
    }

    removeHoverEffects(target) {
        if (!target) return;
        
        target.classList.remove(this.hoverHighlightClass);
        target.style.cursor = '';
        target.removeAttribute('data-hovered');
        
        this.triggerEvent('hoverEffectsRemoved', { target });
    }

    // Utility methods
    findHoverableObject(target) {
        if (!target) return null;
        
        // Walk up the DOM tree to find the closest hoverable object
        let element = target;
        while (element && element !== this.viewportManager.svg) {
            if (this.isHoverableObject(element)) {
                return element;
            }
            element = element.parentElement;
        }
        
        return null;
    }

    isHoverableObject(element) {
        return element && (
            element.classList.contains('hoverable') ||
            element.classList.contains('bim-object') ||
            element.classList.contains('svg-object') ||
            element.hasAttribute('data-hoverable') ||
            element.hasAttribute('data-tooltip')
        );
    }

    getObjectPosition(obj) {
        if (!obj) return null;
        
        const transform = obj.getAttribute('transform');
        if (transform) {
            const translate = transform.match(/translate\(([^,]+),([^)]+)\)/);
            if (translate) {
                return {
                    x: parseFloat(translate[1]),
                    y: parseFloat(translate[2])
                };
            }
        }
        
        return {
            x: parseFloat(obj.getAttribute('x') || '0'),
            y: parseFloat(obj.getAttribute('y') || '0')
        };
    }

    // Hover state queries
    getHoveredObject() {
        return this.hoveredObject;
    }

    isObjectHovered(obj) {
        return this.hoveredObject === obj;
    }

    // Hover controls
    enableHoverEffects() {
        this.hoverEffectsEnabled = true;
    }

    disableHoverEffects() {
        this.hoverEffectsEnabled = false;
        
        // Remove all hover effects
        if (this.hoveredObject) {
            this.removeHoverEffects(this.hoveredObject);
        }
    }

    enableTooltip() {
        this.tooltipEnabled = true;
    }

    disableTooltip() {
        this.tooltipEnabled = false;
        this.hideTooltip();
    }

    setHoverDelay(delay) {
        this.hoverDelay = delay;
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, hover: this });
                } catch (error) {
                    console.error(`Error in hover event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        // End current hover
        if (this.hoveredObject) {
            this.endHover(this.hoveredObject, {});
        }
        
        // Clear timeout
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
        }
        
        // Remove tooltip
        if (this.tooltip) {
            this.tooltip.remove();
        }
        
        // Clear event handlers
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 