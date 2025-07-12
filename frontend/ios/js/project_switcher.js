/**
 * Project Switcher for Mobile BIM Viewer
 * Handles building selection, session management, and context switching
 */

class ProjectSwitcher {
    constructor() {
        this.currentProject = null;
        this.userSession = null;
        this.projects = [];
        this.recentProjects = [];
        this.favorites = [];
        this.offlineProjects = [];
        
        this.init();
    }
    
    async init() {
        // Load user session
        await this.loadUserSession();
        
        // Load projects
        await this.loadProjects();
        
        // Load recent projects
        this.loadRecentProjects();
        
        // Load favorites
        this.loadFavorites();
        
        // Setup offline sync
        this.setupOfflineSync();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    async loadUserSession() {
        const token = localStorage.getItem('arx_jwt');
        if (!token) {
            throw new Error('No authentication token found');
        }
        
        try {
            const response = await fetch('/api/user/session', {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            
            if (response.ok) {
                this.userSession = await response.json();
                this.updateSessionDisplay();
            } else {
                throw new Error('Failed to load user session');
            }
        } catch (error) {
            console.error('Error loading user session:', error);
            throw error;
        }
    }
    
    async loadProjects() {
        const token = localStorage.getItem('arx_jwt');
        if (!token) return;
        
        try {
            const response = await fetch('/api/user/projects', {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            
            if (response.ok) {
                this.projects = await response.json();
                this.updateProjectsDisplay();
            } else {
                throw new Error('Failed to load projects');
            }
        } catch (error) {
            console.error('Error loading projects:', error);
            // Try to load from cache
            this.loadProjectsFromCache();
        }
    }
    
    loadProjectsFromCache() {
        const cached = localStorage.getItem('arx_projects_cache');
        if (cached) {
            try {
                this.projects = JSON.parse(cached);
                this.updateProjectsDisplay();
            } catch (error) {
                console.error('Error loading cached projects:', error);
            }
        }
    }
    
    loadRecentProjects() {
        const recent = localStorage.getItem('arx_recent_projects');
        if (recent) {
            try {
                this.recentProjects = JSON.parse(recent);
            } catch (error) {
                console.error('Error loading recent projects:', error);
            }
        }
    }
    
    loadFavorites() {
        const favorites = localStorage.getItem('arx_favorite_projects');
        if (favorites) {
            try {
                this.favorites = JSON.parse(favorites);
            } catch (error) {
                console.error('Error loading favorites:', error);
            }
        }
    }
    
    updateSessionDisplay() {
        if (!this.userSession) return;
        
        // Update session info in UI
        const sessionInfo = document.querySelector('[data-session-info]');
        if (sessionInfo) {
            sessionInfo.innerHTML = `
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <i class="fas fa-user text-blue-600"></i>
                    </div>
                    <div>
                        <p class="font-medium text-gray-800">${this.userSession.name}</p>
                        <p class="text-sm text-gray-600">${this.userSession.email}</p>
                    </div>
                </div>
            `;
        }
    }
    
    updateProjectsDisplay() {
        // Cache projects for offline access
        localStorage.setItem('arx_projects_cache', JSON.stringify(this.projects));
        
        // Update projects list in UI
        const projectsContainer = document.querySelector('[data-projects-list]');
        if (projectsContainer) {
            projectsContainer.innerHTML = this.projects.map(project => `
                <div class="project-card" data-project-id="${project.id}">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                                <i class="fas fa-building text-blue-600"></i>
                            </div>
                            <div>
                                <h3 class="font-medium text-gray-800">${project.name}</h3>
                                <p class="text-sm text-gray-600">${project.address}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-xs text-gray-500">${project.type}</p>
                            <p class="text-xs text-gray-500">${project.floors} floors</p>
                        </div>
                    </div>
                    <div class="mt-3 flex space-x-2">
                        <button class="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded" 
                                onclick="projectSwitcher.openProject('${project.id}')">
                            Open
                        </button>
                        <button class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded" 
                                onclick="projectSwitcher.toggleFavorite('${project.id}')">
                            ${this.favorites.includes(project.id) ? '★' : '☆'}
                        </button>
                    </div>
                </div>
            `).join('');
        }
    }
    
    openProject(projectId) {
        const project = this.projects.find(p => p.id === projectId);
        if (!project) {
            console.error('Project not found:', projectId);
            return;
        }
        
        // Add to recent projects
        this.addToRecent(project);
        
        // Store current project context
        this.currentProject = project;
        localStorage.setItem('arx_current_project', JSON.stringify(project));
        
        // Navigate to BIM viewer
        const url = `bim_viewer.html?building=${project.id}&name=${encodeURIComponent(project.name)}`;
        window.location.href = url;
    }
    
    addToRecent(project) {
        // Remove if already exists
        this.recentProjects = this.recentProjects.filter(p => p.id !== project.id);
        
        // Add to beginning
        this.recentProjects.unshift({
            id: project.id,
            name: project.name,
            timestamp: Date.now()
        });
        
        // Keep only last 10
        this.recentProjects = this.recentProjects.slice(0, 10);
        
        // Save to localStorage
        localStorage.setItem('arx_recent_projects', JSON.stringify(this.recentProjects));
    }
    
    toggleFavorite(projectId) {
        const index = this.favorites.indexOf(projectId);
        if (index > -1) {
            this.favorites.splice(index, 1);
        } else {
            this.favorites.push(projectId);
        }
        
        localStorage.setItem('arx_favorite_projects', JSON.stringify(this.favorites));
        this.updateProjectsDisplay();
    }
    
    getCurrentProject() {
        if (this.currentProject) {
            return this.currentProject;
        }
        
        // Try to load from localStorage
        const stored = localStorage.getItem('arx_current_project');
        if (stored) {
            try {
                this.currentProject = JSON.parse(stored);
                return this.currentProject;
            } catch (error) {
                console.error('Error loading current project:', error);
            }
        }
        
        return null;
    }
    
    async switchProject(projectId) {
        try {
            // Validate project access
            const hasAccess = await this.validateProjectAccess(projectId);
            if (!hasAccess) {
                throw new Error('Access denied to this project');
            }
            
            // Switch to project
            this.openProject(projectId);
            
        } catch (error) {
            console.error('Error switching project:', error);
            this.showError('Failed to switch project: ' + error.message);
        }
    }
    
    async validateProjectAccess(projectId) {
        const token = localStorage.getItem('arx_jwt');
        if (!token) return false;
        
        try {
            const response = await fetch(`/api/user/projects/${projectId}/access`, {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            });
            
            return response.ok;
        } catch (error) {
            console.error('Error validating project access:', error);
            return false;
        }
    }
    
    setupOfflineSync() {
        // Setup service worker for offline functionality
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('SW registered for offline sync:', registration);
                })
                .catch(error => {
                    console.log('SW registration failed:', error);
                });
        }
        
        // Setup periodic sync for offline data
        if ('periodicSync' in navigator.serviceWorker) {
            navigator.serviceWorker.ready.then(registration => {
                registration.periodicSync.register('bim-data-sync', {
                    minInterval: 24 * 60 * 60 * 1000 // 24 hours
                });
            });
        }
    }
    
    setupEventListeners() {
        // Handle online/offline status
        window.addEventListener('online', () => {
            this.handleOnline();
        });
        
        window.addEventListener('offline', () => {
            this.handleOffline();
        });
        
        // Handle app visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.handleAppVisible();
            }
        });
        
