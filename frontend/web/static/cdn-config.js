/**
 * Arxos CDN Configuration
 *
 * This file contains the CDN configuration for the Arxos web frontend.
 * It provides environment-based CDN settings, asset management, and
 * fallback mechanisms for optimal performance and reliability.
 */

// Environment detection
const isDevelopment = window.location.hostname === 'localhost' ||
                     window.location.hostname === '127.0.0.1' ||
                     window.location.hostname.includes('dev') ||
                     window.location.hostname.includes('staging');

const isProduction = window.location.hostname.includes('arxos.io') ||
                    window.location.hostname.includes('production') ||
                    window.location.hostname.includes('prod');

// CDN Configuration
const CDN_CONFIG = {
    // Base CDN URL - environment specific
    baseUrl: isDevelopment ? 'http://localhost:3000' : 'https://cdn.arxos.io',

    // Version for cache busting
    version: 'v1.0.0',

    // Environment-specific settings
    environment: isDevelopment ? 'development' : (isProduction ? 'production' : 'staging'),

    // Asset paths
    assets: {
        css: '/css',
        js: '/js',
        images: '/images',
        fonts: '/fonts',
        icons: '/icons',
        documents: '/documents',
        videos: '/videos',
        audio: '/audio'
    },

    // CDN regions for global distribution
    regions: {
        us: 'https://cdn-us.arxos.io',
        eu: 'https://cdn-eu.arxos.io',
        asia: 'https://cdn-asia.arxos.io',
        australia: 'https://cdn-au.arxos.io'
    },

    // Performance settings
    performance: {
        // Enable compression
        compression: true,
        // Enable HTTP/2
        http2: true,
        // Cache duration in seconds
        cacheDuration: 86400, // 24 hours
        // Enable preloading
        preload: true,
        // Enable prefetching
        prefetch: true
    },

    // Security settings
    security: {
        // Enable HTTPS only in production
        httpsOnly: isProduction,
        // Content Security Policy
        csp: true,
        // Subresource Integrity
        sri: isProduction,
        // Cross-Origin Resource Sharing
        cors: true
    },

    // Fallback configuration
    fallback: {
        // Enable fallback to local assets
        enabled: true,
        // Fallback timeout in milliseconds
        timeout: 5000,
        // Retry attempts
        retryAttempts: 3,
        // Retry delay in milliseconds
        retryDelay: 1000
    },

    // Monitoring and analytics
    monitoring: {
        // Enable performance monitoring
        enabled: true,
        // Track load times
        trackLoadTimes: true,
        // Track errors
        trackErrors: true,
        // Analytics endpoint
        analyticsEndpoint: '/api/analytics/cdn'
    }
};

/**
 * CDN Utility Functions
 */

// Get the optimal CDN URL based on user location
function getOptimalCDNUrl() {
    // In a real implementation, this would use geolocation or IP-based routing
    // For now, return the base URL
    return CDN_CONFIG.baseUrl;
}

// Get asset URL with version and optimization
function getAssetUrl(path, type = 'js') {
    const baseUrl = getOptimalCDNUrl();
    const assetPath = CDN_CONFIG.assets[type] || '';
    const version = CDN_CONFIG.version;

    // Add compression suffix for CSS and JS files
    const compressionSuffix = (type === 'css' || type === 'js') && CDN_CONFIG.performance.compression ? '.gz' : '';

    return `${baseUrl}${assetPath}/${path}?v=${version}${compressionSuffix}`;
}

// Load CSS file with fallback
function loadCSS(href, fallbackHref = null) {
    return new Promise((resolve, reject) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;

        let timeout;
        let retryCount = 0;

        const loadHandler = () => {
            clearTimeout(timeout);
            document.head.removeChild(link);
            resolve(href);
        };

        const errorHandler = () => {
            clearTimeout(timeout);
            document.head.removeChild(link);

            // Try fallback if available
            if (fallbackHref && retryCount < CDN_CONFIG.fallback.retryAttempts) {
                retryCount++;
                setTimeout(() => {
                    loadCSS(fallbackHref).then(resolve).catch(reject);
                }, CDN_CONFIG.fallback.retryDelay);
            } else {
                reject(new Error(`Failed to load CSS: ${href}`));
            }
        };

        link.addEventListener('load', loadHandler);
        link.addEventListener('error', errorHandler);

        document.head.appendChild(link);

        // Set timeout for fallback
        timeout = setTimeout(() => {
            errorHandler();
        }, CDN_CONFIG.fallback.timeout);
    });
}

