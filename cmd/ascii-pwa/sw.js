/**
 * Service Worker for ArxOS ASCII-BIM PWA
 * Handles caching, offline functionality, and background sync
 */

const CACHE_VERSION = 'v1';
const STATIC_CACHE = `arxos-ascii-static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `arxos-ascii-dynamic-${CACHE_VERSION}`;
const BUILDING_CACHE = `arxos-ascii-buildings-${CACHE_VERSION}`;

// Static assets to cache immediately
const STATIC_ASSETS = [
    '.',
    './index.html',
    './manifest.json',
    './ascii-renderer.js',
    './websocket-client.js',
    './pwa-manager.js',
    './app.js',
    './icons/icon-192x192.png',
    './icons/icon-512x512.png'
];

// Dynamic cache patterns
const CACHE_PATTERNS = {
    building: /\/api\/building\//,
    objects: /\/api\/objects\//,
    floors: /\/api\/floors\//
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[SW] Static assets cached successfully');
                return self.skipWaiting(); // Activate immediately
            })
            .catch((error) => {
                console.error('[SW] Failed to cache static assets:', error);
            })
    );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old cache versions
                    if (cacheName.includes('arxos-ascii') && !cacheName.includes(CACHE_VERSION)) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Service worker activated');
            return self.clients.claim(); // Take control immediately
        })
    );
});

// Fetch event - handle requests with cache strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension and other non-http(s) schemes
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // Handle different types of requests
    if (isStaticAsset(url)) {
        // Static assets: Cache First strategy
        event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
    } else if (isBuildingData(url)) {
        // Building data: Network First with long-term cache
        event.respondWith(networkFirstWithLongCache(request, BUILDING_CACHE));
    } else if (isAPIRequest(url)) {
        // API requests: Network First with short-term cache
        event.respondWith(networkFirstStrategy(request, DYNAMIC_CACHE));
    } else if (isNavigationRequest(request)) {
        // Navigation: Network First, fallback to cached index.html
        event.respondWith(navigationStrategy(request));
    } else {
        // Everything else: Network First
        event.respondWith(networkFirstStrategy(request, DYNAMIC_CACHE));
    }
});

// Background sync for building data
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);
    
    if (event.tag === 'building-sync') {
        event.waitUntil(syncBuildingData());
    }
});

// Push notifications (future feature)
self.addEventListener('push', (event) => {
    console.log('[SW] Push message received:', event);
    
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body || 'New update available',
            icon: './icons/icon-192x192.png',
            badge: './icons/icon-96x96.png',
            tag: 'arxos-notification',
            requireInteraction: false,
            actions: [
                {
                    action: 'view',
                    title: 'View',
                    icon: './icons/view-icon.png'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss',
                    icon: './icons/dismiss-icon.png'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title || 'ArxOS ASCII-BIM', options)
        );
    }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/') // Open the PWA
        );
    }
});

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    } else if (event.data.type === 'CLEAR_CACHE') {
        clearAllCaches().then(() => {
            event.ports[0].postMessage({ success: true });
        });
    }
});

// Cache Strategies

async function cacheFirstStrategy(request, cacheName) {
    try {
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            console.log('[SW] Serving from cache:', request.url);
            return cachedResponse;
        }
        
        console.log('[SW] Not in cache, fetching:', request.url);
        const networkResponse = await fetch(request);
        
        if (networkResponse.status === 200) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('[SW] Cache first strategy failed:', error);
        return new Response('Offline', { status: 503 });
    }
}

async function networkFirstStrategy(request, cacheName) {
    try {
        console.log('[SW] Network first for:', request.url);
        const networkResponse = await fetch(request);
        
        if (networkResponse.status === 200) {
            const cache = await caches.open(cacheName);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return new Response('Offline', { 
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

async function networkFirstWithLongCache(request, cacheName) {
    try {
        console.log('[SW] Network first (long cache) for:', request.url);
        const networkResponse = await fetch(request);
        
        if (networkResponse.status === 200) {
            const cache = await caches.open(cacheName);
            // Clone and add cache headers for long-term storage
            const responseToCache = networkResponse.clone();
            cache.put(request, responseToCache);
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, checking long-term cache:', request.url);
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Add offline indicator header
            const headers = new Headers(cachedResponse.headers);
            headers.set('X-Served-From', 'cache');
            
            return new Response(cachedResponse.body, {
                status: cachedResponse.status,
                statusText: cachedResponse.statusText,
                headers: headers
            });
        }
        
        return new Response(JSON.stringify({
            error: 'No cached data available',
            offline: true
        }), { 
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function navigationStrategy(request) {
    try {
        console.log('[SW] Navigation request:', request.url);
        return await fetch(request);
    } catch (error) {
        console.log('[SW] Navigation failed, serving cached index.html');
        const cache = await caches.open(STATIC_CACHE);
        return cache.match('./index.html');
    }
}

// Helper functions

function isStaticAsset(url) {
    const staticExtensions = ['.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.json', '.woff', '.woff2'];
    const pathname = url.pathname.toLowerCase();
    
    return staticExtensions.some(ext => pathname.endsWith(ext)) || 
           pathname === '/' || 
           pathname === '';
}

function isBuildingData(url) {
    return CACHE_PATTERNS.building.test(url.pathname) ||
           CACHE_PATTERNS.objects.test(url.pathname) ||
           CACHE_PATTERNS.floors.test(url.pathname);
}

function isAPIRequest(url) {
    return url.pathname.startsWith('/api/') || 
           url.pathname.startsWith('/ws/');
}

function isNavigationRequest(request) {
    return request.mode === 'navigate' || 
           (request.method === 'GET' && request.headers.get('accept').includes('text/html'));
}

async function syncBuildingData() {
    console.log('[SW] Syncing building data in background...');
    
    try {
        // Get all building caches and sync with server
        const cache = await caches.open(BUILDING_CACHE);
        const requests = await cache.keys();
        
        for (const request of requests) {
            try {
                // Attempt to refresh cached building data
                const response = await fetch(request);
                if (response.status === 200) {
                    await cache.put(request, response.clone());
                }
            } catch (error) {
                console.log('[SW] Failed to sync:', request.url);
            }
        }
        
        console.log('[SW] Background sync completed');
    } catch (error) {
        console.error('[SW] Background sync failed:', error);
        throw error; // This will retry the sync later
    }
}

async function clearAllCaches() {
    const cacheNames = await caches.keys();
    return Promise.all(
        cacheNames.map(cacheName => {
            if (cacheName.includes('arxos-ascii')) {
                return caches.delete(cacheName);
            }
        })
    );
}

// Periodic cache cleanup
setInterval(async () => {
    try {
        const cache = await caches.open(DYNAMIC_CACHE);
        const requests = await cache.keys();
        const now = Date.now();
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours
        
        for (const request of requests) {
            const response = await cache.match(request);
            if (response) {
                const dateHeader = response.headers.get('date');
                if (dateHeader) {
                    const cacheTime = new Date(dateHeader).getTime();
                    if (now - cacheTime > maxAge) {
                        console.log('[SW] Removing stale cache entry:', request.url);
                        cache.delete(request);
                    }
                }
            }
        }
    } catch (error) {
        console.error('[SW] Cache cleanup failed:', error);
    }
}, 60 * 60 * 1000); // Run every hour

console.log('[SW] Service worker script loaded');