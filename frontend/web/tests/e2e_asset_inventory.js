// Asset Inventory E2E Tests with Funding Source Coverage

/**
 * E2E Tests for Asset Inventory with Funding Source Feature
 * 
 * These tests cover the complete asset inventory workflows including:
 * - Asset creation with funding_source
 * - Asset editing with funding_source
 * - Asset listing with funding_source
 * - Asset filtering by funding_source
 * - Asset export with funding_source
 */

// Test configuration
const ASSET_INVENTORY_CONFIG = {
    baseUrl: 'http://localhost:8080',
    testUser: {
        email: 'test@example.com',
        password: 'testpassword',
        role: 'admin'
    },
    timeout: 10000,
    testAssets: [
        {
            name: 'HVAC Unit - Capital Budget',
            type: 'HVAC',
            system: 'mechanical',
            funding_source: 'Capital Budget',
            estimated_value: 50000,
            location: 'Building A - Floor 1'
        },
        {
            name: 'Electrical Panel - Operating Budget',
            type: 'Electrical',
            system: 'electrical',
            funding_source: 'Operating Budget',
            estimated_value: 25000,
            location: 'Building A - Floor 1'
        },
        {
            name: 'Security Camera - Grant Funding',
            type: 'Security',
            system: 'security',
            funding_source: 'Grant Funding',
            estimated_value: 15000,
            location: 'Building A - Floor 1'
        }
    ]
};

