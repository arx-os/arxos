/**
 * Funding Source Configuration
 *
 * Centralized configuration for funding_source feature across all components
 */

// ============================================================================
// FEATURE CONFIGURATION
// ============================================================================

export const FUNDING_SOURCE_CONFIG = {
    // Database configuration
    database: {
        columnName: 'funding_source',
        columnType: 'VARCHAR(255)',
        nullable: false,
        defaultValue: null,
        indexName: 'idx_funding_source'
    },

    // Validation rules
    validation: {
        required: true,
        maxLength: 255,
        minLength: 1,
        pattern: /^[a-zA-Z0-9\s\-\(\)]+$/,
        allowedCharacters: 'Letters, numbers, spaces, hyphens, and parentheses'
    },

    // UI configuration
    ui: {
        fieldType: 'text', // or 'select'
        placeholder: 'Enter funding source (e.g., Capital Budget)',
        showLabel: true,
        labelText: 'Funding Source',
        helpText: 'Specify the funding source for this asset or symbol',
        required: true,
        autoComplete: true,
        recentSourcesLimit: 10
    },

    // Export configuration
    export: {
        includeInCSV: true,
        includeInJSON: true,
        columnName: 'Funding Source',
        sortOrder: 5 // Position in export columns
    },

    // API configuration
    api: {
        endpoints: {
            assets: '/api/bim/devices',
            symbols: '/api/symbol-library',
            export: '/api/export/assets'
        },
        methods: {
            create: 'POST',
            read: 'GET',
            update: 'PUT',
            delete: 'DELETE'
        }
    },

    // Test configuration
    test: {
        baseUrl: 'http://localhost:8080',
        timeout: 30000,
        headless: false,
        viewport: { width: 1280, height: 720 },
        testUser: {
            email: 'test@example.com',
            password: 'testpassword',
            role: 'admin'
        }
    }
};

// ============================================================================
// FUNDING SOURCE OPTIONS
// ============================================================================

export const FUNDING_SOURCE_OPTIONS = {
    // Standard funding sources
    standard: [
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
    ],

    // Industry-specific funding sources
    industry: {
        healthcare: [
            'Medicare Reimbursement',
            'Medicaid Funding',
            'Private Insurance',
            'Pharmaceutical Grants',
            'Medical Research Grants'
        ],
        education: [
            'Department of Education',
            'State Education Grants',
            'Private Foundation Grants',
            'Alumni Donations',
            'Research Grants'
        ],
        government: [
            'Federal Appropriations',
            'State Budget',
            'Local Tax Revenue',
            'Federal Grants',
            'Emergency Relief'
        ],
        commercial: [
            'Capital Expenditure',
            'Operating Expense',
            'R&D Budget',
            'Maintenance Reserve',
            'Project Budget'
        ]
    },

    // Custom funding sources (user-defined)
    custom: []
};

// ============================================================================
// VALIDATION MESSAGES
// ============================================================================

export const VALIDATION_MESSAGES = {
    required: 'Funding source is required',
    maxLength: 'Funding source cannot exceed 255 characters',
    minLength: 'Funding source must be at least 1 character',
    invalidFormat: 'Funding source contains invalid characters. Only letters, numbers, spaces, hyphens, and parentheses are allowed.',
    duplicate: 'This funding source already exists',
    notFound: 'Funding source not found',
    invalidValue: 'Invalid funding source value'
};

// ============================================================================
// ERROR CODES
// ============================================================================

export const ERROR_CODES = {
    VALIDATION_FAILED: 'FUNDING_SOURCE_VALIDATION_FAILED',
    NOT_FOUND: 'FUNDING_SOURCE_NOT_FOUND',
    DUPLICATE: 'FUNDING_SOURCE_DUPLICATE',
    INVALID_FORMAT: 'FUNDING_SOURCE_INVALID_FORMAT',
    DATABASE_ERROR: 'FUNDING_SOURCE_DATABASE_ERROR',
    API_ERROR: 'FUNDING_SOURCE_API_ERROR'
};

// ============================================================================
// FEATURE FLAGS
// ============================================================================

export const FEATURE_FLAGS = {
    // Enable/disable funding source feature
    enabled: true,

    // Enable advanced features
    advanced: {
        customFundingSources: true,
        fundingSourceHistory: true,
        fundingSourceAnalytics: true,
        bulkUpdate: true,
        importExport: true
    },

    // UI features
    ui: {
        autoComplete: true,
        recentSources: true,
        suggestions: true,
        validation: true,
        helpText: true
    },

    // API features
    api: {
        filtering: true,
        sorting: true,
        pagination: true,
        bulkOperations: true
    }
};

