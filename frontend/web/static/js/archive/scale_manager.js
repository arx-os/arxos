/**
 * Scale Manager for SVG Viewer
 * Handles scale reference points, unit conversion, and scale calculations
 */

class ScaleManager {
    constructor() {
        this.scaleMode = false;
        this.referencePoints = {
            point1: null,
            point2: null
        };
        this.scaleFactors = {
            x: 1.0,
            y: 1.0
        };
        this.currentUnit = 'meters';
        this.units = {
            pixels: { name: 'Pixels', conversion: 1 },
            meters: { name: 'Meters', conversion: 1 },
            feet: { name: 'Feet', conversion: 0.3048 },
            inches: { name: 'Inches', conversion: 0.0254 },
            millimeters: { name: 'Millimeters', conversion: 0.001 }
        };

        this.initializeEventListeners();
        this.updateScaleIndicator();
    }

    initializeEventListeners() {
        // Scale mode toggle
        document.getElementById('scale-mode-toggle').addEventListener('click', () => {
            this.toggleScaleMode();
        });

        // Unit selector
        document.getElementById('unit-selector').addEventListener('change', (e) => {
            this.setUnit(e.target.value);
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 's' || e.key === 'S') {
                e.preventDefault();
                this.toggleScaleMode();
            }
        });

