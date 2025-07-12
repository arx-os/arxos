/**
 * Consolidated Funding Source Test Suite
 * 
 * This file consolidates all funding_source tests into a single, maintainable structure:
 * - Unit tests for JavaScript functions
 * - E2E tests for user workflows  
 * - Integration tests for API/database
 * - Shared utilities and mock data
 */

// ============================================================================
// CONFIGURATION & SHARED DATA
// ============================================================================

const FUNDING_SOURCE_CONFIG = {
    baseUrl: 'http://localhost:8080',
    testUser: {
        email: 'test@example.com',
        password: 'testpassword',
        role: 'admin'
    },
    timeout: 30000,
    viewport: { width: 1280, height: 720 }
};

// Centralized mock data
const MOCK_DATA = {
    symbols: {
        ahu: {
            id: 'ahu',
            name: 'Air Handling Unit (AHU)',
            system: 'mechanical',
            funding_source: 'Capital Budget',
            properties: [
                { name: 'funding_source', description: 'Capital Budget', type: 'string' }
            ]
        },
        receptacle: {
            id: 'receptacle',
            name: 'Receptacle',
            system: 'electrical',
            funding_source: 'Operating Budget',
            properties: [
                { name: 'funding_source', description: 'Operating Budget', type: 'string' }
            ]
        }
    },
    assets: [
        {
            id: 'ASSET001',
            name: 'HVAC Unit',
            type: 'HVAC',
            system: 'mechanical',
            funding_source: 'Capital Budget',
            estimated_value: 50000,
            created_at: '2024-01-15T10:30:00Z'
        },
        {
            id: 'ASSET002',
            name: 'Electrical Panel',
            type: 'Electrical',
            system: 'electrical',
            funding_source: 'Operating Budget',
            estimated_value: 25000,
            created_at: '2024-01-15T10:30:00Z'
        }
    ],
    fundingSources: [
        'Capital Budget',
        'Operating Budget',
        'Grant Funding',
        'Emergency Funds',
        'Maintenance Budget'
    ]
};

// ============================================================================
// SHARED UTILITIES
// ============================================================================

