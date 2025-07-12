/**
 * Arxos CDN Loader
 * 
 * This utility integrates with the CDN configuration to load assets
 * efficiently with fallback mechanisms and performance optimization.
 */

class CDNLoader {
    constructor() {
        this.loadedAssets = new Set();
        this.loadingAssets = new Map();
        this.failedAssets = new Set();
    }

    /**
     * Load a CSS file from CDN with fallback
     * @param {string} path - Path to the CSS file
     * @param {string} fallbackPath - Fallback path (optional)
     * @returns {Promise} Promise that resolves when CSS is loaded
     */
    async loadCSS(path, fallbackPath = null) {
        const assetId = `css:${path}`;
        
        // Check if already loaded
        if (this.loadedAssets.has(assetId)) {
            return Promise.resolve();
        }
        
        // Check if currently loading
        if (this.loadingAssets.has(assetId)) {
            return this.loadingAssets.get(assetId);
        }
        
        // Check if previously failed
        if (this.failedAssets.has(assetId)) {
            return Promise.reject(new Error(`Asset previously failed to load: ${path}`));
        }
        
        const cdnUrl = window.CDNUtils.getAssetUrl(path, 'css');
        const fallbackUrl = fallbackPath ? window.CDNUtils.getAssetUrl(fallbackPath, 'css') : null;
        
        const loadPromise = window.CDNUtils.loadCSS(cdnUrl, fallbackUrl)
            .then(() => {
                this.loadedAssets.add(assetId);
                this.loadingAssets.delete(assetId);
                console.log(`✅ CSS loaded: ${path}`);
            })
            .catch(error => {
                this.failedAssets.add(assetId);
                this.loadingAssets.delete(assetId);
                console.error(`❌ Failed to load CSS: ${path}`, error);
                throw error;
            });
        
        this.loadingAssets.set(assetId, loadPromise);
        return loadPromise;
    }

    /**
     * Load a JavaScript file from CDN with fallback
     * @param {string} path - Path to the JavaScript file
     * @param {string} fallbackPath - Fallback path (optional)
     * @returns {Promise} Promise that resolves when JavaScript is loaded
     */
    async loadJS(path, fallbackPath = null) {
        const assetId = `js:${path}`;
        
        // Check if already loaded
        if (this.loadedAssets.has(assetId)) {
            return Promise.resolve();
        }
        
        // Check if currently loading
        if (this.loadingAssets.has(assetId)) {
            return this.loadingAssets.get(assetId);
        }
        
        // Check if previously failed
        if (this.failedAssets.has(assetId)) {
            return Promise.reject(new Error(`Asset previously failed to load: ${path}`));
        }
        
        const cdnUrl = window.CDNUtils.getAssetUrl(path, 'js');
        const fallbackUrl = fallbackPath ? window.CDNUtils.getAssetUrl(fallbackPath, 'js') : null;
        
        const loadPromise = window.CDNUtils.loadJS(cdnUrl, fallbackUrl)
            .then(() => {
                this.loadedAssets.add(assetId);
                this.loadingAssets.delete(assetId);
                console.log(`✅ JavaScript loaded: ${path}`);
            })
            .catch(error => {
                this.failedAssets.add(assetId);
                this.loadingAssets.delete(assetId);
                console.error(`❌ Failed to load JavaScript: ${path}`, error);
                throw error;
            });
        
        this.loadingAssets.set(assetId, loadPromise);
        return loadPromise;
    }

    /**
     * Load multiple CSS files
     * @param {Array} paths - Array of CSS file paths
     * @returns {Promise} Promise that resolves when all CSS files are loaded
     */
    async loadMultipleCSS(paths) {
        const promises = paths.map(path => this.loadCSS(path));
        return Promise.all(promises);
    }

