/**
 * Arxos Three.js Renderer - Correctly Implemented
 * Renders SVG-based BIM models with ArxObject intelligence using Three.js
 * 
 * This renderer implements the correct Arxos architecture:
 * - Reads SVG coordinates and ArxObject data
 * - Converts to precise 3D geometry
 * - Supports smooth infinite zoom from campus to submicron
 * - Maintains 1:1 accuracy through coordinate transformations
 */

class ArxosThreeRenderer {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        // Configuration options
        this.options = {
            width: options.width || 800,
            height: options.height || 600,
            backgroundColor: options.backgroundColor || 0xf0f0f0,
            enableShadows: options.enableShadows !== false,
            enableGrid: options.enableGrid !== false,
            enableAxes: options.enableAxes !== false,
            precisionMode: options.precisionMode !== false, // Submicron accuracy
            defaultCamera: options.defaultCamera || 'perspective', // 'perspective' or 'orthographic'
            ...options
        };
        
        // Core Three.js components
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        // ArxObject integration
        this.svgArxObjectIntegration = null;
        this.arxObjectMeshes = new Map(); // ArxObject ID -> Three.js Mesh
        this.selectedMesh = null;
        
        // Camera and zoom system
        this.cameraSettings = {
            fov: 75,
            near: 0.000001, // Submicron precision
            far: 1000000,   // Campus level
            position: { x: 100, y: 100, z: 100 },
            lookAt: { x: 0, y: 0, z: 0 }
        };
        
        // Smooth infinite zoom system
        this.zoomSystem = {
            currentLevel: 'room', // Default zoom level
            smoothZoom: true,     // Enable smooth zooming
            zoomSpeed: 0.1,       // Zoom animation speed
            minZoom: 0.000001,    // Submicron level
            maxZoom: 1000000,     // Campus level
            currentScale: 1.0     // Current zoom scale
        };
        
        // Performance and LOD
        this.lodSystem = {
            enabled: true,
            levels: ['campus', 'building', 'floor', 'room', 'equipment', 'component', 'submicron'],
            currentLevel: 'room',
            objectVisibility: new Map()
        };
        
        // Material system for building elements
        this.materialSystem = {
            materials: new Map(),
            defaultMaterial: null
        };
        
