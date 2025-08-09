/**
 * Categories Module
 * Handles asset category management and organization
 */

export class Categories {
    constructor(options = {}) {
        this.options = {
            enableCategoryHierarchy: options.enableCategoryHierarchy !== false,
            enableCategoryValidation: options.enableCategoryValidation !== false,
            maxCategoryDepth: options.maxCategoryDepth || 5,
            ...options
        };

        // Category state
        this.categories = [];
        this.categoryTree = {};
        this.selectedCategory = null;
        this.categoryFilters = new Map();

        // Category templates
        this.categoryTemplates = {
            'HVAC': {
                subcategories: ['Air Handler', 'Chiller', 'Compressor', 'Fan', 'Thermostat'],
                attributes: ['capacity', 'efficiency_rating', 'manufacturer', 'model']
            },
            'Electrical': {
                subcategories: ['Panel', 'Transformer', 'Switchgear', 'Outlet', 'Lighting'],
                attributes: ['voltage', 'amperage', 'phase', 'manufacturer']
            },
            'Plumbing': {
                subcategories: ['Pump', 'Valve', 'Pipe', 'Fixture', 'Water Heater'],
                attributes: ['flow_rate', 'pressure', 'material', 'manufacturer']
            },
            'Fire Protection': {
                subcategories: ['Sprinkler', 'Alarm', 'Extinguisher', 'Detector', 'Panel'],
                attributes: ['coverage_area', 'response_time', 'manufacturer']
            }
        };

        // Event handlers
        this.eventHandlers = new Map();

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadCategories();
    }

    setupEventListeners() {
        // Listen for category selection changes
        document.addEventListener('categorySelected', (event) => {
            this.handleCategorySelection(event.detail);
        });

        // Listen for category creation/update
        document.addEventListener('categoryCreated', (event) => {
            this.handleCategoryCreated(event.detail);
        });

        document.addEventListener('categoryUpdated', (event) => {
            this.handleCategoryUpdated(event.detail);
        });

        document.addEventListener('categoryDeleted', (event) => {
            this.handleCategoryDeleted(event.detail);
        });
    }