    /**
     * Load multiple JavaScript files
     * @param {Array} paths - Array of JavaScript file paths
     * @returns {Promise} Promise that resolves when all JavaScript files are loaded
     */
    async loadMultipleJS(paths) {
        const promises = paths.map(path => this.loadJS(path));
        return Promise.all(promises);
    }

    /**
     * Load critical assets for a page
     * @param {Object} assets - Object containing critical assets
     * @returns {Promise} Promise that resolves when all critical assets are loaded
     */
    async loadCriticalAssets(assets = {}) {
        const promises = [];
        
        // Load critical CSS
        if (assets.css) {
            const cssPaths = Array.isArray(assets.css) ? assets.css : [assets.css];
            promises.push(this.loadMultipleCSS(cssPaths));
        }
        
        // Load critical JavaScript
        if (assets.js) {
            const jsPaths = Array.isArray(assets.js) ? assets.js : [assets.js];
            promises.push(this.loadMultipleJS(jsPaths));
        }
        
        return Promise.all(promises);
    }

    /**
     * Preload non-critical assets
     * @param {Object} assets - Object containing non-critical assets
     */
    preloadNonCriticalAssets(assets = {}) {
        const preloadAssets = [];
        
        // Add CSS files
        if (assets.css) {
            const cssPaths = Array.isArray(assets.css) ? assets.css : [assets.css];
            cssPaths.forEach(path => {
                preloadAssets.push({
                    url: window.CDNUtils.getAssetUrl(path, 'css'),
                    type: 'style'
                });
            });
        }
        
        // Add JavaScript files
        if (assets.js) {
            const jsPaths = Array.isArray(assets.js) ? assets.js : [assets.js];
            jsPaths.forEach(path => {
                preloadAssets.push({
                    url: window.CDNUtils.getAssetUrl(path, 'js'),
                    type: 'script'
                });
            });
        }
        
        // Add images
        if (assets.images) {
            const imagePaths = Array.isArray(assets.images) ? assets.images : [assets.images];
            imagePaths.forEach(path => {
                preloadAssets.push({
                    url: window.CDNUtils.getAssetUrl(path, 'images'),
                    type: 'image'
                });
            });
        }
        
        // Add fonts
        if (assets.fonts) {
            const fontPaths = Array.isArray(assets.fonts) ? assets.fonts : [assets.fonts];
            fontPaths.forEach(path => {
                preloadAssets.push({
                    url: window.CDNUtils.getAssetUrl(path, 'fonts'),
                    type: 'font',
                    crossorigin: true
                });
            });
        }
        
        window.CDNUtils.preloadAssets(preloadAssets);
    }

    /**
     * Get asset URL for images, fonts, etc.
     * @param {string} path - Path to the asset
     * @param {string} type - Asset type (images, fonts, icons, etc.)
     * @returns {string} Full CDN URL for the asset
     */
    getAssetURL(path, type = 'images') {
        return window.CDNUtils.getAssetUrl(path, type);
    }

    /**
     * Check if an asset is loaded
     * @param {string} path - Path to the asset
     * @param {string} type - Asset type (css or js)
     * @returns {boolean} True if asset is loaded
     */
    isAssetLoaded(path, type = 'js') {
        const assetId = `${type}:${path}`;
        return this.loadedAssets.has(assetId);
    }

    /**
     * Get loading statistics
     * @returns {Object} Loading statistics
     */
    getStats() {
        return {
            loaded: this.loadedAssets.size,
            loading: this.loadingAssets.size,
            failed: this.failedAssets.size,
            loadedAssets: Array.from(this.loadedAssets),
            failedAssets: Array.from(this.failedAssets)
        };
    }

    /**
     * Clear failed assets to allow retry
     */
    clearFailedAssets() {
        this.failedAssets.clear();
    }

    /**
     * Reset loader state
     */
    reset() {
        this.loadedAssets.clear();
        this.loadingAssets.clear();
        this.failedAssets.clear();
    }
}

// Create global CDN loader instance
window.CDNLoader = new CDNLoader();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CDNLoader;
} 