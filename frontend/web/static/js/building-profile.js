/**
 * Building Profile Module
 * GitHub-style building repository profile with tabs, commit history, and file browser
 * Handles building details, commit timeline, and collaborative features
 */

class BuildingProfile {
    constructor() {
        this.currentTab = 'overview';
        this.buildingData = null;
        this.commitHistory = [];
        this.fileTree = [];
        
        this.initializeProfile();
        this.setupEventListeners();
        this.loadBuildingData();
    }

    /**
     * Initialize building profile components
     */
    initializeProfile() {
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabContent = document.getElementById('tab-content');
        
        // Extract building name from URL
        const urlParams = new URLSearchParams(window.location.search);
        this.buildingName = urlParams.get('name') || 'salesforce-tower-sf';
        
        console.log('Building profile initialized for:', this.buildingName);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Tab navigation
        this.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = button.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });

        // Star/fork buttons
        this.setupActionButtons();
        
        // File tree interactions
        this.setupFileTreeInteractions();
    }

    /**
     * Switch between tabs
     */
    switchTab(tabName) {
        // Update tab buttons
        this.tabButtons.forEach(button => {
            button.classList.remove('active');
            if (button.getAttribute('data-tab') === tabName) {
                button.classList.add('active');
            }
        });

        // Update tab content
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => {
            content.classList.add('hidden');
        });

        const activeContent = document.getElementById(`${tabName}-content`);
        if (activeContent) {
            activeContent.classList.remove('hidden');
        }

        this.currentTab = tabName;

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    /**
     * Load data for specific tab
     */
    async loadTabData(tabName) {
        try {
            switch (tabName) {
                case 'files':
                    await this.loadFileTree();
                    break;
                case 'commits':
                    await this.loadCommitHistory();
                    break;
                case 'issues':
                    await this.loadIssues();
                    break;
                case 'analytics':
                    await this.loadAnalytics();
                    break;
                default:
                    // Overview is already loaded
                    break;
            }
        } catch (error) {
            console.error('Error loading tab data:', error);
        }
    }

    /**
     * Load building data
     */
    async loadBuildingData() {
        try {
            // In production, this would call the actual API
            this.buildingData = await this.fetchBuildingData(this.buildingName);
            this.updateBuildingHeader();
            this.updateBuildingStats();
        } catch (error) {
            console.error('Error loading building data:', error);
            this.showErrorMessage('Failed to load building data');
        }
    }

    /**
     * Fetch building data from API
     */
    async fetchBuildingData(buildingName) {
        // Simulate API call
        await this.delay(500);
        
        // Mock building data
        return {
            id: 'salesforce-tower-sf',
            name: 'Salesforce Tower San Francisco',
            displayName: 'Salesforce Tower San Francisco',
            description: 'Complete BIM model of Salesforce Tower San Francisco. 61-story mixed-use skyscraper with LEED Platinum certification.',
            address: '415 Mission Street, San Francisco, CA 94105',
            type: 'Commercial Office',
            yearBuilt: 2018,
            floors: 61,
            totalArea: 1400000, // sq ft
            height: 1070, // feet
            architect: 'Pelli Clarke Pelli Architects',
            contractor: 'Clark Construction Group',
            cost: 1100000000, // $1.1 billion
            leedCertification: 'Platinum',
            
            // Repository stats
            stars: 1247,
            forks: 342,
            commits: 127,
            files: 1847,
            contributors: 45,
            totalSize: 4.8 * 1024 * 1024 * 1024, // 4.8GB
            
            // Recent activity
            lastUpdated: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
            
            // Tags
            tags: ['Commercial', 'LEED Platinum', 'High-Rise', 'Mixed-Use', '61 Floors'],
            
            // File type breakdown
            fileTypes: {
                'Revit': 87.2,
                'AutoCAD': 8.3,
                'PDF': 4.5
            },
            
            isVerified: true,
            isPublic: true
        };
    }

    /**
     * Update building header
     */
    updateBuildingHeader() {
        if (!this.buildingData) return;

        // Update title
        document.title = `${this.buildingData.displayName} | Building Repository`;
        
        // Update header content dynamically if needed
        const headerTitle = document.querySelector('.building-header h1');
        if (headerTitle) {
            headerTitle.textContent = this.buildingData.displayName;
        }
    }

    /**
     * Update building statistics
     */
    updateBuildingStats() {
        if (!this.buildingData) return;

        const stats = [
            { value: this.buildingData.commits, label: 'Commits' },
            { value: this.buildingData.files.toLocaleString(), label: 'Files' },
            { value: this.buildingData.forks, label: 'Forks' },
            { value: this.buildingData.contributors, label: 'Contributors' },
            { value: this.formatFileSize(this.buildingData.totalSize), label: 'Total Size' }
        ];

        const statElements = document.querySelectorAll('.grid.grid-cols-2.md\\:grid-cols-5 > div');
        stats.forEach((stat, index) => {
            if (statElements[index]) {
                const valueElement = statElements[index].querySelector('.text-2xl');
                const labelElement = statElements[index].querySelector('.text-sm');
                
                if (valueElement) valueElement.textContent = stat.value;
                if (labelElement) labelElement.textContent = stat.label;
            }
        });
    }

    /**
     * Load file tree
     */
    async loadFileTree() {
        try {
            this.fileTree = await this.fetchFileTree();
            this.updateFileTreeDisplay();
        } catch (error) {
            console.error('Error loading file tree:', error);
        }
    }

    /**
     * Fetch file tree data
     */
    async fetchFileTree() {
        // Simulate API call
        await this.delay(300);
        
        return [
            {
                name: 'architectural',
                type: 'folder',
                updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
                children: []
            },
            {
                name: 'structural',
                type: 'folder',
                updatedAt: new Date(Date.now() - 24 * 60 * 60 * 1000),
                children: []
            },
            {
                name: 'mep',
                type: 'folder',
                updatedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
                children: []
            },
            {
                name: 'README.md',
                type: 'file',
                size: 15420,
                updatedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
            },
            {
                name: 'LICENSE',
                type: 'file',
                size: 1024,
                updatedAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
            }
        ];
    }

    /**
     * Update file tree display
     */
    updateFileTreeDisplay() {
        const fileTreeContainer = document.querySelector('.file-tree');
        if (!fileTreeContainer || !this.fileTree) return;

        // Clear existing content (except header)
        const existingItems = fileTreeContainer.querySelectorAll('.px-6.py-3');
        existingItems.forEach(item => item.remove());

        // Add file tree items
        this.fileTree.forEach(item => {
            const itemElement = this.createFileTreeItem(item);
            fileTreeContainer.appendChild(itemElement);
        });
    }

    /**
     * Create file tree item element
     */
    createFileTreeItem(item) {
        const itemElement = document.createElement('div');
        itemElement.className = 'px-6 py-3 border-b border-gray-100 hover:bg-gray-50 flex items-center space-x-3 cursor-pointer';
        
        const icon = item.type === 'folder' 
            ? '<svg class="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"></path></svg>'
            : '<svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path></svg>';

        const nameClass = item.type === 'folder' ? 'text-blue-600 hover:underline' : 'text-gray-900';
        const namePrefix = item.type === 'folder' ? '/' : '';
        
        itemElement.innerHTML = `
            ${icon}
            <span class="${nameClass}">${item.name}${namePrefix}</span>
            <span class="text-gray-500 text-sm ml-auto">Updated ${this.formatTimeAgo(item.updatedAt)}</span>
        `;

        // Add click handler
        itemElement.addEventListener('click', () => {
            this.handleFileTreeItemClick(item);
        });

        return itemElement;
    }

    /**
     * Handle file tree item click
     */
    handleFileTreeItemClick(item) {
        if (item.type === 'folder') {
            // Navigate to folder view
            console.log('Navigating to folder:', item.name);
        } else {
            // Open file viewer
            console.log('Opening file:', item.name);
            this.openFileViewer(item);
        }
    }

    /**
     * Load commit history
     */
    async loadCommitHistory() {
        try {
            this.commitHistory = await this.fetchCommitHistory();
            // Commit history is already rendered in HTML, but you could update it here
        } catch (error) {
            console.error('Error loading commit history:', error);
        }
    }

    /**
     * Fetch commit history
     */
    async fetchCommitHistory() {
        // Simulate API call
        await this.delay(300);
        
        return [
            {
                id: 'a3f4b2c',
                title: 'Add MEP drawings for floors 45-50',
                description: 'Includes HVAC, electrical, and plumbing systems for executive floors...',
                author: 'sarah.architect',
                authorAvatar: 'https://ui-avatars.com/api/?name=Sarah+Chen&background=0ea5e9&color=fff',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
                filesChanged: 47,
                changeType: 'added'
            },
            {
                id: 'b7e1d9f',
                title: 'Update foundation details based on field verification',
                description: 'Corrections to concrete foundation plans after site verification...',
                author: 'mike.structural',
                authorAvatar: 'https://ui-avatars.com/api/?name=Mike+Rodriguez&background=8b5cf6&color=fff',
                timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
                filesChanged: 23,
                changeType: 'modified'
            }
        ];
    }

    /**
     * Load issues
     */
    async loadIssues() {
        // Implementation for issues tab
        console.log('Loading issues...');
    }

    /**
     * Load analytics
     */
    async loadAnalytics() {
        // Implementation for analytics tab
        console.log('Loading analytics...');
    }

    /**
     * Setup action buttons (Star, Fork, etc.)
     */
    setupActionButtons() {
        // Star button
        const starButton = document.querySelector('button:has(svg path[d*="9.049"])');
        if (starButton) {
            starButton.addEventListener('click', () => this.toggleStar());
        }

        // Fork button
        const forkButton = document.querySelector('button:has(svg path[stroke-linecap="round"][d*="8.684"])');
        if (forkButton) {
            forkButton.addEventListener('click', () => this.forkRepository());
        }

        // Add As-Built button
        const addButton = document.querySelector('button:has(svg path[d*="M12 4v16m8-8H4"])');
        if (addButton) {
            addButton.addEventListener('click', () => this.addAsBuilt());
        }
    }

    /**
     * Toggle star status
     */
    async toggleStar() {
        try {
            // Simulate API call
            await this.delay(200);
            
            console.log('Toggling star for building:', this.buildingName);
            
            // Update UI
            const starButton = document.querySelector('button:has(svg path[d*="9.049"])');
            const starCount = starButton?.querySelector('.bg-gray-100');
            
            if (starCount) {
                const currentCount = parseInt(starCount.textContent.replace(',', ''));
                const newCount = currentCount + (Math.random() > 0.5 ? 1 : -1);
                starCount.textContent = newCount.toLocaleString();
            }
            
        } catch (error) {
            console.error('Error toggling star:', error);
        }
    }

    /**
     * Fork repository
     */
    async forkRepository() {
        try {
            console.log('Forking building repository:', this.buildingName);
            
            // Simulate fork creation
            await this.delay(1000);
            
            // Show success message
            this.showSuccessMessage('Repository forked successfully!');
            
        } catch (error) {
            console.error('Error forking repository:', error);
            this.showErrorMessage('Failed to fork repository');
        }
    }

    /**
     * Add as-built drawings
     */
    addAsBuilt() {
        // Navigate to commit page
        window.location.href = `commit.html?building=${encodeURIComponent(this.buildingName)}`;
    }

    /**
     * Setup file tree interactions
     */
    setupFileTreeInteractions() {
        // File tree interactions are handled in createFileTreeItem
    }

    /**
     * Open file viewer
     */
    openFileViewer(file) {
        console.log('Opening file viewer for:', file.name);
        // In production, this would open a file viewer modal or navigate to file view
    }

    /**
     * Show success message
     */
    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    /**
     * Show error message
     */
    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    /**
     * Show message notification
     */
    showMessage(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-100 border-green-400 text-green-700' :
                        type === 'error' ? 'bg-red-100 border-red-400 text-red-700' :
                        'bg-blue-100 border-blue-400 text-blue-700';
        
        notification.className = `fixed top-4 right-4 ${bgColor} border px-6 py-4 rounded-lg shadow-lg z-50`;
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="mr-2">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Utility methods
    formatTimeAgo(date) {
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} ${Math.floor(diff / 60) === 1 ? 'minute' : 'minutes'} ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} ${Math.floor(diff / 3600) === 1 ? 'hour' : 'hours'} ago`;
        if (diff < 2592000) return `${Math.floor(diff / 86400)} ${Math.floor(diff / 86400) === 1 ? 'day' : 'days'} ago`;
        return `${Math.floor(diff / 2592000)} ${Math.floor(diff / 2592000) === 1 ? 'month' : 'months'} ago`;
    }

    formatFileSize(bytes) {
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        if (bytes === 0) return '0 Bytes';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize building profile when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.buildingProfile = new BuildingProfile();
    console.log('Building profile system initialized');
});