    // Category loading methods
    async loadCategories() {
        try {
            const response = await fetch('/api/categories', {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const categories = await response.json();
            this.categories = categories;
            this.buildCategoryTree();

            this.triggerEvent('categoriesLoaded', {
                categories: this.categories,
                count: this.categories.length
            });

        } catch (error) {
            console.error('Failed to load categories:', error);
            this.triggerEvent('categoriesLoadFailed', { error });
        }
    }

    buildCategoryTree() {
        this.categoryTree = {};

        // Build hierarchy
        this.categories.forEach(category => {
            if (!category.parent_id) {
                this.categoryTree[category.id] = {
                    ...category,
                    children: this.getCategoryChildren(category.id)
                };
            }
        });
    }

    getCategoryChildren(parentId) {
        return this.categories
            .filter(cat => cat.parent_id === parentId)
            .map(cat => ({
                ...cat,
                children: this.getCategoryChildren(cat.id)
            }));
    }

    // Category operations
    async createCategory(categoryData) {
        try {
            // Validate category data
            const validationErrors = this.validateCategory(categoryData);
            if (validationErrors.length > 0) {
                throw new Error(`Category validation failed: ${validationErrors.join(', ')}`);
            }

            const response = await fetch('/api/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(categoryData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const category = await response.json();
            this.categories.push(category);
            this.buildCategoryTree();

            this.triggerEvent('categoryCreated', { category });
            return category;

        } catch (error) {
            console.error('Failed to create category:', error);
            this.triggerEvent('categoryCreateFailed', { categoryData, error });
            throw error;
        }
    }

    async updateCategory(categoryId, categoryData) {
        try {
            // Validate category data
            const validationErrors = this.validateCategory(categoryData);
            if (validationErrors.length > 0) {
                throw new Error(`Category validation failed: ${validationErrors.join(', ')}`);
            }

            const response = await fetch(`/api/categories/${categoryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(categoryData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const category = await response.json();

            // Update category in local array
            const index = this.categories.findIndex(c => c.id === categoryId);
            if (index !== -1) {
                this.categories[index] = category;
            }

            this.buildCategoryTree();

            this.triggerEvent('categoryUpdated', { category });
            return category;

        } catch (error) {
            console.error('Failed to update category:', error);
            this.triggerEvent('categoryUpdateFailed', { categoryId, categoryData, error });
            throw error;
        }
    }

    async deleteCategory(categoryId) {
        try {
            const response = await fetch(`/api/categories/${categoryId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Remove category from local array
            this.categories = this.categories.filter(c => c.id !== categoryId);
            this.buildCategoryTree();

            this.triggerEvent('categoryDeleted', { categoryId });

        } catch (error) {
            console.error('Failed to delete category:', error);
            this.triggerEvent('categoryDeleteFailed', { categoryId, error });
            throw error;
        }
    }

    // Category validation
    validateCategory(categoryData) {
        const errors = [];

        if (!categoryData.name || categoryData.name.trim().length === 0) {
            errors.push('Category name is required');
        }

        if (categoryData.name && categoryData.name.length > 100) {
            errors.push('Category name cannot exceed 100 characters');
        }

        if (categoryData.parent_id) {
            // Check if parent exists
            const parent = this.categories.find(c => c.id === categoryData.parent_id);
            if (!parent) {
                errors.push('Parent category does not exist');
            }

            // Check for circular references
            if (this.options.enableCategoryHierarchy) {
                if (this.wouldCreateCircularReference(categoryData.parent_id, categoryData.id)) {
                    errors.push('Cannot create circular reference in category hierarchy');
                }
            }

            // Check depth limit
            if (this.options.maxCategoryDepth) {
                const depth = this.getCategoryDepth(categoryData.parent_id);
                if (depth >= this.options.maxCategoryDepth) {
                    errors.push(`Category depth cannot exceed ${this.options.maxCategoryDepth} levels`);
                }
            }
        }

        return errors;
    }

    wouldCreateCircularReference(parentId, categoryId) {
        if (!categoryId) return false;

        const parent = this.categories.find(c => c.id === parentId);
        if (!parent) return false;

        if (parent.id === categoryId) return true;

        if (parent.parent_id) {
            return this.wouldCreateCircularReference(parent.parent_id, categoryId);
        }

        return false;
    }

    getCategoryDepth(categoryId) {
        const category = this.categories.find(c => c.id === categoryId);
        if (!category || !category.parent_id) return 0;

        return 1 + this.getCategoryDepth(category.parent_id);
    }

    // Category selection
    selectCategory(categoryId) {
        this.selectedCategory = this.categories.find(c => c.id === categoryId);
        this.triggerEvent('categorySelected', { category: this.selectedCategory });
    }

    getSelectedCategory() {
        return this.selectedCategory;
    }

    clearCategorySelection() {
        this.selectedCategory = null;
        this.triggerEvent('categorySelectionCleared');
    }

    // Category filtering
    setCategoryFilter(categoryId, filterValue) {
        this.categoryFilters.set(categoryId, filterValue);
        this.triggerEvent('categoryFilterChanged', { categoryId, filterValue });
    }

    getCategoryFilter(categoryId) {
        return this.categoryFilters.get(categoryId);
    }

    clearCategoryFilters() {
        this.categoryFilters.clear();
        this.triggerEvent('categoryFiltersCleared');
    }

    // Category tree methods
    getCategoryTree() {
        return { ...this.categoryTree };
    }

    getCategoryPath(categoryId) {
        const path = [];
        let current = this.categories.find(c => c.id === categoryId);

        while (current) {
            path.unshift(current);
            current = this.categories.find(c => c.id === current.parent_id);
        }

        return path;
    }

    getCategoryAncestors(categoryId) {
        return this.getCategoryPath(categoryId).slice(0, -1);
    }

    getCategoryDescendants(categoryId) {
        const descendants = [];
        const children = this.categories.filter(c => c.parent_id === categoryId);

        children.forEach(child => {
            descendants.push(child);
            descendants.push(...this.getCategoryDescendants(child.id));
        });

        return descendants;
    }

    // Category templates
    getCategoryTemplate(categoryName) {
        return this.categoryTemplates[categoryName] || null;
    }

    getAvailableTemplates() {
        return Object.keys(this.categoryTemplates);
    }

    createCategoryFromTemplate(templateName, categoryData) {
        const template = this.getCategoryTemplate(templateName);
        if (!template) {
            throw new Error(`Template '${templateName}' not found`);
        }

        return {
            ...categoryData,
            template: templateName,
            subcategories: template.subcategories,
            attributes: template.attributes
        };
    }

    // Category statistics
    getCategoryStatistics() {
        const stats = {
            totalCategories: this.categories.length,
            rootCategories: this.categories.filter(c => !c.parent_id).length,
            leafCategories: this.categories.filter(c =>
                !this.categories.some(child => child.parent_id === c.id)
            ).length,
            maxDepth: this.getMaxCategoryDepth(),
            averageDepth: this.getAverageCategoryDepth()
        };

        return stats;
    }

    getMaxCategoryDepth() {
        return Math.max(...this.categories.map(c => this.getCategoryDepth(c.id)));
    }

    getAverageCategoryDepth() {
        const depths = this.categories.map(c => this.getCategoryDepth(c.id));
        return depths.reduce((sum, depth) => sum + depth, 0) / depths.length;
    }

    // Category search
    searchCategories(query) {
        if (!query) return this.categories;

        const searchTerm = query.toLowerCase();
        return this.categories.filter(category =>
            category.name.toLowerCase().includes(searchTerm) ||
            (category.description && category.description.toLowerCase().includes(searchTerm))
        );
    }

    // Event handlers
    handleCategorySelection(detail) {
        const { categoryId } = detail;
        this.selectCategory(categoryId);
    }

    handleCategoryCreated(detail) {
        const { category } = detail;
        this.categories.push(category);
        this.buildCategoryTree();
    }

    handleCategoryUpdated(detail) {
        const { category } = detail;
        const index = this.categories.findIndex(c => c.id === category.id);
        if (index !== -1) {
            this.categories[index] = category;
        }
        this.buildCategoryTree();
    }

    handleCategoryDeleted(detail) {
        const { categoryId } = detail;
        this.categories = this.categories.filter(c => c.id !== categoryId);
        this.buildCategoryTree();
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
                    handler({ ...data, categories: this });
                } catch (error) {
                    console.error(`Error in categories event handler for ${event}:`, error);
                }
            });
        }
    }

    // Cleanup
    destroy() {
        this.categories = [];
        this.categoryTree = {};
        this.selectedCategory = null;
        this.categoryFilters.clear();

        if (this.eventHandlers) {
            this.eventHandlers.clear();
        }
    }
}
