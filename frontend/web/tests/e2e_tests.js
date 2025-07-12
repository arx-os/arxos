/**
 * E2E Tests for Arxos Data Library Frontend
 * 
 * These tests cover the complete user workflows for:
 * - Security management
 * - Compliance reporting
 * - Export analytics
 * - API key management
 */

// Test configuration
const TEST_CONFIG = {
    baseUrl: 'http://localhost:8080',
    testUser: {
        email: 'test@example.com',
        password: 'testpassword',
        role: 'admin'
    },
    timeout: 10000
};

// Test utilities
class TestUtils {
    static async wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static async login(page, credentials = TEST_CONFIG.testUser) {
        await page.goto(`${TEST_CONFIG.baseUrl}/login.html`);
        await page.fill('#email', credentials.email);
        await page.fill('#password', credentials.password);
        await page.click('#login-btn');
        await this.wait(1000);
    }

    static async logout(page) {
        await page.click('button[onclick="logout()"]');
        await this.wait(500);
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

// Mock API responses for testing
const mockAPIResponses = {
    login: {
        success: {
            token: 'mock-jwt-token',
            user: {
                id: 1,
                email: 'test@example.com',
                username: 'testuser',
                role: 'admin'
            }
        }
    },
    security: {
        dashboard: {
            alerts: {
                total: 5,
                resolved: 3,
                critical: 1,
                unresolved: 2
            },
            api_usage: {
                total_requests: 1500,
                failed_requests: 25,
                rate_limit_violations: 3,
                success_rate: 98.3
            },
            recent_alerts: [
                {
                    id: 1,
                    alert_type: 'authentication_failure',
                    severity: 'high',
                    ip_address: '192.168.1.100',
                    created_at: '2024-01-15T10:30:00Z'
                }
            ]
        },
        apiKeys: [
            {
                id: 1,
                key: 'arx_test_key_123',
                vendor_name: 'Test Vendor',
                email: 'vendor@test.com',
                access_level: 'premium',
                is_active: true,
                created_at: '2024-01-01T00:00:00Z'
            }
        ]
    },
    compliance: {
        dataAccessLogs: [
            {
                id: 1,
                user_id: 1,
                action: 'view',
                object_type: 'building_asset',
                object_id: 'asset_123',
                ip_address: '192.168.1.100',
                created_at: '2024-01-15T10:30:00Z'
            }
        ],
        exportActivitySummary: [
            {
                period: '2024-01',
                total_exports: 150,
                total_downloads: 300,
                total_file_size: 1048576000,
                unique_users: 25
            }
        ]
    }
};

// Test suites
class SecurityTests {
    static async testSecurityDashboard(page) {
        console.log('Testing Security Dashboard...');
        
        // Navigate to security page
        await page.goto(`${TEST_CONFIG.baseUrl}/security.html`);
        await TestUtils.wait(1000);

        // Check if dashboard loads
        const dashboardExists = await TestUtils.checkElementExists(page, '#active-alerts');
        if (!dashboardExists) {
            throw new Error('Security dashboard not loaded');
        }

        // Check dashboard metrics
        const activeAlerts = await page.$eval('#active-alerts', el => el.textContent);
        const apiRequests = await page.$eval('#api-requests', el => el.textContent);
        const successRate = await page.$eval('#success-rate', el => el.textContent);

        console.log(`Active Alerts: ${activeAlerts}`);
        console.log(`API Requests: ${apiRequests}`);
        console.log(`Success Rate: ${successRate}`);

        // Test tab switching
        await page.click('[data-tab="alerts"]');
        await TestUtils.wait(500);
        
        const alertsTabActive = await page.$eval('[data-tab="alerts"]', el => 
            el.classList.contains('active')
        );
        if (!alertsTabActive) {
            throw new Error('Alerts tab not activated');
        }

        console.log('✓ Security Dashboard test passed');
    }

    static async testAPIKeyManagement(page) {
        console.log('Testing API Key Management...');

        // Navigate to API Keys tab
        await page.goto(`${TEST_CONFIG.baseUrl}/security.html`);
        await page.click('[data-tab="api-keys"]');
        await TestUtils.wait(500);

        // Test generate new API key
        await page.click('button:contains("Generate New Key")');
        await TestUtils.wait(500);

        // Fill form
        await page.fill('input[name="vendor_name"]', 'E2E Test Vendor');
        await page.fill('input[name="email"]', 'e2e@test.com');
        await page.selectOption('select[name="access_level"]', 'premium');
        await page.fill('input[name="rate_limit"]', '1000');
        await page.selectOption('select[name="security_level"]', 'enhanced');

        // Submit form
        await page.click('button[type="submit"]');
        await TestUtils.wait(1000);

        // Check for success message
        const successMessage = await page.$eval('.alert-success', el => el.textContent);
        if (!successMessage.includes('API key generated successfully')) {
            throw new Error('API key generation failed');
        }

        // Test API key listing
        const apiKeysTable = await page.$('#api-keys-table');
        if (!apiKeysTable) {
            throw new Error('API keys table not found');
        }

        console.log('✓ API Key Management test passed');
    }

    static async testSecurityAlerts(page) {
        console.log('Testing Security Alerts...');

        // Navigate to alerts tab
        await page.goto(`${TEST_CONFIG.baseUrl}/security.html`);
        await page.click('[data-tab="alerts"]');
        await TestUtils.wait(500);

        // Test filtering
        await page.selectOption('#alert-filter', 'authentication_failure');
        await page.selectOption('#severity-filter', 'high');
        await TestUtils.wait(500);

        // Check if filters are applied
        const alertsTable = await page.$('#alerts-table');
        if (!alertsTable) {
            throw new Error('Alerts table not found');
        }

        // Test resolving an alert
        const resolveButton = await page.$('button:contains("Resolve")');
        if (resolveButton) {
            await resolveButton.click();
            await TestUtils.wait(500);

            // Fill resolution notes
            await page.fill('textarea[name="notes"]', 'Resolved during E2E testing');
            await page.click('button[type="submit"]');
            await TestUtils.wait(500);

            // Check for success message
            const successMessage = await page.$eval('.alert-success', el => el.textContent);
            if (!successMessage.includes('Security alert resolved successfully')) {
                throw new Error('Alert resolution failed');
            }
        }

        console.log('✓ Security Alerts test passed');
    }
}

class ComplianceTests {
    static async testComplianceDashboard(page) {
        console.log('Testing Compliance Dashboard...');

        // Navigate to compliance page
        await page.goto(`${TEST_CONFIG.baseUrl}/compliance.html`);
        await TestUtils.wait(1000);

        // Check if page loads
        const pageTitle = await page.$eval('h1', el => el.textContent);
        if (!pageTitle.includes('Compliance')) {
            throw new Error('Compliance page not loaded');
        }

        // Test tab switching
        const tabs = ['data-access-logs', 'change-history', 'export-activity', 'data-retention'];
        
        for (const tab of tabs) {
            await page.click(`[data-tab="${tab}"]`);
            await TestUtils.wait(500);

            const tabActive = await page.$eval(`[data-tab="${tab}"]`, el => 
                el.classList.contains('active')
            );
            if (!tabActive) {
                throw new Error(`Tab ${tab} not activated`);
            }
        }

        console.log('✓ Compliance Dashboard test passed');
    }

    static async testDataAccessLogs(page) {
        console.log('Testing Data Access Logs...');

        // Navigate to data access logs tab
        await page.goto(`${TEST_CONFIG.baseUrl}/compliance.html`);
        await page.click('[data-tab="data-access-logs"]');
        await TestUtils.wait(500);

        // Test filtering
        await page.fill('input[name="user"]', 'testuser');
        await page.fill('input[name="start_date"]', '2024-01-01');
        await page.fill('input[name="end_date"]', '2024-01-31');
        await page.click('button[type="submit"]');
        await TestUtils.wait(500);

        // Check if logs are displayed
        const logsTable = await page.$('#data-access-logs-table');
        if (!logsTable) {
            throw new Error('Data access logs table not found');
        }

        console.log('✓ Data Access Logs test passed');
    }

    static async testExportActivitySummary(page) {
        console.log('Testing Export Activity Summary...');

        // Navigate to export activity tab
        await page.goto(`${TEST_CONFIG.baseUrl}/compliance.html`);
        await page.click('[data-tab="export-activity"]');
        await TestUtils.wait(500);

        // Test date range selection
        await page.fill('input[name="start_date"]', '2024-01-01');
        await page.fill('input[name="end_date"]', '2024-01-31');
        await page.click('button:contains("Generate Report")');
        await TestUtils.wait(1000);

        // Check if summary is displayed
        const summaryTable = await page.$('#export-summary-table');
        if (!summaryTable) {
            throw new Error('Export summary table not found');
        }

        console.log('✓ Export Activity Summary test passed');
    }

    static async testDataRetentionManagement(page) {
        console.log('Testing Data Retention Management...');

        // Navigate to data retention tab
        await page.goto(`${TEST_CONFIG.baseUrl}/compliance.html`);
        await page.click('[data-tab="data-retention"]');
        await TestUtils.wait(500);

        // Test creating retention policy
        await page.click('button:contains("Create Policy")');
        await TestUtils.wait(500);

        // Fill form
        await page.fill('input[name="object_type"]', 'test_logs');
        await page.fill('input[name="retention_period"]', '365');
        await page.fill('input[name="archive_after"]', '30');
        await page.fill('input[name="delete_after"]', '365');
        await page.fill('textarea[name="description"]', 'E2E test retention policy');

        // Submit form
        await page.click('button[type="submit"]');
        await TestUtils.wait(1000);

        // Check for success message
        const successMessage = await page.$eval('.alert-success', el => el.textContent);
        if (!successMessage.includes('Data retention policy created successfully')) {
            throw new Error('Retention policy creation failed');
        }

        console.log('✓ Data Retention Management test passed');
    }
}

class ExportAnalyticsTests {
    static async testExportAnalyticsDashboard(page) {
        console.log('Testing Export Analytics Dashboard...');

        // Navigate to export analytics page
        await page.goto(`${TEST_CONFIG.baseUrl}/export_analytics.html`);
        await TestUtils.wait(1000);

        // Check if dashboard loads
        const dashboardExists = await TestUtils.checkElementExists(page, '#today-exports');
        if (!dashboardExists) {
            throw new Error('Export analytics dashboard not loaded');
        }

        // Check dashboard metrics
        const todayExports = await page.$eval('#today-exports', el => el.textContent);
        const weekExports = await page.$eval('#week-exports', el => el.textContent);
        const monthExports = await page.$eval('#month-exports', el => el.textContent);

        console.log(`Today's Exports: ${todayExports}`);
        console.log(`Week's Exports: ${weekExports}`);
        console.log(`Month's Exports: ${monthExports}`);

        // Test date range filtering
        await page.fill('input[name="start_date"]', '2024-01-01');
        await page.fill('input[name="end_date"]', '2024-01-31');
        await page.click('button:contains("Apply Filter")');
        await TestUtils.wait(1000);

        console.log('✓ Export Analytics Dashboard test passed');
    }

    static async testExportHistory(page) {
        console.log('Testing Export History...');

        // Navigate to export history section
        await page.goto(`${TEST_CONFIG.baseUrl}/export_analytics.html`);
        await page.click('[data-tab="history"]');
        await TestUtils.wait(500);

        // Test filtering
        await page.selectOption('select[name="export_type"]', 'asset_inventory');
        await page.selectOption('select[name="format"]', 'csv');
        await page.click('button:contains("Filter")');
        await TestUtils.wait(500);

        // Check if filtered results are displayed
        const historyTable = await page.$('#export-history-table');
        if (!historyTable) {
            throw new Error('Export history table not found');
        }

        console.log('✓ Export History test passed');
    }
}

class NavigationTests {
    static async testNavigation(page) {
        console.log('Testing Navigation...');

        // Test navigation between pages
        const pages = [
            { url: '/index.html', title: 'Dashboard' },
            { url: '/security.html', title: 'Security' },
            { url: '/compliance.html', title: 'Compliance' },
            { url: '/export_analytics.html', title: 'Export Analytics' },
            { url: '/audit_logs.html', title: 'Audit Logs' }
        ];

        for (const pageInfo of pages) {
            await page.goto(`${TEST_CONFIG.baseUrl}${pageInfo.url}`);
            await TestUtils.wait(500);

            const pageTitle = await page.$eval('h1, h2', el => el.textContent);
            if (!pageTitle.includes(pageInfo.title)) {
                throw new Error(`Page ${pageInfo.url} not loaded correctly`);
            }
        }

        console.log('✓ Navigation test passed');
    }

    static async testAuthentication(page) {
        console.log('Testing Authentication...');

        // Test login
        await TestUtils.login(page);
        
        // Check if user is logged in
        const logoutButton = await page.$('button[onclick="logout()"]');
        if (!logoutButton) {
            throw new Error('User not logged in');
        }

        // Test logout
        await TestUtils.logout(page);
        
        // Check if redirected to login page
        const currentUrl = page.url();
        if (!currentUrl.includes('login.html')) {
            throw new Error('User not logged out');
        }

        console.log('✓ Authentication test passed');
    }
}

class AssetInventoryTests {
    static async testViewAndFilterAssets(page) {
        console.log('Testing Asset Inventory: View and Filter...');
        await TestUtils.login(page);
        await page.goto(`${TEST_CONFIG.baseUrl}/asset_inventory.html`);
        await TestUtils.wait(1000);
        // Check table loads
        const tableExists = await TestUtils.checkElementExists(page, '#asset-table');
        if (!tableExists) throw new Error('Asset table not loaded');
        // Try filtering by system
        await page.fill('#filter-system', 'HVAC');
        await page.click('button:has-text("Search")');
        await TestUtils.wait(1000);
        // Check at least one row
        const rows = await page.$$('#asset-table-body tr');
        if (rows.length === 0) throw new Error('No assets found after filtering');
        console.log('✓ Asset Inventory: View and Filter test passed');
    }

    static async testCreateEditDeleteAsset(page) {
        console.log('Testing Asset Inventory: Create, Edit, Delete...');
        await page.goto(`${TEST_CONFIG.baseUrl}/asset_inventory.html`);
        await TestUtils.wait(1000);
        // Open add asset modal
        await page.click('button:has-text("+ Add Asset")');
        await TestUtils.wait(500);
        // Fill form
        await page.selectOption('#asset-building', { index: 1 });
        await TestUtils.wait(300);
        await page.selectOption('#asset-floor', { index: 1 });
        await page.fill('#asset-room', 'E2E Room');
        await page.fill('#asset-type', 'E2E Type');
        await page.fill('#asset-system', 'E2E System');
        await page.fill('#asset-x', '10');
        await page.fill('#asset-y', '20');
        await page.fill('#asset-specs', '{"capacity": "5 ton"}');
        await page.fill('#asset-value', '12345');
        await page.fill('#asset-replacement', '23456');
        await page.selectOption('#asset-status', 'active');
        await page.click('button:has-text("Create Asset")');
        await TestUtils.wait(1500);
        // Check toast
        const toast = await page.$('#toast-area div');
        if (!toast) throw new Error('No toast after asset creation');
        // Edit asset (open first row)
        await page.click('#asset-table-body tr:first-child button:has-text("View")');
        await TestUtils.wait(500);
        await page.fill('#asset-room', 'E2E Room Edited');
        await page.click('button:has-text("Save Changes")');
        await TestUtils.wait(1000);
        // Delete asset
        await page.click('#asset-table-body tr:first-child input[type="checkbox"]');
        await page.click('button:has-text("Delete Selected")');
        await page.waitForSelector('#toast-area div');
        console.log('✓ Asset Inventory: Create, Edit, Delete test passed');
    }

    static async testViewAssetDetailsTabs(page) {
        console.log('Testing Asset Inventory: Asset Details Tabs...');
        await page.goto(`${TEST_CONFIG.baseUrl}/asset_inventory.html`);
        await TestUtils.wait(1000);
        // Open first asset
        await page.click('#asset-table-body tr:first-child button:has-text("View")');
        await TestUtils.wait(500);
        // Switch tabs
        await page.click('button.tab-btn:has-text("Maintenance")');
        await TestUtils.wait(300);
        await page.click('button.tab-btn:has-text("Valuation")');
        await TestUtils.wait(300);
        await page.click('button.tab-btn:has-text("Documents")');
        await TestUtils.wait(300);
        // Check content loads
        const history = await page.$('#asset-history-timeline');
        const maintenance = await page.$('#asset-maintenance-records');
        const valuation = await page.$('#asset-valuation-history');
        if (!history || !maintenance || !valuation) throw new Error('Asset details tabs not loaded');
        console.log('✓ Asset Inventory: Asset Details Tabs test passed');
    }

    static async testExportInventory(page) {
        console.log('Testing Asset Inventory: Export...');
        await page.goto(`${TEST_CONFIG.baseUrl}/asset_inventory.html`);
        await TestUtils.wait(1000);
        // Click export CSV
        await page.click('button:has-text("Export CSV")');
        await TestUtils.wait(1000);
        // Click export JSON
        await page.click('button:has-text("Export JSON")');
        await TestUtils.wait(1000);
        // Advanced export
        await page.click('button:has-text("Export")');
        await TestUtils.wait(1500);
        // Check toast
        const toast = await page.$('#toast-area div');
        if (!toast) throw new Error('No toast after export');
        console.log('✓ Asset Inventory: Export test passed');
    }

    static async testSymbolPlacementIntegration(page) {
        console.log('Testing Asset Inventory: Symbol Placement Integration...');
        await page.goto(`${TEST_CONFIG.baseUrl}/asset_inventory.html`);
        await TestUtils.wait(1000);
        // Open modal and click symbol placement button
        await page.click('button:has-text("+ Add Asset")');
        await TestUtils.wait(500);
        await page.click('button:has-text("Add from Symbol Placement")');
        await TestUtils.wait(500);
        // Check toast
        const toast = await page.$('#toast-area div');
        if (!toast) throw new Error('No toast after symbol placement');
        console.log('✓ Asset Inventory: Symbol Placement Integration test passed');
    }

    static async testUserFeedbackNotifications(page) {
        console.log('Testing Asset Inventory: User Feedback/Notifications...');
        await page.goto(`${TEST_CONFIG.baseUrl}/asset_inventory.html`);
        await TestUtils.wait(1000);
        // Trigger a known error (invalid JSON in specs)
        await page.click('button:has-text("+ Add Asset")');
        await TestUtils.wait(500);
        await page.fill('#asset-specs', '{invalid json');
        await page.click('button:has-text("Create Asset")');
        await TestUtils.wait(500);
        // Check error toast
        const toast = await page.$('#toast-area div');
        if (!toast) throw new Error('No toast after error');
        const text = await toast.textContent();
        if (!text.includes('Invalid')) throw new Error('Error toast not shown for invalid input');
        console.log('✓ Asset Inventory: User Feedback/Notifications test passed');
    }
}

// SVG Zoom History E2E Tests
class SVGZoomHistoryTests {
    static async testZoomHistoryUndoRedo(page) {
        console.log('Testing SVG Zoom History Undo/Redo...');
        await page.goto(`${TEST_CONFIG.baseUrl}/svg_view.html`);
        await TestUtils.wait(1000);
        // Initial zoom should be 100%
        let zoomText = await page.$eval('#zoom-level', el => el.textContent);
        if (zoomText.trim() !== '100%') throw new Error('Initial zoom not 100%');
        // Zoom in twice
        await page.click('#zoom-in');
        await TestUtils.wait(200);
        await page.click('#zoom-in');
        await TestUtils.wait(200);
        zoomText = await page.$eval('#zoom-level', el => el.textContent);
        if (zoomText.trim() === '100%') throw new Error('Zoom did not change after zoom in');
        // Undo zoom (button)
        await page.click('#zoom-undo');
        await TestUtils.wait(200);
        let zoomAfterUndo = await page.$eval('#zoom-level', el => el.textContent);
        if (zoomAfterUndo === zoomText) throw new Error('Undo did not change zoom');
        // Redo zoom (button)
        await page.click('#zoom-redo');
        await TestUtils.wait(200);
        let zoomAfterRedo = await page.$eval('#zoom-level', el => el.textContent);
        if (zoomAfterRedo !== zoomText) throw new Error('Redo did not restore zoom');
        // Undo zoom (keyboard)
        await page.keyboard.down('Control');
        await page.keyboard.press('z');
        await page.keyboard.up('Control');
        await TestUtils.wait(200);
        let zoomAfterUndoKey = await page.$eval('#zoom-level', el => el.textContent);
        if (zoomAfterUndoKey === zoomAfterRedo) throw new Error('Keyboard undo did not work');
        // Redo zoom (keyboard)
        await page.keyboard.down('Control');
        await page.keyboard.press('y');
        await page.keyboard.up('Control');
        await TestUtils.wait(200);
        let zoomAfterRedoKey = await page.$eval('#zoom-level', el => el.textContent);
        if (zoomAfterRedoKey !== zoomAfterRedo) throw new Error('Keyboard redo did not work');
        // Check button disabled state
        const undoDisabled = await page.$eval('#zoom-undo', el => el.disabled);
        const redoDisabled = await page.$eval('#zoom-redo', el => el.disabled);
        if (typeof undoDisabled !== 'boolean' || typeof redoDisabled !== 'boolean') throw new Error('Undo/Redo button state not found');
        console.log('✓ SVG Zoom History Undo/Redo test passed');
    }
}

// Main test runner
class E2ETestRunner {
    static async runAllTests() {
        console.log('🚀 Starting E2E Tests for Arxos Data Library...\n');

        const tests = [
            { name: 'Navigation', test: NavigationTests.testNavigation },
            { name: 'Authentication', test: NavigationTests.testAuthentication },
            { name: 'Security Dashboard', test: SecurityTests.testSecurityDashboard },
            { name: 'API Key Management', test: SecurityTests.testAPIKeyManagement },
            { name: 'Security Alerts', test: SecurityTests.testSecurityAlerts },
            { name: 'Compliance Dashboard', test: ComplianceTests.testComplianceDashboard },
            { name: 'Data Access Logs', test: ComplianceTests.testDataAccessLogs },
            { name: 'Export Activity Summary', test: ComplianceTests.testExportActivitySummary },
            { name: 'Data Retention Management', test: ComplianceTests.testDataRetentionManagement },
            { name: 'Export Analytics Dashboard', test: ExportAnalyticsTests.testExportAnalyticsDashboard },
            { name: 'Export History', test: ExportAnalyticsTests.testExportHistory },
            // Asset Inventory E2E tests:
            { name: 'Asset Inventory: View and Filter', test: AssetInventoryTests.testViewAndFilterAssets },
            { name: 'Asset Inventory: Create, Edit, Delete', test: AssetInventoryTests.testCreateEditDeleteAsset },
            { name: 'Asset Inventory: Asset Details Tabs', test: AssetInventoryTests.testViewAssetDetailsTabs },
            { name: 'Asset Inventory: Export', test: AssetInventoryTests.testExportInventory },
            { name: 'Asset Inventory: Symbol Placement Integration', test: AssetInventoryTests.testSymbolPlacementIntegration },
            { name: 'Asset Inventory: User Feedback/Notifications', test: AssetInventoryTests.testUserFeedbackNotifications },
            // SVG Zoom History test:
            { name: 'SVG Zoom History: Undo/Redo', test: SVGZoomHistoryTests.testZoomHistoryUndoRedo }
        ];

        let passed = 0;
        let failed = 0;

        for (const test of tests) {
            try {
                console.log(`\n📋 Running ${test.name}...`);
                await test.test();
                passed++;
                console.log(`✅ ${test.name} - PASSED`);
            } catch (error) {
                failed++;
                console.log(`❌ ${test.name} - FAILED: ${error.message}`);
            }
        }

        console.log(`\n📊 Test Results:`);
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`📈 Success Rate: ${((passed / (passed + failed)) * 100).toFixed(1)}%`);

        if (failed > 0) {
            console.log('\n⚠️  Some tests failed. Please check the implementation.');
            process.exit(1);
        } else {
            console.log('\n🎉 All tests passed!');
        }
    }
}

// Export for use in different environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        E2ETestRunner,
        SecurityTests,
        ComplianceTests,
        ExportAnalyticsTests,
        NavigationTests,
        TestUtils
    };
}

// Run tests if this file is executed directly
if (typeof window === 'undefined') {
    E2ETestRunner.runAllTests().catch(console.error);
} 