// Load JavaScript file with fallback
function loadJS(src, fallbackSrc = null) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;

        let timeout;
        let retryCount = 0;

        const loadHandler = () => {
            clearTimeout(timeout);
            document.head.removeChild(script);
            resolve(src);
        };

        const errorHandler = () => {
            clearTimeout(timeout);
            document.head.removeChild(script);

            // Try fallback if available
            if (fallbackSrc && retryCount < CDN_CONFIG.fallback.retryAttempts) {
                retryCount++;
                setTimeout(() => {
                    loadJS(fallbackSrc).then(resolve).catch(reject);
                }, CDN_CONFIG.fallback.retryDelay);
            } else {
                reject(new Error(`Failed to load JavaScript: ${src}`));
            }
        };

        script.addEventListener('load', loadHandler);
        script.addEventListener('error', errorHandler);

        document.head.appendChild(script);

        // Set timeout for fallback
        timeout = setTimeout(() => {
            errorHandler();
        }, CDN_CONFIG.fallback.timeout);
    });
}

// Preload critical assets
function preloadAssets(assets) {
    if (!CDN_CONFIG.performance.preload) return;

    assets.forEach(asset => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = asset.url;
        link.as = asset.type;

        if (asset.crossorigin) {
            link.crossOrigin = 'anonymous';
        }

        document.head.appendChild(link);
    });
}

// Prefetch non-critical assets
function prefetchAssets(assets) {
    if (!CDN_CONFIG.performance.prefetch) return;

    assets.forEach(asset => {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = asset.url;

        document.head.appendChild(link);
    });
}

// Track CDN performance
function trackCDNPerformance(url, loadTime, success) {
    if (!CDN_CONFIG.monitoring.enabled) return;

    const data = {
        url: url,
        loadTime: loadTime,
        success: success,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        connection: navigator.connection ? navigator.connection.effectiveType : 'unknown'
    };

    // Send to analytics endpoint
    fetch(CDN_CONFIG.monitoring.analyticsEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).catch(error => {
        console.warn('Failed to track CDN performance:', error);
    });
}

// Initialize CDN configuration
function initCDN() {
    // Set up performance monitoring
    if (CDN_CONFIG.monitoring.enabled) {
        // Monitor page load performance
        window.addEventListener('load', () => {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            trackCDNPerformance(window.location.href, loadTime, true);
        });

        // Monitor resource loading errors
        window.addEventListener('error', (event) => {
            if (event.target && event.target.src) {
                trackCDNPerformance(event.target.src, 0, false);
            }
        });
    }

    // Preload critical assets
    preloadAssets([
        { url: getAssetUrl('main.css', 'css'), type: 'style' },
        { url: getAssetUrl('main.js', 'js'), type: 'script' },
        { url: getAssetUrl('fonts/arxos-font.woff2', 'fonts'), type: 'font', crossorigin: true }
    ]);

    // Prefetch non-critical assets
    prefetchAssets([
        { url: getAssetUrl('icons/sprite.svg', 'icons') },
        { url: getAssetUrl('images/logo.png', 'images') }
    ]);

    console.log('CDN Configuration initialized:', CDN_CONFIG);
}

// Export configuration and utilities
window.CDN_CONFIG = CDN_CONFIG;
window.CDNUtils = {
    getOptimalCDNUrl,
    getAssetUrl,
    loadCSS,
    loadJS,
    preloadAssets,
    prefetchAssets,
    trackCDNPerformance,
    initCDN
};

// Auto-initialize CDN when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCDN);
} else {
    initCDN();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CDN_CONFIG,
        CDNUtils: {
            getOptimalCDNUrl,
            getAssetUrl,
            loadCSS,
            loadJS,
            preloadAssets,
            prefetchAssets,
            trackCDNPerformance,
            initCDN
        }
    };
}
