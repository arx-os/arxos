/**
 * ASCII Renderer - Browser-based ASCII rendering engine for ArxOS Layer 4
 * Translates ArxObjects into ASCII art representation with viewport management
 */

class ASCIIRenderer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.width = 120;  // ASCII columns
        this.height = 40;  // ASCII rows
        this.buffer = [];
        this.depthBuffer = [];
        this.viewport = {
            centerX: 0,
            centerY: 0,
            scale: 1.0,
            nearZ: -10,
            farZ: 10
        };
        this.objects = [];
        this.selectedObject = null;
        
        // ASCII character sets for different materials
        this.characters = {
            empty: ' ',
            wall: '█',
            wallThin: '│',
            wallCorner: '┐┘└┌',
            wallJunction: '┬┴├┤┼',
            door: 'D',
            doorOpen: '/',
            window: 'W',
            room: '·',
            equipment: '■',
            outlet: 'o',
            panel: '▣',
            text: '░'
        };
        
        // Material type mapping
        this.materials = {
            MATERIAL_EMPTY: 0,
            MATERIAL_WALL: 1,
            MATERIAL_DOOR: 2,
            MATERIAL_WINDOW: 3,
            MATERIAL_EQUIPMENT: 4,
            MATERIAL_OUTLET: 5,
            MATERIAL_PANEL: 6,
            MATERIAL_ROOM_OFFICE: 7,
            MATERIAL_ROOM_CORRIDOR: 8,
            MATERIAL_ROOM_CLASSROOM: 9,
            MATERIAL_ROOM_LARGE: 10
        };
        
        this.initializeBuffers();
        this.setupEventHandlers();
        this.updateCanvasSize();
        
        // Performance tracking
        this.frameCount = 0;
        this.lastFrameTime = performance.now();
        this.fps = 0;
        
        // Start render loop
        this.renderLoop();
    }
    
    initializeBuffers() {
        const totalCells = this.width * this.height;
        this.buffer = new Array(totalCells).fill(this.characters.empty);
        this.depthBuffer = new Array(totalCells).fill(1.0);
    }
    
    updateCanvasSize() {
        // Calculate optimal size based on container
        const rect = this.canvas.getBoundingClientRect();
        const containerWidth = rect.width - 20; // Account for padding
        const containerHeight = rect.height - 20;
        
        // Calculate character dimensions based on font
        const fontSize = parseInt(window.getComputedStyle(this.canvas).fontSize);
        const charWidth = fontSize * 0.6; // Monospace approximation
        const charHeight = fontSize * 1.2; // Line height
        
        this.width = Math.floor(containerWidth / charWidth);
        this.height = Math.floor(containerHeight / charHeight);
        
        // Ensure minimum size
        this.width = Math.max(this.width, 40);
        this.height = Math.max(this.height, 20);
        
        this.initializeBuffers();
    }
    
    setupEventHandlers() {
        // Mouse interaction
        this.canvas.addEventListener('mousemove', (e) => {
            this.handleMouseMove(e);
        });
        
        this.canvas.addEventListener('click', (e) => {
            this.handleMouseClick(e);
        });
        
        this.canvas.addEventListener('wheel', (e) => {
            this.handleMouseWheel(e);
            e.preventDefault();
        });
        
        // Touch interaction for mobile
        let lastTouch = null;
        this.canvas.addEventListener('touchstart', (e) => {
            lastTouch = e.touches[0];
            e.preventDefault();
        });
        
        this.canvas.addEventListener('touchmove', (e) => {
            if (lastTouch && e.touches[0]) {
                const deltaX = e.touches[0].clientX - lastTouch.clientX;
                const deltaY = e.touches[0].clientY - lastTouch.clientY;
                this.viewport.centerX -= deltaX / this.viewport.scale;
                this.viewport.centerY -= deltaY / this.viewport.scale;
                lastTouch = e.touches[0];
                this.render();
            }
            e.preventDefault();
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            this.updateCanvasSize();
            this.render();
        });
    }
    
    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const worldCoords = this.screenToWorld(x, y);
        
        // Update coordinate display
        const coordDisplay = document.getElementById('coordinateDisplay');
        if (coordDisplay) {
            coordDisplay.textContent = `x: ${worldCoords.x.toFixed(1)}, y: ${worldCoords.y.toFixed(1)}`;
        }
    }
    
    handleMouseClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const worldCoords = this.screenToWorld(x, y);
        const clickedObject = this.findObjectAt(worldCoords.x, worldCoords.y);
        
        if (clickedObject) {
            this.selectObject(clickedObject);
        } else {
            this.selectObject(null);
        }
        
        this.render();
    }
    
    handleMouseWheel(e) {
        const zoomFactor = 1.1;
        const newScale = e.deltaY > 0 ? 
            this.viewport.scale / zoomFactor : 
            this.viewport.scale * zoomFactor;
            
        this.setZoom(Math.max(0.1, Math.min(5.0, newScale)));
    }
    
    setZoom(scale) {
        this.viewport.scale = scale;
        
        // Update zoom slider if exists
        const zoomSlider = document.getElementById('zoomSlider');
        const zoomValue = document.getElementById('zoomValue');
        if (zoomSlider) zoomSlider.value = scale;
        if (zoomValue) zoomValue.textContent = scale.toFixed(1) + 'x';
        
        this.render();
    }
    
    screenToWorld(screenX, screenY) {
        // Convert screen coordinates to ASCII canvas coordinates
        const fontSize = parseInt(window.getComputedStyle(this.canvas).fontSize);
        const charWidth = fontSize * 0.6;
        const charHeight = fontSize * 1.2;
        
        const canvasX = Math.floor(screenX / charWidth);
        const canvasY = Math.floor(screenY / charHeight);
        
        // Convert to world coordinates
        const worldX = (canvasX - this.width / 2) / this.viewport.scale + this.viewport.centerX;
        const worldY = (canvasY - this.height / 2) / this.viewport.scale + this.viewport.centerY;
        
        return { x: worldX, y: worldY };
    }
    
    worldToScreen(worldX, worldY) {
        const screenX = (worldX - this.viewport.centerX) * this.viewport.scale + this.width / 2;
        const screenY = (worldY - this.viewport.centerY) * this.viewport.scale + this.height / 2;
        
        return {
            x: Math.round(screenX),
            y: Math.round(screenY)
        };
    }
    
    findObjectAt(worldX, worldY) {
        // Find the topmost object at the given world coordinates
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            if (this.isPointInObject(worldX, worldY, obj)) {
                return obj;
            }
        }
        return null;
    }
    
    isPointInObject(x, y, obj) {
        if (!obj.geometry || !obj.geometry.bounding_box) return false;
        
        const bbox = obj.geometry.bounding_box;
        return x >= bbox.min.x && x <= bbox.max.x &&
               y >= bbox.min.y && y <= bbox.max.y;
    }
    
    selectObject(obj) {
        this.selectedObject = obj;
        
        // Update object list UI
        document.querySelectorAll('.object-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        if (obj) {
            const objectItem = document.querySelector(`[data-object-id="${obj.id}"]`);
            if (objectItem) {
                objectItem.classList.add('selected');
            }
            
            this.displayObjectProperties(obj);
        } else {
            this.clearObjectProperties();
        }
    }
    
    displayObjectProperties(obj) {
        const propertiesContent = document.getElementById('propertiesContent');
        if (!propertiesContent) return;
        
        let html = `
            <div class="prop-group">
                <div class="prop-label">Object ID</div>
                <div class="prop-value">${obj.id}</div>
            </div>
            <div class="prop-group">
                <div class="prop-label">Type</div>
                <div class="prop-value">${obj.type}</div>
            </div>
            <div class="prop-group">
                <div class="prop-label">Name</div>
                <div class="prop-value">${obj.name || 'Unnamed'}</div>
            </div>
        `;
        
        if (obj.geometry) {
            html += `
                <div class="prop-group">
                    <div class="prop-label">Position</div>
                    <div class="prop-value">
                        x: ${obj.geometry.position?.x?.toFixed(2) || 0}<br>
                        y: ${obj.geometry.position?.y?.toFixed(2) || 0}<br>
                        z: ${obj.geometry.position?.z?.toFixed(2) || 0}
                    </div>
                </div>
            `;
        }
        
        if (obj.properties) {
            html += '<div class="prop-group"><div class="prop-label">Properties</div>';
            for (const [key, value] of Object.entries(obj.properties)) {
                html += `<div class="prop-value"><strong>${key}:</strong> ${value}</div>`;
            }
            html += '</div>';
        }
        
        if (obj.confidence) {
            html += `
                <div class="prop-group">
                    <div class="prop-label">Confidence</div>
                    <div class="prop-value">${(obj.confidence * 100).toFixed(1)}%</div>
                </div>
            `;
        }
        
        propertiesContent.innerHTML = html;
    }
    
    clearObjectProperties() {
        const propertiesContent = document.getElementById('propertiesContent');
        if (propertiesContent) {
            propertiesContent.innerHTML = '<p style="color: #666; font-size: 12px;">Select an object to view properties</p>';
        }
    }
    
    updateObjects(objects) {
        this.objects = objects || [];
        this.render();
        
        // Update object count
        const objectCount = document.getElementById('objectCount');
        if (objectCount) {
            objectCount.textContent = this.objects.length;
        }
    }
    
    clear() {
        this.buffer.fill(this.characters.empty);
        this.depthBuffer.fill(1.0);
    }
    
    setPixel(x, y, char, depth = 0.5) {
        if (x < 0 || x >= this.width || y < 0 || y >= this.height) return;
        
        const index = y * this.width + x;
        
        // Z-buffer test
        if (depth < this.depthBuffer[index]) {
            this.buffer[index] = char;
            this.depthBuffer[index] = depth;
        }
    }
    
    drawLine(x1, y1, x2, y2, char, depth = 0.5) {
        const dx = Math.abs(x2 - x1);
        const dy = Math.abs(y2 - y1);
        const sx = x1 < x2 ? 1 : -1;
        const sy = y1 < y2 ? 1 : -1;
        let err = dx - dy;
        
        let x = x1, y = y1;
        
        while (true) {
            this.setPixel(x, y, char, depth);
            
            if (x === x2 && y === y2) break;
            
            const e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x += sx;
            }
            if (e2 < dx) {
                err += dx;
                y += sy;
            }
        }
    }
    
    fillRect(x, y, width, height, char, depth = 0.6) {
        for (let fy = y; fy < y + height && fy < this.height; fy++) {
            for (let fx = x; fx < x + width && fx < this.width; fx++) {
                this.setPixel(fx, fy, char, depth);
            }
        }
    }
    
    renderWall(obj) {
        const screenPos = this.worldToScreen(
            obj.geometry.position?.x || 0,
            obj.geometry.position?.y || 0
        );
        
        const bbox = obj.geometry.bounding_box;
        if (!bbox) return;
        
        const screenStart = this.worldToScreen(bbox.min.x, bbox.min.y);
        const screenEnd = this.worldToScreen(bbox.max.x, bbox.max.y);
        
        const char = obj === this.selectedObject ? '▓' : this.characters.wall;
        const depth = obj.geometry.position?.z || 0;
        
        // Draw wall as line or filled rectangle based on dimensions
        const width = Math.abs(screenEnd.x - screenStart.x);
        const height = Math.abs(screenEnd.y - screenStart.y);
        
        if (width > height) {
            // Horizontal wall
            this.drawLine(screenStart.x, screenStart.y, screenEnd.x, screenStart.y, char, depth);
        } else if (height > width) {
            // Vertical wall
            this.drawLine(screenStart.x, screenStart.y, screenStart.x, screenEnd.y, char, depth);
        } else {
            // Square wall - fill as rectangle
            this.fillRect(screenStart.x, screenStart.y, width, height, char, depth);
        }
    }
    
    renderDoor(obj) {
        const screenPos = this.worldToScreen(
            obj.geometry.position?.x || 0,
            obj.geometry.position?.y || 0
        );
        
        const char = obj === this.selectedObject ? '▣' : this.characters.door;
        const depth = obj.geometry.position?.z || 0;
        
        this.setPixel(screenPos.x, screenPos.y, char, depth);
        
        // Add door opening indicator if properties suggest it's open
        if (obj.properties?.is_open) {
            this.setPixel(screenPos.x + 1, screenPos.y, this.characters.doorOpen, depth);
        }
    }
    
    renderWindow(obj) {
        const screenPos = this.worldToScreen(
            obj.geometry.position?.x || 0,
            obj.geometry.position?.y || 0
        );
        
        const char = obj === this.selectedObject ? '▣' : this.characters.window;
        const depth = obj.geometry.position?.z || 0;
        
        this.setPixel(screenPos.x, screenPos.y, char, depth);
    }
    
    renderRoom(obj) {
        const bbox = obj.geometry.bounding_box;
        if (!bbox) return;
        
        const screenStart = this.worldToScreen(bbox.min.x, bbox.min.y);
        const screenEnd = this.worldToScreen(bbox.max.x, bbox.max.y);
        
        const width = Math.abs(screenEnd.x - screenStart.x);
        const height = Math.abs(screenEnd.y - screenStart.y);
        
        const char = obj === this.selectedObject ? '▒' : this.characters.room;
        const depth = obj.geometry.position?.z || 0.8; // Rooms behind walls
        
        this.fillRect(screenStart.x, screenStart.y, width, height, char, depth);
        
        // Add room label if there's space
        if (width > 6 && height > 2 && obj.name) {
            const labelX = screenStart.x + Math.floor(width / 2) - Math.floor(obj.name.length / 2);
            const labelY = screenStart.y + Math.floor(height / 2);
            
            for (let i = 0; i < obj.name.length && i + labelX < screenStart.x + width; i++) {
                this.setPixel(labelX + i, labelY, obj.name[i], depth - 0.1);
            }
        }
    }
    
    renderEquipment(obj) {
        const screenPos = this.worldToScreen(
            obj.geometry.position?.x || 0,
            obj.geometry.position?.y || 0
        );
        
        let char = this.characters.equipment;
        
        // Use specific characters for different equipment types
        switch (obj.type) {
            case 'electrical_outlet':
                char = this.characters.outlet;
                break;
            case 'electrical_panel':
                char = this.characters.panel;
                break;
        }
        
        if (obj === this.selectedObject) {
            char = '▣';
        }
        
        const depth = obj.geometry.position?.z || 0;
        this.setPixel(screenPos.x, screenPos.y, char, depth);
    }
    
    renderObject(obj) {
        if (!obj || !obj.geometry) return;
        
        switch (obj.type) {
            case 'wall':
                this.renderWall(obj);
                break;
            case 'door':
                this.renderDoor(obj);
                break;
            case 'window':
                this.renderWindow(obj);
                break;
            case 'room':
                this.renderRoom(obj);
                break;
            case 'electrical_outlet':
            case 'electrical_panel':
            default:
                this.renderEquipment(obj);
                break;
        }
    }
    
    render() {
        this.clear();
        
        // Sort objects by depth (far to near) for proper rendering
        const sortedObjects = [...this.objects].sort((a, b) => {
            const aZ = a.geometry?.position?.z || 0;
            const bZ = b.geometry?.position?.z || 0;
            return bZ - aZ; // Far to near
        });
        
        // Render all objects
        sortedObjects.forEach(obj => {
            this.renderObject(obj);
        });
        
        // Convert buffer to HTML and update canvas
        this.updateCanvasDisplay();
    }
    
    updateCanvasDisplay() {
        let html = '';
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                const index = y * this.width + x;
                html += this.buffer[index];
            }
            html += '\n';
        }
        
        this.canvas.textContent = html;
    }
    
    renderLoop() {
        const currentTime = performance.now();
        this.frameCount++;
        
        // Calculate FPS every second
        if (currentTime - this.lastFrameTime >= 1000) {
            this.fps = Math.round((this.frameCount * 1000) / (currentTime - this.lastFrameTime));
            this.frameCount = 0;
            this.lastFrameTime = currentTime;
            
            // Update FPS display
            const fpsCounter = document.getElementById('fpsCounter');
            if (fpsCounter) {
                fpsCounter.textContent = this.fps;
            }
        }
        
        // Continue render loop
        requestAnimationFrame(() => this.renderLoop());
    }
    
    // Viewport management
    panTo(x, y) {
        this.viewport.centerX = x;
        this.viewport.centerY = y;
        this.render();
    }
    
    fitToObjects() {
        if (this.objects.length === 0) return;
        
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        this.objects.forEach(obj => {
            if (obj.geometry?.bounding_box) {
                const bbox = obj.geometry.bounding_box;
                minX = Math.min(minX, bbox.min.x);
                minY = Math.min(minY, bbox.min.y);
                maxX = Math.max(maxX, bbox.max.x);
                maxY = Math.max(maxY, bbox.max.y);
            }
        });
        
        if (minX !== Infinity) {
            // Center on bounding box
            this.viewport.centerX = (minX + maxX) / 2;
            this.viewport.centerY = (minY + maxY) / 2;
            
            // Calculate scale to fit
            const objectWidth = maxX - minX;
            const objectHeight = maxY - minY;
            const scaleX = this.width / objectWidth * 0.8;
            const scaleY = this.height / objectHeight * 0.8;
            
            this.setZoom(Math.min(scaleX, scaleY));
        }
    }
}

// Export for use in other modules
window.ASCIIRenderer = ASCIIRenderer;