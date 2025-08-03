/**
 * Asset Lifecycle Manager for Floor-Based Asset Management
 * Handles lifecycle events, replacement schedules, analytics, and compliance reporting
 */

class AssetLifecycleManager {
    constructor() {
        this.baseUrl = '/v1/asset-lifecycle';
        this.eventListeners = {
            'lifecycle_event_logged': [],
            'replacement_schedule_created': [],
            'analytics_updated': [],
            'compliance_report_updated': []
        };
    }

    // Event system
    addEventListener(event, callback) {
        if (!this.eventListeners[event]) this.eventListeners[event] = [];
        this.eventListeners[event].push(callback);
    }
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(cb => {
                try { cb(data); } catch (e) { console.error(e); }
            });
        }
    }

    // --- Lifecycle Events ---
    async logLifecycleEvent(event) {
        const res = await fetch(`${this.baseUrl}/event`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(event)
        });
        const result = await res.json();
        this.emit('lifecycle_event_logged', result);
        return result;
    }
    async getLifecycleEvents(buildingId, floorId, assetId) {
        const res = await fetch(`${this.baseUrl}/events/${buildingId}/${floorId}/${assetId}`);
        return await res.json();
    }

    // --- Replacement Schedules ---
    async createReplacementSchedule(schedule) {
        const res = await fetch(`${this.baseUrl}/replacement-schedule`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(schedule)
        });
        const result = await res.json();
        this.emit('replacement_schedule_created', result);
        return result;
    }
    async getReplacementSchedules(buildingId, floorId) {
        const res = await fetch(`${this.baseUrl}/replacement-schedules/${buildingId}/${floorId}`);
        return await res.json();
    }

    // --- Analytics ---
    async getAssetAnalytics(buildingId, floorId) {
        const res = await fetch(`${this.baseUrl}/analytics/${buildingId}/${floorId}`);
        const result = await res.json();
        this.emit('analytics_updated', result);
        return result;
    }

    // --- Compliance Reporting ---
    async getComplianceReport(buildingId, floorId) {
        const res = await fetch(`${this.baseUrl}/compliance/${buildingId}/${floorId}`);
        const result = await res.json();
        this.emit('compliance_report_updated', result);
        return result;
    }

    // --- Visualization Helpers ---
    renderAnalyticsTable(analytics, container) {
        if (!container) return;
        container.innerHTML = '';
        const table = document.createElement('table');
        table.className = 'asset-analytics-table';
        table.innerHTML = `
            <thead><tr>
                <th>Asset ID</th><th>Events</th><th>Total Labor Hours</th><th>Total Cost</th>
            </tr></thead>
            <tbody>
                ${analytics.map(a => `
                    <tr>
                        <td>${a.asset_id}</td>
                        <td>${a.event_count}</td>
                        <td>${a.total_labor_hours ?? 0}</td>
                        <td>${a.total_cost ?? 0}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        container.appendChild(table);
    }

    renderComplianceTable(assets, container) {
        if (!container) return;
        container.innerHTML = '';
        const table = document.createElement('table');
        table.className = 'compliance-report-table';
        table.innerHTML = `
            <thead><tr>
                <th>Asset ID</th><th>Name</th><th>Type</th><th>Status</th><th>Condition</th><th>Next Maintenance</th><th>Overdue</th>
            </tr></thead>
            <tbody>
                ${assets.map(a => `
                    <tr${a.overdue ? ' class="overdue"' : ''}>
                        <td>${a.asset_id}</td>
                        <td>${a.asset_name}</td>
                        <td>${a.asset_type}</td>
                        <td>${a.status}</td>
                        <td>${a.condition}</td>
                        <td>${a.next_maintenance ?? ''}</td>
                        <td>${a.overdue ? '⚠️' : ''}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        container.appendChild(table);
    }
}

window.assetLifecycleManager = new AssetLifecycleManager();
if (typeof module !== 'undefined' && module.exports) module.exports = AssetLifecycleManager; 