// ============================================================================
// PERFORMANCE SETTINGS
// ============================================================================

export const PERFORMANCE_CONFIG = {
    // Caching
    cache: {
        enabled: true,
        ttl: 300000, // 5 minutes
        maxSize: 1000
    },

    // Debouncing
    debounce: {
        input: 300, // 300ms
        search: 500, // 500ms
        validation: 200 // 200ms
    },

    // Pagination
    pagination: {
        defaultPageSize: 25,
        maxPageSize: 100,
        pageSizeOptions: [10, 25, 50, 100]
    }
};

// ============================================================================
// SECURITY SETTINGS
// ============================================================================

export const SECURITY_CONFIG = {
    // Input sanitization
    sanitization: {
        enabled: true,
        allowedTags: [],
        allowedAttributes: []
    },

    // Rate limiting
    rateLimit: {
        enabled: true,
        maxRequests: 100,
        windowMs: 900000 // 15 minutes
    },

    // Validation
    validation: {
        strict: true,
        sanitizeInput: true,
        logValidationErrors: false
    }
};

// ============================================================================
// LOGGING CONFIGURATION
// ============================================================================

export const LOGGING_CONFIG = {
    // Log levels
    level: process.env.NODE_ENV === 'production' ? 'warn' : 'debug',

    // What to log
    log: {
        validationErrors: true,
        apiCalls: false,
        userActions: true,
        performance: true
    },

    // Log format
    format: {
        includeTimestamp: true,
        includeUserId: true,
        includeRequestId: true
    }
};

// ============================================================================
// ENVIRONMENT-SPECIFIC CONFIGURATION
// ============================================================================

export const getEnvironmentConfig = () => {
    const env = process.env.NODE_ENV || 'development';

    const configs = {
        development: {
            ...FUNDING_SOURCE_CONFIG,
            test: {
                ...FUNDING_SOURCE_CONFIG.test,
                baseUrl: 'http://localhost:8080',
                headless: false
            },
            logging: {
                ...LOGGING_CONFIG,
                level: 'debug'
            }
        },
        test: {
            ...FUNDING_SOURCE_CONFIG,
            test: {
                ...FUNDING_SOURCE_CONFIG.test,
                baseUrl: 'http://localhost:8080',
                headless: true
            },
            logging: {
                ...LOGGING_CONFIG,
                level: 'warn'
            }
        },
        production: {
            ...FUNDING_SOURCE_CONFIG,
            test: {
                ...FUNDING_SOURCE_CONFIG.test,
                baseUrl: 'https://api.arxos.io',
                headless: true
            },
            logging: {
                ...LOGGING_CONFIG,
                level: 'error'
            },
            security: {
                ...SECURITY_CONFIG,
                validation: {
                    ...SECURITY_CONFIG.validation,
                    strict: true
                }
            }
        }
    };

    return configs[env] || configs.development;
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export const ConfigUtils = {
    // Get configuration value with fallback
    get(key, defaultValue = null) {
        const keys = key.split('.');
        let value = FUNDING_SOURCE_CONFIG;

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return defaultValue;
            }
        }

        return value;
    },

    // Check if feature is enabled
    isFeatureEnabled(feature) {
        return FEATURE_FLAGS[feature] === true;
    },

    // Get validation rules
    getValidationRules() {
        return FUNDING_SOURCE_CONFIG.validation;
    },

    // Get funding source options
    getFundingSourceOptions(industry = null) {
        if (industry && FUNDING_SOURCE_OPTIONS.industry[industry]) {
            return [
                ...FUNDING_SOURCE_OPTIONS.standard,
                ...FUNDING_SOURCE_OPTIONS.industry[industry]
            ];
        }
        return FUNDING_SOURCE_OPTIONS.standard;
    },

    // Get error message by code
    getErrorMessage(code) {
        return VALIDATION_MESSAGES[code] || 'An unknown error occurred';
    }
};

// ============================================================================
// EXPORTS
// ============================================================================

export default {
    FUNDING_SOURCE_CONFIG,
    FUNDING_SOURCE_OPTIONS,
    VALIDATION_MESSAGES,
    ERROR_CODES,
    FEATURE_FLAGS,
    PERFORMANCE_CONFIG,
    SECURITY_CONFIG,
    LOGGING_CONFIG,
    getEnvironmentConfig,
    ConfigUtils
};
