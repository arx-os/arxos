/**
 * Search Module
 * Handles asset search, filtering, and advanced search functionality
 */

export class Search {
    constructor(options = {}) {
        this.options = {
            searchDelay: options.searchDelay || 300,
            enableAdvancedSearch: options.enableAdvancedSearch !== false,
            enableSearchHistory: options.enableSearchHistory !== false,
            maxSearchHistory: options.maxSearchHistory || 10,
            ...options
        };
        
        // Search state
        this.searchQuery = '';
        this.searchHistory = [];
        this.searchResults = [];
        this.isSearching = false;
        this.searchTimer = null;
        
        // Advanced search filters
        this.advancedFilters = {
            ageRange: { min: null, max: null },
            efficiencyRange: { min: null, max: null },
            valueRange: { min: null, max: null },
            maintenanceDue: null,
            lastMaintenance: null,
            manufacturer: '',
            model: '',
            serialNumber: '',
            location: {
                floor: '',
                room: '',
                area: ''
            }
        };
        
        // Event handlers
        this.eventHandlers = new Map();
        
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadSearchHistory();
    }

    setupEventListeners() {
        // Listen for search input changes
        document.addEventListener('searchInputChanged', (event) => {
            this.handleSearchInput(event.detail);
        });
        
        // Listen for advanced filter changes
        document.addEventListener('advancedFilterChanged', (event) => {
            this.handleAdvancedFilterChange(event.detail);
        });
        
        // Listen for search form submission
        document.addEventListener('searchSubmitted', (event) => {
            this.handleSearchSubmit(event.detail);
        });
    }

