/**
 * Mobile Gesture Handlers for BIM Viewer
 * Handles touch interactions, pinch-zoom, pan, and tap gestures
 */

class MobileGestureHandler {
    constructor() {
        this.isDragging = false;
        this.isZooming = false;
        this.lastTouch = null;
        this.initialDistance = 0;
        this.initialZoom = 1;
        this.initialPan = { x: 0, y: 0 };
        this.touchStartTime = 0;
        this.touchEndTime = 0;
        this.longPressTimer = null;
        this.longPressThreshold = 500; // ms
        
        this.bindEvents();
    }
    
    bindEvents() {
        const container = document.getElementById('svg-container');
        if (!container) return;
        
        // Touch events
        container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse events for desktop testing
        container.addEventListener('mousedown', this.handleMouseDown.bind(this));
        container.addEventListener('mousemove', this.handleMouseMove.bind(this));
        container.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Wheel events for zoom
        container.addEventListener('wheel', this.handleWheel.bind(this), { passive: false });
        
        // Prevent context menu on long press
        container.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    handleTouchStart(event) {
        event.preventDefault();
        
        const touches = event.touches;
        this.touchStartTime = Date.now();
        
        if (touches.length === 1) {
            // Single touch - potential pan or tap
            this.handleSingleTouchStart(touches[0]);
        } else if (touches.length === 2) {
            // Two touches - potential pinch zoom
            this.handlePinchStart(touches);
        }
    }
    
    handleTouchMove(event) {
        event.preventDefault();
        
        const touches = event.touches;
        
        if (touches.length === 1 && this.isDragging) {
            this.handlePan(touches[0]);
        } else if (touches.length === 2 && this.isZooming) {
            this.handlePinchMove(touches);
        }
    }
    
    handleTouchEnd(event) {
        event.preventDefault();
        
        this.touchEndTime = Date.now();
        const touchDuration = this.touchEndTime - this.touchStartTime;
        
        // Clear long press timer
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
        
        if (event.touches.length === 0) {
            // All touches ended
            if (touchDuration < 200 && !this.isDragging && !this.isZooming) {
                // Short touch - potential tap
                this.handleTap(event.changedTouches[0]);
            }
            
            this.isDragging = false;
            this.isZooming = false;
            this.lastTouch = null;
        }
    }
    
    handleSingleTouchStart(touch) {
        this.lastTouch = {
            x: touch.clientX,
            y: touch.clientY
        };
        
        // Start long press timer
        this.longPressTimer = setTimeout(() => {
            this.handleLongPress(touch);
        }, this.longPressThreshold);
        
        // Store initial pan position
        const currentState = Alpine.store('panOffset');
        this.initialPan = { ...currentState };
    }
    
    handlePinchStart(touches) {
        this.isZooming = true;
        this.isDragging = false;
        
        // Calculate initial distance between touches
        this.initialDistance = this.getDistance(touches[0], touches[1]);
        this.initialZoom = Alpine.store('zoomLevel');
        
        // Store initial pan position
        const currentState = Alpine.store('panOffset');
        this.initialPan = { ...currentState };
    }
    
    handlePan(touch) {
        if (!this.lastTouch) return;
        
        this.isDragging = true;
        
        const deltaX = touch.clientX - this.lastTouch.x;
        const deltaY = touch.clientY - this.lastTouch.y;
        
        const currentPan = Alpine.store('panOffset');
        const newPan = {
            x: currentPan.x + deltaX,
            y: currentPan.y + deltaY
        };
        
        // Apply pan limits
        const limitedPan = this.applyPanLimits(newPan);
        Alpine.store('panOffset', limitedPan);
        
        this.lastTouch = {
            x: touch.clientX,
            y: touch.clientY
        };
        
        this.showGestureFeedback('Panning');
    }
    
    handlePinchMove(touches) {
        if (touches.length !== 2) return;
        
        const currentDistance = this.getDistance(touches[0], touches[1]);
        const scale = currentDistance / this.initialDistance;
        const newZoom = Math.max(0.1, Math.min(5, this.initialZoom * scale));
        
        Alpine.store('zoomLevel', newZoom);
        
        // Calculate center point for zoom
        const centerX = (touches[0].clientX + touches[1].clientX) / 2;
        const centerY = (touches[0].clientY + touches[1].clientY) / 2;
        
        this.showGestureFeedback(`Zoom: ${Math.round(newZoom * 100)}%`);
    }
    
    handleTap(touch) {
        // Find element under touch
        const element = document.elementFromPoint(touch.clientX, touch.clientY);
        
        if (element && element.hasAttribute('data-object-id')) {
            // Tap on BIM object
            this.handleObjectTap(element, touch);
        } else {
            // Tap on background - hide object info
            Alpine.store('showObjectInfo', false);
            Alpine.store('selectedObject', null);
        }
    }
    
    handleLongPress(touch) {
        this.showGestureFeedback('Long press detected');
        
        // Could be used for context menu or object selection
        const element = document.elementFromPoint(touch.clientX, touch.clientY);
        if (element && element.hasAttribute('data-object-id')) {
            this.handleObjectLongPress(element, touch);
        }
    }
    
    handleObjectTap(element, touch) {
        const objectId = element.dataset.objectId;
        const objectType = element.dataset.objectType;
        const layer = element.dataset.layer;
        const properties = JSON.parse(element.dataset.properties || '{}');
        
        const objectData = {
            id: objectId,
            type: objectType,
            layer: layer,
            properties: properties
        };
        
        Alpine.store('selectedObject', objectData);
        Alpine.store('showObjectInfo', true);
        
        // Add visual feedback
        this.highlightObject(element);
    }
    
    handleObjectLongPress(element, touch) {
        // Show context menu or additional options
        this.showContextMenu(element, touch);
    }
    
    highlightObject(element) {
        // Remove previous highlights
        document.querySelectorAll('.object-highlight').forEach(el => {
            el.classList.remove('object-highlight');
        });
        
        // Add highlight to current element
        element.classList.add('object-highlight');
        
        // Remove highlight after animation
        setTimeout(() => {
            element.classList.remove('object-highlight');
        }, 1000);
    }
    
    showContextMenu(element, touch) {
        // Create context menu
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.innerHTML = `
            <div class="context-menu-item" data-action="info">
                <i class="fas fa-info-circle"></i> Info
            </div>
            <div class="context-menu-item" data-action="edit">
                <i class="fas fa-edit"></i> Edit
            </div>
            <div class="context-menu-item" data-action="delete">
                <i class="fas fa-trash"></i> Delete
            </div>
        `;
        
        // Position menu
        menu.style.position = 'fixed';
        menu.style.left = touch.clientX + 'px';
        menu.style.top = touch.clientY + 'px';
        menu.style.zIndex = '1000';
        
        document.body.appendChild(menu);
        
        // Handle menu clicks
        menu.addEventListener('click', (e) => {
            const action = e.target.closest('.context-menu-item')?.dataset.action;
            if (action) {
                this.handleContextMenuAction(action, element);
            }
            document.body.removeChild(menu);
        });
        
        // Remove menu on outside click
        setTimeout(() => {
            if (document.body.contains(menu)) {
                document.body.removeChild(menu);
            }
        }, 3000);
    }
    
    handleContextMenuAction(action, element) {
        const objectId = element.dataset.objectId;
        
        switch (action) {
            case 'info':
                this.handleObjectTap(element, { clientX: 0, clientY: 0 });
                break;
            case 'edit':
                this.editObject(objectId);
                break;
            case 'delete':
                this.deleteObject(objectId);
                break;
        }
    }
    
    editObject(objectId) {
        // Navigate to edit mode
        const currentUrl = new URL(window.location);
        currentUrl.searchParams.set('edit', objectId);
        window.location.href = currentUrl.toString();
    }
    
    deleteObject(objectId) {
        if (confirm('Are you sure you want to delete this object?')) {
            // Send delete request
            fetch(`/api/bim/objects/${objectId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': 'Bearer ' + localStorage.getItem('arx_jwt')
                }
            }).then(response => {
                if (response.ok) {
                    // Remove element from DOM
                    const element = document.querySelector(`[data-object-id="${objectId}"]`);
                    if (element) {
                        element.remove();
                    }
                    Alpine.store('showObjectInfo', false);
                    Alpine.store('selectedObject', null);
                }
            });
        }
    }
    
    // Mouse event handlers for desktop testing
    handleMouseDown(event) {
        this.lastTouch = {
            x: event.clientX,
            y: event.clientY
        };
        
        const currentState = Alpine.store('panOffset');
        this.initialPan = { ...currentState };
    }
    
    handleMouseMove(event) {
        if (!this.lastTouch) return;
        
        this.isDragging = true;
        
        const deltaX = event.clientX - this.lastTouch.x;
        const deltaY = event.clientY - this.lastTouch.y;
        
        const currentPan = Alpine.store('panOffset');
        const newPan = {
            x: currentPan.x + deltaX,
            y: currentPan.y + deltaY
        };
        
        const limitedPan = this.applyPanLimits(newPan);
        Alpine.store('panOffset', limitedPan);
        
        this.lastTouch = {
            x: event.clientX,
            y: event.clientY
        };
    }
    
    handleMouseUp(event) {
        this.isDragging = false;
        this.lastTouch = null;
    }
    
    handleWheel(event) {
        event.preventDefault();
        
        const delta = event.deltaY > 0 ? 0.9 : 1.1;
        const currentZoom = Alpine.store('zoomLevel');
        const newZoom = Math.max(0.1, Math.min(5, currentZoom * delta));
        
        Alpine.store('zoomLevel', newZoom);
    }
    
    // Utility methods
    getDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    applyPanLimits(pan) {
        const container = document.getElementById('svg-container');
        if (!container) return pan;
        
        const rect = container.getBoundingClientRect();
        const maxPan = rect.width * 0.5;
        
        return {
            x: Math.max(-maxPan, Math.min(maxPan, pan.x)),
            y: Math.max(-maxPan, Math.min(maxPan, pan.y))
        };
    }
    
    showGestureFeedback(message) {
        const feedback = document.getElementById('gesture-feedback');
        if (feedback) {
            feedback.textContent = message;
            feedback.classList.add('show');
            
            setTimeout(() => {
                feedback.classList.remove('show');
            }, 1000);
        }
    }
}

// Layer management functions
function toggleLayer(layerCode, visible) {
    const elements = document.querySelectorAll(`[data-layer="${layerCode}"]`);
    elements.forEach(element => {
        element.style.display = visible ? 'block' : 'none';
    });
}

function showAllLayers() {
    const layerVisibility = Alpine.store('layerVisibility');
    Object.keys(layerVisibility).forEach(layer => {
        layerVisibility[layer] = true;
    });
    
    // Show all elements
    document.querySelectorAll('[data-layer]').forEach(element => {
        element.style.display = 'block';
    });
}

function hideAllLayers() {
    const layerVisibility = Alpine.store('layerVisibility');
    Object.keys(layerVisibility).forEach(layer => {
        layerVisibility[layer] = false;
    });
    
    // Hide all elements
    document.querySelectorAll('[data-layer]').forEach(element => {
        element.style.display = 'none';
    });
}

// Zoom functions
function zoomIn() {
    const currentZoom = Alpine.store('zoomLevel');
    const newZoom = Math.min(5, currentZoom * 1.2);
    Alpine.store('zoomLevel', newZoom);
}

function zoomOut() {
    const currentZoom = Alpine.store('zoomLevel');
    const newZoom = Math.max(0.1, currentZoom / 1.2);
    Alpine.store('zoomLevel', newZoom);
}

// Initialize gesture handler when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new MobileGestureHandler();
});

// Export for use in other modules
window.MobileGestureHandler = MobileGestureHandler;
window.toggleLayer = toggleLayer;
window.showAllLayers = showAllLayers;
window.hideAllLayers = hideAllLayers;
window.zoomIn = zoomIn;
window.zoomOut = zoomOut; 