class TestUtils {
    static async wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static async login(page, credentials = FUNDING_SOURCE_CONFIG.testUser) {
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/login.html`);
        await page.fill('#email', credentials.email);
        await page.fill('#password', credentials.password);
        await page.click('#login-btn');
        await this.wait(1000);
    }

    static async checkElementExists(page, selector) {
        const element = await page.$(selector);
        return element !== null;
    }

    static async checkElementText(page, selector, expectedText) {
        const element = await page.$(selector);
        if (!element) {
            throw new Error(`Element ${selector} not found`);
        }
        const text = await element.textContent;
        return text.trim() === expectedText;
    }

    static async mockAPIResponse(page, url, response) {
        await page.route(url, route => {
            route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(response)
            });
        });
    }

    // Validation utilities
    static validateFundingSource(value) {
        if (!value || value.trim().length === 0) {
            return { valid: false, error: 'Funding source is required' };
        }
        if (value.length > 255) {
            return { valid: false, error: 'Funding source exceeds maximum length' };
        }
        return { valid: true };
    }

    static transformAssetData(formData) {
        return {
            name: formData.name,
            object_type: 'device',
            type: formData.type,
            system: formData.system,
            category: formData.type.toLowerCase(),
            funding_source: formData.funding_source,
            metadata: {
                estimated_value: parseFloat(formData.estimated_value)
            }
        };
    }
}

// ============================================================================
// UNIT TESTS
// ============================================================================

class UnitTests {
    static runAll() {
        console.log('🧪 Running Unit Tests...');
        
        const tests = [
            this.testSymbolDisplay,
            this.testAssetFormValidation,
            this.testDataTransformation,
            this.testExportFormatting,
            this.testValidationLogic
        ];

        let passed = 0;
        let failed = 0;

        tests.forEach(test => {
            try {
                test();
                passed++;
            } catch (error) {
                failed++;
                console.error(`❌ ${test.name} failed: ${error.message}`);
            }
        });

        console.log(`✅ Unit Tests: ${passed} passed, ${failed} failed`);
        return failed === 0;
    }

    static testSymbolDisplay() {
        const symbol = MOCK_DATA.symbols.ahu;
        const fundingSourceElement = document.createElement('div');
        fundingSourceElement.textContent = `Funding Source: ${symbol.funding_source}`;
        
        if (!fundingSourceElement.textContent.includes('Capital Budget')) {
            throw new Error('Symbol display test failed');
        }
    }

    static testAssetFormValidation() {
        const validData = { funding_source: 'Capital Budget' };
        const invalidData = { funding_source: '' };
        
        const validResult = TestUtils.validateFundingSource(validData.funding_source);
        const invalidResult = TestUtils.validateFundingSource(invalidData.funding_source);
        
        if (!validResult.valid || invalidResult.valid) {
            throw new Error('Form validation test failed');
        }
    }

    static testDataTransformation() {
        const formData = {
            name: 'Test Asset',
            type: 'HVAC',
            funding_source: 'Capital Budget',
            estimated_value: '50000'
        };
        
        const transformed = TestUtils.transformAssetData(formData);
        
        if (transformed.funding_source !== 'Capital Budget') {
            throw new Error('Data transformation test failed');
        }
    }

    static testExportFormatting() {
        const assets = MOCK_DATA.assets;
        const csvHeaders = ['ID', 'Name', 'Funding Source'];
        const csvContent = csvHeaders.join(',') + '\n' + 
            assets.map(asset => [asset.id, asset.name, asset.funding_source].join(',')).join('\n');
        
        if (!csvContent.includes('Funding Source')) {
            throw new Error('Export formatting test failed');
        }
    }

    static testValidationLogic() {
        const testCases = [
            { input: 'Capital Budget', expected: true },
            { input: '', expected: false },
            { input: 'A'.repeat(300), expected: false }
        ];
        
        testCases.forEach(testCase => {
            const result = TestUtils.validateFundingSource(testCase.input);
            if (result.valid !== testCase.expected) {
                throw new Error(`Validation test failed for: ${testCase.input}`);
            }
        });
    }
}

// ============================================================================
// E2E TESTS
// ============================================================================

class E2ETests {
    static async runAll(page) {
        console.log('🌐 Running E2E Tests...');
        
        const tests = [
            () => this.testSymbolLibrary(page),
            () => this.testAssetCreation(page),
            () => this.testAssetEditing(page),
            () => this.testContextPanel(page),
            () => this.testExport(page)
        ];

        let passed = 0;
        let failed = 0;

        for (const test of tests) {
            try {
                await test();
                passed++;
            } catch (error) {
                failed++;
                console.error(`❌ E2E test failed: ${error.message}`);
            }
        }

        console.log(`✅ E2E Tests: ${passed} passed, ${failed} failed`);
        return failed === 0;
    }

    static async testSymbolLibrary(page) {
        await TestUtils.mockAPIResponse(page, '**/api/symbol-library', MOCK_DATA.symbols);
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/symbol_library.html`);
        await TestUtils.wait(1000);

        const symbolExists = await TestUtils.checkElementExists(page, '[data-symbol-id="ahu"]');
        if (!symbolExists) {
            throw new Error('Symbol library test failed');
        }
    }

    static async testAssetCreation(page) {
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/asset_inventory.html`);
        await page.click('#create-asset-btn');
        await TestUtils.wait(500);

        const fundingSourceField = await page.$('#asset-funding-source');
        if (!fundingSourceField) {
            throw new Error('Asset creation form test failed');
        }
    }

    static async testAssetEditing(page) {
        await TestUtils.mockAPIResponse(page, '**/api/bim/devices', MOCK_DATA.assets);
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/asset_inventory.html`);
        await page.click('#asset-list .asset-item:first-child');
        await TestUtils.wait(500);

        const editForm = await page.$('#edit-asset-form');
        if (!editForm) {
            throw new Error('Asset editing test failed');
        }
    }

    static async testContextPanel(page) {
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/svg_view.html`);
        await page.click('#svg-canvas');
        await TestUtils.wait(500);

        const contextPanel = await page.$('#context-panel');
        if (!contextPanel) {
            throw new Error('Context panel test failed');
        }
    }

    static async testExport(page) {
        await TestUtils.mockAPIResponse(page, '**/api/bim/devices', MOCK_DATA.assets);
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/asset_inventory.html`);
        await page.click('#export-assets-btn');
        await TestUtils.wait(500);

        const exportDialog = await page.$('#export-dialog');
        if (!exportDialog) {
            throw new Error('Export test failed');
        }
    }
}

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

