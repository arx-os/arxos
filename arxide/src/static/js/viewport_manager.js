/**
 * Viewport Manager for SVG-BIM System
 * Handles zoom, pan, coordinate conversion, and viewport state management
 */

class ViewportManager {
    constructor(svgElement, options = {}) {
        this.svg = svgElement;
        this.container = svgElement.parentElement;

        // Viewport state
        this.currentZoom = options.initialZoom || 1.0;
        this.panX = options.initialPanX || 0;
        this.panY = options.initialPanY || 0;

        // Zoom constraints
        this.minZoom = options.minZoom || 0.1;
        this.maxZoom = options.maxZoom || 5.0;
        this.zoomStep = options.zoomStep || 0.1;

        // Mouse wheel zoom settings
        this.wheelZoomSpeed = options.wheelZoomSpeed || 0.001;
        this.wheelZoomSmooth = options.wheelZoomSmooth !== false; // Default to true
        this.wheelZoomDuration = options.wheelZoomDuration || 150;

        // Pan settings
        this.panEnabled = options.panEnabled !== false; // Default to true
        this.panInertia = options.panInertia !== false; // Default to true
        this.panInertiaDecay = options.panInertiaDecay || 0.95; // Decay factor for inertia
        this.panInertiaDuration = options.panInertiaDuration || 300; // Inertia duration in ms
        this.panBoundaries = options.panBoundaries || {
            enabled: true,
            padding: 100, // Padding from edges
            maxDistance: 2000 // Maximum pan distance from center
        };

        // Zoom history for undo/redo
        this.zoomHistory = [];
        this.maxHistorySize = options.maxHistorySize || 50;
        this.historyIndex = -1;

        // Performance optimization with throttled updates
        this.isUpdating = false;
        this.updateQueue = [];
        this.lastUpdateTime = 0;
        this.updateThrottle = options.updateThrottle || 16; // ~60fps

        // Throttled update manager integration
        this.throttledUpdateManager = null;
        this.enableThrottledUpdates = options.enableThrottledUpdates !== false; // Default to true

        // Animation state
        this.isAnimating = false;
        this.targetZoom = null;
        this.targetPanX = null;
        this.targetPanY = null;

        // Event handlers
        this.eventHandlers = new Map();

        // Pan state
        this.isPanning = false;
        this.panStartX = 0;
        this.panStartY = 0;
        this.panStartViewX = 0;
        this.panStartViewY = 0;
        this.panVelocityX = 0;
        this.panVelocityY = 0;
        this.panInertiaAnimation = null;
        this.hasShownPanIndicator = false;
        this.lastPanTime = null;

        // Scale factors for real-world coordinate conversion
        this.scaleFactors = {
            x: 1.0,
            y: 1.0
        };
        this.currentUnit = 'pixels';

        // Viewport culling for performance optimization
        this.cullingEnabled = options.cullingEnabled !== false; // Default to true
        this.cullingMargin = options.cullingMargin || 100; // Extra margin around viewport
        this.cullingUpdateThrottle = options.cullingUpdateThrottle || 50; // ms between culling updates
        this.lastCullingUpdate = 0;
        this.visibleObjects = new Set();
        this.totalObjects = 0;
        this.cullingStats = {
            totalObjects: 0,
            visibleObjects: 0,
            culledObjects: 0,
            cullingTime: 0,
            lastUpdate: 0
        };

        // Object bounds cache for culling optimization
        this.objectBoundsCache = new Map();
        this.boundsCacheExpiry = options.boundsCacheExpiry || 5000; // 5 seconds
        this.lastBoundsCacheCleanup = 0;

        // Touch support for mobile devices
        this.touchEnabled = options.touchEnabled !== false; // Default to true
        this.touchZoomEnabled = options.touchZoomEnabled !== false; // Default to true
        this.touchPanEnabled = options.touchPanEnabled !== false; // Default to true
        this.touchGestureEnabled = options.touchGestureEnabled !== false; // Default to true

        // Touch state
        this.touchState = {
            isTouching: false,
            touchCount: 0,
            startTouches: [],
            currentTouches: [],
            startDistance: 0,
            startCenter: { x: 0, y: 0 },
            lastDistance: 0,
            lastCenter: { x: 0, y: 0 },
            startTime: 0,
            lastMoveTime: 0,
            velocity: { x: 0, y: 0 },
            gestureType: null // 'pinch', 'pan', 'tap', 'double-tap', 'swipe'
        };

        // Touch configuration
        this.touchConfig = {
            pinchSensitivity: options.pinchSensitivity || 0.01,
            panSensitivity: options.panSensitivity || 1.0,
            tapThreshold: options.tapThreshold || 10, // pixels
            tapTimeout: options.tapTimeout || 300, // milliseconds
            doubleTapTimeout: options.doubleTapTimeout || 300,
            swipeThreshold: options.swipeThreshold || 50, // pixels
            swipeVelocity: options.swipeVelocity || 0.3, // pixels per millisecond
            longPressTimeout: options.longPressTimeout || 500,
            touchInertia: options.touchInertia !== false, // Default to true
            touchInertiaDecay: options.touchInertiaDecay || 0.95
        };

        // Touch gesture history
        this.touchGestureHistory = [];
        this.maxGestureHistory = options.maxGestureHistory || 10;

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the viewport manager
     */
    initialize() {
        if (!this.svg || !this.container) {
            console.error('ViewportManager: SVG element or container not found');
            return;
        }

        // Add pan-enabled class for cursor styling
        this.container.classList.add('pan-enabled');

        // Connect to throttled update manager
        this.connectToThrottledUpdateManager();

        // Set initial viewport
        this.updateViewport();

        // Setup event listeners
        this.setupEventListeners();

        // Save initial state
        this.saveZoomState();

        // Trigger initialized event
        this.triggerEvent('initialized', {
            zoom: this.currentZoom,
            panX: this.panX,
            panY: this.panY
        });

        // Initialize ArxLogger
        if (window.arxLogger) {
          window.arxLogger.info('ViewportManager initialized', {
            component: 'viewport_manager',
            version: '1.0.0'
          });
        }
    }

    /**
     * Connect to the throttled update manager
     */
    connectToThrottledUpdateManager() {
        if (!this.enableThrottledUpdates) {
            if (window.arxLogger) {
              window.arxLogger.info('ViewportManager: Throttled updates disabled', {
                component: 'viewport_manager',
                feature: 'throttled_updates',
                status: 'disabled'
              });
            }
            return;
        }

        // Wait for throttled update manager to be available
        const checkThrottledUpdateManager = () => {
            if (window.throttledUpdateManager) {
                this.throttledUpdateManager = window.throttledUpdateManager;
                if (window.arxLogger) {
                  window.arxLogger.info('ViewportManager connected to ThrottledUpdateManager', {
                    component: 'viewport_manager',
                    integration: 'throttled_update_manager',
                    status: 'connected'
                  });
                }

                // Listen for update events
                this.throttledUpdateManager.addEventListener('update', (data) => {
                    this.handleThrottledUpdate(data);
                });

                this.throttledUpdateManager.addEventListener('batchedUpdate', (data) => {
                    this.handleBatchedUpdate(data);
                });

                // Listen for performance events
                this.throttledUpdateManager.addEventListener('updateProcessed', (data) => {
                    this.handleUpdateProcessed(data);
                });

            } else {
                // Retry after a short delay
                setTimeout(checkThrottledUpdateManager, 100);
            }
        };
        checkThrottledUpdateManager();


    }

    /**
     * Setup event listeners for zoom and pan
     */
    setupEventListeners() {
        // Mouse wheel zoom
        this.container.addEventListener('wheel', this.handleWheel.bind(this), { passive: false });

        // Middle mouse button pan
        this.container.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));

        // Prevent context menu on right click during pan
        this.container.addEventListener('contextmenu', (e) => {
            if (this.isPanning) {
                e.preventDefault();
            }
        });

        // Touch events for mobile devices
        if (this.touchEnabled) {
            this.setupTouchEventListeners();
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyDown.bind(this));

