/**
 * Arxos Coordinate System - Nanometer Precision Support
 * Handles conversion between nanometers and display units
 * Enables zooming from campus (km) to circuit traces (nm)
 */

// Unit conversion constants matching Go backend
const Units = {
    // Base unit is nanometer (1 nm = 10^-9 m)
    Nanometer: 1n,
    Micrometer: 1000n,              // 1 μm = 1000 nm
    Millimeter: 1000000n,           // 1 mm = 1,000,000 nm  
    Centimeter: 10000000n,          // 1 cm = 10,000,000 nm
    Meter: 1000000000n,             // 1 m = 1,000,000,000 nm
    Kilometer: 1000000000000n,      // 1 km = 10^12 nm
    
    // Imperial units
    Inch: 25400000n,                // 1 in = 25.4 mm = 25,400,000 nm
    Foot: 304800000n,               // 1 ft = 304.8 mm = 304,800,000 nm
    Yard: 914400000n,               // 1 yd = 914.4 mm
    Mile: 1609344000000n,           // 1 mi = 1.609344 km
    
    // PCB/Manufacturing units
    Mil: 25400n,                    // 1 mil = 0.001 inch = 25.4 μm
    Micron: 1000n                   // Common in PCB manufacturing
};

// Scale levels for different zoom ranges
const ScaleLevels = {
    CIRCUIT: 0,    // Circuit board traces, chips
    COMPONENT: 1,  // IoT devices, sensors, outlets
    ROOM: 2,       // Room-level objects
    BUILDING: 3,   // Building structure
    CAMPUS: 4      // Campus/site level
};

// Coordinate converter class
class CoordinateSystem {
    constructor() {
        // Current viewport scale (nanometers per pixel)
        this.scaleNanoPerPixel = Number(Units.Millimeter); // Start at 1mm per pixel
        
        // Viewport center in nanometers
        this.centerX = 0n;
        this.centerY = 0n;
        this.centerZ = 0n;
    }
    
    // Convert nanometers to pixels for display
    nanoToPixel(nanoCoord) {
        // Use Number for display calculations
        return Number(nanoCoord) / this.scaleNanoPerPixel;
    }
    
    // Convert pixels to nanometers
    pixelToNano(pixelCoord) {
        return BigInt(Math.round(pixelCoord * this.scaleNanoPerPixel));
    }
    
    // Convert nanometers to meters
    nanoToMeters(nano) {
        return Number(nano) / Number(Units.Meter);
    }
    
    // Convert meters to nanometers
    metersToNano(meters) {
        return BigInt(Math.round(meters * Number(Units.Meter)));
    }
    
    // Convert nanometers to millimeters
    nanoToMillimeters(nano) {
        return Number(nano) / Number(Units.Millimeter);
    }
    
    // Convert millimeters to nanometers
    millimetersToNano(mm) {
        return BigInt(Math.round(mm * Number(Units.Millimeter)));
    }
    
    // Convert nanometers to micrometers
    nanoToMicrometers(nano) {
        return Number(nano) / Number(Units.Micrometer);
    }
    
    // Convert micrometers to nanometers
    micrometersToNano(um) {
        return BigInt(Math.round(um * Number(Units.Micrometer)));
    }
    
    // Get appropriate unit label for current scale
    getUnitLabel() {
        if (this.scaleNanoPerPixel < 10) {
            return 'nm';
        } else if (this.scaleNanoPerPixel < 10000) {
            return 'μm';
        } else if (this.scaleNanoPerPixel < 10000000) {
            return 'mm';
        } else if (this.scaleNanoPerPixel < 1000000000) {
            return 'cm';
        } else if (this.scaleNanoPerPixel < 1000000000000) {
            return 'm';
        } else {
            return 'km';
        }
    }
    
    // Format coordinate for display with appropriate precision
    formatCoordinate(nanoCoord) {
        const unit = this.getUnitLabel();
        let value;
        
        switch(unit) {
            case 'nm':
                value = Number(nanoCoord);
                return `${value.toFixed(0)} nm`;
            case 'μm':
                value = this.nanoToMicrometers(nanoCoord);
                return `${value.toFixed(1)} μm`;
            case 'mm':
                value = this.nanoToMillimeters(nanoCoord);
                return `${value.toFixed(2)} mm`;
            case 'cm':
                value = this.nanoToMillimeters(nanoCoord) / 10;
                return `${value.toFixed(2)} cm`;
            case 'm':
                value = this.nanoToMeters(nanoCoord);
                return `${value.toFixed(3)} m`;
            case 'km':
                value = this.nanoToMeters(nanoCoord) / 1000;
                return `${value.toFixed(3)} km`;
            default:
                return `${nanoCoord} nm`;
        }
    }
    
