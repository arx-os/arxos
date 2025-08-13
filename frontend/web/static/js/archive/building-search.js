/**
 * Building Search Module
 * GitHub-style search functionality for building repository discovery
 * Integrates with Arxos backend for real-time building data
 */

class BuildingSearch {
    constructor() {
        this.searchInput = null;
        this.filterTabs = null;
        this.resultsContainer = null;
        this.currentFilter = 'all';
        this.searchCache = new Map();
        this.debounceTimer = null;
        this.isLoading = false;
        
        this.initializeSearch();
        this.setupEventListeners();
        this.loadInitialResults();
    }

    /**
     * Initialize search components
     */
    initializeSearch() {
        this.searchInput = document.getElementById('building-search');
        this.filterTabs = document.querySelectorAll('.filter-tab');
        this.resultsContainer = document.querySelector('.grid.grid-cols-1.gap-4');
        
        if (!this.searchInput || !this.resultsContainer) {
            console.warn('Building search components not found');
            return;
        }

        // Setup search input with advanced features
        this.setupAdvancedSearch();
        
        console.log('Building search initialized');
    }

    /**
     * Setup advanced search features
     */
    setupAdvancedSearch() {
        // Add search suggestions dropdown
        const searchContainer = this.searchInput.parentElement;
        const suggestionsDropdown = document.createElement('div');
        suggestionsDropdown.className = 'absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-b-md shadow-lg z-10 hidden';
        suggestionsDropdown.id = 'search-suggestions';
        searchContainer.appendChild(suggestionsDropdown);

        // Add search stats
        const searchStats = document.createElement('div');
        searchStats.className = 'text-sm text-gray-500 mt-2';
        searchStats.id = 'search-stats';
        searchContainer.insertAdjacentElement('afterend', searchStats);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Search input with debouncing
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });

            this.searchInput.addEventListener('focus', () => {
                this.showSearchSuggestions();
            });

            this.searchInput.addEventListener('blur', () => {
                // Delay hiding to allow clicking suggestions
                setTimeout(() => this.hideSearchSuggestions(), 150);
            });

            // Handle enter key
            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.executeSearch(e.target.value);
                }
            });
        }

        // Filter tabs
        this.filterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.handleFilterChange(e.target);
            });
        });

        // Type and location filters
        const typeFilter = document.querySelector('select[placeholder="Building Type"]');
        const locationFilter = document.querySelector('select[placeholder="Location"]');
        
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this.handleFilterChange(null, 'type', e.target.value);
            });
        }

        if (locationFilter) {
            locationFilter.addEventListener('change', (e) => {
                this.handleFilterChange(null, 'location', e.target.value);
            });
        }

        // Repository card interactions
        this.setupCardInteractions();
    }

    /**
     * Handle search input with debouncing
     */
    handleSearchInput(query) {
        clearTimeout(this.debounceTimer);
        
        if (query.length < 2) {
            this.hideSearchSuggestions();
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.showSearchSuggestions(query);
            if (query.length >= 3) {
                this.executeSearch(query);
            }
        }, 300);
    }

    /**
     * Show search suggestions
     */
    async showSearchSuggestions(query = '') {
        const dropdown = document.getElementById('search-suggestions');
        if (!dropdown) return;

        if (query.length < 2) {
            // Show popular searches
            dropdown.innerHTML = this.generatePopularSearches();
        } else {
            // Show query-based suggestions
            dropdown.innerHTML = await this.generateQuerySuggestions(query);
        }

        dropdown.classList.remove('hidden');
    }

    /**
     * Hide search suggestions
     */
    hideSearchSuggestions() {
        const dropdown = document.getElementById('search-suggestions');
        if (dropdown) {
            dropdown.classList.add('hidden');
        }
    }

    /**
     * Generate popular searches HTML
     */
    generatePopularSearches() {
        const popularSearches = [
            { text: 'LEED certified office buildings', count: '247 results' },
            { text: 'San Francisco commercial', count: '156 results' },
            { text: 'Hospital as-built drawings', count: '89 results' },
            { text: 'High-rise residential', count: '312 results' },
            { text: 'Data center infrastructure', count: '67 results' }
        ];

        let html = '<div class="p-3"><div class="text-xs font-medium text-gray-500 mb-2">Popular searches</div>';
        
        popularSearches.forEach(search => {
            html += `
                <div class="flex items-center justify-between p-2 hover:bg-gray-50 cursor-pointer rounded" 
                     onclick="buildingSearch.selectSuggestion('${search.text}')">
                    <span class="text-sm text-gray-700">${search.text}</span>
                    <span class="text-xs text-gray-400">${search.count}</span>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    /**
     * Generate query-based suggestions
     */
    async generateQuerySuggestions(query) {
        try {
            // In production, this would call the API
            const suggestions = await this.getSuggestions(query);
            
            let html = '<div class="p-3">';
            
            suggestions.forEach(suggestion => {
                html += `
                    <div class="flex items-center p-2 hover:bg-gray-50 cursor-pointer rounded"
                         onclick="buildingSearch.selectSuggestion('${suggestion.text}')">
                        <svg class="w-4 h-4 text-gray-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                        <span class="text-sm text-gray-700">${suggestion.text}</span>
                        ${suggestion.count ? `<span class="ml-auto text-xs text-gray-400">${suggestion.count}</span>` : ''}
                    </div>
                `;
            });
            
            html += '</div>';
            return html;
        } catch (error) {
            console.error('Error generating suggestions:', error);
            return '<div class="p-3 text-sm text-gray-500">No suggestions available</div>';
        }
    }

    /**
     * Get search suggestions from API or cache
     */
    async getSuggestions(query) {
        // Check cache first
        if (this.searchCache.has(query)) {
            return this.searchCache.get(query);
        }

        try {
            // In production, call actual API
            const suggestions = [
                { text: `${query} office buildings`, count: '23 results' },
                { text: `${query} commercial space`, count: '15 results' },
                { text: `${query} as-built drawings`, count: '8 results' }
            ];

            this.searchCache.set(query, suggestions);
            return suggestions;
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            return [];
        }
    }

    /**
     * Select a search suggestion
     */
    selectSuggestion(text) {
        if (this.searchInput) {
            this.searchInput.value = text;
            this.executeSearch(text);
        }
        this.hideSearchSuggestions();
    }

    /**
     * Execute search with query
     */
    async executeSearch(query) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showSearchStats(`Searching for "${query}"...`);
        
        try {
            const results = await this.performSearch(query);
            this.displaySearchResults(results, query);
            this.updateSearchStats(results.length, query);
        } catch (error) {
            console.error('Search error:', error);
            this.showSearchError('Search failed. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Perform the actual search
     */
    async performSearch(query) {
        // In production, this would call the actual API
        await this.delay(500); // Simulate API call

        // Mock search results based on query
        const mockResults = this.generateMockResults(query);
        
        // Simulate filtering logic
        return mockResults.filter(result => 
            result.name.toLowerCase().includes(query.toLowerCase()) ||
            result.description.toLowerCase().includes(query.toLowerCase()) ||
            result.location.toLowerCase().includes(query.toLowerCase()) ||
            result.type.toLowerCase().includes(query.toLowerCase())
        );
    }

    /**
     * Generate mock search results
     */
    generateMockResults(query) {
        const mockBuildings = [
            {
                id: 1,
                name: 'google-headquarters-mountain-view',
                displayName: 'Google Headquarters Mountain View',
                description: 'Googleplex campus with innovative office spaces and sustainable design features.',
                location: 'Mountain View, CA',
                type: 'Commercial Office',
                stars: 1567,
                forks: 234,
                updated: '3 hours ago',
                language: 'Revit',
                languagePercent: 92.3,
                tags: ['Commercial', 'LEED Gold', 'Campus', 'Tech'],
                isVerified: true,
                isFeatured: false
            },
            {
                id: 2,
                name: 'tesla-gigafactory-nevada',
                displayName: 'Tesla Gigafactory Nevada',
                description: 'Massive battery manufacturing facility with advanced automation systems.',
                location: 'Nevada, USA',
                type: 'Industrial Manufacturing',
                stars: 2341,
                forks: 445,
                updated: '1 day ago',
                language: 'AutoCAD',
                languagePercent: 87.6,
                tags: ['Industrial', 'Manufacturing', 'Sustainable', 'Automated'],
                isVerified: true,
                isFeatured: false
            },
            {
                id: 3,
                name: 'mayo-clinic-rochester',
                displayName: 'Mayo Clinic Rochester',
                description: 'Comprehensive medical facility with state-of-the-art surgical suites and patient care areas.',
                location: 'Rochester, MN',
                type: 'Healthcare',
                stars: 892,
                forks: 156,
                updated: '2 days ago',
                language: 'Revit',
                languagePercent: 94.1,
                tags: ['Healthcare', 'Medical', 'LEED Platinum', 'Research'],
                isVerified: false,
                isFeatured: false
            },
            {
                id: 4,
                name: 'amazon-spheres-seattle',
                displayName: 'Amazon Spheres Seattle',
                description: 'Unique biosphere office buildings with integrated plant life and innovative workspace design.',
                location: 'Seattle, WA',
                type: 'Commercial Office',
                stars: 3245,
                forks: 567,
                updated: '5 hours ago',
                language: 'Revit',
                languagePercent: 89.4,
                tags: ['Commercial', 'Innovative', 'Biophilic', 'Unique'],
                isVerified: true,
                isFeatured: query.toLowerCase().includes('seattle') || query.toLowerCase().includes('amazon')
            }
        ];

        return mockBuildings;
    }

    /**
     * Display search results
     */
    displaySearchResults(results, query) {
        if (!this.resultsContainer) return;

        // Clear existing results (except featured)
        const featuredCard = this.resultsContainer.querySelector('.border-l-4.border-l-yellow-400');
        this.resultsContainer.innerHTML = '';
        
        // Re-add featured card if it matches search
        if (featuredCard && this.shouldShowFeatured(query)) {
            this.resultsContainer.appendChild(featuredCard);
        }

        // Add search results
        results.forEach(building => {
            const card = this.createBuildingCard(building);
            this.resultsContainer.appendChild(card);
        });

        // Add load more button
        this.addLoadMoreButton();
    }

    /**
     * Create building card HTML
     */
    createBuildingCard(building) {
        const card = document.createElement('div');
        card.className = 'repository-card p-4';
        
        const tagsHtml = building.tags.map(tag => 
            `<span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">${tag}</span>`
        ).join('');

        const verifiedBadge = building.isVerified ? 
            '<span class="ml-2 bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded">Verified</span>' : '';

        card.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <div class="flex items-center mb-2">
                        <h3 class="text-lg font-medium text-blue-600 hover:underline cursor-pointer"
                            onclick="buildingSearch.viewBuilding('${building.name}')">
                            ${building.name}
                        </h3>
                        <span class="ml-2 text-sm text-gray-500">Public</span>
                        ${verifiedBadge}
                    </div>
                    
                    <p class="text-gray-600 text-sm mb-3">
                        ${building.description}
                    </p>
                    
                    <div class="flex flex-wrap gap-2 mb-3">
                        ${tagsHtml}
                    </div>
                    
                    <div class="flex items-center text-sm text-gray-500 space-x-4">
                        <span class="flex items-center">
                            <div class="building-type-dot bg-blue-500"></div>
                            ${building.language}
                        </span>
                        <span class="flex items-center">
                            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                            </svg>
                            ${building.stars.toLocaleString()}
                        </span>
                        <span>Updated ${building.updated}</span>
                    </div>
                </div>
                
                <div>
                    <button class="text-gray-400 hover:text-yellow-500 px-2 py-1 text-sm"
                            onclick="buildingSearch.toggleStar('${building.name}')">
                        <svg class="w-4 h-4 fill-current" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        return card;
    }

    /**
     * Check if featured card should show for query
     */
    shouldShowFeatured(query) {
        const featuredTerms = ['salesforce', 'tower', 'san francisco', 'featured', 'leed'];
        return featuredTerms.some(term => 
            query.toLowerCase().includes(term.toLowerCase())
        );
    }

    /**
     * Add load more button
     */
    addLoadMoreButton() {
        const loadMoreContainer = document.createElement('div');
        loadMoreContainer.className = 'text-center mt-8';
        loadMoreContainer.innerHTML = `
            <button class="bg-gray-100 hover:bg-gray-200 border border-gray-300 px-6 py-3 rounded-md text-sm font-medium"
                    onclick="buildingSearch.loadMore()">
                Load more buildings...
            </button>
        `;
        
        this.resultsContainer.appendChild(loadMoreContainer);
    }

    /**
     * Handle filter tab changes
     */
    handleFilterChange(tab, filterType = 'tab', value = null) {
        if (tab) {
            // Remove active class from all tabs
            this.filterTabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            tab.classList.add('active');
            
            this.currentFilter = tab.textContent.trim().toLowerCase();
        }

        // Apply filter and refresh results
        this.applyFilters();
    }

    /**
     * Apply current filters
     */
    applyFilters() {
        const currentQuery = this.searchInput?.value || '';
        if (currentQuery) {
            this.executeSearch(currentQuery);
        } else {
            this.loadInitialResults();
        }
    }

    /**
     * Load initial results
     */
    async loadInitialResults() {
        try {
            const results = await this.performSearch(''); // Get all results
            this.displaySearchResults(results.slice(0, 10), ''); // Show first 10
            this.updateSearchStats(results.length, 'all buildings');
        } catch (error) {
            console.error('Error loading initial results:', error);
        }
    }

    /**
     * Update search statistics
     */
    updateSearchStats(count, query) {
        this.showSearchStats(`Found ${count.toLocaleString()} results for "${query}"`);
    }

    /**
     * Show search stats
     */
    showSearchStats(message) {
        const statsElement = document.getElementById('search-stats');
        if (statsElement) {
            statsElement.textContent = message;
        }
    }

    /**
     * Show search error
     */
    showSearchError(message) {
        this.showSearchStats(`Error: ${message}`);
    }

    /**
     * Setup repository card interactions
     */
    setupCardInteractions() {
        // These will be called by onclick handlers in the generated HTML
        window.buildingSearch = this;
    }

    /**
     * View building details
     */
    viewBuilding(buildingName) {
        console.log('Viewing building:', buildingName);
        // In production, navigate to building detail page
        window.location.href = `building.html?name=${encodeURIComponent(buildingName)}`;
    }

    /**
     * Toggle star on building
     */
    async toggleStar(buildingName) {
        console.log('Toggling star for:', buildingName);
        // In production, call API to star/unstar building
        try {
            // Simulate API call
            await this.delay(200);
            
            // Update UI feedback
            const button = event.target.closest('button');
            const svg = button.querySelector('svg');
            
            if (svg.classList.contains('text-yellow-500')) {
                svg.classList.remove('text-yellow-500');
                svg.classList.add('text-gray-400');
            } else {
                svg.classList.remove('text-gray-400');
                svg.classList.add('text-yellow-500');
            }
        } catch (error) {
            console.error('Error toggling star:', error);
        }
    }

    /**
     * Load more results
     */
    async loadMore() {
        console.log('Loading more results...');
        // In production, load next page of results
        const currentQuery = this.searchInput?.value || '';
        const additionalResults = await this.performSearch(currentQuery);
        
        // Simulate loading more results
        additionalResults.slice(4, 8).forEach(building => {
            const card = this.createBuildingCard(building);
            this.resultsContainer.insertBefore(card, this.resultsContainer.lastElementChild);
        });
    }

    /**
     * Utility: Delay function
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize building search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.buildingSearch = new BuildingSearch();
    console.log('Building search system initialized');
});