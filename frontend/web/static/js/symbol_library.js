// Symbol Library Module

class SymbolLibrary {
    constructor() {
        this.symbols = [];
        this.categories = [];
        this.sidebar = document.getElementById('symbol-library');
        this.list = this.sidebar ? this.sidebar.querySelector('#symbol-list') : null;
        this.searchInput = this.sidebar ? this.sidebar.querySelector('#symbol-search') : null;
        this.categoryFilter = this.sidebar ? this.sidebar.querySelector('#category-filter') : null;
        this.uploadForm = this.sidebar ? this.sidebar.querySelector('#symbol-upload-form') : null;
        this.uploadStatus = this.sidebar ? this.sidebar.querySelector('#symbol-upload-status') : null;
        this.isDragging = false;
        this.draggedSymbol = null;
        this.viewportManager = null; // Reference to viewport manager
        this.symbolScaler = null; // Reference to symbol scaler
        this.lodManager = null; // Reference to LOD manager
        this.init();
    }

    async init() {
        await this.fetchCategories();
        await this.fetchSymbols();
        this.renderSymbols();
        this.setupDragDrop();
        this.setupFilterEvents();
        this.setupUpload();
        this.connectToViewportManager();
        this.connectToSymbolScaler();
        this.connectToLODManager();
    }

    /**
     * Connect to the viewport manager for coordinate conversion
     */
    connectToViewportManager() {
        // Wait for viewport manager to be available
        const checkViewportManager = () => {
            if (window.viewportManager) {
                this.viewportManager = window.viewportManager;
                window.arxLogger.info('SymbolLibrary connected to ViewportManager', { file: 'symbol_library.js' });
            } else {
                // Retry after a short delay
                setTimeout(checkViewportManager, 100);
            }
        };
        checkViewportManager();
    }

    /**
     * Connect to the symbol scaler for dynamic scaling
     */
    connectToSymbolScaler() {
        // Wait for symbol scaler to be available
        const checkSymbolScaler = () => {
            if (window.symbolScaler) {
                this.symbolScaler = window.symbolScaler;
                window.arxLogger.info('SymbolLibrary connected to SymbolScaler', { file: 'symbol_library.js' });

                // Update symbol previews when scaler is ready
                this.updateSymbolPreviews();
            } else {
                // Retry after a short delay
                setTimeout(checkSymbolScaler, 100);
            }
        };
        checkSymbolScaler();
    }

    /**
     * Connect to the LOD manager for level of detail optimization
     */
    connectToLODManager() {
        // Wait for LOD manager to be available
        const checkLODManager = () => {
            if (window.lodManager) {
                this.lodManager = window.lodManager;
                window.arxLogger.info('SymbolLibrary connected to LODManager', { file: 'symbol_library.js' });

                // Listen for LOD changes to update symbol previews
                this.lodManager.addEventListener('lodChanged', (data) => {
                    this.updateSymbolPreviews();
                });
            } else {
                // Retry after a short delay
                setTimeout(checkLODManager, 100);
            }
        };
        checkLODManager();
    }

    async fetchCategories() {
        try {
            const res = await fetch('/api/symbols/categories');
            this.categories = await res.json();
            this.populateCategoryDropdown();
        } catch (e) {
            this.categories = [];
        }
    }

