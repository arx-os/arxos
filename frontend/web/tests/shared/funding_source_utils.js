/**
 * Shared Utilities for Funding Source Feature
 *
 * This module provides reusable utilities for funding_source functionality
 * across all frontend components and tests.
 */

// ============================================================================
// VALIDATION UTILITIES
// ============================================================================

export class FundingSourceValidator {
    static validate(value) {
        const errors = [];

        // Required field validation
        if (!value || value.trim().length === 0) {
            errors.push('Funding source is required');
        }

        // Length validation
        if (value && value.length > 255) {
            errors.push('Funding source cannot exceed 255 characters');
        }

        // Format validation (alphanumeric, spaces, hyphens, parentheses)
        if (value && !/^[a-zA-Z0-9\s\-\(\)]+$/.test(value)) {
            errors.push('Funding source contains invalid characters');
        }

        return {
            valid: errors.length === 0,
            errors,
            value: value ? value.trim() : ''
        };
    }

    static getCommonFundingSources() {
        return [
            'Capital Budget',
            'Operating Budget',
            'Grant Funding',
            'Emergency Funds',
            'Maintenance Budget',
            'Renewal and Replacement',
            'Special Projects',
            'Federal Funding',
            'State Funding',
            'Local Funding'
        ];
    }
}

// ============================================================================
// DATA TRANSFORMATION UTILITIES
// ============================================================================

export class FundingSourceTransformer {
    static transformFormData(formData) {
        return {
            name: formData.name,
            object_type: 'device',
            type: formData.type,
            system: formData.system,
            category: formData.type?.toLowerCase(),
            funding_source: formData.funding_source?.trim(),
            metadata: {
                estimated_value: parseFloat(formData.estimated_value) || 0,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            }
        };
    }

    static transformAPIData(apiData) {
        return {
            id: apiData.object_id || apiData.id,
            name: apiData.name,
            type: apiData.type,
            system: apiData.system,
            funding_source: apiData.funding_source,
            estimated_value: apiData.metadata?.estimated_value || 0,
            created_at: apiData.created_at,
            updated_at: apiData.updated_at
        };
    }

    static transformForExport(data, format = 'csv') {
        switch (format.toLowerCase()) {
            case 'csv':
                return this.transformToCSV(data);
            case 'json':
                return this.transformToJSON(data);
            default:
                throw new Error(`Unsupported export format: ${format}`);
        }
    }

    static transformToCSV(data) {
        const headers = ['ID', 'Name', 'Type', 'System', 'Funding Source', 'Estimated Value', 'Created At'];
        const rows = data.map(item => [
            item.id,
            item.name,
            item.type,
            item.system,
            item.funding_source,
            item.estimated_value,
            item.created_at
        ]);

        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    static transformToJSON(data) {
        return JSON.stringify({
            assets: data,
            export_date: new Date().toISOString(),
            total_count: data.length,
            funding_sources: [...new Set(data.map(item => item.funding_source))]
        }, null, 2);
    }
}

// ============================================================================
// UI UTILITIES
// ============================================================================

export class FundingSourceUI {
    static createFundingSourceField(value = '', required = true) {
        const field = document.createElement('input');
        field.type = 'text';
        field.id = 'funding-source';
        field.name = 'funding_source';
        field.className = 'form-control funding-source-field';
        field.value = value;
        field.placeholder = 'Enter funding source (e.g., Capital Budget)';
        field.maxLength = 255;

        if (required) {
            field.required = true;
        }

        return field;
    }

    static createFundingSourceSelect(value = '', includeEmpty = true) {
        const select = document.createElement('select');
        select.id = 'funding-source-select';
        select.name = 'funding_source';
        select.className = 'form-control funding-source-select';

        if (includeEmpty) {
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = 'Select funding source...';
            select.appendChild(emptyOption);
        }

        const fundingSources = FundingSourceValidator.getCommonFundingSources();
        fundingSources.forEach(source => {
            const option = document.createElement('option');
            option.value = source;
            option.textContent = source;
            if (source === value) {
                option.selected = true;
            }
            select.appendChild(option);
        });

        return select;
    }

    static createFundingSourceDisplay(value, showLabel = true) {
        const container = document.createElement('div');
        container.className = 'funding-source-display';

        if (showLabel) {
            const label = document.createElement('span');
            label.className = 'funding-source-label';
            label.textContent = 'Funding Source: ';
            container.appendChild(label);
        }

        const valueSpan = document.createElement('span');
        valueSpan.className = 'funding-source-value';
        valueSpan.textContent = value || 'Not specified';
        container.appendChild(valueSpan);

        return container;
    }

    static showValidationError(field, message) {
        // Remove existing error
        this.clearValidationError(field);

        // Add error styling
        field.classList.add('is-invalid');

        // Create error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback funding-source-error';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    static clearValidationError(field) {
        field.classList.remove('is-invalid');
        const existingError = field.parentNode.querySelector('.funding-source-error');
        if (existingError) {
            existingError.remove();
        }
    }
}

// ============================================================================
// API UTILITIES
// ============================================================================

export class FundingSourceAPI {
    static async fetchAssets(filters = {}) {
        const params = new URLSearchParams();
        if (filters.funding_source) {
            params.append('funding_source', filters.funding_source);
        }
        if (filters.system) {
            params.append('system', filters.system);
        }

        const response = await fetch(`/api/bim/devices?${params}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch assets: ${response.statusText}`);
        }