// Mock API responses for asset inventory testing
const mockAssetInventoryAPI = {
    assets: [
        {
            object_id: 'ASSET001',
            name: 'HVAC Unit - Capital Budget',
            object_type: 'device',
            type: 'HVAC',
            system: 'mechanical',
            category: 'hvac',
            funding_source: 'Capital Budget',
            estimated_value: 50000,
            location: 'Building A - Floor 1',
            created_at: '2024-01-15T10:30:00Z',
            updated_at: '2024-01-15T10:30:00Z'
        },
        {
            object_id: 'ASSET002',
            name: 'Electrical Panel - Operating Budget',
            object_type: 'device',
            type: 'Electrical',
            system: 'electrical',
            category: 'electrical',
            funding_source: 'Operating Budget',
            estimated_value: 25000,
            location: 'Building A - Floor 1',
            created_at: '2024-01-15T10:30:00Z',
            updated_at: '2024-01-15T10:30:00Z'
        },
        {
            object_id: 'ASSET003',
            name: 'Security Camera - Grant Funding',
            object_type: 'device',
            type: 'Security',
            system: 'security',
            category: 'security',
            funding_source: 'Grant Funding',
            estimated_value: 15000,
            location: 'Building A - Floor 1',
            created_at: '2024-01-15T10:30:00Z',
            updated_at: '2024-01-15T10:30:00Z'
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

// Test utilities for asset inventory
class AssetInventoryTestUtils {
    static async wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static async login(page, credentials = ASSET_INVENTORY_CONFIG.testUser) {
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/login.html`);
        await page.fill('#email', credentials.email);
        await page.fill('#password', credentials.password);
        await page.click('#login-btn');
        await this.wait(1000);
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

    static async checkElementExists(page, selector) {
        const element = await page.$(selector);
        return element !== null;
    }

    static async checkElementText(page, selector, expectedText) {
        const element = await page.$(selector);
        if (!element) {
            throw new Error(`Element ${selector} not found`);
        }
        const text = await element.textContent();
        return text.trim() === expectedText;
    }
}

// Asset Creation Tests
class AssetCreationTests {
    static async testCreateAssetWithFundingSource(page) {
        console.log('Testing Asset Creation with funding_source...');

        // Mock API responses
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/bim/devices', 
            mockAssetInventoryAPI.assets
        );

        // Navigate to asset inventory
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await AssetInventoryTestUtils.wait(1000);

        // Click create new asset button
        await page.click('#create-asset-btn');
        await AssetInventoryTestUtils.wait(500);

        // Check if funding_source field exists
        const fundingSourceField = await page.$('#asset-funding-source');
        if (!fundingSourceField) {
            throw new Error('Funding source field not found in asset creation form');
        }

        // Fill asset creation form
        const testAsset = ASSET_INVENTORY_CONFIG.testAssets[0];
        await page.fill('#asset-name', testAsset.name);
        await page.selectOption('#asset-type', testAsset.type);
        await page.selectOption('#asset-system', testAsset.system);
        await page.fill('#asset-funding-source', testAsset.funding_source);
        await page.fill('#asset-value', testAsset.estimated_value.toString());
        await page.fill('#asset-location', testAsset.location);

        // Check form validation
        const formValid = await page.$eval('#asset-form', form => form.checkValidity());
        if (!formValid) {
            throw new Error('Asset creation form validation failed');
        }

        // Mock successful asset creation
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/bim/devices', 
            { 
                success: true, 
                object_id: 'NEW_ASSET_001',
                ...testAsset
            }
        );

        // Submit form
        await page.click('#submit-asset-btn');
        await AssetInventoryTestUtils.wait(1000);

        // Check success message
        const successMessage = await page.$eval('.alert-success', el => el.textContent);
        if (!successMessage.includes('Asset created successfully')) {
            throw new Error('Asset creation failed');
        }

        console.log('✅ Asset creation with funding_source test passed');
    }

    static async testCreateAssetWithDifferentFundingSources(page) {
        console.log('Testing Asset Creation with different funding sources...');

        // Navigate to asset inventory
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await AssetInventoryTestUtils.wait(1000);

        // Test each funding source type
        for (const testAsset of ASSET_INVENTORY_CONFIG.testAssets) {
            // Click create new asset
            await page.click('#create-asset-btn');
            await AssetInventoryTestUtils.wait(500);

            // Fill form with different funding source
            await page.fill('#asset-name', testAsset.name);
            await page.selectOption('#asset-type', testAsset.type);
            await page.selectOption('#asset-system', testAsset.system);
            await page.fill('#asset-funding-source', testAsset.funding_source);
            await page.fill('#asset-value', testAsset.estimated_value.toString());

            // Verify funding source is set correctly
            const fundingSourceValue = await page.$eval('#asset-funding-source', el => el.value);
            if (fundingSourceValue !== testAsset.funding_source) {
                throw new Error(`Funding source not set correctly: expected ${testAsset.funding_source}, got ${fundingSourceValue}`);
            }

            // Cancel form to test next asset
            await page.click('#cancel-asset-btn');
            await AssetInventoryTestUtils.wait(500);
        }

        console.log('✅ Asset creation with different funding sources test passed');
    }
}

// Asset Editing Tests
class AssetEditingTests {
    static async testEditAssetFundingSource(page) {
        console.log('Testing Asset Editing with funding_source...');

        // Mock API responses
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/bim/devices', 
            mockAssetInventoryAPI.assets
        );

        // Navigate to asset inventory
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await AssetInventoryTestUtils.wait(1000);

        // Click on first asset to edit
        await page.click('#asset-list .asset-item:first-child');
        await AssetInventoryTestUtils.wait(500);

        // Check if edit form opens with funding_source
        const editForm = await page.$('#edit-asset-form');
        if (!editForm) {
            throw new Error('Asset edit form not found');
        }

        // Check if funding_source field has current value
        const fundingSourceValue = await page.$eval('#edit-asset-funding-source', el => el.value);
        if (fundingSourceValue !== 'Capital Budget') {
            throw new Error('Funding source field not populated with current value');
        }

        // Update funding_source
        const newFundingSource = 'Grant Funding';
        await page.fill('#edit-asset-funding-source', newFundingSource);

        // Mock successful asset update
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/bim/devices/ASSET001', 
            { 
                success: true, 
                funding_source: newFundingSource
            }
        );

        // Submit update
        await page.click('#update-asset-btn');
        await AssetInventoryTestUtils.wait(1000);

        // Check success message
        const successMessage = await page.$eval('.alert-success', el => el.textContent);
        if (!successMessage.includes('Asset updated successfully')) {
            throw new Error('Asset update failed');
        }

        console.log('✅ Asset editing with funding_source test passed');
    }
}

// Asset Listing Tests
class AssetListingTests {
    static async testAssetListWithFundingSource(page) {
        console.log('Testing Asset List with funding_source...');

        // Mock API responses
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/bim/devices', 
            mockAssetInventoryAPI.assets
        );

        // Navigate to asset inventory
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await AssetInventoryTestUtils.wait(1000);

        // Check if asset list loads with funding_source
        const assetList = await page.$('#asset-list');
        if (!assetList) {
            throw new Error('Asset list not found');
        }

        // Check if funding_source is displayed in asset items
        const assetItems = await page.$$('#asset-list .asset-item');
        if (assetItems.length === 0) {
            throw new Error('No asset items found');
        }

        // Check first asset has funding_source
        const firstAssetFundingSource = await page.$eval(
            '#asset-list .asset-item:first-child .asset-funding-source',
            el => el.textContent
        );

        if (!firstAssetFundingSource.includes('Capital Budget')) {
            throw new Error('Asset list does not display funding_source correctly');
        }

        console.log('✅ Asset list with funding_source test passed');
    }

    static async testAssetFilteringByFundingSource(page) {
        console.log('Testing Asset Filtering by funding_source...');

        // Mock API responses
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/bim/devices', 
            mockAssetInventoryAPI.assets
        );

        // Navigate to asset inventory
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await AssetInventoryTestUtils.wait(1000);

        // Check if funding source filter exists
        const fundingSourceFilter = await page.$('#funding-source-filter');
        if (!fundingSourceFilter) {
            throw new Error('Funding source filter not found');
        }

        // Test filtering by Capital Budget
        await page.selectOption('#funding-source-filter', 'Capital Budget');
        await AssetInventoryTestUtils.wait(500);

        // Check filtered results
        const filteredAssets = await page.$$('#asset-list .asset-item');
        if (filteredAssets.length !== 1) {
            throw new Error('Funding source filter not working correctly');
        }

        // Test filtering by Operating Budget
        await page.selectOption('#funding-source-filter', 'Operating Budget');
        await AssetInventoryTestUtils.wait(500);

        const operatingBudgetAssets = await page.$$('#asset-list .asset-item');
        if (operatingBudgetAssets.length !== 1) {
            throw new Error('Operating Budget filter not working correctly');
        }

        // Test clearing filter
        await page.selectOption('#funding-source-filter', 'All');
        await AssetInventoryTestUtils.wait(500);

        const allAssets = await page.$$('#asset-list .asset-item');
        if (allAssets.length !== 3) {
            throw new Error('Filter clear not working correctly');
        }

        console.log('✅ Asset filtering by funding_source test passed');
    }
}

// Asset Export Tests
class AssetExportTests {
    static async testExportWithFundingSource(page) {
        console.log('Testing Asset Export with funding_source...');

        // Mock API responses
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/bim/devices', 
            mockAssetInventoryAPI.assets
        );

        // Navigate to asset inventory
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await AssetInventoryTestUtils.wait(1000);

        // Click export button
        await page.click('#export-assets-btn');
        await AssetInventoryTestUtils.wait(500);

        // Check if export dialog opens
        const exportDialog = await page.$('#export-dialog');
        if (!exportDialog) {
            throw new Error('Export dialog not found');
        }

        // Check if funding_source option is available
        const fundingSourceOption = await page.$('#include-funding-source');
        if (!fundingSourceOption) {
            throw new Error('Funding source export option not found');
        }

        // Enable funding_source export
        await page.check('#include-funding-source');

        // Select CSV format
        await page.selectOption('#export-format', 'csv');

        // Mock export API response
        await AssetInventoryTestUtils.mockAPIResponse(
            page, 
            '**/api/export/assets', 
            {
                success: true,
                download_url: '/downloads/assets_export.csv',
                filename: 'assets_export.csv',
                record_count: 3
            }
        );

        // Start export
        await page.click('#start-export-btn');
        await AssetInventoryTestUtils.wait(1000);

        // Check success message
        const successMessage = await page.$eval('.alert-success', el => el.textContent);
        if (!successMessage.includes('Export completed successfully')) {
            throw new Error('Export failed');
        }

        // Check download link
        const downloadLink = await page.$('#download-export-link');
        if (!downloadLink) {
            throw new Error('Download link not found');
        }

        console.log('✅ Asset export with funding_source test passed');
    }
}

// Form Validation Tests
class FormValidationTests {
    static async testFundingSourceValidation(page) {
        console.log('Testing Funding Source Validation...');

        // Navigate to asset creation form
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await page.click('#create-asset-btn');
        await AssetInventoryTestUtils.wait(500);

        // Test required field validation
        await page.fill('#asset-name', 'Test Asset');
        await page.selectOption('#asset-type', 'HVAC');
        
        // Try to submit without funding_source
        await page.click('#submit-asset-btn');
        await AssetInventoryTestUtils.wait(500);

        // Check for validation error
        const validationError = await page.$('.validation-error');
        if (!validationError) {
            throw new Error('Required field validation not working');
        }

        // Test valid funding_source
        await page.fill('#asset-funding-source', 'Capital Budget');
        await page.click('#submit-asset-btn');
        await AssetInventoryTestUtils.wait(500);

        // Check that validation error is gone
        const validationErrorAfter = await page.$('.validation-error');
        if (validationErrorAfter) {
            throw new Error('Validation error still present after valid input');
        }

        console.log('✅ Funding source validation test passed');
    }

    static async testFundingSourceFormatValidation(page) {
        console.log('Testing Funding Source Format Validation...');

        // Navigate to asset creation form
        await page.goto(`${ASSET_INVENTORY_CONFIG.baseUrl}/asset_inventory.html`);
        await page.click('#create-asset-btn');
        await AssetInventoryTestUtils.wait(500);

        // Test invalid funding_source format (too long)
        const longFundingSource = 'A'.repeat(300); // Exceeds VARCHAR(255)
        await page.fill('#asset-funding-source', longFundingSource);
        await page.click('#submit-asset-btn');
        await AssetInventoryTestUtils.wait(500);

        // Check for format validation error
        const formatError = await page.$('.format-error');
        if (!formatError) {
            throw new Error('Format validation not working');
        }

        // Test valid format
        await page.fill('#asset-funding-source', 'Capital Budget');
        await page.click('#submit-asset-btn');
        await AssetInventoryTestUtils.wait(500);

        // Check that format error is gone
        const formatErrorAfter = await page.$('.format-error');
        if (formatErrorAfter) {
            throw new Error('Format error still present after valid input');
        }

        console.log('✅ Funding source format validation test passed');
    }
}

// Test Runner
class AssetInventoryTestRunner {
    static async runAllTests() {
        console.log('🚀 Starting Asset Inventory Funding Source Tests...');
        console.log('==================================================');

        const tests = [
            { name: 'Asset Creation', test: AssetCreationTests.testCreateAssetWithFundingSource },
            { name: 'Asset Creation - Different Sources', test: AssetCreationTests.testCreateAssetWithDifferentFundingSources },
            { name: 'Asset Editing', test: AssetEditingTests.testEditAssetFundingSource },
            { name: 'Asset List', test: AssetListingTests.testAssetListWithFundingSource },
            { name: 'Asset Filtering', test: AssetListingTests.testAssetFilteringByFundingSource },
            { name: 'Asset Export', test: AssetExportTests.testExportWithFundingSource },
            { name: 'Form Validation', test: FormValidationTests.testFundingSourceValidation },
            { name: 'Format Validation', test: FormValidationTests.testFundingSourceFormatValidation }
        ];

        let passed = 0;
        let failed = 0;

        for (const test of tests) {
            try {
                console.log(`\n📋 Running ${test.name} test...`);
                await test.test();
                console.log(`✅ ${test.name} test passed`);
                passed++;
            } catch (error) {
                console.error(`❌ ${test.name} test failed: ${error.message}`);
                failed++;
            }
        }

        console.log('\n📊 Asset Inventory Test Results:');
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

        if (failed === 0) {
            console.log('\n🎉 All asset inventory funding_source tests passed!');
        } else {
            console.log('\n⚠️ Some tests failed. Please review the errors above.');
        }

        return failed === 0;
    }
}

// Export for use in other test files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AssetInventoryTestRunner,
        AssetCreationTests,
        AssetEditingTests,
        AssetListingTests,
        AssetExportTests,
        FormValidationTests,
        AssetInventoryTestUtils,
        mockAssetInventoryAPI,
        ASSET_INVENTORY_CONFIG
    };
}

// Run tests if this file is executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.AssetInventoryTestRunner = AssetInventoryTestRunner;
    console.log('Asset Inventory Tests loaded. Run AssetInventoryTestRunner.runAllTests() to start testing.');
}