    populateCategoryDropdown() {
        if (!this.categoryFilter) return;
        this.categoryFilter.innerHTML = '<option value="">All</option>';
        this.categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
            this.categoryFilter.appendChild(opt);
        });
    }

    async fetchSymbols() {
        try {
            const res = await fetch('/api/symbols');
            this.symbols = await res.json();
        } catch (e) {
            this.symbols = [];
        }
    }

    getFilteredSymbols() {
        let filtered = this.symbols;
        const search = this.searchInput?.value?.toLowerCase() || '';
        const cat = this.categoryFilter?.value || '';
        if (cat) filtered = filtered.filter(s => s.category === cat);
        if (search) filtered = filtered.filter(s => s.name.toLowerCase().includes(search) || s.id.toLowerCase().includes(search));
        return filtered;
    }

    renderSymbols() {
        if (!this.list) return;
        this.list.innerHTML = '';
        const symbols = this.getFilteredSymbols();
        if (symbols.length === 0) {
            this.list.innerHTML = '<div class="text-gray-400 text-center col-span-2">No symbols found.</div>';
            return;
        }
        symbols.forEach(symbol => {
            const div = document.createElement('div');
            div.className = 'symbol-item mb-2 p-2 border rounded flex flex-col items-center cursor-grab bg-white shadow-sm';
            div.setAttribute('draggable', 'true');
            div.setAttribute('data-symbol-id', symbol.id);
            div.setAttribute('data-base-scale', '1.0'); // Default base scale

            // Create symbol preview with LOD support
            const previewDiv = document.createElement('div');
            previewDiv.className = 'symbol-preview mb-1';
            previewDiv.setAttribute('data-base-scale', '1.0');
            previewDiv.setAttribute('data-symbol-id', symbol.id);

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', '32');
            svg.setAttribute('height', '32');
            svg.setAttribute('viewBox', '0 0 20 20');

            // Use LOD-optimized SVG for preview if available
            if (this.lodManager) {
                const lodData = this.lodManager.getSymbolLODData(symbol.id);
                if (lodData) {
                    const currentLODLevel = this.lodManager.getCurrentLODLevel();
                    const lodSVG = this.lodManager.getLODSVG(lodData, currentLODLevel);
                    if (lodSVG) {
                        svg.innerHTML = lodSVG;
                    } else {
                        svg.innerHTML = symbol.svg || '';
                    }
                } else {
                    svg.innerHTML = symbol.svg || '';
                }
            } else {
                svg.innerHTML = symbol.svg || '';
            }

            previewDiv.appendChild(svg);

            div.innerHTML = '';
            div.appendChild(previewDiv);

            const nameSpan = document.createElement('span');
            nameSpan.className = 'text-xs text-gray-700';
            nameSpan.textContent = symbol.name;
            div.appendChild(nameSpan);

            // Add LOD indicator if available
            if (this.lodManager) {
                const lodIndicator = document.createElement('span');
                lodIndicator.className = 'text-xs text-blue-500 mt-1';
                lodIndicator.textContent = `LOD: ${this.lodManager.getCurrentLODLevel()}`;
                div.appendChild(lodIndicator);
            }

            div.addEventListener('dragstart', e => this.handleDragStart(e, symbol));
            div.addEventListener('dragend', e => this.handleDragEnd(e));
            this.list.appendChild(div);
        });

        // Apply scaling to previews if scaler is available
        this.updateSymbolPreviews();
    }

    setupFilterEvents() {
        if (this.searchInput) this.searchInput.addEventListener('input', () => this.renderSymbols());
        if (this.categoryFilter) this.categoryFilter.addEventListener('change', () => this.renderSymbols());
    }

    setupDragDrop() {
        const svgContainer = document.getElementById('svg-container');
        if (!svgContainer) return;
        svgContainer.addEventListener('dragover', e => {
            e.preventDefault();
            svgContainer.classList.add('svg-drop-hover');
        });
        svgContainer.addEventListener('dragleave', e => {
            svgContainer.classList.remove('svg-drop-hover');
        });
        svgContainer.addEventListener('drop', e => this.handleDrop(e, svgContainer));
    }

    handleDragStart(e, symbol) {
        this.isDragging = true;
        this.draggedSymbol = symbol;
        e.dataTransfer.effectAllowed = 'copy';
        e.dataTransfer.setData('application/json', JSON.stringify(symbol));
    }

    handleDragEnd(e) {
        this.isDragging = false;
        this.draggedSymbol = null;
        const svgContainer = document.getElementById('svg-container');
        if (svgContainer) svgContainer.classList.remove('svg-drop-hover');
    }

    handleDrop(e, svgContainer) {
        e.preventDefault();
        svgContainer.classList.remove('svg-drop-hover');
        let symbol = this.draggedSymbol;
        if (!symbol) {
            try {
                symbol = JSON.parse(e.dataTransfer.getData('application/json'));
            } catch (err) { return; }
        }
        if (!symbol) return;

        // Get drop coordinates using viewport manager if available
        const svg = svgContainer.querySelector('svg');
        if (!svg) return;

        const coordinates = this.getDropCoordinates(e, svg);

        // Convert to real-world coordinates if scale factors are available
        let realWorldCoords = null;
        if (this.viewportManager && this.viewportManager.scaleFactors.x !== 1.0) {
            realWorldCoords = this.viewportManager.svgToRealWorld(coordinates.x, coordinates.y);
            window.arxLogger.info(`Symbol placed at real-world coordinates: (${realWorldCoords.x.toFixed(2)}, ${realWorldCoords.y.toFixed(2)}) ${this.viewportManager.currentUnit}`, { file: 'symbol_library.js' });
        }

        this.placeSymbol(svg, symbol, coordinates.x, coordinates.y, realWorldCoords);
    }

    /**
     * Get drop coordinates with proper viewport transformation
     */
    getDropCoordinates(e, svg) {
        // If viewport manager is available, use its coordinate conversion
        if (window.viewportManager && window.viewportManager.screenToSVG) {
            return window.viewportManager.screenToSVG(e.clientX, e.clientY);
        }

        // Fallback to original method
        const pt = svg.createSVGPoint();
        pt.x = e.clientX;
        pt.y = e.clientY;
        const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
        return { x: svgP.x, y: svgP.y };
    }

    placeSymbol(svg, symbol, x, y, realWorldCoords) {
        // Create unique ID
        const objectId = `${symbol.id}_${Date.now()}_${Math.floor(Math.random()*10000)}`;

        // Create symbol element
        const symbolElement = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        symbolElement.setAttribute('id', objectId);
        symbolElement.setAttribute('class', 'placed-symbol');
        symbolElement.setAttribute('data-id', objectId);
        symbolElement.setAttribute('data-symbol-id', symbol.id);
        symbolElement.setAttribute('data-symbol-name', symbol.name);
        symbolElement.setAttribute('data-category', symbol.category);
        symbolElement.setAttribute('data-base-scale', '1.0');
        symbolElement.setAttribute('data-x', x.toString());
        symbolElement.setAttribute('data-y', y.toString());
        symbolElement.setAttribute('data-rotation', '0');
        symbolElement.setAttribute('data-type', 'symbol');
        symbolElement.setAttribute('data-system', 'electrical');
        symbolElement.setAttribute('data-status', 'active');
        symbolElement.setAttribute('data-priority', 'normal');

        // Add LOD attributes
        symbolElement.setAttribute('data-lod-level', 'medium'); // Default LOD level
        symbolElement.setAttribute('data-lod-complexity', '0.7'); // Default complexity
        symbolElement.setAttribute('data-lod-enabled', 'true'); // Enable LOD by default

        // Add scale metadata if viewport manager is available
        if (this.viewportManager && this.viewportManager.scaleFactors.x !== 1.0) {
            symbolElement.setAttribute('data-scale-x', this.viewportManager.scaleFactors.x.toString());
            symbolElement.setAttribute('data-scale-y', this.viewportManager.scaleFactors.y.toString());
            symbolElement.setAttribute('data-coordinate-system', 'real_world');
            symbolElement.setAttribute('data-unit', this.viewportManager.currentUnit);

            // Store original SVG coordinates
            symbolElement.setAttribute('data-svg-x', x.toString());
            symbolElement.setAttribute('data-svg-y', y.toString());
        }

        // Store real-world coordinates as metadata if available
        if (realWorldCoords) {
            symbolElement.setAttribute('data-real-world-x', realWorldCoords.x.toString());
            symbolElement.setAttribute('data-real-world-y', realWorldCoords.y.toString());
            symbolElement.setAttribute('data-unit', this.viewportManager.currentUnit);
        }

        // Create the SVG content with LOD support
        const symbolSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        symbolSvg.setAttribute('width', '40');
        symbolSvg.setAttribute('height', '40');
        symbolSvg.setAttribute('viewBox', '0 0 20 20');

        // Use LOD-optimized SVG if available
        if (this.lodManager) {
            const lodData = this.lodManager.getSymbolLODData(symbol.id);
            if (lodData) {
                const currentLODLevel = this.lodManager.getCurrentLODLevel();
                const lodSVG = this.lodManager.getLODSVG(lodData, currentLODLevel);
                if (lodSVG) {
                    symbolSvg.innerHTML = lodSVG;
                } else {
                    symbolSvg.innerHTML = symbol.svg || '';
                }
            } else {
                symbolSvg.innerHTML = symbol.svg || '';
            }
        } else {
            symbolSvg.innerHTML = symbol.svg || '';
        }

        // Apply base scaling if symbol scaler is available
        if (this.symbolScaler) {
            this.symbolScaler.applyBaseScaling(symbolSvg, 1.0);
        }

        symbolElement.appendChild(symbolSvg);

        // Position the symbol
        symbolElement.setAttribute('transform', `translate(${x}, ${y})`);

        // Add to SVG
        svg.appendChild(symbolElement);

        // Add placement animation
        symbolElement.classList.add('placing');
        setTimeout(() => {
            symbolElement.classList.remove('placing');
        }, 400);

        // Log placement with real-world coordinates if available
        if (realWorldCoords) {
            window.arxLogger.debug(`Symbol "${symbol.name}" placed at:`, { symbol, file: 'symbol_library.js' });
        } else {
            window.arxLogger.debug(`Symbol "${symbol.name}" placed at SVG coordinates: (${x.toFixed(2)}, ${y.toFixed(2)})`, { file: 'symbol_library.js' });
        }

        // Trigger symbol placed event
        this.triggerSymbolPlacedEvent(symbol, x, y, realWorldCoords, symbolElement);

        return symbolElement;
    }

    /**
     * Update symbol positions when viewport changes
     */
    updateSymbolPositions() {
        if (!window.viewportManager) return;

        const placedSymbols = document.querySelectorAll('.placed-symbol[data-placed-symbol="true"]');
        placedSymbols.forEach(symbol => {
            const x = parseFloat(symbol.getAttribute('data-x'));
            const y = parseFloat(symbol.getAttribute('data-y'));
            const rotation = parseFloat(symbol.getAttribute('data-rotation') || '0');

            // Apply transform with rotation
            const transform = `translate(${x},${y}) rotate(${rotation})`;
            symbol.setAttribute('transform', transform);
        });
    }

    /**
     * Get symbol position in SVG coordinates
     */
    getSymbolPosition(symbolElement) {
        const x = parseFloat(symbolElement.getAttribute('data-x'));
        const y = parseFloat(symbolElement.getAttribute('data-y'));
        return { x, y };
    }

    /**
     * Set symbol position in SVG coordinates
     */
    setSymbolPosition(symbolElement, x, y) {
        symbolElement.setAttribute('data-x', x);
        symbolElement.setAttribute('data-y', y);
        const rotation = parseFloat(symbolElement.getAttribute('data-rotation') || '0');
        const transform = `translate(${x},${y}) rotate(${rotation})`;
        symbolElement.setAttribute('transform', transform);

        // Trigger viewport manager event
        if (window.viewportManager) {
            window.viewportManager.triggerEvent('objectMoved', {
                objectId: symbolElement.getAttribute('data-id'),
                x: x,
                y: y,
                element: symbolElement
            });
        }
    }

    /**
     * Convert screen coordinates to SVG coordinates
     */
    screenToSVGCoordinates(screenX, screenY) {
        if (window.viewportManager && window.viewportManager.screenToSVG) {
            return window.viewportManager.screenToSVG(screenX, screenY);
        }
        return { x: screenX, y: screenY };
    }

    /**
     * Convert SVG coordinates to screen coordinates
     */
    svgToScreenCoordinates(svgX, svgY) {
        if (window.viewportManager && window.viewportManager.svgToScreen) {
            return window.viewportManager.svgToScreen(svgX, svgY);
        }
        return { x: svgX, y: svgY };
    }

    setupUpload() {
        if (!this.uploadForm) return;
        this.uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!this.uploadForm.symbolFile || !this.uploadForm.symbolFile.files[0]) return;
            const formData = new FormData();
            formData.append('file', this.uploadForm.symbolFile.files[0]);
            formData.append('name', this.uploadForm.symbolName.value);
            formData.append('category', this.uploadForm.symbolCategory.value);
            formData.append('meta', this.uploadForm.symbolMeta.value);
            this.uploadStatus.textContent = 'Uploading...';
            try {
                const res = await fetch('/api/symbols', {
                    method: 'POST',
                    body: formData
                });
                if (!res.ok) throw new Error('Upload failed');
                this.uploadStatus.textContent = 'Upload successful!';
                await this.fetchSymbols();
                this.renderSymbols();
                this.uploadForm.reset();
            } catch (err) {
                this.uploadStatus.textContent = 'Upload failed.';
            }
        });
    }

    /**
     * Update symbol previews with current zoom level
     */
    updateSymbolPreviews() {
        if (!this.list) return;

        const previews = this.list.querySelectorAll('.symbol-preview');
        previews.forEach(preview => {
            const symbolId = preview.getAttribute('data-symbol-id');
            const baseScale = parseFloat(preview.getAttribute('data-base-scale')) || 1.0;

            // Update scaling if symbol scaler is available
            if (this.symbolScaler) {
                this.symbolScaler.scaleSymbolPreview(preview, baseScale);
            }

            // Update LOD if LOD manager is available
            if (this.lodManager && symbolId) {
                const svg = preview.querySelector('svg');
                if (svg) {
                    const lodData = this.lodManager.getSymbolLODData(symbolId);
                    if (lodData) {
                        const currentLODLevel = this.lodManager.getCurrentLODLevel();
                        const lodSVG = this.lodManager.getLODSVG(lodData, currentLODLevel);
                        if (lodSVG) {
                            svg.innerHTML = lodSVG;
                        }
                    }
                }
            }
        });

        // Update LOD indicators
        const lodIndicators = this.list.querySelectorAll('.text-blue-500');
        lodIndicators.forEach(indicator => {
            if (this.lodManager) {
                indicator.textContent = `LOD: ${this.lodManager.getCurrentLODLevel()}`;
            }
        });
    }

    /**
     * Set base scale for a symbol preview
     */
    setSymbolPreviewScale(symbolId, baseScale) {
        const symbolItem = this.list?.querySelector(`[data-symbol-id="${symbolId}"]`);
        if (!symbolItem) return;

        const preview = symbolItem.querySelector('.symbol-preview');
        if (!preview) return;

        preview.setAttribute('data-base-scale', baseScale);

        if (this.symbolScaler) {
            this.symbolScaler.updateSymbolScale(preview, baseScale);
        }
    }

    /**
     * Trigger symbol placed event with real-world coordinates
     */
    triggerSymbolPlacedEvent(symbol, x, y, realWorldCoords, symbolElement) {
        // Trigger selection and events
        if (window.svgObjectInteraction) {
            window.svgObjectInteraction.selectObject(symbolElement);
        }

        // Trigger viewport manager event for new object placement
        if (window.viewportManager) {
            window.viewportManager.triggerEvent('objectPlaced', {
                objectId: symbolElement.id,
                symbolId: symbol.id,
                x: x,
                y: y,
                realWorldCoords: realWorldCoords,
                element: symbolElement
            });
        }

        // Trigger custom event for other components
        const event = new CustomEvent('symbolPlaced', {
            detail: {
                symbol: symbol,
                svgCoords: { x, y },
                realWorldCoords: realWorldCoords,
                element: symbolElement
            }
        });
        document.dispatchEvent(event);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.symbolLibrary = new SymbolLibrary();
});