    // Get current scale level based on zoom
    getCurrentScaleLevel() {
        if (this.scaleNanoPerPixel < Number(Units.Micrometer)) {
            return ScaleLevels.CIRCUIT;
        } else if (this.scaleNanoPerPixel < Number(Units.Millimeter) * 10) {
            return ScaleLevels.COMPONENT;
        } else if (this.scaleNanoPerPixel < Number(Units.Meter)) {
            return ScaleLevels.ROOM;
        } else if (this.scaleNanoPerPixel < Number(Units.Meter) * 100) {
            return ScaleLevels.BUILDING;
        } else {
            return ScaleLevels.CAMPUS;
        }
    }
    
    // Zoom in/out by factor
    zoom(factor, pivotX = null, pivotY = null) {
        const oldScale = this.scaleNanoPerPixel;
        this.scaleNanoPerPixel *= factor;
        
        // Clamp to reasonable limits (1nm to 10km per pixel)
        this.scaleNanoPerPixel = Math.max(1, Math.min(10000000000000, this.scaleNanoPerPixel));
        
        // Adjust center to keep pivot point stationary
        if (pivotX !== null && pivotY !== null) {
            const scaleDiff = this.scaleNanoPerPixel - oldScale;
            this.centerX += BigInt(Math.round(pivotX * scaleDiff));
            this.centerY += BigInt(Math.round(pivotY * scaleDiff));
        }
    }
    
    // Pan the viewport
    pan(deltaXPixels, deltaYPixels) {
        this.centerX -= this.pixelToNano(deltaXPixels);
        this.centerY -= this.pixelToNano(deltaYPixels);
    }
    
    // Convert world coordinates to screen coordinates
    worldToScreen(xNano, yNano, viewportWidth, viewportHeight) {
        const x = this.nanoToPixel(xNano - this.centerX) + viewportWidth / 2;
        const y = this.nanoToPixel(yNano - this.centerY) + viewportHeight / 2;
        return { x, y };
    }
    
    // Convert screen coordinates to world coordinates
    screenToWorld(xPixel, yPixel, viewportWidth, viewportHeight) {
        const xNano = this.centerX + this.pixelToNano(xPixel - viewportWidth / 2);
        const yNano = this.centerY + this.pixelToNano(yPixel - viewportHeight / 2);
        return { x: xNano, y: yNano };
    }
}

// ArxObject class with nanometer coordinates
class ArxObjectNano {
    constructor(data) {
        this.id = data.id;
        this.type = data.type;
        
        // Store coordinates as BigInt for precision
        this.x = BigInt(data.x || 0);
        this.y = BigInt(data.y || 0);
        this.z = BigInt(data.z || 0);
        this.length = BigInt(data.length || Units.Meter);
        this.width = BigInt(data.width || Units.Meter);
        this.height = BigInt(data.height || Units.Meter);
        
        this.rotationMillideg = data.rotationMillideg || 0;
        this.scaleLevel = data.scaleLevel || ScaleLevels.ROOM;
        
        this.system = data.system;
        this.properties = data.properties || {};
    }
    
    // Get bounding box in nanometers
    getBounds() {
        const halfLength = this.length / 2n;
        const halfWidth = this.width / 2n;
        
        return {
            minX: this.x - halfLength,
            maxX: this.x + halfLength,
            minY: this.y - halfWidth,
            maxY: this.y + halfWidth,
            minZ: this.z,
            maxZ: this.z + this.height
        };
    }
    
    // Check if object should be visible at current scale
    isVisibleAtScale(scaleLevel) {
        // Objects are visible at their scale level and above
        return this.scaleLevel <= scaleLevel;
    }
    
    // Convert to display coordinates
    toDisplayCoords(coordinateSystem, viewportWidth, viewportHeight) {
        const screen = coordinateSystem.worldToScreen(this.x, this.y, viewportWidth, viewportHeight);
        const lengthPixels = coordinateSystem.nanoToPixel(this.length);
        const widthPixels = coordinateSystem.nanoToPixel(this.width);
        
        return {
            x: screen.x,
            y: screen.y,
            length: lengthPixels,
            width: widthPixels,
            rotation: this.rotationMillideg / 1000
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Units, ScaleLevels, CoordinateSystem, ArxObjectNano };
}