        return await response.json();
    }

    static async createAsset(assetData) {
        const response = await fetch('/api/bim/devices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(assetData)
        });

        if (!response.ok) {
            throw new Error(`Failed to create asset: ${response.statusText}`);
        }

        return await response.json();
    }

    static async updateAsset(assetId, assetData) {
        const response = await fetch(`/api/bim/devices/${assetId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(assetData)
        });

        if (!response.ok) {
            throw new Error(`Failed to update asset: ${response.statusText}`);
        }

        return await response.json();
    }

    static async exportAssets(format = 'csv', includeFundingSource = true) {
        const params = new URLSearchParams({
            format,
            include_funding_source: includeFundingSource.toString()
        });

        const response = await fetch(`/api/export/assets?${params}`);
        if (!response.ok) {
            throw new Error(`Failed to export assets: ${response.statusText}`);
        }

        return await response.blob();
    }
}

// ============================================================================
// STORAGE UTILITIES
// ============================================================================

export class FundingSourceStorage {
    static getRecentFundingSources() {
        try {
            const stored = localStorage.getItem('recent_funding_sources');
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.warn('Failed to load recent funding sources:', error);
            return [];
        }
    }

    static addRecentFundingSource(source) {
        if (!source || source.trim().length === 0) return;

        try {
            const recent = this.getRecentFundingSources();
            const trimmedSource = source.trim();

            // Remove if already exists
            const filtered = recent.filter(s => s !== trimmedSource);

            // Add to beginning
            filtered.unshift(trimmedSource);

            // Keep only last 10
            const limited = filtered.slice(0, 10);

            localStorage.setItem('recent_funding_sources', JSON.stringify(limited));
        } catch (error) {
            console.warn('Failed to save recent funding source:', error);
        }
    }

    static getFundingSourcePreferences() {
        try {
            const stored = localStorage.getItem('funding_source_preferences');
            return stored ? JSON.parse(stored) : {};
        } catch (error) {
            console.warn('Failed to load funding source preferences:', error);
            return {};
        }
    }

    static setFundingSourcePreferences(preferences) {
        try {
            localStorage.setItem('funding_source_preferences', JSON.stringify(preferences));
        } catch (error) {
            console.warn('Failed to save funding source preferences:', error);
        }
    }
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

export class FundingSourceEvents {
    static handleFundingSourceChange(event) {
        const field = event.target;
        const value = field.value;

        // Clear any existing errors
        FundingSourceUI.clearValidationError(field);

        // Validate on change
        const validation = FundingSourceValidator.validate(value);
        if (!validation.valid) {
            FundingSourceUI.showValidationError(field, validation.errors[0]);
        }

        // Store in recent sources if valid
        if (validation.valid && value.trim().length > 0) {
            FundingSourceStorage.addRecentFundingSource(value);
        }

        // Trigger custom event
        const customEvent = new CustomEvent('fundingSourceChanged', {
            detail: { value, valid: validation.valid, errors: validation.errors }
        });
        field.dispatchEvent(customEvent);
    }

    static handleFundingSourceSubmit(event) {
        event.preventDefault();

        const form = event.target;
        const fundingSourceField = form.querySelector('[name="funding_source"]');

        if (!fundingSourceField) return;

        const validation = FundingSourceValidator.validate(fundingSourceField.value);
        if (!validation.valid) {
            FundingSourceUI.showValidationError(fundingSourceField, validation.errors[0]);
            return false;
        }

        return true;
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

export class FundingSourceInitializer {
    static initializeForm(formSelector) {
        const form = document.querySelector(formSelector);
        if (!form) return;

        // Add funding source field if it doesn't exist
        if (!form.querySelector('[name="funding_source"]')) {
            const field = FundingSourceUI.createFundingSourceField();
            form.appendChild(field);
        }

        // Add event listeners
        const fundingSourceField = form.querySelector('[name="funding_source"]');
        if (fundingSourceField) {
            fundingSourceField.addEventListener('input', FundingSourceEvents.handleFundingSourceChange);
            fundingSourceField.addEventListener('blur', FundingSourceEvents.handleFundingSourceChange);
        }

        form.addEventListener('submit', FundingSourceEvents.handleFundingSourceSubmit);
    }

    static initializeDisplay(containerSelector) {
        const containers = document.querySelectorAll(containerSelector);
        containers.forEach(container => {
            const fundingSource = container.dataset.fundingSource;
            const display = FundingSourceUI.createFundingSourceDisplay(fundingSource);
            container.appendChild(display);
        });
    }
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
    FundingSourceValidator,
    FundingSourceTransformer,
    FundingSourceUI,
    FundingSourceAPI,
    FundingSourceStorage,
    FundingSourceEvents,
    FundingSourceInitializer
};