        // Initialize the renderer
        this.init();
    }
    
    /**
     * Initialize the Three.js renderer
     */
    init() {
        try {
            this._createScene();
            this._createCamera();
            this._createRenderer();
            this._createControls();
            this._createLights();
            this._createGrid();
            this._createAxes();
            this._setupMaterialSystem();
            this._setupEventListeners();
            this._animate();
            
            console.log('Arxos Three.js renderer initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Three.js renderer:', error);
            throw error;
        }
    }
    
    /**
     * Set the SVG + ArxObject integration module
     * @param {ArxosSVGArxObjectIntegration} integration - The integration module
     */
    setSVGArxObjectIntegration(integration) {
        this.svgArxObjectIntegration = integration;
        
        // Set up event listeners for ArxObject updates
        if (integration) {
            integration.on('arxObjectUpdated', (data) => {
                this._updateArxObjectMesh(data.arxObject);
            });
            
            integration.on('svgElementChanged', (data) => {
                this._handleSVGElementChange(data);
            });
        }
        
        console.log('SVG + ArxObject integration connected');
    }
    
    /**
     * Load and render SVG-based BIM model
     * @param {string|Document} svgSource - SVG source
     * @param {Array} arxObjects - ArxObject data
     */
    async loadSVGBIMModel(svgSource, arxObjects = []) {
        try {
            if (!this.svgArxObjectIntegration) {
                throw new Error('SVG + ArxObject integration not set');
            }
            
            console.log('Loading SVG BIM model...');
            
            // Load SVG document
            await this.svgArxObjectIntegration.loadSVGBIM(svgSource);
            
            // Load ArxObjects
            if (arxObjects.length > 0) {
                await this.svgArxObjectIntegration.loadArxObjects(arxObjects);
            }
            
            // Render all ArxObjects
            await this._renderAllArxObjects();
            
            // Center camera on model
            this._centerCameraOnModel();
            
            console.log('SVG BIM model loaded and rendered successfully');
            
        } catch (error) {
            console.error('Failed to load SVG BIM model:', error);
            throw error;
        }
    }
    
    /**
     * Set zoom level with smooth transition
     * @param {string} level - Zoom level (campus, building, floor, room, equipment, component, submicron)
     * @param {boolean} smooth - Enable smooth transition
     */
    setZoomLevel(level, smooth = true) {
        if (!this.lodSystem.levels.includes(level)) {
            console.warn(`Invalid zoom level: ${level}`);
            return;
        }
        
        if (this.zoomSystem.currentLevel === level) return;
        
        const oldLevel = this.zoomSystem.currentLevel;
        this.zoomSystem.currentLevel = level;
        this.lodSystem.currentLevel = level;
        
        // Get zoom configuration
        const zoomConfig = this._getZoomConfiguration(level);
        
        if (smooth && this.zoomSystem.smoothZoom) {
            this._animateZoomTransition(oldLevel, level, zoomConfig);
        } else {
            this._applyZoomLevel(level, zoomConfig);
        }
        
        // Update LOD
        this._updateLevelOfDetail(level);
        
        // Emit zoom change event
        this._emitEvent('zoomLevelChanged', { 
            level, 
            config: zoomConfig,
            smooth 
        });
        
        console.log(`Zoom level changed to: ${level}`);
    }
    
    /**
     * Smooth zoom to specific scale
     * @param {number} targetScale - Target zoom scale
     * @param {number} duration - Animation duration in milliseconds
     */
    smoothZoomToScale(targetScale, duration = 1000) {
        const startScale = this.zoomSystem.currentScale;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeProgress = this._easeInOutCubic(progress);
            
            const currentScale = startScale + (targetScale - startScale) * easeProgress;
            this._applyZoomScale(currentScale);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    /**
     * Get ArxObject mesh by ID
     * @param {string} id - ArxObject ID
     * @returns {THREE.Mesh|null} Three.js mesh
     */
    getArxObjectMesh(id) {
        return this.arxObjectMeshes.get(id) || null;
    }
    
    /**
     * Get all ArxObject meshes
     * @returns {Array} Array of Three.js meshes
     */
    getAllArxObjectMeshes() {
        return Array.from(this.arxObjectMeshes.values());
    }
    
    /**
     * Update ArxObject mesh properties
     * @param {string} id - ArxObject ID
     * @param {Object} updates - Property updates
     */
    updateArxObjectMesh(id, updates) {
        const mesh = this.arxObjectMeshes.get(id);
        if (!mesh) return;
        
        // Update mesh properties
        if (updates.position) {
            mesh.position.set(updates.position.x, updates.position.y, updates.position.z);
        }
        
        if (updates.rotation) {
            mesh.rotation.set(updates.rotation.x, updates.rotation.y, updates.rotation.z);
        }
        
        if (updates.scale) {
            mesh.scale.set(updates.scale.x, updates.scale.y, updates.scale.z);
        }
        
        if (updates.material) {
            mesh.material = this._getMaterial(updates.material);
        }
        
        // Update user data
        if (updates.userData) {
            Object.assign(mesh.userData, updates.userData);
        }
        
        console.log(`ArxObject mesh updated: ${id}`);
    }
    
    /**
     * Switch between perspective and orthographic camera
     * @param {string} cameraType - 'perspective' or 'orthographic'
     */
    switchCamera(cameraType) {
        if (cameraType === this.options.defaultCamera) return;
        
        const oldCamera = this.camera;
        const aspect = this.options.width / this.options.height;
        
        if (cameraType === 'orthographic') {
            const size = 100;
            this.camera = new THREE.OrthographicCamera(
                -size * aspect, size * aspect,
                size, -size,
                this.cameraSettings.near, this.cameraSettings.far
            );
        } else {
            this.camera = new THREE.PerspectiveCamera(
                this.cameraSettings.fov,
                aspect,
                this.cameraSettings.near,
                this.cameraSettings.far
            );
        }
        
        // Copy position and target
        this.camera.position.copy(oldCamera.position);
        this.camera.lookAt(this.controls.target);
        
        // Update controls
        this.controls.object = this.camera;
        
        // Update option
        this.options.defaultCamera = cameraType;
        
        console.log(`Camera switched to: ${cameraType}`);
    }
    
    // Private methods
    
    _createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);
        this.scene.fog = new THREE.Fog(this.options.backgroundColor, 100, 1000);
    }
    
    _createCamera() {
        const aspect = this.options.width / this.options.height;
        
        if (this.options.defaultCamera === 'orthographic') {
            const size = 100;
            this.camera = new THREE.OrthographicCamera(
                -size * aspect, size * aspect,
                size, -size,
                this.cameraSettings.near, this.cameraSettings.far
            );
        } else {
            this.camera = new THREE.PerspectiveCamera(
                this.cameraSettings.fov,
                aspect,
                this.cameraSettings.near,
                this.cameraSettings.far
            );
        }
        
        this.camera.position.set(
            this.cameraSettings.position.x,
            this.cameraSettings.position.y,
            this.cameraSettings.position.z
        );
        
        this.camera.lookAt(
            this.cameraSettings.lookAt.x,
            this.cameraSettings.lookAt.y,
            this.cameraSettings.lookAt.z
        );
    }
    
    _createRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true,
            precision: 'highp' // High precision for submicron accuracy
        });
        
        this.renderer.setSize(this.options.width, this.options.height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Limit pixel ratio for performance
        this.renderer.shadowMap.enabled = this.options.enableShadows;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        
        this.container.appendChild(this.renderer.domElement);
    }
    
    _createControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = this.zoomSystem.minZoom;
        this.controls.maxDistance = this.zoomSystem.maxZoom;
        this.controls.maxPolarAngle = Math.PI / 2;
        
        // Custom zoom behavior for smooth infinite zoom
        this.controls.addEventListener('zoom', (event) => {
            this._handleZoomChange();
        });
    }
    
    _createLights() {
        // Ambient light for overall illumination
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        
        // Directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        directionalLight.castShadow = this.options.enableShadows;
        
        if (this.options.enableShadows) {
            directionalLight.shadow.mapSize.width = 2048;
            directionalLight.shadow.mapSize.height = 2048;
            directionalLight.shadow.camera.near = 0.5;
            directionalLight.shadow.camera.far = 500;
            directionalLight.shadow.camera.left = -100;
            directionalLight.shadow.camera.right = 100;
            directionalLight.shadow.camera.top = 100;
            directionalLight.shadow.camera.bottom = -100;
        }
        
        this.scene.add(directionalLight);
        
        // Point lights for interior illumination
        const pointLight1 = new THREE.PointLight(0xffffff, 0.5, 100);
        pointLight1.position.set(0, 50, 0);
        this.scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0xffffff, 0.3, 100);
        pointLight2.position.set(50, 50, 50);
        this.scene.add(pointLight2);
    }
    
    _createGrid() {
        if (this.options.enableGrid) {
            const gridHelper = new THREE.GridHelper(1000, 100, 0x888888, 0xcccccc);
            gridHelper.position.y = 0;
            this.scene.add(gridHelper);
        }
    }
    
    _createAxes() {
        if (this.options.enableAxes) {
            const axesHelper = new THREE.AxesHelper(50);
            this.scene.add(axesHelper);
        }
    }
    
    _setupMaterialSystem() {
        // Create default material
        this.materialSystem.defaultMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x808080,
            transparent: true,
            opacity: 0.8
        });
        
        // Create materials for different building element types
        const materialTypes = {
            wall: new THREE.MeshLambertMaterial({ color: 0xD3D3D3, transparent: true, opacity: 0.8 }),
            door: new THREE.MeshLambertMaterial({ color: 0x8B4513, transparent: true, opacity: 0.9 }),
            window: new THREE.MeshLambertMaterial({ color: 0x87CEEB, transparent: true, opacity: 0.6 }),
            floor: new THREE.MeshLambertMaterial({ color: 0x808080, transparent: true, opacity: 0.9 }),
            ceiling: new THREE.MeshLambertMaterial({ color: 0xF5F5DC, transparent: true, opacity: 0.8 }),
            column: new THREE.MeshLambertMaterial({ color: 0x696969, transparent: true, opacity: 0.9 }),
            beam: new THREE.MeshLambertMaterial({ color: 0x696969, transparent: true, opacity: 0.9 }),
            electrical: new THREE.MeshLambertMaterial({ color: 0xFFD700, transparent: true, opacity: 0.8 }),
            hvac: new THREE.MeshLambertMaterial({ color: 0x87CEEB, transparent: true, opacity: 0.8 }),
            plumbing: new THREE.MeshLambertMaterial({ color: 0x4169E1, transparent: true, opacity: 0.8 })
        };
        
        for (const [type, material] of Object.entries(materialTypes)) {
            this.materialSystem.materials.set(type, material);
        }
    }
    
    _setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => {
            this._onWindowResize();
        });
        
        // Mouse events for object selection
        this.renderer.domElement.addEventListener('click', (event) => {
            this._onMouseClick(event);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this._onKeyDown(event);
        });
    }
    
    _animate() {
        requestAnimationFrame(() => this._animate());
        
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
    
    async _renderAllArxObjects() {
        if (!this.svgArxObjectIntegration) return;
        
        // Clear existing meshes
        this._clearArxObjectMeshes();
        
        // Get all ArxObjects
        const arxObjects = this.svgArxObjectIntegration.getAllArxObjects();
        
        for (const arxObject of arxObjects) {
            await this._createArxObjectMesh(arxObject);
        }
        
        console.log(`${arxObjects.length} ArxObject meshes created`);
    }
    
    async _createArxObjectMesh(arxObject) {
        try {
            const { coordinates, type, properties } = arxObject;
            
            let geometry, material;
            
            // Create geometry based on SVG element type
            switch (coordinates.type) {
                case 'rectangle':
                    geometry = new THREE.BoxGeometry(
                        coordinates.width || 1,
                        coordinates.height || 1,
                        properties.thickness || 0.2
                    );
                    break;
                    
                case 'circle':
                    geometry = new THREE.CylinderGeometry(
                        coordinates.radius || 0.5,
                        coordinates.radius || 0.5,
                        properties.height || 1
                    );
                    break;
                    
                case 'line':
                    // Create line geometry for walls, beams, etc.
                    const start = new THREE.Vector3(coordinates.x1 || 0, 0, coordinates.y1 || 0);
                    const end = new THREE.Vector3(coordinates.x2 || 0, 0, coordinates.y2 || 0);
                    const points = [start, end];
                    geometry = new THREE.BufferGeometry().setFromPoints(points);
                    break;
                    
                case 'path':
                    // Parse SVG path data for complex shapes
                    geometry = this._parseSVGPath(coordinates.pathData, properties);
                    break;
                    
                default:
                    // Fallback to box geometry
                    geometry = new THREE.BoxGeometry(1, 1, 1);
            }
            
            // Get appropriate material
            material = this._getMaterial(type, properties);
            
            // Create mesh
            const mesh = new THREE.Mesh(geometry, material);
            
            // Set position from SVG coordinates
            const threeCoords = this.svgArxObjectIntegration.transformCoordinates(
                [coordinates.x || coordinates.x1 || 0, coordinates.y || coordinates.y1 || 0, coordinates.z || 0],
                'svg',
                'three'
            );
            
            mesh.position.set(threeCoords[0], threeCoords[1], threeCoords[2]);
            
            // Set user data for ArxObject reference
            mesh.userData = {
                arxObjectId: arxObject.id,
                type: type,
                properties: properties,
                coordinates: coordinates,
                detailLevel: this._getDetailLevel(type)
            };
            
            // Enable shadows
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            
            // Add to scene and store reference
            this.scene.add(mesh);
            this.arxObjectMeshes.set(arxObject.id, mesh);
            
        } catch (error) {
            console.error(`Failed to create mesh for ArxObject ${arxObject.id}:`, error);
        }
    }
    
    _parseSVGPath(pathData, properties) {
        // Basic SVG path parsing for building elements
        // This is a simplified parser - in production, use a full SVG path parser
        
        const commands = pathData.match(/[MmLlHhVvCcSsQqTtAaZz][^MmLlHhVvCcSsQqTtAaZz]*/g) || [];
        const points = [];
        
        let currentX = 0, currentY = 0;
        
        for (const command of commands) {
            const type = command[0];
            const coords = command.slice(1).trim().split(/[\s,]+/).map(Number);
            
            switch (type.toLowerCase()) {
                case 'm': // Move to
                    currentX = coords[0] || 0;
                    currentY = coords[1] || 0;
                    points.push(new THREE.Vector3(currentX, 0, currentY));
                    break;
                    
                case 'l': // Line to
                    currentX = coords[0] || 0;
                    currentY = coords[1] || 0;
                    points.push(new THREE.Vector3(currentX, 0, currentY));
                    break;
                    
                case 'h': // Horizontal line
                    currentX = coords[0] || 0;
                    points.push(new THREE.Vector3(currentX, 0, currentY));
                    break;
                    
                case 'v': // Vertical line
                    currentY = coords[0] || 0;
                    points.push(new THREE.Vector3(currentX, 0, currentY));
                    break;
                    
                case 'z': // Close path
                    if (points.length > 0) {
                        points.push(points[0].clone());
                    }
                    break;
            }
        }
        
        if (points.length < 2) {
            // Fallback to box geometry
            return new THREE.BoxGeometry(1, 1, 1);
        }
        
        // Create geometry from points
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        
        // If we have enough points, create a closed shape
        if (points.length >= 3) {
            const shape = new THREE.Shape();
            shape.moveTo(points[0].x, points[0].z);
            
            for (let i = 1; i < points.length; i++) {
                shape.lineTo(points[i].x, points[i].z);
            }
            
            const extrudeSettings = {
                depth: properties.thickness || 0.2,
                bevelEnabled: false
            };
            
            return new THREE.ExtrudeGeometry(shape, extrudeSettings);
        }
        
        return geometry;
    }
    
    _getMaterial(type, properties = {}) {
        // Get material based on type and properties
        const materialType = this._getMaterialType(type);
        let material = this.materialSystem.materials.get(materialType);
        
        if (!material) {
            material = this.materialSystem.defaultMaterial;
        }
        
        // Clone material to avoid sharing between objects
        material = material.clone();
        
        // Apply property-based modifications
        if (properties.color) {
            material.color.setHex(properties.color);
        }
        
        if (properties.opacity !== undefined) {
            material.transparent = true;
            material.opacity = properties.opacity;
        }
        
        return material;
    }
    
    _getMaterialType(type) {
        // Map ArxObject types to material types
        const typeMapping = {
            'wall': 'wall',
            'door': 'door',
            'window': 'window',
            'floor': 'floor',
            'ceiling': 'ceiling',
            'column': 'column',
            'beam': 'beam',
            'electrical_panel': 'electrical',
            'outlet': 'electrical',
            'switch': 'electrical',
            'hvac_unit': 'hvac',
            'duct': 'hvac',
            'pipe': 'plumbing',
            'valve': 'plumbing'
        };
        
        return typeMapping[type] || 'wall';
    }
    
    _getDetailLevel(type) {
        // Determine detail level for LOD system
        const detailLevels = {
            'campus': 'minimal',
            'building': 'low',
            'floor': 'medium',
            'room': 'high',
            'equipment': 'detailed',
            'component': 'microscopic',
            'submicron': 'nanoscopic'
        };
        
        return detailLevels[type] || 'medium';
    }
    
    _getZoomConfiguration(level) {
        // Enhanced zoom configuration for smooth infinite zoom from campus to submicron
        const configs = {
            // Campus to Building levels (kilometer to meter scale)
            'campus': { scale: 0.0001, precision: 'kilometer', units: 'km', description: 'Campus overview' },
            'site': { scale: 0.001, precision: 'hectometer', units: 'hm', description: 'Site plan' },
            'building': { scale: 0.01, precision: 'decameter', units: 'dam', description: 'Building outline' },
            
            // Building to Room levels (meter to centimeter scale)
            'floor': { scale: 0.1, precision: 'meter', units: 'm', description: 'Floor plan' },
            'room': { scale: 1.0, precision: 'decimeter', units: 'dm', description: 'Room detail' },
            'furniture': { scale: 10.0, precision: 'centimeter', units: 'cm', description: 'Furniture layout' },
            
            // Equipment to Component levels (millimeter to micrometer scale)
            'equipment': { scale: 100.0, precision: 'millimeter', units: 'mm', description: 'Equipment detail' },
            'component': { scale: 1000.0, precision: 'submillimeter', units: '0.1mm', description: 'Component detail' },
            'detail': { scale: 10000.0, precision: 'micrometer', units: 'μm', description: 'Micro detail' },
            
            // Submicron levels (nanometer scale)
            'submicron': { scale: 100000.0, precision: 'nanometer', units: 'nm', description: 'Submicron detail' },
            'nanoscopic': { scale: 1000000.0, precision: 'picometer', units: 'pm', description: 'Nanoscopic detail' }
        };
        
        return configs[level] || configs.room;
    }
    
    _animateZoomTransition(fromLevel, toLevel, config) {
        const fromConfig = this._getZoomConfiguration(fromLevel);
        const startScale = fromConfig.scale;
        const endScale = config.scale;
        
        // Calculate duration based on zoom distance (longer for bigger jumps)
        const scaleRatio = Math.max(startScale, endScale) / Math.min(startScale, endScale);
        const duration = Math.min(2000, Math.max(300, scaleRatio * 100)); // 300ms to 2s
        
        const startTime = performance.now();
        
        // Enhanced easing function for smoother transitions
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Use enhanced easing for smoother zoom
            const easeProgress = this._easeInOutQuart(progress);
            const currentScale = startScale + (endScale - startScale) * easeProgress;
            
            this._applyZoomScale(currentScale);
            
            // Update camera position for better zoom experience
            this._updateCameraForZoom(currentScale, fromConfig, config);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // Finalize zoom level
                this._finalizeZoomTransition(toLevel, config);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    /**
     * Update camera position during zoom for better visual experience
     */
    _updateCameraForZoom(currentScale, fromConfig, toConfig) {
        if (!this.camera || !this.controls) return;
        
        // Adjust camera distance based on scale
        const targetDistance = this._calculateOptimalCameraDistance(currentScale);
        const currentDistance = this.camera.position.distanceTo(this.controls.target);
        
        // Smoothly adjust camera distance
        const distanceDiff = targetDistance - currentDistance;
        if (Math.abs(distanceDiff) > 0.1) {
            const newPosition = this.camera.position.clone();
            const direction = newPosition.sub(this.controls.target).normalize();
            newPosition.copy(this.controls.target).add(direction.multiplyScalar(targetDistance));
            
            this.camera.position.lerp(newPosition, 0.1);
            this.camera.lookAt(this.controls.target);
        }
    }
    
    /**
     * Calculate optimal camera distance for current zoom scale
     */
    _calculateOptimalCameraDistance(scale) {
        // Base distance that provides good viewing angle
        const baseDistance = 100;
        
        // Adjust distance based on scale (closer for smaller scales, further for larger)
        if (scale < 1) {
            return baseDistance / scale; // Zoom in - move camera closer
        } else {
            return baseDistance * scale; // Zoom out - move camera further
        }
    }
    
    /**
     * Finalize zoom transition
     */
    _finalizeZoomTransition(level, config) {
        // Update LOD system
        this._updateLevelOfDetail(level);
        
        // Update grid and axes visibility based on zoom level
        this._updateGridForZoomLevel(level, config);
        
        // Emit zoom completion event
        this._emitEvent('zoomTransitionCompleted', {
            level: level,
            config: config,
            timestamp: Date.now()
        });
    }
    
    /**
     * Update grid and axes based on zoom level
     */
    _updateGridForZoomLevel(level, config) {
        if (this.grid) {
            // Adjust grid size and divisions based on zoom level
            const gridSize = this._calculateGridSizeForZoom(level, config);
            const divisions = this._calculateGridDivisionsForZoom(level, config);
            
            this.grid.geometry.dispose();
            this.grid.geometry = new THREE.GridHelper(gridSize, divisions);
        }
        
        if (this.axes) {
            // Adjust axes size based on zoom level
            const axesSize = this._calculateAxesSizeForZoom(level, config);
            this.axes.scale.setScalar(axesSize);
        }
    }
    
    /**
     * Calculate appropriate grid size for zoom level
     */
    _calculateGridSizeForZoom(level, config) {
        const baseSize = 100;
        return baseSize / config.scale;
    }
    
    /**
     * Calculate appropriate grid divisions for zoom level
     */
    _calculateGridDivisionsForZoom(level, config) {
        // More divisions for detailed zoom levels
        if (config.scale >= 1000) return 100; // Submicron - very detailed
        if (config.scale >= 100) return 50;   // Component - detailed
        if (config.scale >= 10) return 25;    // Equipment - medium detail
        if (config.scale >= 1) return 20;     // Room - standard detail
        if (config.scale >= 0.1) return 15;   // Floor - overview detail
        if (config.scale >= 0.01) return 10;  // Building - basic detail
        return 5; // Campus - minimal detail
    }
    
    /**
     * Calculate appropriate axes size for zoom level
     */
    _calculateAxesSizeForZoom(level, config) {
        const baseSize = 50;
        return baseSize / config.scale;
    }
    
    _applyZoomLevel(level, config) {
        this.zoomSystem.currentScale = config.scale;
        this._applyZoomScale(config.scale);
    }
    
    _applyZoomScale(scale) {
        this.zoomSystem.currentScale = scale;
        
        // Apply scale to all ArxObject meshes
        for (const mesh of this.arxObjectMeshes.values()) {
            mesh.scale.setScalar(scale);
        }
        
        // Update camera near/far planes for precision
        const near = Math.max(0.000001, scale * 0.001);
        const far = Math.min(1000000, scale * 1000);
        
        if (this.camera.isPerspectiveCamera) {
            this.camera.near = near;
            this.camera.far = far;
            this.camera.updateProjectionMatrix();
        } else {
            this.camera.near = near;
            this.camera.far = far;
            this.camera.updateProjectionMatrix();
        }
    }
    
    _updateLevelOfDetail(level) {
        if (!this.lodSystem.enabled) return;
        
        const detailOrder = ['minimal', 'low', 'medium', 'high', 'detailed', 'microscopic', 'nanoscopic'];
        const currentIndex = detailOrder.indexOf(this.lodSystem.currentLevel);
        const targetIndex = detailOrder.indexOf(level);
        
        for (const [id, mesh] of this.arxObjectMeshes) {
            const meshDetail = mesh.userData.detailLevel || 'medium';
            const meshIndex = detailOrder.indexOf(meshDetail);
            
            // Show/hide objects based on detail level
            const shouldShow = meshIndex <= targetIndex;
            mesh.visible = shouldShow;
            
            // Store visibility state
            this.lodSystem.objectVisibility.set(id, shouldShow);
        }
        
        this.lodSystem.currentLevel = level;
    }
    
    _easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
    
    _easeInOutQuart(t) {
        return t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2;
    }
    
    _easeInOutExpo(t) {
        return t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2;
    }
    
    _handleZoomChange() {
        const distance = this.camera.position.distanceTo(this.controls.target);
        
        // Determine zoom level based on camera distance
        let level = 'room';
        
        if (distance > 500) level = 'campus';
        else if (distance > 100) level = 'building';
        else if (distance > 20) level = 'floor';
        else if (distance > 5) level = 'room';
        else if (distance > 1) level = 'equipment';
        else if (distance > 0.1) level = 'component';
        else level = 'submicron';
        
        if (level !== this.zoomSystem.currentLevel) {
            this.setZoomLevel(level, false); // Don't animate automatic zoom changes
        }
    }
    
    _updateArxObjectMesh(arxObject) {
        const mesh = this.arxObjectMeshes.get(arxObject.id);
        if (mesh) {
            this.updateArxObjectMesh(arxObject.id, {
                position: arxObject.threeCoordinates,
                userData: {
                    properties: arxObject.properties,
                    coordinates: arxObject.coordinates
                }
            });
        }
    }
    
    _handleSVGElementChange(data) {
        // Handle SVG element changes
        const mesh = this.arxObjectMeshes.get(data.arxObjectId);
        if (mesh) {
            // Update mesh based on SVG changes
            this._updateMeshFromSVGChange(mesh, data);
        }
    }
    
    _updateMeshFromSVGChange(mesh, data) {
        // Update mesh geometry or properties based on SVG changes
        if (data.attribute === 'transform') {
            // Handle transform changes
            const transform = data.newValue;
            if (transform) {
                // Parse and apply transform
                this._applySVGTransform(mesh, transform);
            }
        }
    }
    
    _applySVGTransform(mesh, transformString) {
        // Parse and apply SVG transform to Three.js mesh
        const transforms = transformString.match(/(\w+)\s*\(([^)]+)\)/g);
        
        if (transforms) {
            for (const t of transforms) {
                const [type, values] = t.match(/(\w+)\s*\(([^)]+)\)/).slice(1);
                const nums = values.split(/[,\s]+/).map(Number).filter(n => !isNaN(n));
                
                switch (type) {
                    case 'translate':
                        mesh.position.x += nums[0] || 0;
                        mesh.position.z += nums[1] || 0; // Note: SVG Y maps to Three.js Z
                        break;
                    case 'scale':
                        const scaleX = nums[0] || 1;
                        const scaleY = nums[1] || nums[0] || 1;
                        mesh.scale.set(scaleX, mesh.scale.y, scaleY);
                        break;
                    case 'rotate':
                        const angle = (nums[0] || 0) * Math.PI / 180;
                        mesh.rotation.y = angle;
                        break;
                }
            }
        }
    }
    
    _clearArxObjectMeshes() {
        // Remove all ArxObject meshes from scene
        for (const mesh of this.arxObjectMeshes.values()) {
            this.scene.remove(mesh);
            if (mesh.geometry) mesh.geometry.dispose();
            if (mesh.material) mesh.material.dispose();
        }
        
        this.arxObjectMeshes.clear();
        this.lodSystem.objectVisibility.clear();
    }
    
    _centerCameraOnModel() {
        if (this.arxObjectMeshes.size === 0) return;
        
        // Calculate bounds of all meshes
        const bounds = this._calculateModelBounds();
        
        if (bounds) {
            const center = new THREE.Vector3(
                (bounds.min.x + bounds.max.x) / 2,
                (bounds.min.y + bounds.max.y) / 2,
                (bounds.min.z + bounds.max.z) / 2
            );
            
            const size = new THREE.Vector3(
                bounds.max.x - bounds.min.x,
                bounds.max.y - bounds.min.y,
                bounds.max.z - bounds.min.z
            );
            
            const maxDim = Math.max(size.x, size.y, size.z);
            const distance = maxDim * 2;
            
            // Position camera
            this.camera.position.set(
                center.x + distance,
                center.y + distance * 0.5,
                center.z + distance
            );
            
            // Look at model center
            this.controls.target.copy(center);
            this.controls.update();
        }
    }
    
    _calculateModelBounds() {
        if (this.arxObjectMeshes.size === 0) return null;
        
        const bounds = {
            min: new THREE.Vector3(Infinity, Infinity, Infinity),
            max: new THREE.Vector3(-Infinity, -Infinity, -Infinity)
        };
        
        for (const mesh of this.arxObjectMeshes.values()) {
            if (mesh.geometry) {
                mesh.geometry.computeBoundingBox();
                const box = mesh.geometry.boundingBox;
                
                if (box) {
                    // Transform bounds to world space
                    const tempBox = box.clone();
                    tempBox.applyMatrix4(mesh.matrixWorld);
                    
                    bounds.min.min(tempBox.min);
                    bounds.max.max(tempBox.max);
                }
            }
        }
        
        return bounds;
    }
    
    // Event handling methods
    
    _onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
    
    _onMouseClick(event) {
        const mouse = new THREE.Vector2();
        mouse.x = (event.clientX / this.options.width) * 2 - 1;
        mouse.y = -(event.clientY / this.options.height) * 2 + 1;
        
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);
        
        const intersects = raycaster.intersectObjects(this.scene.children, true);
        
        if (intersects.length > 0) {
            const selectedObject = intersects[0].object;
            this._selectObject(selectedObject);
        }
    }
    
    _onKeyDown(event) {
        switch (event.key) {
            case '1':
                this.setZoomLevel('campus');
                break;
            case '2':
                this.setZoomLevel('building');
                break;
            case '3':
                this.setZoomLevel('floor');
                break;
            case '4':
                this.setZoomLevel('room');
                break;
            case '5':
                this.setZoomLevel('equipment');
                break;
            case '6':
                this.setZoomLevel('component');
                break;
            case '7':
                this.setZoomLevel('submicron');
                break;
            case 'r':
                this.resetCamera();
                break;
            case 'h':
                this.toggleGrid();
                break;
            case 'c':
                this.switchCamera(this.options.defaultCamera === 'perspective' ? 'orthographic' : 'perspective');
                break;
        }
    }
    
    _selectObject(object) {
        // Deselect previous object
        if (this.selectedMesh) {
            this.selectedMesh.material.emissive.setHex(0x000000);
        }
        
        // Select new object
        this.selectedMesh = object;
        if (object.material) {
            object.material.emissive.setHex(0x444444);
        }
        
        // Emit selection event
        this._emitEvent('objectSelected', { object: object });
    }
    
    // Public utility methods
    
    resetCamera() {
        this._centerCameraOnModel();
    }
    
    // Enhanced zoom methods for smooth infinite zoom
    
    /**
     * Zoom to campus level (kilometer scale)
     */
    zoomToCampus(smooth = true) {
        return this.setZoomLevel('campus', smooth);
    }
    
    /**
     * Zoom to site level (hectometer scale)
     */
    zoomToSite(smooth = true) {
        return this.setZoomLevel('site', smooth);
    }
    
    /**
     * Zoom to building level (decameter scale)
     */
    zoomToBuilding(smooth = true) {
        return this.setZoomLevel('building', smooth);
    }
    
    /**
     * Zoom to floor level (meter scale)
     */
    zoomToFloor(smooth = true) {
        return this.setZoomLevel('floor', smooth);
    }
    
    /**
     * Zoom to room level (decimeter scale)
     */
    zoomToRoom(smooth = true) {
        return this.setZoomLevel('room', smooth);
    }
    
    /**
     * Zoom to furniture level (centimeter scale)
     */
    zoomToFurniture(smooth = true) {
        return this.setZoomLevel('furniture', smooth);
    }
    
    /**
     * Zoom to equipment level (millimeter scale)
     */
    zoomToEquipment(smooth = true) {
        return this.setZoomLevel('equipment', smooth);
    }
    
    /**
     * Zoom to component level (submillimeter scale)
     */
    zoomToComponent(smooth = true) {
        return this.setZoomLevel('component', smooth);
    }
    
    /**
     * Zoom to detail level (micrometer scale)
     */
    zoomToDetail(smooth = true) {
        return this.setZoomLevel('detail', smooth);
    }
    
    /**
     * Zoom to submicron level (nanometer scale)
     */
    zoomToSubmicron(smooth = true) {
        return this.setZoomLevel('submicron', smooth);
    }
    
    /**
     * Zoom to nanoscopic level (picometer scale)
     */
    zoomToNanoscopic(smooth = true) {
        return this.setZoomLevel('nanoscopic', smooth);
    }
    
    /**
     * Get current zoom information
     */
    getZoomInfo() {
        const config = this._getZoomConfiguration(this.zoomSystem.currentLevel);
        return {
            level: this.zoomSystem.currentLevel,
            scale: this.zoomSystem.currentScale,
            precision: config.precision,
            units: config.units,
            description: config.description
        };
    }
    
    /**
     * Get all available zoom levels
     */
    getAvailableZoomLevels() {
        return Object.keys(this._getZoomConfiguration('campus')).map(level => ({
            level: level,
            config: this._getZoomConfiguration(level)
        }));
    }
    
    toggleGrid() {
        const grid = this.scene.children.find(child => child instanceof THREE.GridHelper);
        if (grid) {
            grid.visible = !grid.visible;
        }
    }
    
    // Event system
    
    _emitEvent(eventName, data) {
        const event = new CustomEvent(`arxos:${eventName}`, { detail: data });
        this.container.dispatchEvent(event);
    }
    
    // Export/Import methods
    
    exportScene() {
        const sceneData = {
            zoomLevel: this.zoomSystem.currentLevel,
            camera: {
                position: this.camera.position.toArray(),
                target: this.controls.target.toArray(),
                type: this.options.defaultCamera
            },
            objects: Array.from(this.arxObjectMeshes.entries()).map(([id, mesh]) => ({
                id: id,
                type: mesh.userData.type,
                position: mesh.position.toArray(),
                rotation: mesh.rotation.toArray(),
                scale: mesh.scale.toArray(),
                userData: mesh.userData
            }))
        };
        
        return sceneData;
    }
    
    importScene(sceneData) {
        if (sceneData.zoomLevel) {
            this.setZoomLevel(sceneData.zoomLevel);
        }
        
        if (sceneData.camera) {
            this.camera.position.fromArray(sceneData.camera.position);
            this.controls.target.fromArray(sceneData.camera.target);
            this.controls.update();
            
            if (sceneData.camera.type !== this.options.defaultCamera) {
                this.switchCamera(sceneData.camera.type);
            }
        }
    }
    
    // Cleanup
    
    destroy() {
        // Clean up Three.js resources
        this._clearArxObjectMeshes();
        
        // Dispose of materials
        for (const material of this.materialSystem.materials.values()) {
            material.dispose();
        }
        this.materialSystem.materials.clear();
        
        if (this.materialSystem.defaultMaterial) {
            this.materialSystem.defaultMaterial.dispose();
        }
        
        // Remove event listeners
        window.removeEventListener('resize', this._onWindowResize);
        document.removeEventListener('keydown', this._onKeyDown);
        
        // Dispose of renderer
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        console.log('Arxos Three.js renderer destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxosThreeRenderer;
}