        // SVG container click for reference points
        document.getElementById('svg-container').addEventListener('click', (e) => {
            if (this.scaleMode) {
                this.handleReferencePointClick(e);
            }
        });
    }

    toggleScaleMode() {
        this.scaleMode = !this.scaleMode;
        const toggleButton = document.getElementById('scale-mode-toggle');

        if (this.scaleMode) {
            toggleButton.classList.add('scale-mode-active');
            toggleButton.textContent = 'Scale Mode Active';
            this.showScaleReferencePanel();
            this.updateCursor();
        } else {
            toggleButton.classList.remove('scale-mode-active');
            toggleButton.innerHTML = '<svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>Scale';
            this.hideScaleReferencePanel();
            this.updateCursor();
        }
    }

    updateCursor() {
        const container = document.getElementById('svg-container');
        if (this.scaleMode) {
            container.style.cursor = 'crosshair';
        } else {
            container.style.cursor = 'default';
        }
    }

    showScaleReferencePanel() {
        const panel = document.getElementById('scale-reference-panel');
        panel.classList.remove('hidden');
        panel.classList.add('scale-panel-enter');

        setTimeout(() => {
            panel.classList.remove('scale-panel-enter');
        }, 300);
    }

    hideScaleReferencePanel() {
        const panel = document.getElementById('scale-reference-panel');
        panel.classList.add('scale-panel-exit');

        setTimeout(() => {
            panel.classList.add('hidden');
            panel.classList.remove('scale-panel-exit');
        }, 300);
    }

    closeScaleReferencePanel() {
        this.scaleMode = false;
        this.toggleScaleMode();
    }

    handleReferencePointClick(event) {
        const rect = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Convert screen coordinates to SVG coordinates
        const svgCoords = this.screenToSVGCoordinates(x, y);

        // Determine which reference point to set
        let pointNumber = 1;
        if (this.referencePoints.point1) {
            pointNumber = 2;
        }

        this.setReferencePointFromClick(pointNumber, svgCoords);
    }

    setReferencePointFromClick(pointNumber, svgCoords) {
        const point = {
            svg: svgCoords,
            real: [0, 0] // Will be filled by user
        };

        if (pointNumber === 1) {
            this.referencePoints.point1 = point;
            this.updateReferencePointInputs(1, point);
            this.addReferencePointMarker(1, svgCoords);
        } else {
            this.referencePoints.point2 = point;
            this.updateReferencePointInputs(2, point);
            this.addReferencePointMarker(2, svgCoords);
        }

        this.updateScaleLine();
        this.validateReferencePoints();
    }

    setReferencePoint(pointNumber) {
        // This function is called from the UI buttons
        if (pointNumber === 1) {
            const x = parseFloat(document.getElementById('ref1-svg-x').value) || 0;
            const y = parseFloat(document.getElementById('ref1-svg-y').value) || 0;
            this.referencePoints.point1 = { svg: [x, y], real: [0, 0] };
            this.addReferencePointMarker(1, [x, y]);
        } else {
            const x = parseFloat(document.getElementById('ref2-svg-x').value) || 100;
            const y = parseFloat(document.getElementById('ref2-svg-y').value) || 100;
            this.referencePoints.point2 = { svg: [x, y], real: [0, 0] };
            this.addReferencePointMarker(2, [x, y]);
        }

        this.updateScaleLine();
        this.validateReferencePoints();
    }

    updateReferencePointInputs(pointNumber, point) {
        if (pointNumber === 1) {
            document.getElementById('ref1-svg-x').value = point.svg[0].toFixed(2);
            document.getElementById('ref1-svg-y').value = point.svg[1].toFixed(2);
        } else {
            document.getElementById('ref2-svg-x').value = point.svg[0].toFixed(2);
            document.getElementById('ref2-svg-y').value = point.svg[1].toFixed(2);
        }
    }

    addReferencePointMarker(pointNumber, coords) {
        const markersContainer = document.getElementById('scale-reference-markers');
        const markerId = `ref-marker-${pointNumber}`;

        // Remove existing marker
        const existingMarker = document.getElementById(markerId);
        if (existingMarker) {
            existingMarker.remove();
        }

        // Create new marker
        const marker = document.createElement('div');
        marker.id = markerId;
        marker.className = `reference-point-marker point-${pointNumber}`;
        marker.style.left = `${coords[0] - 10}px`;
        marker.style.top = `${coords[1] - 10}px`;

        // Add label
        const label = document.createElement('div');
        label.className = 'reference-point-label';
        label.textContent = `Point ${pointNumber}`;
        label.style.left = `${coords[0] + 15}px`;
        label.style.top = `${coords[1] - 10}px`;

        marker.appendChild(label);
        markersContainer.appendChild(marker);
    }

    updateScaleLine() {
        const markersContainer = document.getElementById('scale-reference-markers');
        const lineId = 'scale-line';

        // Remove existing line
        const existingLine = document.getElementById(lineId);
        if (existingLine) {
            existingLine.remove();
        }

        // Add line if both points exist
        if (this.referencePoints.point1 && this.referencePoints.point2) {
            const line = document.createElement('div');
            line.id = lineId;
            line.className = 'scale-line';

            const x1 = this.referencePoints.point1.svg[0];
            const y1 = this.referencePoints.point1.svg[1];
            const x2 = this.referencePoints.point2.svg[0];
            const y2 = this.referencePoints.point2.svg[1];

            const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
            const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;

            line.style.left = `${x1}px`;
            line.style.top = `${y1}px`;
            line.style.width = `${length}px`;
            line.style.transform = `rotate(${angle}deg)`;
            line.style.transformOrigin = '0 50%';

            markersContainer.appendChild(line);
        }
    }

    validateReferencePoints() {
        const inputs = [
            'ref1-svg-x', 'ref1-svg-y', 'ref1-real-x', 'ref1-real-y',
            'ref2-svg-x', 'ref2-svg-y', 'ref2-real-x', 'ref2-real-y'
        ];

        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            const value = parseFloat(input.value);

            input.classList.remove('valid', 'invalid');

            if (input.value === '' || isNaN(value)) {
                input.classList.add('invalid');
            } else {
                input.classList.add('valid');
            }
        });
    }

    calculateScaleFactors() {
        if (!this.referencePoints.point1 || !this.referencePoints.point2) {
            this.showError('Please set both reference points');
            return;
        }

        // Get real-world coordinates from inputs
        const real1x = parseFloat(document.getElementById('ref1-real-x').value);
        const real1y = parseFloat(document.getElementById('ref1-real-y').value);
        const real2x = parseFloat(document.getElementById('ref2-real-x').value);
        const real2y = parseFloat(document.getElementById('ref2-real-y').value);

        if (isNaN(real1x) || isNaN(real1y) || isNaN(real2x) || isNaN(real2y)) {
            this.showError('Please enter valid real-world coordinates');
            return;
        }

        // Calculate scale factors
        const svg1 = this.referencePoints.point1.svg;
        const svg2 = this.referencePoints.point2.svg;

        const dxSvg = svg2[0] - svg1[0];
        const dySvg = svg2[1] - svg1[1];
        const dxReal = real2x - real1x;
        const dyReal = real2y - real1y;

        if (dxSvg === 0 || dySvg === 0) {
            this.showError('Reference points cannot be on the same vertical or horizontal line');
            return;
        }

        this.scaleFactors.x = dxReal / dxSvg;
        this.scaleFactors.y = dyReal / dySvg;

        // Calculate confidence and uniformity
        const scaleRatio = Math.abs(this.scaleFactors.x - this.scaleFactors.y) / Math.max(Math.abs(this.scaleFactors.x), Math.abs(this.scaleFactors.y));
        const uniform = scaleRatio < 0.01;
        const confidence = Math.min(1.0, 0.5 + (1 - scaleRatio) * 0.5);

        // Update UI
        this.updateScaleCalculationResults(uniform, confidence);
        this.updateScaleFactorDisplay();
        this.updateScaleIndicator();

        this.showSuccess('Scale factors calculated successfully');
    }

    updateScaleCalculationResults(uniform, confidence) {
        const resultsDiv = document.getElementById('scale-calculation-results');
        const scaleXSpan = document.getElementById('calculated-scale-x');
        const scaleYSpan = document.getElementById('calculated-scale-y');
        const uniformSpan = document.getElementById('scale-uniform');
        const confidenceSpan = document.getElementById('scale-confidence');

        scaleXSpan.textContent = this.scaleFactors.x.toFixed(6);
        scaleYSpan.textContent = this.scaleFactors.y.toFixed(6);
        uniformSpan.textContent = uniform ? 'Yes' : 'No';
        confidenceSpan.textContent = `${(confidence * 100).toFixed(1)}%`;

        resultsDiv.classList.remove('hidden');
        resultsDiv.classList.add('show');
    }

    updateScaleFactorDisplay() {
        const display = document.getElementById('scale-factor-display');
        const valueSpan = document.getElementById('scale-factor-value');

        const scaleX = this.scaleFactors.x;
        const scaleY = this.scaleFactors.y;

        if (Math.abs(scaleX - scaleY) < 0.01) {
            valueSpan.textContent = `1:${(1/scaleX).toFixed(2)}`;
        } else {
            valueSpan.textContent = `X:${(1/scaleX).toFixed(2)} Y:${(1/scaleY).toFixed(2)}`;
        }

        display.classList.add('updated');
        setTimeout(() => {
            display.classList.remove('updated');
        }, 600);
    }

    updateScaleIndicator() {
        const ratioSpan = document.getElementById('scale-ratio');
        const unitsSpan = document.getElementById('scale-units');
        const distanceSpan = document.getElementById('scale-distance');
        const indicator = document.getElementById('scale-indicator');

        const scaleX = this.scaleFactors.x;
        const scaleY = this.scaleFactors.y;

        if (Math.abs(scaleX - scaleY) < 0.01) {
            ratioSpan.textContent = `1:${(1/scaleX).toFixed(2)}`;
        } else {
            ratioSpan.textContent = `X:${(1/scaleX).toFixed(2)} Y:${(1/scaleY).toFixed(2)}`;
        }

        unitsSpan.textContent = this.currentUnit;

        // Show example distance
        const examplePixels = 100;
        const exampleReal = examplePixels * scaleX;
        const convertedReal = this.convertUnits(exampleReal, this.currentUnit);
        distanceSpan.textContent = `${examplePixels}px = ${convertedReal.toFixed(2)}${this.currentUnit}`;

        indicator.classList.add('updated');
        setTimeout(() => {
            indicator.classList.remove('updated');
        }, 500);
    }

    applyScaleFactors() {
        if (!this.scaleFactors.x || !this.scaleFactors.y) {
            this.showError('Please calculate scale factors first');
            return;
        }

        // Store scale factors for use by other components
        window.currentScaleFactors = {
            x: this.scaleFactors.x,
            y: this.scaleFactors.y,
            unit: this.currentUnit
        };

        // Update viewport manager with scale factors
        if (window.viewportManager) {
            window.viewportManager.setScaleFactors(this.scaleFactors.x, this.scaleFactors.y);
        }

        this.showSuccess('Scale factors applied successfully');
    }

    clearReferencePoints() {
        this.referencePoints = { point1: null, point2: null };

        // Clear inputs
        ['ref1-svg-x', 'ref1-svg-y', 'ref1-real-x', 'ref1-real-y',
         'ref2-svg-x', 'ref2-svg-y', 'ref2-real-x', 'ref2-real-y'].forEach(id => {
            document.getElementById(id).value = '';
            document.getElementById(id).classList.remove('valid', 'invalid');
        });

        // Clear markers and line
        document.getElementById('scale-reference-markers').innerHTML = '';

        // Hide results
        document.getElementById('scale-calculation-results').classList.add('hidden');

        this.showSuccess('Reference points cleared');
    }

    setUnit(unit) {
        this.currentUnit = unit;
        this.updateScaleIndicator();

        // Update unit display
        document.getElementById('scale-units').textContent = unit;

        this.showSuccess(`Unit changed to ${this.units[unit].name}`);
    }

    convertUnits(value, targetUnit) {
        const baseUnit = 'meters';
        const baseValue = value * this.units[this.currentUnit].conversion;
        return baseValue / this.units[targetUnit].conversion;
    }

    screenToSVGCoordinates(screenX, screenY) {
        // This would need to be integrated with the viewport manager
        // For now, return screen coordinates as SVG coordinates
        return [screenX, screenY];
    }

    showError(message) {
        // Create temporary error notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showSuccess(message) {
        // Create temporary success notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Public methods for external use
    getScaleFactors() {
        return this.scaleFactors;
    }

    getCurrentUnit() {
        return this.currentUnit;
    }

    convertToRealWorld(svgCoords) {
        return [
            svgCoords[0] * this.scaleFactors.x,
            svgCoords[1] * this.scaleFactors.y
        ];
    }

    convertToSVG(realWorldCoords) {
        return [
            realWorldCoords[0] / this.scaleFactors.x,
            realWorldCoords[1] / this.scaleFactors.y
        ];
    }
}

// Global functions for HTML onclick handlers
function toggleScaleMode() {
    if (window.scaleManager) {
        window.scaleManager.toggleScaleMode();
    }
}

function setReferencePoint(pointNumber) {
    if (window.scaleManager) {
        window.scaleManager.setReferencePoint(pointNumber);
    }
}

function calculateScaleFactors() {
    if (window.scaleManager) {
        window.scaleManager.calculateScaleFactors();
    }
}

function applyScaleFactors() {
    if (window.scaleManager) {
        window.scaleManager.applyScaleFactors();
    }
}

function clearReferencePoints() {
    if (window.scaleManager) {
        window.scaleManager.clearReferencePoints();
    }
}

function closeScaleReferencePanel() {
    if (window.scaleManager) {
        window.scaleManager.closeScaleReferencePanel();
    }
}

// Initialize scale manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.scaleManager = new ScaleManager();
});