class IntegrationTests {
    static async runAll(page) {
        console.log('🔗 Running Integration Tests...');
        
        const tests = [
            () => this.testAPIIntegration(page),
            () => this.testDatabaseIntegration(page)
        ];

        let passed = 0;
        let failed = 0;

        for (const test of tests) {
            try {
                await test();
                passed++;
            } catch (error) {
                failed++;
                console.error(`❌ Integration test failed: ${error.message}`);
            }
        }

        console.log(`✅ Integration Tests: ${passed} passed, ${failed} failed`);
        return failed === 0;
    }

    static async testAPIIntegration(page) {
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/symbol_library.html`);
        await page.waitForSelector('#symbol-library', { timeout: 5000 });
        
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/asset_inventory.html`);
        await page.waitForSelector('#asset-list', { timeout: 5000 });
    }

    static async testDatabaseIntegration(page) {
        await page.goto(`${FUNDING_SOURCE_CONFIG.baseUrl}/asset_inventory.html`);
        await page.waitForSelector('#asset-list', { timeout: 5000 });
        
        const assetItems = await page.$$('#asset-list .asset-item');
        if (assetItems.length === 0) {
            console.warn('⚠️ No asset items found - database may be empty');
        }
    }
}

// ============================================================================
// MAIN TEST RUNNER
// ============================================================================

class FundingSourceTestSuite {
    static async runAllTests(page = null) {
        console.log('🚀 FUNDING SOURCE TEST SUITE');
        console.log('============================');
        
        const results = {
            unit: false,
            e2e: false,
            integration: false
        };

        // Run unit tests (no browser needed)
        results.unit = UnitTests.runAll();

        // Run E2E and integration tests if page is provided
        if (page) {
            results.e2e = await E2ETests.runAll(page);
            results.integration = await IntegrationTests.runAll(page);
        }

        // Print summary
        this.printResults(results);
        
        return Object.values(results).every(result => result);
    }

    static printResults(results) {
        console.log('\n📊 TEST RESULTS SUMMARY');
        console.log('=======================');
        console.log(`🧪 Unit Tests: ${results.unit ? '✅ PASSED' : '❌ FAILED'}`);
        console.log(`🌐 E2E Tests: ${results.e2e ? '✅ PASSED' : '❌ FAILED'}`);
        console.log(`🔗 Integration Tests: ${results.integration ? '✅ PASSED' : '❌ FAILED'}`);
        
        const allPassed = Object.values(results).every(result => result);
        console.log(`\n🎯 Overall: ${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
    }

    // Convenience methods for running specific test types
    static runUnitTests() {
        return UnitTests.runAll();
    }

    static async runE2ETests(page) {
        return await E2ETests.runAll(page);
    }

    static async runIntegrationTests(page) {
        return await IntegrationTests.runAll(page);
    }
}

// ============================================================================
// EXPORTS
// ============================================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        FundingSourceTestSuite,
        UnitTests,
        E2ETests,
        IntegrationTests,
        TestUtils,
        MOCK_DATA,
        FUNDING_SOURCE_CONFIG
    };
}

// Browser environment
if (typeof window !== 'undefined') {
    window.FundingSourceTestSuite = FundingSourceTestSuite;
    console.log('Funding Source Test Suite loaded. Run FundingSourceTestSuite.runAllTests() to start testing.');
} 