        // Handle beforeunload for session cleanup
        window.addEventListener('beforeunload', () => {
            this.cleanupSession();
        });
    }
    
    handleOnline() {
        console.log('App is online');
        this.showSuccess('Connection restored');
        
        // Sync offline changes
        this.syncOfflineChanges();
        
        // Refresh project data
        this.loadProjects();
    }
    
    handleOffline() {
        console.log('App is offline');
        this.showWarning('You are currently offline. Some features may be limited.');
    }
    
    handleAppVisible() {
        // Refresh session when app becomes visible
        this.refreshSession();
    }
    
    async syncOfflineChanges() {
        const offlineChanges = localStorage.getItem('arx_offline_changes');
        if (!offlineChanges) return;
        
        try {
            const changes = JSON.parse(offlineChanges);
            const token = localStorage.getItem('arx_jwt');
            
            for (const change of changes) {
                await fetch(change.url, {
                    method: change.method,
                    headers: {
                        'Authorization': 'Bearer ' + token,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(change.data)
                });
            }
            
            // Clear offline changes
            localStorage.removeItem('arx_offline_changes');
            this.showSuccess('Offline changes synced successfully');
            
        } catch (error) {
            console.error('Error syncing offline changes:', error);
            this.showError('Failed to sync offline changes');
        }
    }
    
    async refreshSession() {
        try {
            await this.loadUserSession();
        } catch (error) {
            console.error('Error refreshing session:', error);
            // Redirect to login if session is invalid
            if (error.message.includes('authentication')) {
                window.location.href = 'login.html';
            }
        }
    }
    
    cleanupSession() {
        // Save current state
        if (this.currentProject) {
            localStorage.setItem('arx_current_project', JSON.stringify(this.currentProject));
        }
        
        // Clear sensitive data
        // Note: Don't clear JWT token as it's needed for session persistence
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showWarning(message) {
        this.showNotification(message, 'warning');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 left-4 right-4 p-4 rounded-lg z-50 transition-all duration-300 ${
            type === 'success' ? 'bg-green-100 border border-green-400 text-green-700' :
            type === 'error' ? 'bg-red-100 border border-red-400 text-red-700' :
            type === 'warning' ? 'bg-yellow-100 border border-yellow-400 text-yellow-700' :
            'bg-blue-100 border border-blue-400 text-blue-700'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <i class="fas fa-${
                        type === 'success' ? 'check-circle' :
                        type === 'error' ? 'exclamation-triangle' :
                        type === 'warning' ? 'exclamation-triangle' :
                        'info-circle'
                    }"></i>
                    <span>${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="text-gray-500">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Utility methods
    getProjectById(projectId) {
        return this.projects.find(p => p.id === projectId);
    }
    
    getRecentProjects() {
        return this.recentProjects;
    }
    
    getFavoriteProjects() {
        return this.projects.filter(p => this.favorites.includes(p.id));
    }
    
    searchProjects(query) {
        const lowerQuery = query.toLowerCase();
        return this.projects.filter(project => 
            project.name.toLowerCase().includes(lowerQuery) ||
            project.address.toLowerCase().includes(lowerQuery) ||
            project.type.toLowerCase().includes(lowerQuery)
        );
    }
}

// Global instance
const projectSwitcher = new ProjectSwitcher();

// Export for use in other modules
window.ProjectSwitcher = ProjectSwitcher;
window.projectSwitcher = projectSwitcher; 