    // Basic search methods
    async search(query, options = {}) {
        if (this.isSearching) return;
        
        this.isSearching = true;
        this.searchQuery = query;
        this.triggerEvent('searchStarted', { query });
        
        try {
            const searchParams = this.buildSearchParams(query, options);
            const response = await fetch('/api/assets/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(searchParams)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const results = await response.json();
            this.searchResults = results;
            
            // Add to search history
            this.addToSearchHistory(query);
            
            this.triggerEvent('searchCompleted', { 
                query, 
                results: this.searchResults,
                count: this.searchResults.length 
            });
            
        } catch (error) {
            console.error('Search failed:', error);
            this.triggerEvent('searchFailed', { query, error });
        } finally {
            this.isSearching = false;
            this.triggerEvent('searchEnded');
        }
    }

    buildSearchParams(query, options = {}) {
        const params = {
            query: query,
            filters: {
                ...this.advancedFilters,
                ...options.filters
            },
            options: {
                includeArchived: options.includeArchived || false,
                includeInactive: options.includeInactive || false,
                sortBy: options.sortBy || 'relevance',
                sortOrder: options.sortOrder || 'desc',
                limit: options.limit || 100
            }
        };
        
        return params;
    }

    // Advanced search methods
    async advancedSearch(filters, options = {}) {
        if (this.isSearching) return;
        
        this.isSearching = true;
        this.advancedFilters = { ...this.advancedFilters, ...filters };
        this.triggerEvent('advancedSearchStarted', { filters });
        
        try {
            const searchParams = {
                filters: this.advancedFilters,
                options: {
                    includeArchived: options.includeArchived || false,
                    includeInactive: options.includeInactive || false,
                    sortBy: options.sortBy || 'id',
                    sortOrder: options.sortOrder || 'asc',
                    limit: options.limit || 1000
                }
            };
            
            const response = await fetch('/api/assets/advanced-search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(searchParams)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const results = await response.json();
            this.searchResults = results;
            
            this.triggerEvent('advancedSearchCompleted', { 
                filters: this.advancedFilters,
                results: this.searchResults,
                count: this.searchResults.length 
            });
            
        } catch (error) {
            console.error('Advanced search failed:', error);
            this.triggerEvent('advancedSearchFailed', { filters, error });
        } finally {
            this.isSearching = false;
            this.triggerEvent('searchEnded');
        }
    }

    // Filter methods
    setFilter(filterName, value) {
        if (filterName.includes('.')) {
            const [parent, child] = filterName.split('.');
            if (!this.advancedFilters[parent]) {
                this.advancedFilters[parent] = {};
            }
            this.advancedFilters[parent][child] = value;
        } else {
            this.advancedFilters[filterName] = value;
        }
        
        this.triggerEvent('filterChanged', { filterName, value });
    }

    getFilter(filterName) {
        if (filterName.includes('.')) {
            const [parent, child] = filterName.split('.');
            return this.advancedFilters[parent]?.[child];
        }
        return this.advancedFilters[filterName];
    }

    clearFilters() {
        this.advancedFilters = {
            ageRange: { min: null, max: null },
            efficiencyRange: { min: null, max: null },
            valueRange: { min: null, max: null },
            maintenanceDue: null,
            lastMaintenance: null,
            manufacturer: '',
            model: '',
            serialNumber: '',
            location: {
                floor: '',
                room: '',
                area: ''
            }
        };
        
        this.triggerEvent('filtersCleared');
    }

    // Search history methods
    addToSearchHistory(query) {
        if (!this.options.enableSearchHistory) return;
        
        // Remove existing entry if it exists
        this.searchHistory = this.searchHistory.filter(q => q !== query);
        
        // Add to beginning
        this.searchHistory.unshift(query);
        
        // Limit history size
        if (this.searchHistory.length > this.options.maxSearchHistory) {
            this.searchHistory = this.searchHistory.slice(0, this.options.maxSearchHistory);
        }
        
        this.saveSearchHistory();
        this.triggerEvent('searchHistoryUpdated', { history: this.searchHistory });
    }

    getSearchHistory() {
        return [...this.searchHistory];
    }

    clearSearchHistory() {
        this.searchHistory = [];
        this.saveSearchHistory();
        this.triggerEvent('searchHistoryCleared');
    }

    loadSearchHistory() {
        if (!this.options.enableSearchHistory) return;
        
        try {
            const history = localStorage.getItem('asset_search_history');
            if (history) {
                this.searchHistory = JSON.parse(history);
            }
        } catch (error) {
            console.error('Failed to load search history:', error);
        }
    }

    saveSearchHistory() {
        if (!this.options.enableSearchHistory) return;
        
        try {
            localStorage.setItem('asset_search_history', JSON.stringify(this.searchHistory));
        } catch (error) {
            console.error('Failed to save search history:', error);
        }
    }

    // Debounced search
    debouncedSearch(query, options = {}) {
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        
        this.searchTimer = setTimeout(() => {
            this.search(query, options);
        }, this.options.searchDelay);
    }

    // Event handlers
    handleSearchInput(detail) {
        const { query } = detail;
        this.debouncedSearch(query);
    }

    handleAdvancedFilterChange(detail) {
        const { filterName, value } = detail;
        this.setFilter(filterName, value);
    }

    handleSearchSubmit(detail) {
        const { query, filters, options } = detail;
        
        if (filters && Object.keys(filters).length > 0) {
            this.advancedSearch(filters, options);
        } else {
            this.search(query, options);
        }
    }

    // Search result methods
    getSearchResults() {
        return [...this.searchResults];
    }

    getSearchResultCount() {
        return this.searchResults.length;
    }

    getSearchQuery() {
        return this.searchQuery;
    }

    isSearching() {
        return this.isSearching;
    }

    // Filter validation
    validateFilters(filters) {
        const errors = [];
        
        // Validate ranges
        if (filters.ageRange) {
            if (filters.ageRange.min !== null && filters.ageRange.max !== null) {
                if (filters.ageRange.min > filters.ageRange.max) {
                    errors.push('Age range minimum cannot be greater than maximum');
                }
            }
        }
        
        if (filters.efficiencyRange) {
            if (filters.efficiencyRange.min !== null && filters.efficiencyRange.max !== null) {
                if (filters.efficiencyRange.min > filters.efficiencyRange.max) {
                    errors.push('Efficiency range minimum cannot be greater than maximum');
                }
            }
        }
        
        if (filters.valueRange) {
            if (filters.valueRange.min !== null && filters.valueRange.max !== null) {
                if (filters.valueRange.min > filters.valueRange.max) {
                    errors.push('Value range minimum cannot be greater than maximum');
                }
            }
        }
        
        // Validate dates
        if (filters.maintenanceDue && filters.lastMaintenance) {
            const dueDate = new Date(filters.maintenanceDue);
            const lastDate = new Date(filters.lastMaintenance);
            
            if (dueDate < lastDate) {
                errors.push('Maintenance due date cannot be before last maintenance date');
            }
        }
        
        return errors;
    }

    // Search suggestions
    async getSearchSuggestions(query) {
        if (!query || query.length < 2) return [];
        
        try {
            const response = await fetch(`/api/assets/suggestions?q=${encodeURIComponent(query)}`, {
                headers: this.getAuthHeaders()
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const suggestions = await response.json();
            return suggestions;
            
        } catch (error) {
            console.error('Failed to get search suggestions:', error);
            return [];
        }
    }

    // Export search results
    async exportSearchResults(format = 'csv', options = {}) {
        try {
            const exportParams = {
                results: this.searchResults,
                format: format,
                options: {
                    includeHeaders: options.includeHeaders !== false,
                    includeMetadata: options.includeMetadata !== false,
                    ...options
                }
            };
            
            const response = await fetch('/api/assets/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(exportParams)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = `asset_search_results_${Date.now()}.${format}`;
            a.click();
            
            URL.revokeObjectURL(url);
            
            this.triggerEvent('searchResultsExported', { 
                format, 
                count: this.searchResults.length 
            });
            
        } catch (error) {
            console.error('Failed to export search results:', error);
            this.triggerEvent('searchResultsExportFailed', { format, error });
            throw error;
        }
    }

    // Utility methods
    getAuthHeaders() {
        const token = localStorage.getItem('arx_jwt');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    // Event system
    addEventListener(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    removeEventListener(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    triggerEvent(event, data = {}) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            handlers.forEach(handler => {
                try {
                    handler({ ...data, search: this });
                } catch (error) {
                    console.error(`Error in search event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.searchResults = [];
        this.searchHistory = [];
        this.advancedFilters = {};
        
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
            this.searchTimer = null;
        }
        
        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
} 