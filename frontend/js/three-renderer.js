/**
 * Arxos Three.js 3D Renderer
 * Provides 3D visualization of building models with infinite zoom capabilities
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
            enableShadows: options.enableShadows || true,
            enableGrid: options.enableGrid || true,
            enableAxes: options.enableAxes || true,
            ...options
        };
        
        // Scene state
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.buildingObjects = new Map();
        this.selectedObject = null;
        
        // Camera settings
        this.cameraSettings = {
            fov: 75,
            near: 0.1,
            far: 10000,
            position: { x: 100, y: 100, z: 100 },
            lookAt: { x: 0, y: 0, z: 0 }
        };
        
        // Zoom levels for infinite zoom
        this.zoomLevels = {
            CAMPUS: { scale: 1000, detail: 'minimal' },
            BUILDING: { scale: 100, detail: 'low' },
            FLOOR: { scale: 10, detail: 'medium' },
            ROOM: { scale: 1, detail: 'high' },
            EQUIPMENT: { scale: 0.1, detail: 'detailed' },
            COMPONENT: { scale: 0.01, detail: 'microscopic' }
        };
        
        this.currentZoomLevel = 'FLOOR';
        
        // Initialize the renderer
        this.init();
    }
    
    init() {
        try {
            this._createScene();
            this._createCamera();
            this._createRenderer();
            this._createControls();
            this._createLights();
            this._createGrid();
            this._createAxes();
            this._setupEventListeners();
            this._animate();
            
            console.log('Arxos Three.js renderer initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Three.js renderer:', error);
        }
    }
    
    _createScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(this.options.backgroundColor);
        this.scene.fog = new THREE.Fog(this.options.backgroundColor, 100, 1000);
    }
    
    _createCamera() {
        const aspect = this.options.width / this.options.height;
        this.camera = new THREE.PerspectiveCamera(
            this.cameraSettings.fov,
            aspect,
            this.cameraSettings.near,
            this.cameraSettings.far
        );
        
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
            alpha: true
        });
        
        this.renderer.setSize(this.options.width, this.options.height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
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
        this.controls.minDistance = 1;
        this.controls.maxDistance = 10000;
        this.controls.maxPolarAngle = Math.PI / 2;
        
        // Custom zoom behavior for infinite zoom
        this.controls.addEventListener('zoom', (event) => {
            this._handleZoomChange();
        });
    }
    
    _createLights() {
        // Ambient light
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
                this.setZoomLevel('CAMPUS');
                break;
            case '2':
                this.setZoomLevel('BUILDING');
                break;
            case '3':
                this.setZoomLevel('FLOOR');
                break;
            case '4':
                this.setZoomLevel('ROOM');
                break;
            case '5':
                this.setZoomLevel('EQUIPMENT');
                break;
            case '6':
                this.setZoomLevel('COMPONENT');
                break;
            case 'r':
                this.resetCamera();
                break;
            case 'h':
                this.toggleGrid();
                break;
        }
    }
    
    _selectObject(object) {
        // Deselect previous object
        if (this.selectedObject) {
            this.selectedObject.material.emissive.setHex(0x000000);
        }
        
        // Select new object
        this.selectedObject = object;
        if (object.material) {
            object.material.emissive.setHex(0x444444);
        }
        
        // Emit selection event
        this._emitEvent('objectSelected', { object: object });
    }
    
    _handleZoomChange() {
        const distance = this.camera.position.distanceTo(this.controls.target);
        
        // Determine zoom level based on camera distance
        if (distance > 500) {
            this.setZoomLevel('CAMPUS');
        } else if (distance > 100) {
            this.setZoomLevel('BUILDING');
        } else if (distance > 20) {
            this.setZoomLevel('FLOOR');
        } else if (distance > 5) {
            this.setZoomLevel('ROOM');
        } else if (distance > 1) {
            this.setZoomLevel('EQUIPMENT');
        } else {
            this.setZoomLevel('COMPONENT');
        }
    }
    
    setZoomLevel(level) {
        if (this.currentZoomLevel === level) return;
        
        this.currentZoomLevel = level;
        const zoomConfig = this.zoomLevels[level];
        
        // Update level of detail based on zoom
        this._updateLevelOfDetail(zoomConfig.detail);
        
        // Emit zoom change event
        this._emitEvent('zoomLevelChanged', { 
            level: level, 
            config: zoomConfig 
        });
        
        console.log(`Zoom level changed to: ${level}`);
    }
    
    _updateLevelOfDetail(detail) {
        // Update object visibility and detail based on zoom level
        this.buildingObjects.forEach((object, id) => {
            const shouldShow = this._shouldShowObject(object, detail);
            object.visible = shouldShow;
            
            if (shouldShow) {
                this._updateObjectDetail(object, detail);
            }
        });
    }
    
    _shouldShowObject(object, detail) {
        // Determine object visibility based on detail level
        const objectDetail = object.userData.detailLevel || 'medium';
        const detailOrder = ['minimal', 'low', 'medium', 'high', 'detailed', 'microscopic'];
        
        const objectIndex = detailOrder.indexOf(objectDetail);
        const currentIndex = detailOrder.indexOf(detail);
        
        return objectIndex <= currentIndex;
    }
    
    _updateObjectDetail(object, detail) {
        // Update object geometry detail based on zoom level
        if (object.geometry && object.userData.lodLevels) {
            const lodLevels = object.userData.lodLevels;
            const targetLOD = lodLevels[detail] || lodLevels.medium;
            
            if (targetLOD && targetLOD !== object.geometry) {
                object.geometry = targetLOD;
            }
        }
    }
    
    // Public API methods
    
    loadBuildingModel(buildingData) {
        try {
            console.log('Loading building model:', buildingData);
            
            // Clear existing objects
            this.clearScene();
            
            // Create building structure
            this._createBuildingStructure(buildingData);
            
            // Center camera on building
            this._centerCameraOnBuilding();
            
            console.log('Building model loaded successfully');
        } catch (error) {
            console.error('Failed to load building model:', error);
        }
    }
    
    _createBuildingStructure(buildingData) {
        // Create building foundation
        this._createFoundation(buildingData.foundation);
        
        // Create floors
        if (buildingData.floors) {
            buildingData.floors.forEach((floor, index) => {
                this._createFloor(floor, index);
            });
        }
        
        // Create structural elements
        if (buildingData.structural) {
            this._createStructuralElements(buildingData.structural);
        }
        
        // Create MEP systems
        if (buildingData.mep) {
            this._createMEPSystems(buildingData.mep);
        }
    }
    
    _createFoundation(foundationData) {
        if (!foundationData) return;
        
        const geometry = new THREE.BoxGeometry(
            foundationData.width || 100,
            foundationData.height || 10,
            foundationData.depth || 100
        );
        
        const material = new THREE.MeshLambertMaterial({ 
            color: 0x8B4513,
            transparent: true,
            opacity: 0.8
        });
        
        const foundation = new THREE.Mesh(geometry, material);
        foundation.position.set(
            foundationData.x || 0,
            -(foundationData.height || 10) / 2,
            foundationData.z || 0
        );
        foundation.castShadow = true;
        foundation.receiveShadow = true;
        foundation.userData = {
            type: 'foundation',
            detailLevel: 'minimal',
            arxObjectId: foundationData.id
        };
        
        this.scene.add(foundation);
        this.buildingObjects.set(foundationData.id, foundation);
    }
    
    _createFloor(floorData, floorIndex) {
        if (!floorData) return;
        
        const floorHeight = floorData.height || 10;
        const floorY = floorIndex * floorHeight;
        
        // Create floor slab
        const slabGeometry = new THREE.BoxGeometry(
            floorData.width || 100,
            floorData.slabThickness || 2,
            floorData.depth || 100
        );
        
        const slabMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x808080,
            transparent: true,
            opacity: 0.9
        });
        
        const slab = new THREE.Mesh(slabGeometry, slabMaterial);
        slab.position.set(
            floorData.x || 0,
            floorY + (floorData.slabThickness || 2) / 2,
            floorData.z || 0
        );
        slab.castShadow = true;
        slab.receiveShadow = true;
        slab.userData = {
            type: 'floor_slab',
            detailLevel: 'low',
            floorIndex: floorIndex,
            arxObjectId: floorData.id
        };
        
        this.scene.add(slab);
        this.buildingObjects.set(floorData.id, slab);
        
        // Create walls for this floor
        if (floorData.walls) {
            floorData.walls.forEach(wallData => {
                this._createWall(wallData, floorY);
            });
        }
        
        // Create rooms for this floor
        if (floorData.rooms) {
            floorData.rooms.forEach(roomData => {
                this._createRoom(roomData, floorY);
            });
        }
    }
    
    _createWall(wallData, floorY) {
        if (!wallData) return;
        
        const startPoint = wallData.start_point || [0, 0];
        const endPoint = wallData.end_point || [10, 0];
        const height = wallData.height || 10;
        const thickness = wallData.thickness || 0.2;
        
        // Calculate wall dimensions
        const dx = endPoint[0] - startPoint[0];
        const dz = endPoint[1] - startPoint[1];
        const length = Math.sqrt(dx * dx + dz * dz);
        const angle = Math.atan2(dz, dx);
        
        const geometry = new THREE.BoxGeometry(length, height, thickness);
        const material = new THREE.MeshLambertMaterial({ 
            color: 0xD3D3D3,
            transparent: true,
            opacity: 0.8
        });
        
        const wall = new THREE.Mesh(geometry, material);
        
        // Position and rotate wall
        wall.position.set(
            (startPoint[0] + endPoint[0]) / 2,
            floorY + height / 2,
            (startPoint[1] + endPoint[1]) / 2
        );
        wall.rotation.y = angle;
        
        wall.castShadow = true;
        wall.receiveShadow = true;
        wall.userData = {
            type: 'wall',
            detailLevel: 'medium',
            arxObjectId: wallData.id,
            properties: wallData.properties || {}
        };
        
        this.scene.add(wall);
        this.buildingObjects.set(wallData.id, wall);
    }
    
    _createRoom(roomData, floorY) {
        if (!roomData) return;
        
        // Create room boundary visualization
        if (roomData.corners && roomData.corners.length >= 3) {
            const points = roomData.corners.map(corner => 
                new THREE.Vector3(corner[0], floorY, corner[1])
            );
            
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({ color: 0x0000FF });
            const roomOutline = new THREE.Line(geometry, material);
            
            roomOutline.userData = {
                type: 'room_outline',
                detailLevel: 'medium',
                arxObjectId: roomData.id,
                properties: roomData.properties || {}
            };
            
            this.scene.add(roomOutline);
            this.buildingObjects.set(roomData.id, roomOutline);
        }
    }
    
    _createStructuralElements(structuralData) {
        if (!structuralData) return;
        
        // Create columns
        if (structuralData.columns) {
            structuralData.columns.forEach(columnData => {
                this._createColumn(columnData);
            });
        }
        
        // Create beams
        if (structuralData.beams) {
            structuralData.beams.forEach(beamData => {
                this._createBeam(beamData);
            });
        }
    }
    
    _createColumn(columnData) {
        if (!columnData) return;
        
        const geometry = new THREE.CylinderGeometry(
            columnData.radius || 0.5,
            columnData.radius || 0.5,
            columnData.height || 10
        );
        
        const material = new THREE.MeshLambertMaterial({ 
            color: 0x696969,
            transparent: true,
            opacity: 0.9
        });
        
        const column = new THREE.Mesh(geometry, material);
        column.position.set(
            columnData.x || 0,
            columnData.y || 0,
            columnData.z || 0
        );
        
        column.castShadow = true;
        column.receiveShadow = true;
        column.userData = {
            type: 'column',
            detailLevel: 'medium',
            arxObjectId: columnData.id,
            properties: columnData.properties || {}
        };
        
        this.scene.add(column);
        this.buildingObjects.set(columnData.id, column);
    }
    
    _createBeam(beamData) {
        if (!beamData) return;
        
        const geometry = new THREE.BoxGeometry(
            beamData.width || 0.3,
            beamData.height || 0.3,
            beamData.length || 10
        );
        
        const material = new THREE.MeshLambertMaterial({ 
            color: 0x696969,
            transparent: true,
            opacity: 0.9
        });
        
        const beam = new THREE.Mesh(geometry, material);
        beam.position.set(
            beamData.x || 0,
            beamData.y || 0,
            beamData.z || 0
        );
        
        if (beamData.rotation) {
            beam.rotation.set(
                beamData.rotation.x || 0,
                beamData.rotation.y || 0,
                beamData.rotation.z || 0
            );
        }
        
        beam.castShadow = true;
        beam.receiveShadow = true;
        beam.userData = {
            type: 'beam',
            detailLevel: 'medium',
            arxObjectId: beamData.id,
            properties: beamData.properties || {}
        };
        
        this.scene.add(beam);
        this.buildingObjects.set(beamData.id, beam);
    }
    
    _createMEPSystems(mepData) {
        if (!mepData) return;
        
        // Create electrical panels
        if (mepData.electrical && mepData.electrical.panels) {
            mepData.electrical.panels.forEach(panelData => {
                this._createElectricalPanel(panelData);
            });
        }
        
        // Create HVAC units
        if (mepData.hvac && mepData.hvac.units) {
            mepData.hvac.units.forEach(unitData => {
                this._createHVACUnit(unitData);
            });
        }
    }
    
    _createElectricalPanel(panelData) {
        if (!panelData) return;
        
        const geometry = new THREE.BoxGeometry(
            panelData.width || 1,
            panelData.height || 2,
            panelData.depth || 0.3
        );
        
        const material = new THREE.MeshLambertMaterial({ 
            color: 0xFFD700,
            transparent: true,
            opacity: 0.8
        });
        
        const panel = new THREE.Mesh(geometry, material);
        panel.position.set(
            panelData.x || 0,
            panelData.y || 0,
            panelData.z || 0
        );
        
        panel.castShadow = true;
        panel.receiveShadow = true;
        panel.userData = {
            type: 'electrical_panel',
            detailLevel: 'high',
            arxObjectId: panelData.id,
            properties: panelData.properties || {}
        };
        
        this.scene.add(panel);
        this.buildingObjects.set(panelData.id, panel);
    }
    
    _createHVACUnit(unitData) {
        if (!unitData) return;
        
        const geometry = new THREE.BoxGeometry(
            unitData.width || 2,
            unitData.height || 1,
            unitData.depth || 2
        );
        
        const material = new THREE.MeshLambertMaterial({ 
            color: 0x87CEEB,
            transparent: true,
            opacity: 0.8
        });
        
        const unit = new THREE.Mesh(geometry, material);
        unit.position.set(
            unitData.x || 0,
            unitData.y || 0,
            unitData.z || 0
        );
        
        unit.castShadow = true;
        unit.receiveShadow = true;
        unit.userData = {
            type: 'hvac_unit',
            detailLevel: 'high',
            arxObjectId: unitData.id,
            properties: unitData.properties || {}
        };
        
        this.scene.add(unit);
        this.buildingObjects.set(unitData.id, unit);
    }
    
    _centerCameraOnBuilding() {
        // Calculate building bounds
        const bounds = this._calculateBuildingBounds();
        
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
            
            // Look at building center
            this.controls.target.copy(center);
            this.controls.update();
        }
    }
    
    _calculateBuildingBounds() {
        if (this.buildingObjects.size === 0) return null;
        
        const bounds = {
            min: new THREE.Vector3(Infinity, Infinity, Infinity),
            max: new THREE.Vector3(-Infinity, -Infinity, -Infinity)
        };
        
        this.buildingObjects.forEach(object => {
            if (object.geometry) {
                object.geometry.computeBoundingBox();
                const box = object.geometry.boundingBox;
                
                if (box) {
                    // Transform bounds to world space
                    const tempBox = box.clone();
                    tempBox.applyMatrix4(object.matrixWorld);
                    
                    bounds.min.min(tempBox.min);
                    bounds.max.max(tempBox.max);
                }
            }
        });
        
        return bounds;
    }
    
    clearScene() {
        // Remove all building objects
        this.buildingObjects.forEach(object => {
            this.scene.remove(object);
        });
        this.buildingObjects.clear();
        
        // Reset selection
        this.selectedObject = null;
    }
    
    resetCamera() {
        this._centerCameraOnBuilding();
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
    
    // Public utility methods
    getObjectById(id) {
        return this.buildingObjects.get(id);
    }
    
    getAllObjects() {
        return Array.from(this.buildingObjects.values());
    }
    
    getSelectedObject() {
        return this.selectedObject;
    }
    
    getCurrentZoomLevel() {
        return this.currentZoomLevel;
    }
    
    // Export scene data
    exportScene() {
        const sceneData = {
            zoomLevel: this.currentZoomLevel,
            camera: {
                position: this.camera.position.toArray(),
                target: this.controls.target.toArray()
            },
            objects: Array.from(this.buildingObjects.entries()).map(([id, obj]) => ({
                id: id,
                type: obj.userData.type,
                position: obj.position.toArray(),
                rotation: obj.rotation.toArray(),
                scale: obj.scale.toArray(),
                userData: obj.userData
            }))
        };
        
        return sceneData;
    }
    
    // Import scene data
    importScene(sceneData) {
        if (sceneData.zoomLevel) {
            this.setZoomLevel(sceneData.zoomLevel);
        }
        
        if (sceneData.camera) {
            this.camera.position.fromArray(sceneData.camera.position);
            this.controls.target.fromArray(sceneData.camera.target);
            this.controls.update();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ArxosThreeRenderer;
}