        // Window resize handling
        window.addEventListener('resize', this.handleResize.bind(this));
    }

    /**
     * Setup touch event listeners for mobile devices
     */
    setupTouchEventListeners() {
        // Touch start
        this.container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });

        // Touch move
        this.container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });

        // Touch end
        this.container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });

        // Touch cancel
        this.container.addEventListener('touchcancel', this.handleTouchCancel.bind(this), { passive: false });

        // Prevent default touch behaviors that might interfere
        this.container.addEventListener('touchstart', (e) => {
            if (this.touchState.isTouching) {
                e.preventDefault();
            }
        }, { passive: false });

        this.container.addEventListener('touchmove', (e) => {
            if (this.touchState.isTouching) {
                e.preventDefault();
            }
        }, { passive: false });
    }

    /**
     * Handle touch start events
     */
    handleTouchStart(event) {
        event.preventDefault();

        const touches = Array.from(event.touches);
        this.touchState.touchCount = touches.length;
        this.touchState.startTouches = touches.map(touch => ({
            id: touch.identifier,
            x: touch.clientX,
            y: touch.clientY
        }));
        this.touchState.currentTouches = [...this.touchState.startTouches];
        this.touchState.startTime = performance.now();
        this.touchState.lastMoveTime = this.touchState.startTime;
        this.touchState.isTouching = true;
        this.touchState.gestureType = null;

        // Calculate initial distance and center for multi-touch
        if (touches.length === 2) {
            this.touchState.startDistance = this.calculateTouchDistance(touches[0], touches[1]);
            this.touchState.startCenter = this.calculateTouchCenter(touches[0], touches[1]);
            this.touchState.lastDistance = this.touchState.startDistance;
            this.touchState.lastCenter = { ...this.touchState.startCenter };
        }

        // Add touch feedback
        this.container.classList.add('touching');

        // Trigger touch start event
        this.triggerEvent('touchStart', {
            touchCount: this.touchState.touchCount,
            touches: this.touchState.startTouches
        });
    }

    /**
     * Handle touch move events
     */
    handleTouchMove(event) {
        event.preventDefault();

        if (!this.touchState.isTouching) return;

        const touches = Array.from(event.touches);
        this.touchState.currentTouches = touches.map(touch => ({
            id: touch.identifier,
            x: touch.clientX,
            y: touch.clientY
        }));

        const currentTime = performance.now();
        const timeDelta = currentTime - this.touchState.lastMoveTime;

        // Handle different touch counts
        if (touches.length === 1 && this.touchPanEnabled) {
            this.handleSingleTouchMove(touches[0], timeDelta);
        } else if (touches.length === 2 && this.touchZoomEnabled) {
            this.handlePinchZoom(touches[0], touches[1], timeDelta);
        }

        this.touchState.lastMoveTime = currentTime;

        // Trigger touch move event
        this.triggerEvent('touchMove', {
            touchCount: touches.length,
            touches: this.touchState.currentTouches,
            gestureType: this.touchState.gestureType
        });
    }

    /**
     * Handle touch end events
     */
    handleTouchEnd(event) {
        event.preventDefault();

        if (!this.touchState.isTouching) return;

        const currentTime = performance.now();
        const touchDuration = currentTime - this.touchState.startTime;

        // Determine gesture type based on touch duration and movement
        this.determineTouchGesture(touchDuration);

        // Handle inertia for pan gestures
        if (this.touchState.gestureType === 'pan' && this.touchConfig.touchInertia) {
            this.startTouchInertia();
        }

        // Save state for undo/redo
        this.saveZoomState();

        // Reset touch state
        this.touchState.isTouching = false;
        this.touchState.touchCount = 0;
        this.touchState.gestureType = null;

        // Remove touch feedback
        this.container.classList.remove('touching');

        // Trigger touch end event
        this.triggerEvent('touchEnd', {
            gestureType: this.touchState.gestureType,
            duration: touchDuration,
            velocity: this.touchState.velocity
        });
    }

    /**
     * Handle touch cancel events
     */
    handleTouchCancel(event) {
        event.preventDefault();

        // Reset touch state
        this.touchState.isTouching = false;
        this.touchState.touchCount = 0;
        this.touchState.gestureType = null;

        // Remove touch feedback
        this.container.classList.remove('touching');

        // Trigger touch cancel event
        this.triggerEvent('touchCancel');
    }

    /**
     * Handle single touch move (pan)
     */
    handleSingleTouchMove(touch, timeDelta) {
        const startTouch = this.touchState.startTouches[0];
        if (!startTouch) return;

        // Calculate movement
        const deltaX = touch.clientX - startTouch.x;
        const deltaY = touch.clientY - startTouch.y;

        // Check if movement exceeds threshold for pan
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        if (distance > this.touchConfig.tapThreshold) {
            this.touchState.gestureType = 'pan';

            // Calculate pan delta in SVG coordinates
            const panDeltaX = deltaX / this.currentZoom * this.touchConfig.panSensitivity;
            const panDeltaY = deltaY / this.currentZoom * this.touchConfig.panSensitivity;

            // Apply pan
            const newPanX = this.panX + panDeltaX;
            const newPanY = this.panY + panDeltaY;

            // Apply boundaries
            const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);
            this.panX = constrainedPan.x;
            this.panY = constrainedPan.y;

            // Update velocity
            if (timeDelta > 0) {
                this.touchState.velocity.x = deltaX / timeDelta;
                this.touchState.velocity.y = deltaY / timeDelta;
            }

            // Queue throttled viewport update
            if (this.throttledUpdateManager) {
                this.throttledUpdateManager.queueUpdate('touchPan', {
                    panX: this.panX,
                    panY: this.panY,
                    deltaX: deltaX,
                    deltaY: deltaY
                });
            } else {
                this.updateViewport();
            }

            // Update start position for next move
            this.touchState.startTouches[0] = {
                id: startTouch.id,
                x: touch.clientX,
                y: touch.clientY
            };
        }
    }

    /**
     * Handle pinch zoom gesture
     */
    handlePinchZoom(touch1, touch2, timeDelta) {
        const currentDistance = this.calculateTouchDistance(touch1, touch2);
        const currentCenter = this.calculateTouchCenter(touch1, touch2);

        // Calculate zoom factor based on distance change
        const distanceRatio = currentDistance / this.touchState.startDistance;
        const zoomFactor = Math.pow(distanceRatio, this.touchConfig.pinchSensitivity);

        // Calculate zoom center in SVG coordinates
        const rect = this.container.getBoundingClientRect();
        const centerX = currentCenter.x - rect.left;
        const centerY = currentCenter.y - rect.top;

        // Apply zoom
        this.zoomAtPoint(zoomFactor, centerX, centerY, true);

        // Calculate pan to keep center point fixed
        const centerDeltaX = currentCenter.x - this.touchState.startCenter.x;
        const centerDeltaY = currentCenter.y - this.touchState.startCenter.y;

        if (Math.abs(centerDeltaX) > 5 || Math.abs(centerDeltaY) > 5) {
            const panDeltaX = centerDeltaX / this.currentZoom * this.touchConfig.panSensitivity;
            const panDeltaY = centerDeltaY / this.currentZoom * this.touchConfig.panSensitivity;

            const newPanX = this.panX + panDeltaX;
            const newPanY = this.panY + panDeltaY;

            const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);
            this.panX = constrainedPan.x;
            this.panY = constrainedPan.y;
        }

        // Update last values
        this.touchState.lastDistance = currentDistance;
        this.touchState.lastCenter = { ...currentCenter };
        this.touchState.gestureType = 'pinch';

        // Queue throttled viewport update
        if (this.throttledUpdateManager) {
            this.throttledUpdateManager.queueUpdate('touchZoom', {
                zoom: this.currentZoom,
                zoomFactor: zoomFactor,
                centerX: centerX,
                centerY: centerY
            });
        } else {
            this.updateViewport();
        }
    }

    /**
     * Calculate distance between two touch points
     */
    calculateTouchDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * Calculate center point between two touch points
     */
    calculateTouchCenter(touch1, touch2) {
        return {
            x: (touch1.clientX + touch2.clientX) / 2,
            y: (touch1.clientY + touch2.clientY) / 2
        };
    }

    /**
     * Determine the type of touch gesture
     */
    determineTouchGesture(touchDuration) {
        const startTouch = this.touchState.startTouches[0];
        const currentTouch = this.touchState.currentTouches[0];

        if (!startTouch || !currentTouch) return;

        // Calculate total movement
        const deltaX = currentTouch.x - startTouch.x;
        const deltaY = currentTouch.y - startTouch.y;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

        // Determine gesture type
        if (distance < this.touchConfig.tapThreshold) {
            if (touchDuration < this.touchConfig.tapTimeout) {
                this.touchState.gestureType = 'tap';
                this.handleTapGesture();
            } else {
                this.touchState.gestureType = 'long-press';
                this.handleLongPressGesture();
            }
        } else if (distance > this.touchConfig.swipeThreshold) {
            const velocity = distance / touchDuration;
            if (velocity > this.touchConfig.swipeVelocity) {
                this.touchState.gestureType = 'swipe';
                this.handleSwipeGesture(deltaX, deltaY, velocity);
            } else {
                this.touchState.gestureType = 'pan';
            }
        } else {
            this.touchState.gestureType = 'pan';
        }

        // Add to gesture history
        this.addToGestureHistory(this.touchState.gestureType);
    }

    /**
     * Handle tap gesture
     */
    handleTapGesture() {
        const startTouch = this.touchState.startTouches[0];
        if (!startTouch) return;

        // Check for double tap
        const lastGesture = this.touchGestureHistory[this.touchGestureHistory.length - 1];
        if (lastGesture && lastGesture.type === 'tap') {
            const timeSinceLastTap = performance.now() - lastGesture.timestamp;
            if (timeSinceLastTap < this.touchConfig.doubleTapTimeout) {
                this.touchState.gestureType = 'double-tap';
                this.handleDoubleTapGesture();
                return;
            }
        }

        // Single tap - could be used for object selection
        this.triggerEvent('tap', {
            x: startTouch.x,
            y: startTouch.y,
            timestamp: performance.now()
        });
    }

    /**
     * Handle double tap gesture
     */
    handleDoubleTapGesture() {
        const startTouch = this.touchState.startTouches[0];
        if (!startTouch) return;

        // Double tap to reset view or fit to view
        this.resetView();

        this.triggerEvent('doubleTap', {
            x: startTouch.x,
            y: startTouch.y,
            timestamp: performance.now()
        });
    }

    /**
     * Handle long press gesture
     */
    handleLongPressGesture() {
        const startTouch = this.touchState.startTouches[0];
        if (!startTouch) return;

        // Long press could be used for context menu or object details
        this.triggerEvent('longPress', {
            x: startTouch.x,
            y: startTouch.y,
            timestamp: performance.now()
        });
    }

    /**
     * Handle swipe gesture
     */
    handleSwipeGesture(deltaX, deltaY, velocity) {
        const startTouch = this.touchState.startTouches[0];
        if (!startTouch) return;

        // Determine swipe direction
        const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
        let direction = 'unknown';

        if (angle >= -45 && angle <= 45) direction = 'right';
        else if (angle >= 45 && angle <= 135) direction = 'down';
        else if (angle >= 135 || angle <= -135) direction = 'left';
        else direction = 'up';

        this.triggerEvent('swipe', {
            direction: direction,
            deltaX: deltaX,
            deltaY: deltaY,
            velocity: velocity,
            x: startTouch.x,
            y: startTouch.y,
            timestamp: performance.now()
        });
    }

    /**
     * Start touch inertia animation
     */
    startTouchInertia() {
        if (!this.touchConfig.touchInertia ||
            (Math.abs(this.touchState.velocity.x) < 0.1 && Math.abs(this.touchState.velocity.y) < 0.1)) {
            return;
        }

        const startTime = performance.now();
        const startPanX = this.panX;
        const startPanY = this.panY;
        const startVelocityX = this.touchState.velocity.x / this.currentZoom;
        const startVelocityY = this.touchState.velocity.y / this.currentZoom;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = elapsed / this.panInertiaDuration;

            if (progress >= 1) {
                return;
            }

            // Calculate decay factor
            const decay = Math.pow(this.touchConfig.touchInertiaDecay, progress * 10);

            // Apply velocity with decay
            const currentVelocityX = startVelocityX * decay;
            const currentVelocityY = startVelocityY * decay;

            // Update pan position
            const newPanX = startPanX + currentVelocityX * progress * 10;
            const newPanY = startPanY + currentVelocityY * progress * 10;

            // Apply boundaries
            const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);

            this.panX = constrainedPan.x;
            this.panY = constrainedPan.y;

            // Queue throttled viewport update
            if (this.throttledUpdateManager) {
                this.throttledUpdateManager.queueUpdate('touchInertia', {
                    panX: this.panX,
                    panY: this.panY,
                    velocityX: currentVelocityX,
                    velocityY: currentVelocityY
                });
            } else {
                this.updateViewport();
            }

            // Continue animation if velocity is still significant
            if (Math.abs(currentVelocityX) > 0.1 || Math.abs(currentVelocityY) > 0.1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    /**
     * Add gesture to history
     */
    addToGestureHistory(gestureType) {
        this.touchGestureHistory.push({
            type: gestureType,
            timestamp: performance.now()
        });

        // Limit history size
        if (this.touchGestureHistory.length > this.maxGestureHistory) {
            this.touchGestureHistory.shift();
        }
    }

    /**
     * Enable/disable touch support
     */
    enableTouch() {
        this.touchEnabled = true;
        this.setupTouchEventListeners();
    }

    disableTouch() {
        this.touchEnabled = false;
        // Remove touch event listeners would require storing references
        // For simplicity, we'll just set the flag
    }

    /**
     * Get touch configuration
     */
    getTouchConfig() {
        return { ...this.touchConfig };
    }

    /**
     * Update touch configuration
     */
    updateTouchConfig(newConfig) {
        Object.assign(this.touchConfig, newConfig);
    }

    /**
     * Handle mouse wheel events for zooming
     */
    handleWheel(event) {
        event.preventDefault();

        // Check if Ctrl/Cmd key is pressed for zoom (standard browser behavior)
        const isCtrlZoom = event.ctrlKey || event.metaKey;

        // If Ctrl/Cmd is pressed, handle zoom
        if (isCtrlZoom) {
            this.handleZoomWheel(event);
        } else {
            // If no Ctrl/Cmd, handle as regular scroll (for panning if needed)
            this.handleScrollWheel(event);
        }
    }

    /**
     * Handle zoom wheel events
     */
    handleZoomWheel(event) {
        // Calculate zoom factor based on wheel delta
        const delta = event.deltaY;
        const zoomSpeed = this.wheelZoomSpeed;
        const zoomFactor = 1 - (delta * zoomSpeed);

        // Get mouse position relative to container
        const rect = this.container.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        // Apply zoom with smooth transition
        this.zoomAtPoint(zoomFactor, mouseX, mouseY, this.wheelZoomSmooth);

        // Add visual feedback
        this.showZoomFeedback(event);
    }

    /**
     * Handle regular scroll wheel events (for potential future panning)
     */
    handleScrollWheel(event) {
        // For now, just prevent default to avoid page scrolling
        // In the future, this could be used for vertical panning
        event.preventDefault();
    }

    /**
     * Show zoom feedback (visual indicator)
     */
    showZoomFeedback(event) {
        // Add zooming class to container
        this.container.classList.add('zooming');

        // Remove class after animation completes
        setTimeout(() => {
            this.container.classList.remove('zooming');
        }, 200);

        // Show zoom constraint indicator if at limits
        if (this.currentZoom <= this.minZoom || this.currentZoom >= this.maxZoom) {
            this.showZoomConstraint();
        }
    }

    /**
     * Show zoom constraint indicator
     */
    showZoomConstraint() {
        let constraintElement = document.getElementById('zoom-constraint');

        if (!constraintElement) {
            constraintElement = document.createElement('div');
            constraintElement.id = 'zoom-constraint';
            constraintElement.className = 'zoom-constraint';
            this.container.appendChild(constraintElement);
        }

        const message = this.currentZoom <= this.minZoom ?
            `Min zoom: ${Math.round(this.minZoom * 100)}%` :
            `Max zoom: ${Math.round(this.maxZoom * 100)}%`;

        constraintElement.textContent = message;
        constraintElement.classList.add('show');

        // Hide after 2 seconds
        setTimeout(() => {
            constraintElement.classList.remove('show');
        }, 2000);
    }

    /**
     * Check if zoom is at constraints
     */
    isAtZoomConstraint() {
        return this.currentZoom <= this.minZoom || this.currentZoom >= this.maxZoom;
    }

    /**
     * Get zoom constraint message
     */
    getZoomConstraintMessage() {
        if (this.currentZoom <= this.minZoom) {
            return `Min zoom: ${Math.round(this.minZoom * 100)}%`;
        } else if (this.currentZoom >= this.maxZoom) {
            return `Max zoom: ${Math.round(this.maxZoom * 100)}%`;
        }
        return null;
    }

    /**
     * Apply zoom with constraint feedback
     */
    applyZoomWithConstraints(newZoom, newPanX, newPanY, smooth = false) {
        const wasAtConstraint = this.isAtZoomConstraint();

        // Apply zoom
        if (smooth) {
            this.applySmoothZoom(newZoom, newPanX, newPanY);
        } else {
            this.currentZoom = newZoom;
            this.panX = newPanX;
            this.panY = newPanY;
            this.queueViewportUpdate();
        }

        // Show constraint feedback if we just hit a limit
        const isAtConstraint = this.isAtZoomConstraint();
        if (isAtConstraint && !wasAtConstraint) {
            this.showZoomConstraint();
        }

        // Update zoom buttons state
        this.updateZoomButtonStates();
    }

    /**
     * Update zoom button states based on constraints
     */
    updateZoomButtonStates() {
        const zoomInBtn = document.getElementById('zoom-in');
        const zoomOutBtn = document.getElementById('zoom-out');

        if (zoomInBtn) {
            zoomInBtn.disabled = this.currentZoom >= this.maxZoom;
            zoomInBtn.title = this.currentZoom >= this.maxZoom ?
                `Max zoom: ${Math.round(this.maxZoom * 100)}%` :
                'Zoom In (Ctrl + +)';
        }

        if (zoomOutBtn) {
            zoomOutBtn.disabled = this.currentZoom <= this.minZoom;
            zoomOutBtn.title = this.currentZoom <= this.minZoom ?
                `Min zoom: ${Math.round(this.minZoom * 100)}%` :
                'Zoom Out (Ctrl + -)';
        }
    }

    /**
     * Handle mouse down events for panning
     */
    handleMouseDown(event) {
        // Only handle middle mouse button (button 1) for panning
        if (event.button === 1 && this.panEnabled) {
            event.preventDefault();
            this.startPan(event);
        }
    }

    /**
     * Start pan operation
     */
    startPan(event) {
        this.isPanning = true;
        this.panStartX = event.clientX;
        this.panStartY = event.clientY;
        this.panStartViewX = this.panX;
        this.panStartViewY = this.panY;
        this.panVelocityX = 0;
        this.panVelocityY = 0;

        // Stop any existing inertia animation
        if (this.panInertiaAnimation) {
            cancelAnimationFrame(this.panInertiaAnimation);
            this.panInertiaAnimation = null;
        }

        // Add panning class and update cursor
        this.container.classList.add('panning');
        this.container.style.cursor = 'grabbing';

        // Show pan mode indicator on first pan
        if (!this.hasShownPanIndicator) {
            this.showPanModeIndicator();
            this.hasShownPanIndicator = true;
        }

        // Trigger pan start event
        this.triggerEvent('panStart', { x: this.panStartX, y: this.panStartY });
    }

    /**
     * Handle mouse move events for panning
     */
    handleMouseMove(event) {
        if (!this.isPanning) return;

        // Calculate pan delta
        const deltaX = event.clientX - this.panStartX;
        const deltaY = event.clientY - this.panStartY;

        // Calculate new pan position
        const newPanX = this.panStartViewX + deltaX / this.currentZoom;
        const newPanY = this.panStartViewY + deltaY / this.currentZoom;

        // Apply pan boundaries
        const boundedPan = this.applyPanBoundaries(newPanX, newPanY);

        // Update pan position
        this.panX = boundedPan.x;
        this.panY = boundedPan.y;

        // Queue throttled viewport update
        if (this.throttledUpdateManager) {
            this.throttledUpdateManager.queueUpdate('pan', {
                panX: this.panX,
                panY: this.panY,
                deltaX: deltaX,
                deltaY: deltaY
            });
        } else {
            // Fallback to immediate update
            this.updateViewport();
        }

        // Update pan velocity for inertia
        const currentTime = performance.now();
        if (this.lastPanTime) {
            const timeDelta = currentTime - this.lastPanTime;
            if (timeDelta > 0) {
                this.panVelocityX = deltaX / timeDelta;
                this.panVelocityY = deltaY / timeDelta;
            }
        }
        this.lastPanTime = currentTime;

        // Show pan feedback
        this.showPanModeIndicator();
    }

    /**
     * Handle mouse up events for panning
     */
    handleMouseUp(event) {
        if (this.isPanning) {
            this.endPan();
        }
    }

    /**
     * End pan operation
     */
    endPan() {
        this.isPanning = false;

        // Remove panning class and reset cursor
        this.container.classList.remove('panning');
        this.container.style.cursor = '';

        // Show velocity indicator if velocity is significant
        if (Math.abs(this.panVelocityX) > 0.5 || Math.abs(this.panVelocityY) > 0.5) {
            this.showPanVelocityIndicator();
        }

        // Start inertia animation if enabled and velocity is significant
        if (this.panInertia && (Math.abs(this.panVelocityX) > 0.1 || Math.abs(this.panVelocityY) > 0.1)) {
            this.showPanInertiaIndicator();
            this.startPanInertia();
        }

        // Save state
        this.saveZoomState();

        // Trigger pan end event
        this.triggerEvent('panEnd', {
            x: this.panX,
            y: this.panY,
            velocityX: this.panVelocityX,
            velocityY: this.panVelocityY
        });
    }

    /**
     * Apply pan boundaries
     */
    applyPanBoundaries(panX, panY) {
        if (!this.panBoundaries.enabled) {
            return { x: panX, y: panY };
        }

        const rect = this.container.getBoundingClientRect();
        const containerWidth = rect.width;
        const containerHeight = rect.height;

        // Calculate boundaries based on zoom level and container size
        const maxPanX = Math.max(0, (containerWidth * this.currentZoom - containerWidth) / 2 + this.panBoundaries.padding);
        const maxPanY = Math.max(0, (containerHeight * this.currentZoom - containerHeight) / 2 + this.panBoundaries.padding);
        const minPanX = -maxPanX;
        const minPanY = -maxPanY;

        // Apply maximum distance constraint
        const maxDistance = this.panBoundaries.maxDistance;
        const distanceFromCenter = Math.sqrt(panX * panX + panY * panY);

        if (distanceFromCenter > maxDistance) {
            const scale = maxDistance / distanceFromCenter;
            panX *= scale;
            panY *= scale;
        }

        // Apply boundaries with elastic resistance
        const boundaryResistance = 0.3;

        if (panX > maxPanX) {
            const overflow = panX - maxPanX;
            panX = maxPanX + overflow * boundaryResistance;
        } else if (panX < minPanX) {
            const overflow = minPanX - panX;
            panX = minPanX - overflow * boundaryResistance;
        }

        if (panY > maxPanY) {
            const overflow = panY - maxPanY;
            panY = maxPanY + overflow * boundaryResistance;
        } else if (panY < minPanY) {
            const overflow = minPanY - panY;
            panY = minPanY - overflow * boundaryResistance;
        }

        return { x: panX, y: panY };
    }

    /**
     * Start pan inertia animation
     */
    startPanInertia() {
        const startTime = performance.now();
        const startPanX = this.panX;
        const startPanY = this.panY;
        const startVelocityX = this.panVelocityX;
        const startVelocityY = this.panVelocityY;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = elapsed / this.panInertiaDuration;

            if (progress >= 1) {
                // Animation complete
                this.panInertiaAnimation = null;
                return;
            }

            // Calculate decay factor
            const decay = Math.pow(this.panInertiaDecay, progress * 10);

            // Apply velocity with decay
            const currentVelocityX = startVelocityX * decay;
            const currentVelocityY = startVelocityY * decay;

            // Update pan position
            const newPanX = startPanX + currentVelocityX * progress * 10;
            const newPanY = startPanY + currentVelocityY * progress * 10;

            // Apply boundaries
            const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);

            this.panX = constrainedPan.x;
            this.panY = constrainedPan.y;
            this.queueViewportUpdate();

            // Continue animation if velocity is still significant
            if (Math.abs(currentVelocityX) > 0.1 || Math.abs(currentVelocityY) > 0.1) {
                this.panInertiaAnimation = requestAnimationFrame(animate);
            } else {
                this.panInertiaAnimation = null;
            }
        };

        this.panInertiaAnimation = requestAnimationFrame(animate);
    }

    /**
     * Stop pan inertia
     */
    stopPanInertia() {
        if (this.panInertiaAnimation) {
            cancelAnimationFrame(this.panInertiaAnimation);
            this.panInertiaAnimation = null;
        }
        this.panVelocityX = 0;
        this.panVelocityY = 0;
    }

    /**
     * Show pan boundary feedback
     */
    showPanBoundaryFeedback() {
        let feedbackElement = document.getElementById('pan-boundary-feedback');

        if (!feedbackElement) {
            feedbackElement = document.createElement('div');
            feedbackElement.id = 'pan-boundary-feedback';
            feedbackElement.className = 'pan-boundary-feedback';
            this.container.appendChild(feedbackElement);
        }

        feedbackElement.classList.add('show');

        // Hide after 1 second
        setTimeout(() => {
            feedbackElement.classList.remove('show');
        }, 1000);
    }

    /**
     * Show pan inertia indicator
     */
    showPanInertiaIndicator() {
        let indicatorElement = document.getElementById('pan-inertia-indicator');

        if (!indicatorElement) {
            indicatorElement = document.createElement('div');
            indicatorElement.id = 'pan-inertia-indicator';
            indicatorElement.className = 'pan-inertia-indicator';
            this.container.appendChild(indicatorElement);
        }

        indicatorElement.classList.add('show');

        // Remove class after animation completes
        setTimeout(() => {
            indicatorElement.classList.remove('show');
        }, 1000);
    }

    /**
     * Show pan velocity indicator
     */
    showPanVelocityIndicator() {
        let indicatorElement = document.getElementById('pan-velocity-indicator');

        if (!indicatorElement) {
            indicatorElement = document.createElement('div');
            indicatorElement.id = 'pan-velocity-indicator';
            indicatorElement.className = 'pan-velocity-indicator';
            this.container.appendChild(indicatorElement);
        }

        const velocityX = Math.round(this.panVelocityX * 100) / 100;
        const velocityY = Math.round(this.panVelocityY * 100) / 100;
        const speed = Math.sqrt(velocityX * velocityX + velocityY * velocityY);

        indicatorElement.textContent = `V: (${velocityX}, ${velocityY}) | S: ${speed.toFixed(2)}`;
        indicatorElement.classList.add('show');

        // Hide after 2 seconds
        setTimeout(() => {
            indicatorElement.classList.remove('show');
        }, 2000);
    }

    /**
     * Show pan mode indicator
     */
    showPanModeIndicator() {
        let indicatorElement = document.getElementById('pan-mode-indicator');

        if (!indicatorElement) {
            indicatorElement = document.createElement('div');
            indicatorElement.id = 'pan-mode-indicator';
            indicatorElement.className = 'pan-mode-indicator';
            indicatorElement.textContent = 'Middle mouse to pan';
            this.container.appendChild(indicatorElement);
        }

        indicatorElement.classList.add('show');

        // Hide after 3 seconds
        setTimeout(() => {
            indicatorElement.classList.remove('show');
        }, 3000);
    }

    /**
     * Show pan boundary warning
     */
    showPanBoundaryWarning() {
        let warningElement = document.getElementById('pan-boundary-warning');

        if (!warningElement) {
            warningElement = document.createElement('div');
            warningElement.id = 'pan-boundary-warning';
            warningElement.className = 'pan-boundary-warning';
            warningElement.textContent = 'Pan boundary reached';
            this.container.appendChild(warningElement);
        }

        warningElement.classList.add('show');

        // Hide after 1.5 seconds
        setTimeout(() => {
            warningElement.classList.remove('show');
        }, 1500);
    }

    /**
     * Check if pan is at boundaries
     */
    isAtPanBoundary() {
        if (!this.panBoundaries.enabled) return false;

        const rect = this.container.getBoundingClientRect();
        const containerWidth = rect.width;
        const containerHeight = rect.height;

        const maxPanX = Math.max(0, (containerWidth * this.currentZoom - containerWidth) / 2 + this.panBoundaries.padding);
        const maxPanY = Math.max(0, (containerHeight * this.currentZoom - containerHeight) / 2 + this.panBoundaries.padding);
        const minPanX = -maxPanX;
        const minPanY = -maxPanY;

        return this.panX >= maxPanX || this.panX <= minPanX ||
               this.panY >= maxPanY || this.panY <= minPanY;
    }

    /**
     * Enable pan functionality
     */
    enablePan() {
        this.panEnabled = true;
        this.container.classList.add('pan-enabled');
        this.triggerEvent('panEnabled');
    }

    /**
     * Disable pan functionality
     */
    disablePan() {
        this.panEnabled = false;
        this.container.classList.remove('pan-enabled');

        // Stop any ongoing pan operation
        if (this.isPanning) {
            this.endPan();
        }

        this.triggerEvent('panDisabled');
    }

    /**
     * Toggle pan functionality
     */
    togglePan() {
        if (this.panEnabled) {
            this.disablePan();
        } else {
            this.enablePan();
        }
    }

    /**
     * Get pan enabled state
     */
    isPanEnabled() {
        return this.panEnabled;
    }

    /**
     * Set pan boundaries
     */
    setPanBoundaries(boundaries) {
        this.panBoundaries = { ...this.panBoundaries, ...boundaries };
        this.triggerEvent('panBoundariesChanged', this.panBoundaries);
    }

    /**
     * Get pan boundaries
     */
    getPanBoundaries() {
        return { ...this.panBoundaries };
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyDown(event) {
        // Prevent shortcuts when typing in input fields
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA' || event.target.contentEditable === 'true') {
            return;
        }

        // Zoom in/out with Ctrl/Cmd + +/- or Ctrl/Cmd + mouse wheel
        if ((event.ctrlKey || event.metaKey) && (event.key === '+' || event.key === '=')) {
            event.preventDefault();
            this.zoomIn();
            this.showKeyboardShortcutFeedback('Zoom In', 'Ctrl + +');
        } else if ((event.ctrlKey || event.metaKey) && event.key === '-') {
            event.preventDefault();
            this.zoomOut();
            this.showKeyboardShortcutFeedback('Zoom Out', 'Ctrl + -');
        } else if ((event.ctrlKey || event.metaKey) && event.key === '0') {
            event.preventDefault();
            this.resetView();
            this.showKeyboardShortcutFeedback('Reset View', 'Ctrl + 0');
        } else if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
            event.preventDefault();
            this.fitToView();
            this.showKeyboardShortcutFeedback('Fit to View', 'Ctrl + F');
        }

        // Undo/Redo zoom
        if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
            event.preventDefault();
            this.undoZoom();
            this.showKeyboardShortcutFeedback('Undo Zoom', 'Ctrl + Z');
        } else if ((event.ctrlKey || event.metaKey) && event.key === 'z' && event.shiftKey) {
            event.preventDefault();
            this.redoZoom();
            this.showKeyboardShortcutFeedback('Redo Zoom', 'Ctrl + Shift + Z');
        } else if ((event.ctrlKey || event.metaKey) && event.key === 'y') {
            event.preventDefault();
            this.redoZoom();
            this.showKeyboardShortcutFeedback('Redo Zoom', 'Ctrl + Y');
        }

        // Pan controls with arrow keys
        if (event.key === 'ArrowUp' || event.key === 'ArrowDown' || event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
            if (event.shiftKey) {
                event.preventDefault();
                const panStep = 50;
                let deltaX = 0;
                let deltaY = 0;

                switch (event.key) {
                    case 'ArrowUp':
                        deltaY = -panStep;
                        break;
                    case 'ArrowDown':
                        deltaY = panStep;
                        break;
                    case 'ArrowLeft':
                        deltaX = -panStep;
                        break;
                    case 'ArrowRight':
                        deltaX = panStep;
                        break;
                }

                this.panX += deltaX;
                this.panY += deltaY;
                this.queueViewportUpdate();
                this.saveZoomState();

                this.showKeyboardShortcutFeedback('Pan', `Shift + ${event.key}`);
            }
        }

        // Zoom presets
        if ((event.ctrlKey || event.metaKey) && event.key >= '1' && event.key <= '9') {
            event.preventDefault();
            const zoomLevel = parseInt(event.key) / 10;
            this.setZoom(zoomLevel);
            this.showKeyboardShortcutFeedback(`Zoom ${Math.round(zoomLevel * 100)}%`, `Ctrl + ${event.key}`);
        }

        // Toggle pan mode
        if (event.key === 'p' && !event.ctrlKey && !event.metaKey) {
            event.preventDefault();
            this.togglePan();
            const status = this.isPanEnabled() ? 'Enabled' : 'Disabled';
            this.showKeyboardShortcutFeedback(`Pan ${status}`, 'P');
        }

        // Toggle help overlay
        if (event.key === 'F1' || ((event.ctrlKey || event.metaKey) && event.key === 'h')) {
            event.preventDefault();
            this.toggleHelpOverlay();
        }

        // Escape key to cancel operations
        if (event.key === 'Escape') {
            event.preventDefault();
            this.cancelOperations();
        }
    }

    /**
     * Show keyboard shortcut feedback
     */
    showKeyboardShortcutFeedback(action, shortcut) {
        let feedbackElement = document.getElementById('keyboard-shortcut-feedback');

        if (!feedbackElement) {
            feedbackElement = document.createElement('div');
            feedbackElement.id = 'keyboard-shortcut-feedback';
            feedbackElement.className = 'keyboard-shortcut-feedback';
            this.container.appendChild(feedbackElement);
        }

        feedbackElement.innerHTML = `
            <div class="shortcut-action">${action}</div>
            <div class="shortcut-keys">${shortcut}</div>
        `;
        feedbackElement.classList.add('show');

        // Hide after 2 seconds
        setTimeout(() => {
            feedbackElement.classList.remove('show');
        }, 2000);
    }

    /**
     * Toggle help overlay
     */
    toggleHelpOverlay() {
        let helpOverlay = document.getElementById('help-overlay');

        if (!helpOverlay) {
            helpOverlay = this.createHelpOverlay();
        }

        if (helpOverlay.classList.contains('show')) {
            helpOverlay.classList.remove('show');
        } else {
            helpOverlay.classList.add('show');
        }
    }

    /**
     * Create help overlay
     */
    createHelpOverlay() {
        const helpOverlay = document.createElement('div');
        helpOverlay.id = 'help-overlay';
        helpOverlay.className = 'help-overlay';

        const helpContent = document.createElement('div');
        helpContent.className = 'help-content';

        helpContent.innerHTML = `
            <div class="help-header">
                <h2>Keyboard Shortcuts</h2>
                <button class="help-close" onclick="this.closest('.help-overlay').classList.remove('show')">&times;</button>
            </div>
            <div class="help-grid">
                <div class="help-section">
                    <h3>Zoom Controls</h3>
                    <div class="space-y-1">
                        <div><kbd>Ctrl</kbd> + <kbd>+</kbd> Zoom In</div>
                        <div><kbd>Ctrl</kbd> + <kbd>-</kbd> Zoom Out</div>
                        <div><kbd>Ctrl</kbd> + <kbd>0</kbd> Reset View</div>
                        <div><kbd>Ctrl</kbd> + <kbd>F</kbd> Fit to View</div>
                        <div><kbd>Ctrl</kbd> + <kbd>1-9</kbd> Zoom Presets (10%-90%)</div>
                    </div>
                </div>
                <div class="help-section">
                    <h3>Pan Controls</h3>
                    <div class="space-y-1">
                        <div><kbd>Shift</kbd> + <kbd>↑↓←→</kbd> Pan View</div>
                        <div><kbd>P</kbd> Toggle Pan Mode</div>
                        <div><kbd>Middle Mouse</kbd> Drag to Pan</div>
                    </div>
                </div>
                <div class="help-section">
                    <h3>History</h3>
                    <div class="space-y-1">
                        <div><kbd>Ctrl</kbd> + <kbd>Z</kbd> Undo Zoom</div>
                        <div><kbd>Ctrl</kbd> + <kbd>Y</kbd> Redo Zoom</div>
                        <div><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Z</kbd> Redo Zoom</div>
                    </div>
                </div>
                <div class="help-section">
                    <h3>General</h3>
                    <div class="space-y-1">
                        <div><kbd>F1</kbd> or <kbd>Ctrl</kbd> + <kbd>H</kbd> Show/Hide Help</div>
                        <div><kbd>Esc</kbd> Cancel Operations</div>
                    </div>
                </div>
            </div>
        `;

        helpOverlay.appendChild(helpContent);
        document.body.appendChild(helpOverlay);

        // Close on overlay click
        helpOverlay.addEventListener('click', (e) => {
            if (e.target === helpOverlay) {
                helpOverlay.classList.remove('show');
            }
        });

        return helpOverlay;
    }

    /**
     * Cancel ongoing operations
     */
    cancelOperations() {
        // Stop pan inertia
        this.stopPanInertia();

        // End panning if active
        if (this.isPanning) {
            this.endPan();
        }

        // Hide any open help overlay
        const helpOverlay = document.getElementById('help-overlay');
        if (helpOverlay && helpOverlay.classList.contains('show')) {
            helpOverlay.classList.remove('show');
        }

        // Reset cursor
        this.container.style.cursor = '';
        this.container.classList.remove('panning');

        this.showKeyboardShortcutFeedback('Operations Cancelled', 'Esc');
    }

    /**
     * Handle window resize
     */
    handleResize() {
        // Debounce resize events
        clearTimeout(this.resizeTimeout);
        this.resizeTimeout = setTimeout(() => {
            this.updateViewport();
        }, 100);
    }

    /**
     * Zoom in by one step
     */
    zoomIn() {
        this.zoomAtPoint(1 + this.zoomStep);
    }

    /**
     * Zoom out by one step
     */
    zoomOut() {
        this.zoomAtPoint(1 - this.zoomStep);
    }

    /**
     * Zoom at a specific point
     */
    zoomAtPoint(zoomFactor, centerX = null, centerY = null, smooth = false) {
        // Calculate new zoom level
        const newZoom = Math.max(this.minZoom, Math.min(this.maxZoom, this.currentZoom * zoomFactor));

        // If zoom hasn't changed, don't update
        if (Math.abs(newZoom - this.currentZoom) < 0.001) return;

        // Calculate zoom center
        const center = centerX !== null && centerY !== null
            ? this.screenToSVG(centerX, centerY)
            : { x: this.container.clientWidth / 2, y: this.container.clientHeight / 2 };

        // Calculate new pan position to keep center point fixed
        const zoomRatio = newZoom / this.currentZoom;
        const newPanX = center.x - (center.x - this.panX) * zoomRatio;
        const newPanY = center.y - (center.y - this.panY) * zoomRatio;

        // Apply zoom with constraints
        this.applyZoomWithConstraints(newZoom, newPanX, newPanY, smooth);

        // Queue throttled zoom update
        if (this.throttledUpdateManager) {
            this.throttledUpdateManager.queueUpdate('zoom', {
                zoom: this.currentZoom,
                zoomFactor: zoomFactor,
                centerX: center.x,
                centerY: center.y
            });
        }
    }

    /**
     * Apply zoom with constraints
     */
    applyZoomWithConstraints(newZoom, newPanX, newPanY, smooth = false) {
        // Apply pan boundaries
        const constrainedPan = this.applyPanBoundaries(newPanX, newPanY);

        // Update viewport state
        this.currentZoom = newZoom;
        this.panX = constrainedPan.x;
        this.panY = constrainedPan.y;

        // Apply smooth transition if requested
        if (smooth) {
            this.applySmoothZoom(newZoom, this.panX, this.panY);
        } else {
            // Queue throttled viewport update
            if (this.throttledUpdateManager) {
                this.throttledUpdateManager.queueUpdate('viewport', {
                    zoom: this.currentZoom,
                    panX: this.panX,
                    panY: this.panY
                });
            } else {
                // Fallback to immediate update
                this.updateViewport();
            }
        }

        // Save zoom state for undo/redo
        this.saveZoomState();

        // Trigger zoom changed event
        this.triggerEvent('zoomChanged', {
            zoom: this.currentZoom,
            panX: this.panX,
            panY: this.panY
        });
    }

    /**
     * Apply smooth zoom transition
     */
    applySmoothZoom(targetZoom, targetPanX, targetPanY) {
        if (this.isAnimating) return;

        this.isAnimating = true;
        this.targetZoom = targetZoom;
        this.targetPanX = targetPanX;
        this.targetPanY = targetPanY;

        const startZoom = this.currentZoom;
        const startPanX = this.panX;
        const startPanY = this.panY;
        const startTime = performance.now();
        const duration = this.wheelZoomDuration;

        const animate = (currentTime) => {
            if (!this.isAnimating) return;

            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Use easing function for smooth animation
            const easeProgress = this.easeInOutCubic(progress);

            // Interpolate values
            this.currentZoom = startZoom + (targetZoom - startZoom) * easeProgress;
            this.panX = startPanX + (targetPanX - startPanX) * easeProgress;
            this.panY = startPanY + (targetPanY - startPanY) * easeProgress;

            // Queue throttled viewport update
            if (this.throttledUpdateManager) {
                this.throttledUpdateManager.queueUpdate('viewport', {
                    zoom: this.currentZoom,
                    panX: this.panX,
                    panY: this.panY
                });
            } else {
                // Fallback to immediate update
                this.updateViewport();
            }

            // Continue animation or finish
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.isAnimating = false;
                this.targetZoom = null;
                this.targetPanX = null;
                this.targetPanY = null;
            }
        };

        requestAnimationFrame(animate);
    }

    /**
     * Easing function for smooth animations
     */
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    /**
     * Reset view to default zoom and pan
     */
    resetView() {
        this.currentZoom = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.updateViewport();
        this.saveZoomState();
        this.triggerEvent('viewReset');
    }

    /**
     * Fit all objects in the viewport
     */
    fitToView() {
        const objects = this.svg.querySelectorAll('[data-placed-symbol="true"], .bim-object');
        if (objects.length === 0) return;

        // Calculate bounding box of all objects
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

        objects.forEach(obj => {
            const bbox = obj.getBBox();
            minX = Math.min(minX, bbox.x);
            minY = Math.min(minY, bbox.y);
            maxX = Math.max(maxX, bbox.x + bbox.width);
            maxY = Math.max(maxY, bbox.y + bbox.height);
        });

        // Add padding
        const padding = 50;
        minX -= padding;
        minY -= padding;
        maxX += padding;
        maxY += padding;

        // Calculate zoom to fit
        const containerRect = this.container.getBoundingClientRect();
        const scaleX = containerRect.width / (maxX - minX);
        const scaleY = containerRect.height / (maxY - minY);
        const scale = Math.min(scaleX, scaleY, this.maxZoom);

        // Calculate pan to center
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;

        this.currentZoom = scale;
        this.panX = containerRect.width / 2 - centerX * scale;
        this.panY = containerRect.height / 2 - centerY * scale;

        this.updateViewport();
        this.saveZoomState();
        this.triggerEvent('fitToView');
    }

    /**
     * Convert screen coordinates to SVG coordinates
     */
    screenToSVG(screenX, screenY) {
        const pt = this.svg.createSVGPoint();
        pt.x = screenX;
        pt.y = screenY;
        const svgPoint = pt.matrixTransform(this.svg.getScreenCTM().inverse());
        return { x: svgPoint.x, y: svgPoint.y };
    }

    /**
     * Convert SVG coordinates to screen coordinates
     */
    svgToScreen(svgX, svgY) {
        const pt = this.svg.createSVGPoint();
        pt.x = svgX;
        pt.y = svgY;
        const screenPoint = pt.matrixTransform(this.svg.getScreenCTM());
        return { x: screenPoint.x, y: screenPoint.y };
    }

    /**
     * Get current viewport transform matrix
     */
    getViewportTransform() {
        return {
            translateX: this.panX,
            translateY: this.panY,
            scale: this.currentZoom
        };
    }

    /**
     * Update the viewport transform
     */
    updateViewport() {
        if (this.isUpdating) return;

        // Queue throttled update if available
        if (this.throttledUpdateManager) {
            this.throttledUpdateManager.queueUpdate('viewport', {
                zoom: this.currentZoom,
                panX: this.panX,
                panY: this.panY
            });
            return;
        }

        // Fallback to immediate update
        this.performViewportUpdate();
    }

    /**
     * Perform the actual viewport update
     */
    performViewportUpdate() {
        this.isUpdating = true;

        try {
            // Calculate transform
            const transform = `translate(${this.panX},${this.panY}) scale(${this.currentZoom})`;

            // Apply transform to SVG viewport
            const viewport = this.svg.querySelector('#svg-viewport');
            if (viewport) {
                viewport.setAttribute('transform', transform);
            }

            // Update zoom display
            this.updateZoomDisplay();

            // Update zoom button states
            this.updateZoomButtonStates();

            // Trigger viewport changed event
            this.triggerEvent('viewportChanged', {
                zoom: this.currentZoom,
                panX: this.panX,
                panY: this.panY,
                transform: transform
            });

        } catch (error) {
            console.error('Error updating viewport:', error);
        } finally {
            this.isUpdating = false;
        }
    }

    /**
     * Update zoom level display
     */
    updateZoomDisplay() {
        const zoomDisplay = document.getElementById('zoom-level');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.currentZoom * 100)}%`;
        }
    }

    /**
     * Save current zoom state to history
     */
    saveZoomState() {
        const state = {
            zoom: this.currentZoom,
            panX: this.panX,
            panY: this.panY,
            timestamp: Date.now()
        };

        // Remove any states after current index (for redo)
        this.zoomHistory = this.zoomHistory.slice(0, this.historyIndex + 1);

        // Add new state
        this.zoomHistory.push(state);
        this.historyIndex++;

        // Limit history size
        if (this.zoomHistory.length > this.maxHistorySize) {
            this.zoomHistory.shift();
            this.historyIndex--;
        }
    }

    /**
     * Undo last zoom operation
     */
    undoZoom() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const state = this.zoomHistory[this.historyIndex];
            this.restoreZoomState(state);
        }
    }

    /**
     * Redo zoom operation
     */
    redoZoom() {
        if (this.historyIndex < this.zoomHistory.length - 1) {
            this.historyIndex++;
            const state = this.zoomHistory[this.historyIndex];
            this.restoreZoomState(state);
        }
    }

    /**
     * Restore zoom state
     */
    restoreZoomState(state) {
        this.currentZoom = state.zoom;
        this.panX = state.panX;
        this.panY = state.panY;
        this.updateViewport();
        this.triggerEvent('zoomRestored', state);
    }

    /**
     * Get current zoom level
     */
    getZoom() {
        return this.currentZoom;
    }

    /**
     * Set zoom level
     */
    setZoom(zoom) {
        const newZoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
        if (newZoom !== this.currentZoom) {
            this.currentZoom = newZoom;
            this.updateViewport();
            this.saveZoomState();
        }
    }

    /**
     * Get current pan position
     */
    getPan() {
        return { x: this.panX, y: this.panY };
    }

    /**
     * Set pan position
     */
    setPan(x, y) {
        this.panX = x;
        this.panY = y;
        this.updateViewport();
        this.triggerEvent('panChanged', { x: this.panX, y: this.panY });
    }

    /**
     * Set scale factors for real-world coordinate conversion
     */
    setScaleFactors(scaleX, scaleY, unit = 'pixels') {
        this.scaleFactors.x = scaleX;
        this.scaleFactors.y = scaleY;
        this.currentUnit = unit;

        this.triggerEvent('scaleFactorsChanged', {
            x: this.scaleFactors.x,
            y: this.scaleFactors.y,
            unit: this.currentUnit
        });

        // Log scale factor updates
        if (window.arxLogger) {
          window.arxLogger.info('ViewportManager: Scale factors updated', {
            component: 'viewport_manager',
            scale_x: scaleX,
            scale_y: scaleY,
            unit: unit
          });
        }
    }

    /**
     * Get current scale factors
     */
    getScaleFactors() {
        return {
            x: this.scaleFactors.x,
            y: this.scaleFactors.y,
            unit: this.currentUnit
        };
    }

    /**
     * Convert screen coordinates to real-world coordinates
     */
    screenToRealWorld(screenX, screenY) {
        const svgCoords = this.screenToSVG(screenX, screenY);
        return this.svgToRealWorld(svgCoords.x, svgCoords.y);
    }

    /**
     * Convert real-world coordinates to screen coordinates
     */
    realWorldToScreen(realWorldX, realWorldY) {
        const svgCoords = this.realWorldToSVG(realWorldX, realWorldY);
        return this.svgToScreen(svgCoords.x, svgCoords.y);
    }

    /**
     * Convert SVG coordinates to real-world coordinates
     */
    svgToRealWorld(svgX, svgY) {
        return {
            x: svgX * this.scaleFactors.x,
            y: svgY * this.scaleFactors.y
        };
    }

    /**
     * Convert real-world coordinates to SVG coordinates
     */
    realWorldToSVG(realWorldX, realWorldY) {
        return {
            x: realWorldX / this.scaleFactors.x,
            y: realWorldY / this.scaleFactors.y
        };
    }

    /**
     * Get distance in real-world units between two points
     */
    getRealWorldDistance(point1, point2) {
        const dx = (point2.x - point1.x) * this.scaleFactors.x;
        const dy = (point2.y - point1.y) * this.scaleFactors.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    /**
     * Get area in real-world units
     */
    getRealWorldArea(width, height) {
        const realWidth = width * this.scaleFactors.x;
        const realHeight = height * this.scaleFactors.y;
        return realWidth * realHeight;
    }

    /**
     * Check if scale factors are uniform (same X and Y scale)
     */
    isUniformScale() {
        const tolerance = 0.01; // 1% tolerance
        return Math.abs(this.scaleFactors.x - this.scaleFactors.y) < tolerance;
    }

    /**
     * Get scale ratio (e.g., "1:100" for 1 pixel = 100 units)
     */
    getScaleRatio() {
        if (this.isUniformScale()) {
            const ratio = 1 / this.scaleFactors.x;
            return `1:${ratio.toFixed(2)}`;
        } else {
            const ratioX = 1 / this.scaleFactors.x;
            const ratioY = 1 / this.scaleFactors.y;
            return `X:1:${ratioX.toFixed(2)} Y:1:${ratioY.toFixed(2)}`;
        }
    }

    /**
     * Add event listener
     */
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Remove event listener
     */
    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Trigger custom event
     */
    triggerEvent(event, data = {}) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    /**
     * ===== VIEWPORT CULLING METHODS =====
     * Performance optimization to only render visible objects
     */

    /**
     * Get current viewport bounds with margin
     */
    getViewportBounds() {
        const rect = this.container.getBoundingClientRect();
        const margin = this.cullingMargin;

        return {
            left: -this.panX / this.currentZoom - margin,
            top: -this.panY / this.currentZoom - margin,
            right: (-this.panX + rect.width) / this.currentZoom + margin,
            bottom: (-this.panY + rect.height) / this.currentZoom + margin,
            width: rect.width / this.currentZoom + (margin * 2),
            height: rect.height / this.currentZoom + (margin * 2)
        };
    }

    /**
     * Get object bounds from cache or calculate
     */
    getObjectBounds(object) {
        const objectId = object.getAttribute('data-object-id') || object.id || object.dataset.placedSymbol;

        if (!objectId) {
            return this.calculateObjectBounds(object);
        }

        // Check cache first
        const cached = this.objectBoundsCache.get(objectId);
        if (cached && Date.now() - cached.timestamp < this.boundsCacheExpiry) {
            return cached.bounds;
        }

        // Calculate and cache
        const bounds = this.calculateObjectBounds(object);
        this.objectBoundsCache.set(objectId, {
            bounds: bounds,
            timestamp: Date.now()
        });

        return bounds;
    }

    /**
     * Calculate object bounds in SVG coordinates
     */
    calculateObjectBounds(object) {
        try {
            // Get the bounding box in SVG coordinates
            const bbox = object.getBBox();

            // Apply any transforms to get actual position
            const transform = object.transform.baseVal;
            let x = bbox.x;
            let y = bbox.y;
            let width = bbox.width;
            let height = bbox.height;

            // Apply transforms if present
            if (transform.numberOfItems > 0) {
                const matrix = transform.consolidate().matrix;
                const points = [
                    { x: bbox.x, y: bbox.y },
                    { x: bbox.x + bbox.width, y: bbox.y },
                    { x: bbox.x, y: bbox.y + bbox.height },
                    { x: bbox.x + bbox.width, y: bbox.y + bbox.height }
                ];

                const transformedPoints = points.map(point => ({
                    x: matrix.a * point.x + matrix.c * point.y + matrix.e,
                    y: matrix.b * point.x + matrix.d * point.y + matrix.f
                }));

                const minX = Math.min(...transformedPoints.map(p => p.x));
                const maxX = Math.max(...transformedPoints.map(p => p.x));
                const minY = Math.min(...transformedPoints.map(p => p.y));
                const maxY = Math.max(...transformedPoints.map(p => p.y));

                x = minX;
                y = minY;
                width = maxX - minX;
                height = maxY - minY;
            }

            return { x, y, width, height };
        } catch (error) {
            // Fallback: use getBoundingClientRect and convert to SVG coordinates
            const rect = object.getBoundingClientRect();
            const svgPoint = this.svg.createSVGPoint();
            svgPoint.x = rect.left;
            svgPoint.y = rect.top;
            const transformed = svgPoint.matrixTransform(this.svg.getScreenCTM().inverse());

            return {
                x: transformed.x,
                y: transformed.y,
                width: rect.width / this.currentZoom,
                height: rect.height / this.currentZoom
            };
        }
    }

    /**
     * Check if object is visible in viewport
     */
    isObjectVisible(object) {
        if (!this.cullingEnabled) {
            return true;
        }

        const viewportBounds = this.getViewportBounds();
        const objectBounds = this.getObjectBounds(object);

        // Check if object bounds intersect with viewport bounds
        return !(
            objectBounds.x + objectBounds.width < viewportBounds.left ||
            objectBounds.x > viewportBounds.right ||
            objectBounds.y + objectBounds.height < viewportBounds.top ||
            objectBounds.y > viewportBounds.bottom
        );
    }

    /**
     * Update object visibility based on viewport culling
     */
    updateObjectVisibility(object) {
        const isVisible = this.isObjectVisible(object);
        const wasVisible = !object.classList.contains('culled');

        if (isVisible !== wasVisible) {
            if (isVisible) {
                object.classList.remove('culled');
                object.style.display = '';
                this.visibleObjects.add(object);
            } else {
                object.classList.add('culled');
                object.style.display = 'none';
                this.visibleObjects.delete(object);
            }
        }

        return isVisible;
    }

    /**
     * Perform viewport culling on all objects
     */
    performViewportCulling() {
        if (!this.cullingEnabled) {
            return;
        }

        const startTime = performance.now();

        // Get all objects that should be culled
        const objects = this.svg.querySelectorAll('.placed-symbol, .bim-object, [data-placed-symbol="true"]');
        this.totalObjects = objects.length;

        // Clear previous visible objects set
        this.visibleObjects.clear();

        let visibleCount = 0;
        let culledCount = 0;

        // Update visibility for each object
        objects.forEach(object => {
            const isVisible = this.updateObjectVisibility(object);
            if (isVisible) {
                visibleCount++;
            } else {
                culledCount++;
            }
        });

        // Update stats
        const cullingTime = performance.now() - startTime;
        this.cullingStats = {
            totalObjects: this.totalObjects,
            visibleObjects: visibleCount,
            culledObjects: culledCount,
            cullingTime: cullingTime,
            lastUpdate: Date.now()
        };

        // Clean up bounds cache periodically
        this.cleanupBoundsCache();

        // Trigger culling update event
        this.triggerEvent('cullingUpdated', this.cullingStats);

        // Line 2340: console.log(`ViewportCulling: ${visibleCount}/${this.totalObjects} objects visible (${culledCount} culled) in ${cullingTime.toFixed(2)}ms`);
        if (window.arxLogger) {
          window.arxLogger.performance('viewport_culling', cullingTime, {
            component: 'viewport_manager',
            visible_count: visibleCount,
            total_objects: this.totalObjects,
            culled_count: culledCount,
            culling_time_ms: cullingTime.toFixed(2)
          });
        }
    }

    /**
     * Clean up expired bounds cache entries
     */
    cleanupBoundsCache() {
        const now = Date.now();
        if (now - this.lastBoundsCacheCleanup < 10000) { // Clean up every 10 seconds
            return;
        }

        this.lastBoundsCacheCleanup = now;
        let cleanedCount = 0;

        for (const [id, entry] of this.objectBoundsCache.entries()) {
            if (now - entry.timestamp > this.boundsCacheExpiry) {
                this.objectBoundsCache.delete(id);
                cleanedCount++;
            }
        }

        if (cleanedCount > 0) {
            // Line 2364: console.log(`ViewportCulling: Cleaned up ${cleanedCount} expired bounds cache entries`);
            if (window.arxLogger) {
              window.arxLogger.info('ViewportCulling: Cleaned up expired bounds cache entries', {
                component: 'viewport_manager',
                cleaned_count: cleanedCount,
                cache_type: 'bounds_cache'
              });
            }
        }
    }

    /**
     * Queue a culling update
     */
    queueCullingUpdate() {
        if (!this.cullingEnabled) return;

        // Queue throttled culling update
        if (this.throttledUpdateManager) {
            this.throttledUpdateManager.queueUpdate('culling', {
                viewportBounds: this.getViewportBounds(),
                totalObjects: this.totalObjects
            });
        } else {
            // Fallback to immediate update
            this.performViewportCulling();
        }
    }

    /**
     * Enable viewport culling
     */
    enableCulling() {
        this.cullingEnabled = true;
        this.performViewportCulling();
        // Line 2392: console.log('ViewportCulling: Enabled');
        if (window.arxLogger) {
          window.arxLogger.info('ViewportCulling: Enabled', {
            component: 'viewport_manager',
            feature: 'viewport_culling',
            status: 'enabled'
          });
        }
    }

    /**
     * Disable viewport culling
     */
    disableCulling() {
        this.cullingEnabled = false;

        // Show all objects
        const objects = this.svg.querySelectorAll('.culled');
        objects.forEach(object => {
            object.classList.remove('culled');
            object.style.display = '';
        });

        this.visibleObjects.clear();
        // Line 2409: console.log('ViewportCulling: Disabled');
        if (window.arxLogger) {
          window.arxLogger.info('ViewportCulling: Disabled', {
            component: 'viewport_manager',
            feature: 'viewport_culling',
            status: 'disabled'
          });
        }
    }

    /**
     * Toggle viewport culling
     */
    toggleCulling() {
        if (this.cullingEnabled) {
            this.disableCulling();
        } else {
            this.enableCulling();
        }
    }

    /**
     * Get culling statistics
     */
    getCullingStats() {
        return { ...this.cullingStats };
    }

    /**
     * Set culling margin
     */
    setCullingMargin(margin) {
        this.cullingMargin = margin;
        this.performViewportCulling();
        // Line 2436: console.log(`ViewportCulling: Margin set to ${margin}px`);
        if (window.arxLogger) {
          window.arxLogger.info('ViewportCulling: Margin set', {
            component: 'viewport_manager',
            feature: 'viewport_culling',
            margin_px: margin
          });
        }
    }

    /**
     * Set culling update throttle
     */
    setCullingThrottle(throttle) {
        this.cullingUpdateThrottle = throttle;
        // Line 2444: console.log(`ViewportCulling: Throttle set to ${throttle}ms`);
        if (window.arxLogger) {
          window.arxLogger.info('ViewportCulling: Throttle set', {
            component: 'viewport_manager',
            feature: 'viewport_culling',
            throttle_ms: throttle
          });
        }
    }

    /**
     * Force immediate culling update
     */
    forceCullingUpdate() {
        this.performViewportCulling();
    }

    /**
     * Destroy the viewport manager
     */
    destroy() {
        // Stop any ongoing pan inertia
        this.stopPanInertia();

        // Cancel culling animation frame
        if (this.cullingAnimationFrame) {
            cancelAnimationFrame(this.cullingAnimationFrame);
            this.cullingAnimationFrame = null;
        }

        // Clear culling resources
        this.visibleObjects.clear();
        this.objectBoundsCache.clear();

        // Remove event listeners
        this.container.removeEventListener('wheel', this.handleWheel);
        this.container.removeEventListener('mousedown', this.handleMouseDown);
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseup', this.handleMouseUp);
        document.removeEventListener('keydown', this.handleKeyDown);
        window.removeEventListener('resize', this.handleResize);

        // Clear timeouts
        if (this.updateTimeout) {
            clearTimeout(this.updateTimeout);
            this.updateTimeout = null;
        }

        // Reset state
        this.isPanning = false;
        this.panVelocityX = 0;
        this.panVelocityY = 0;
        this.lastPanTime = null;

        // Clear event handlers
        this.eventHandlers.clear();

        // Remove any visual feedback classes
        this.container.classList.remove('panning', 'zooming', 'pan-enabled');
        this.container.style.cursor = '';

        // Remove all pan-related visual elements
        const elementsToRemove = [
            'zoom-constraint',
            'pan-boundary-feedback',
            'pan-inertia-indicator',
            'pan-velocity-indicator',
            'pan-mode-indicator',
            'pan-boundary-warning',
            'keyboard-shortcut-feedback',
            'help-overlay'
        ];

        elementsToRemove.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
            }
        });
    }

    /**
     * Handle throttled update events
     */
    handleThrottledUpdate(data) {
        const { type, data: updateData } = data;

        switch (type) {
            case 'viewport':
                this.updateViewport();
                break;
            case 'zoom':
                this.updateZoomDisplay();
                this.updateZoomButtonStates();
                break;
            case 'pan':
                this.updateViewport();
                break;
            case 'culling':
                this.performViewportCulling();
                break;
            case 'symbols':
                this.updateSymbolPositions();
                break;
            case 'ui':
                this.updateUIElements();
                break;
        }
    }

    /**
     * Handle batched update events
     */
    handleBatchedUpdate(data) {
        const { type, data: batchedData } = data;

        switch (type) {
            case 'viewport':
                // Process multiple viewport updates efficiently
                this.updateViewport();
                break;
            case 'symbols':
                // Process multiple symbol updates in batch
                this.updateSymbolPositionsBatch(batchedData.updates);
                break;
            case 'culling':
                // Process multiple culling updates
                this.performViewportCulling();
                break;
        }
    }

    /**
     * Handle update processed events for performance monitoring
     */
    handleUpdateProcessed(data) {
        const { processedCount, currentFPS, frameTime, pendingUpdates } = data;

        // Update performance metrics
        this.updatePerformanceMetrics({
            processedUpdates: processedCount,
            currentFPS: currentFPS,
            frameTime: frameTime,
            pendingUpdates: pendingUpdates
        });

        // Trigger performance event
        this.triggerEvent('performanceUpdate', {
            processedUpdates: processedCount,
            currentFPS: currentFPS,
            frameTime: frameTime,
            pendingUpdates: pendingUpdates
        });
    }

    /**
     * Update performance metrics
     */
    updatePerformanceMetrics(metrics) {
        // Store performance metrics for monitoring
        this.performanceMetrics = {
            ...this.performanceMetrics,
            ...metrics,
            lastUpdate: performance.now()
        };
    }

    /**
     * Update symbol positions in batch
     */
    updateSymbolPositionsBatch(updates) {
        if (!updates || updates.length === 0) return;

        // Process all symbol updates efficiently
        const symbols = document.querySelectorAll('.placed-symbol');
        symbols.forEach(symbol => {
            const x = parseFloat(symbol.getAttribute('data-x'));
            const y = parseFloat(symbol.getAttribute('data-y'));
            const rotation = parseFloat(symbol.getAttribute('data-rotation') || '0');

            // Apply transform with rotation
            const transform = `translate(${x},${y}) rotate(${rotation})`;
            symbol.setAttribute('transform', transform);
        });
    }

    /**
     * Update UI elements
     */
    updateUIElements() {
        // Update any UI elements that depend on viewport state
        this.updateZoomDisplay();
        this.updateZoomButtonStates();

        // Update any other UI elements
        const zoomLevel = document.getElementById('zoom-level');
        if (zoomLevel) {
            zoomLevel.textContent = `${(this.currentZoom * 100).toFixed(0)}%`;
        }
    }

    getZoomPercent() {
        return Math.round(this.currentZoom * 100);
    }
    setZoomPercent(percent) {
        const zoom = Math.max(this.minZoom, Math.min(this.maxZoom, percent / 100));
        this.setZoom(zoom);
    }
    getMinZoom() {
        return this.minZoom;
    }
    getMaxZoom() {
        return this.maxZoom;
    }

    /**
     * Zoom to full extent (show all SVG content)
     */
    zoomToFullExtent() {
        const svg = this.svg;
        if (!svg) return;
        let bbox;
        try {
            bbox = svg.getBBox();
        } catch (e) {
            return;
        }
        const containerRect = this.container.getBoundingClientRect();
        const scaleX = containerRect.width / bbox.width;
        const scaleY = containerRect.height / bbox.height;
        const scale = Math.min(scaleX, scaleY, this.maxZoom);
        // Center the view
        const centerX = bbox.x + bbox.width / 2;
        const centerY = bbox.y + bbox.height / 2;
        this.currentZoom = scale;
        this.panX = containerRect.width / 2 - centerX * scale;
        this.panY = containerRect.height / 2 - centerY * scale;
        this.updateViewport();
        this.saveZoomState();
        this.triggerEvent('zoomToFullExtent');
    }

    /**
     * Zoom to fit a given bounding box (selection or object)
     * bbox: {x, y, width, height}
     */
    zoomToSelection(bbox) {
        if (!bbox || bbox.width === 0 || bbox.height === 0) return;
        const containerRect = this.container.getBoundingClientRect();
        const scaleX = containerRect.width / bbox.width;
        const scaleY = containerRect.height / bbox.height;
        const scale = Math.min(scaleX, scaleY, this.maxZoom);
        // Center the view
        const centerX = bbox.x + bbox.width / 2;
        const centerY = bbox.y + bbox.height / 2;
        this.currentZoom = scale;
        this.panX = containerRect.width / 2 - centerX * scale;
        this.panY = containerRect.height / 2 - centerY * scale;
        this.updateViewport();
        this.saveZoomState();
        this.triggerEvent('zoomToSelection', bbox);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ViewportManager;
} else if (typeof window !== 'undefined') {
    window.ViewportManager = ViewportManager;
}
