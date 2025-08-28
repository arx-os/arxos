/**
 * PWA Manager - Service Worker registration and offline capability management
 * Handles caching, offline mode, and background sync for Layer 4 ASCII PWA
 */

class PWAManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.swRegistration = null;
        this.updateAvailable = false;
        this.deferredPrompt = null;
        
        // Cache storage names
        this.cacheNames = {
            static: 'arxos-ascii-static-v1',
            dynamic: 'arxos-ascii-dynamic-v1',
            buildings: 'arxos-ascii-buildings-v1'
        };
        
        // Offline storage for building data
        this.offlineStorage = {
            buildings: new Map(),
            lastSync: null
        };
        
        this.init();
    }
    
    async init() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            try {
                this.swRegistration = await navigator.serviceWorker.register('./sw.js');
                console.log('Service Worker registered:', this.swRegistration);
                
                // Check for updates
                this.swRegistration.addEventListener('updatefound', () => {
                    this.handleServiceWorkerUpdate();
                });
                
                // Handle controlled change
                navigator.serviceWorker.addEventListener('controllerchange', () => {
                    window.location.reload();
                });
                
            } catch (error) {
                console.warn('Service Worker registration failed:', error);
            }
        }
        
        // Handle install prompt
        window.addEventListener('beforeinstallprompt', (event) => {
            event.preventDefault();
            this.deferredPrompt = event;
            this.showInstallButton();
        });
        
        // Handle app installed
        window.addEventListener('appinstalled', () => {
            console.log('PWA installed successfully');
            this.hideInstallButton();
            this.deferredPrompt = null;
        });
        
        // Handle online/offline events
        window.addEventListener('online', () => {
            this.handleOnline();
        });
        
        window.addEventListener('offline', () => {
            this.handleOffline();
        });
        
        // Initialize background sync
        this.initBackgroundSync();
        
        // Load cached building data
        await this.loadCachedData();
    }
    
    handleServiceWorkerUpdate() {
        const newWorker = this.swRegistration.installing;
        
        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.updateAvailable = true;
                this.showUpdateNotification();
            }
        });
    }
    
    showUpdateNotification() {
        // Create update notification
        const notification = document.createElement('div');
        notification.className = 'update-notification';
        notification.innerHTML = `
            <div class="update-content">
                <span>New version available!</span>
                <button onclick="pwaManager.applyUpdate()">Update</button>
                <button onclick="this.parentElement.parentElement.remove()">Later</button>
            </div>
        `;
        
        // Add styles if not already present
        if (!document.querySelector('#update-notification-style')) {
            const style = document.createElement('style');
            style.id = 'update-notification-style';
            style.textContent = `
                .update-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--bg-secondary);
                    border: 1px solid var(--accent);
                    padding: 15px;
                    z-index: 10000;
                    max-width: 300px;
                }
                .update-content {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex-wrap: wrap;
                }
                .update-content button {
                    background: var(--accent);
                    color: var(--bg-primary);
                    border: none;
                    padding: 5px 10px;
                    cursor: pointer;
                    font-size: 12px;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 30000);
    }
    
    applyUpdate() {
        if (this.swRegistration && this.swRegistration.waiting) {
            this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
        }
        
        // Remove notification
        document.querySelectorAll('.update-notification').forEach(n => n.remove());
    }
    
    showInstallButton() {
        // Create install button if it doesn't exist
        let installBtn = document.getElementById('installBtn');
        if (!installBtn) {
            installBtn = document.createElement('button');
            installBtn.id = 'installBtn';
            installBtn.className = 'btn';
            installBtn.innerHTML = '⬇ Install';
            installBtn.onclick = () => this.promptInstall();
            
            // Add to header controls
            const controls = document.querySelector('.controls');
            if (controls) {
                controls.appendChild(installBtn);
            }
        }
        
        installBtn.style.display = 'block';
    }
    
    hideInstallButton() {
        const installBtn = document.getElementById('installBtn');
        if (installBtn) {
            installBtn.style.display = 'none';
        }
    }
    
    async promptInstall() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            console.log(`User ${outcome} the install prompt`);
            this.deferredPrompt = null;
            this.hideInstallButton();
        }
    }
    
    handleOnline() {
        this.isOnline = true;
        this.hideOfflineBanner();
        console.log('App is online');
        
        // Sync cached data when back online
        this.syncCachedData();
    }
    
    handleOffline() {
        this.isOnline = false;
        this.showOfflineBanner();
        console.log('App is offline');
    }
    
    showOfflineBanner() {
        const banner = document.getElementById('offlineBanner');
        if (banner) {
            banner.classList.add('show');
        }
    }
    
    hideOfflineBanner() {
        const banner = document.getElementById('offlineBanner');
        if (banner) {
            banner.classList.remove('show');
        }
    }
    
    async initBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            try {
                // Register for background sync
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('building-sync');
                console.log('Background sync registered');
            } catch (error) {
                console.warn('Background sync not available:', error);
            }
        }
    }
    
    async cacheBuilding(buildingId, buildingData) {
        try {
            // Store in memory
            this.offlineStorage.buildings.set(buildingId, {
                data: buildingData,
                timestamp: Date.now()
            });
            
            // Store in IndexedDB for persistence
            await this.storeInIndexedDB('buildings', buildingId, {
                data: buildingData,
                timestamp: Date.now()
            });
            
            console.log('Building data cached:', buildingId);
        } catch (error) {
            console.error('Failed to cache building data:', error);
        }
    }
    
    async getCachedBuilding(buildingId) {
        // Try memory first
        if (this.offlineStorage.buildings.has(buildingId)) {
            return this.offlineStorage.buildings.get(buildingId);
        }
        
        // Try IndexedDB
        try {
            const cached = await this.getFromIndexedDB('buildings', buildingId);
            if (cached) {
                // Load into memory
                this.offlineStorage.buildings.set(buildingId, cached);
                return cached;
            }
        } catch (error) {
            console.error('Failed to get cached building data:', error);
        }
        
        return null;
    }
    
    async storeInIndexedDB(storeName, key, data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('ArxOSASCII', 1);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains(storeName)) {
                    db.createObjectStore(storeName);
                }
            };
            
            request.onsuccess = (event) => {
                const db = event.target.result;
                const transaction = db.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(storeName);
                
                store.put(data, key);
                
                transaction.oncomplete = () => {
                    db.close();
                    resolve();
                };
                
                transaction.onerror = () => {
                    db.close();
                    reject(transaction.error);
                };
            };
            
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    
    async getFromIndexedDB(storeName, key) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('ArxOSASCII', 1);
            
            request.onsuccess = (event) => {
                const db = event.target.result;
                
                if (!db.objectStoreNames.contains(storeName)) {
                    db.close();
                    resolve(null);
                    return;
                }
                
                const transaction = db.transaction([storeName], 'readonly');
                const store = transaction.objectStore(storeName);
                const getRequest = store.get(key);
                
                getRequest.onsuccess = () => {
                    db.close();
                    resolve(getRequest.result);
                };
                
                getRequest.onerror = () => {
                    db.close();
                    reject(getRequest.error);
                };
            };
            
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    
    async loadCachedData() {
        try {
            // Load all cached buildings
            const request = indexedDB.open('ArxOSASCII', 1);
            
            request.onsuccess = (event) => {
                const db = event.target.result;
                
                if (db.objectStoreNames.contains('buildings')) {
                    const transaction = db.transaction(['buildings'], 'readonly');
                    const store = transaction.objectStore(storeName);
                    const getAllRequest = store.getAll();
                    
                    getAllRequest.onsuccess = () => {
                        const buildings = getAllRequest.result;
                        console.log('Loaded cached buildings:', buildings.length);
                        
                        // Populate building selector with cached data if offline
                        if (!this.isOnline && buildings.length > 0) {
                            this.populateCachedBuildings(buildings);
                        }
                    };
                }
                
                db.close();
            };
        } catch (error) {
            console.error('Failed to load cached data:', error);
        }
    }
    
    populateCachedBuildings(buildings) {
        const buildingSelect = document.getElementById('buildingSelect');
        if (!buildingSelect) return;
        
        buildingSelect.innerHTML = '<option value="">Cached Buildings (Offline)</option>';
        
        buildings.forEach((building, index) => {
            const option = document.createElement('option');
            option.value = `cached-${index}`;
            option.textContent = `${building.name || 'Unknown'} (Cached)`;
            option.dataset.buildingData = JSON.stringify(building.data);
            buildingSelect.appendChild(option);
        });
    }
    
    async syncCachedData() {
        if (!this.isOnline) return;
        
        try {
            // Send cached data to server for sync
            for (const [buildingId, cached] of this.offlineStorage.buildings) {
                // Check if data needs sync (has local changes)
                if (cached.needsSync) {
                    // Send to server via WebSocket or fetch
                    console.log('Syncing building data:', buildingId);
                    // Implementation would depend on server API
                }
            }
            
            this.offlineStorage.lastSync = Date.now();
        } catch (error) {
            console.error('Failed to sync cached data:', error);
        }
    }
    
    // Utility methods
    isOfflineCapable() {
        return 'serviceWorker' in navigator && 'caches' in window;
    }
    
    async getStorageUsage() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            try {
                const estimate = await navigator.storage.estimate();
                return {
                    used: estimate.usage,
                    available: estimate.quota - estimate.usage,
                    total: estimate.quota
                };
            } catch (error) {
                console.error('Failed to get storage estimate:', error);
                return null;
            }
        }
        return null;
    }
    
    async clearCache() {
        try {
            // Clear service worker caches
            const cacheNames = await caches.keys();
            await Promise.all(
                cacheNames.map(cacheName => caches.delete(cacheName))
            );
            
            // Clear IndexedDB
            await this.clearIndexedDB();
            
            // Clear memory
            this.offlineStorage.buildings.clear();
            
            console.log('Cache cleared successfully');
        } catch (error) {
            console.error('Failed to clear cache:', error);
        }
    }
    
    async clearIndexedDB() {
        return new Promise((resolve, reject) => {
            const deleteRequest = indexedDB.deleteDatabase('ArxOSASCII');
            
            deleteRequest.onsuccess = () => {
                resolve();
            };
            
            deleteRequest.onerror = () => {
                reject(deleteRequest.error);
            };
        });
    }
}

// Initialize PWA Manager
const pwaManager = new PWAManager();

// Export for global access
window.pwaManager = pwaManager;