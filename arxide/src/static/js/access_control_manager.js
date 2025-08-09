/**
 * Access Control Manager
 * Frontend module for managing role-based permissions, floor-specific access controls,
 * audit trails, and permission inheritance
 */

class AccessControlManager {
    constructor() {
        this.baseUrl = '/access-control';
        this.currentUser = null;
        this.userPermissions = new Map();
        this.auditLogs = [];
        this.init();
    }

    async init() {
        try {
            await this.loadCurrentUser();
            await this.loadUserPermissions();
            this.setupEventListeners();
            this.setupRealTimeUpdates();
        } catch (error) {
            console.error('Failed to initialize Access Control Manager:', error);
        }
    }

    setupEventListeners() {
        // User management
        document.addEventListener('DOMContentLoaded', () => {
            this.setupUserManagementListeners();
            this.setupPermissionListeners();
            this.setupAuditLogListeners();
            this.setupFloorAccessListeners();
        });
    }

    setupUserManagementListeners() {
        // Create user form
        const createUserForm = document.getElementById('create-user-form');
        if (createUserForm) {
            createUserForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createUser();
            });
        }

        // User list refresh
        const refreshUsersBtn = document.getElementById('refresh-users');
        if (refreshUsersBtn) {
            refreshUsersBtn.addEventListener('click', () => this.loadUsers());
        }

        // User search
        const userSearchInput = document.getElementById('user-search');
        if (userSearchInput) {
            userSearchInput.addEventListener('input', (e) => {
                this.searchUsers(e.target.value);
            });
        }
    }

    setupPermissionListeners() {
        // Grant permission form
        const grantPermissionForm = document.getElementById('grant-permission-form');
        if (grantPermissionForm) {
            grantPermissionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.grantPermission();
            });
        }

        // Permission check form
        const checkPermissionForm = document.getElementById('check-permission-form');
        if (checkPermissionForm) {
            checkPermissionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.checkPermission();
            });
        }

        // Revoke permission buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('revoke-permission-btn')) {
                const permissionId = e.target.dataset.permissionId;
                this.revokePermission(permissionId);
            }
        });
    }

    setupAuditLogListeners() {
        // Audit log filters
        const auditLogFilters = document.getElementById('audit-log-filters');
        if (auditLogFilters) {
            auditLogFilters.addEventListener('change', () => {
                this.loadAuditLogs();
            });
        }

        // Export audit logs
        const exportAuditLogsBtn = document.getElementById('export-audit-logs');
        if (exportAuditLogsBtn) {
            exportAuditLogsBtn.addEventListener('click', () => this.exportAuditLogs());
        }
    }

    setupFloorAccessListeners() {
        // Floor access summary
        const floorAccessSummaryBtn = document.getElementById('floor-access-summary');
        if (floorAccessSummaryBtn) {
            floorAccessSummaryBtn.addEventListener('click', () => this.loadFloorAccessSummary());
        }

        // Bulk permission grant
        const bulkPermissionForm = document.getElementById('bulk-permission-form');
        if (bulkPermissionForm) {
            bulkPermissionForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.grantBulkPermissions();
            });
        }
    }

    setupRealTimeUpdates() {
        // Set up WebSocket connection for real-time updates
        if (window.accessControlSocket) {
            window.accessControlSocket.addEventListener('message', (event) => {
                const data = JSON.parse(event.data);
                this.handleRealTimeUpdate(data);
            });
        }
    }

    async loadCurrentUser() {
        try {
            // This would typically come from your authentication system
            const response = await fetch('/api/auth/current-user');
            if (response.ok) {
                this.currentUser = await response.json();
            }
        } catch (error) {
            console.error('Failed to load current user:', error);
        }
    }

    async loadUserPermissions() {
        try {
            if (!this.currentUser) return;

            const response = await fetch(`${this.baseUrl}/permissions/role/${this.currentUser.primary_role}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    data.permissions.forEach(permission => {
                        this.userPermissions.set(
                            `${permission.resource_type}:${permission.resource_id || 'global'}`,
                            permission.permission_level
                        );
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load user permissions:', error);
        }
    }

    async createUser() {
        try {
            const form = document.getElementById('create-user-form');
            const formData = new FormData(form);

            const userData = {
                username: formData.get('username'),
                email: formData.get('email'),
                primary_role: formData.get('primary_role'),
                secondary_roles: formData.get('secondary_roles')?.split(',').filter(r => r.trim()) || [],
                organization: formData.get('organization') || ''
            };

            const response = await fetch(`${this.baseUrl}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('User created successfully', 'success');
                form.reset();
                await this.loadUsers();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            console.error('Failed to create user:', error);
            this.showNotification('Failed to create user', 'error');
        }
    }

    async loadUsers() {
        try {
            const response = await fetch(`${this.baseUrl}/users`);
            const data = await response.json();

            if (data.success) {
                this.renderUserList(data.users);
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Failed to load users:', error);
            this.showNotification('Failed to load users', 'error');
        }
    }

    renderUserList(users) {
        const userListContainer = document.getElementById('user-list');
        if (!userListContainer) return;

        userListContainer.innerHTML = users.map(user => `
            <div class="user-item" data-user-id="${user.user_id}">
                <div class="user-info">
                    <h4>${user.username}</h4>
                    <p>${user.email}</p>
                    <span class="role-badge primary">${user.primary_role}</span>
                    ${user.secondary_roles.map(role => `<span class="role-badge secondary">${role}</span>`).join('')}
                </div>
                <div class="user-actions">
                    <button class="btn btn-sm btn-primary" onclick="accessControlManager.editUser('${user.user_id}')">
                        Edit
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="accessControlManager.deleteUser('${user.user_id}')">
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    async grantPermission() {
        try {
            const form = document.getElementById('grant-permission-form');
            const formData = new FormData(form);

            const permissionData = {
                role: formData.get('role'),
                resource_type: formData.get('resource_type'),
                resource_id: formData.get('resource_id') || null,
                permission_level: parseInt(formData.get('permission_level')),
                floor_id: formData.get('floor_id') || null,
                building_id: formData.get('building_id') || null,
                expires_at: formData.get('expires_at') || null
            };

            const response = await fetch(`${this.baseUrl}/permissions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(permissionData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Permission granted successfully', 'success');
                form.reset();
                await this.loadPermissions();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            console.error('Failed to grant permission:', error);
            this.showNotification('Failed to grant permission', 'error');
        }
    }

    async checkPermission() {
        try {
            const form = document.getElementById('check-permission-form');
            const formData = new FormData(form);

            const checkData = {
                user_id: formData.get('user_id'),
                resource_type: formData.get('resource_type'),
                action: formData.get('action'),
                resource_id: formData.get('resource_id') || null,
                floor_id: formData.get('floor_id') || null,
                building_id: formData.get('building_id') || null
            };

            const response = await fetch(`${this.baseUrl}/permissions/check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(checkData)
            });

            const result = await response.json();

            this.showPermissionCheckResult(result);
        } catch (error) {
            console.error('Failed to check permission:', error);
            this.showNotification('Failed to check permission', 'error');
        }
    }

    showPermissionCheckResult(result) {
        const resultContainer = document.getElementById('permission-check-result');
        if (!resultContainer) return;

        if (result.success) {
            resultContainer.innerHTML = `
                <div class="alert alert-success">
                    <h5>Permission Granted</h5>
                    <p>User has sufficient permissions for this action.</p>
                    <small>Permission Level: ${result.permission?.permission_level}</small>
                </div>
            `;
        } else {
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h5>Permission Denied</h5>
                    <p>${result.message}</p>
                </div>
            `;
        }
    }

    async loadPermissions() {
        try {
            const response = await fetch(`${this.baseUrl}/permissions`);
            const data = await response.json();

            if (data.success) {
                this.renderPermissionList(data.permissions);
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Failed to load permissions:', error);
            this.showNotification('Failed to load permissions', 'error');
        }
    }

    renderPermissionList(permissions) {
        const permissionListContainer = document.getElementById('permission-list');
        if (!permissionListContainer) return;

        permissionListContainer.innerHTML = permissions.map(permission => `
            <div class="permission-item" data-permission-id="${permission.permission_id}">
                <div class="permission-info">
                    <h5>${permission.role} - ${permission.resource_type}</h5>
                    <p>Level: ${permission.permission_level}</p>
                    ${permission.resource_id ? `<p>Resource: ${permission.resource_id}</p>` : ''}
                    ${permission.floor_id ? `<p>Floor: ${permission.floor_id}</p>` : ''}
                    <small>Created: ${new Date(permission.created_at).toLocaleDateString()}</small>
                </div>
                <div class="permission-actions">
                    <button class="btn btn-sm btn-danger revoke-permission-btn"
                            data-permission-id="${permission.permission_id}">
                        Revoke
                    </button>
                </div>
            </div>
        `).join('');
    }

    async revokePermission(permissionId) {
        try {
            if (!confirm('Are you sure you want to revoke this permission?')) {
                return;
            }

            const response = await fetch(`${this.baseUrl}/permissions/${permissionId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Permission revoked successfully', 'success');
                await this.loadPermissions();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            console.error('Failed to revoke permission:', error);
            this.showNotification('Failed to revoke permission', 'error');
        }
    }

    async loadAuditLogs() {
        try {
            const filters = this.getAuditLogFilters();
            const queryParams = new URLSearchParams(filters);

            const response = await fetch(`${this.baseUrl}/audit-logs?${queryParams}`);
            const data = await response.json();

            if (data.success) {
                this.renderAuditLogs(data.logs);
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Failed to load audit logs:', error);
            this.showNotification('Failed to load audit logs', 'error');
        }
    }

    getAuditLogFilters() {
        const filters = {};
        const form = document.getElementById('audit-log-filters');
        if (form) {
            const formData = new FormData(form);
            for (const [key, value] of formData.entries()) {
                if (value) filters[key] = value;
            }
        }
        return filters;
    }

    renderAuditLogs(logs) {
        const auditLogContainer = document.getElementById('audit-logs');
        if (!auditLogContainer) return;

        auditLogContainer.innerHTML = logs.map(log => `
            <div class="audit-log-item ${log.success ? 'success' : 'error'}" data-log-id="${log.log_id}">
                <div class="log-header">
                    <span class="log-action">${log.action}</span>
                    <span class="log-resource">${log.resource_type}: ${log.resource_id}</span>
                    <span class="log-timestamp">${new Date(log.timestamp).toLocaleString()}</span>
                </div>
                <div class="log-details">
                    <p><strong>User:</strong> ${log.user_id}</p>
                    ${log.floor_id ? `<p><strong>Floor:</strong> ${log.floor_id}</p>` : ''}
                    ${log.building_id ? `<p><strong>Building:</strong> ${log.building_id}</p>` : ''}
                    ${log.ip_address ? `<p><strong>IP:</strong> ${log.ip_address}</p>` : ''}
                    ${log.error_message ? `<p class="error-message"><strong>Error:</strong> ${log.error_message}</p>` : ''}
                </div>
                ${Object.keys(log.details).length > 0 ? `
                    <div class="log-metadata">
                        <details>
                            <summary>Additional Details</summary>
                            <pre>${JSON.stringify(log.details, null, 2)}</pre>
                        </details>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    async exportAuditLogs() {
        try {
            const filters = this.getAuditLogFilters();
            const queryParams = new URLSearchParams(filters);

            const response = await fetch(`${this.baseUrl}/audit-logs/export?${queryParams}`);
            const blob = await response.blob();

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.showNotification('Audit logs exported successfully', 'success');
        } catch (error) {
            console.error('Failed to export audit logs:', error);
            this.showNotification('Failed to export audit logs', 'error');
        }
    }

    async loadFloorAccessSummary() {
        try {
            const buildingId = document.getElementById('building-id')?.value;
            const floorId = document.getElementById('floor-id')?.value;

            if (!buildingId || !floorId) {
                this.showNotification('Please provide building ID and floor ID', 'error');
                return;
            }

            const response = await fetch(`${this.baseUrl}/floors/${buildingId}/${floorId}/access-summary`);
            const data = await response.json();

            if (data.success) {
                this.renderFloorAccessSummary(data);
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('Failed to load floor access summary:', error);
            this.showNotification('Failed to load floor access summary', 'error');
        }
    }

    renderFloorAccessSummary(data) {
        const summaryContainer = document.getElementById('floor-access-summary');
        if (!summaryContainer) return;

        summaryContainer.innerHTML = `
            <div class="access-summary">
                <h4>Access Summary for Floor ${data.floor_id}</h4>
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-number">${data.permission_count}</span>
                        <span class="stat-label">Permissions</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${data.activity_count}</span>
                        <span class="stat-label">Recent Activities</span>
                    </div>
                </div>

                <div class="permissions-section">
                    <h5>Floor Permissions</h5>
                    <div class="permission-list">
                        ${data.permissions.map(permission => `
                            <div class="permission-item">
                                <span class="role">${permission.role}</span>
                                <span class="resource">${permission.resource_type}</span>
                                <span class="level">Level ${permission.permission_level}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="activity-section">
                    <h5>Recent Activity</h5>
                    <div class="activity-list">
                        ${data.recent_activity.map(activity => `
                            <div class="activity-item">
                                <span class="action">${activity.action}</span>
                                <span class="user">${activity.user_id}</span>
                                <span class="time">${new Date(activity.timestamp).toLocaleString()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    async grantBulkPermissions() {
        try {
            const form = document.getElementById('bulk-permission-form');
            const formData = new FormData(form);

            const buildingId = formData.get('building_id');
            const floorId = formData.get('floor_id');
            const permissionsData = JSON.parse(formData.get('permissions') || '[]');

            if (!buildingId || !floorId || permissionsData.length === 0) {
                this.showNotification('Please provide building ID, floor ID, and permissions', 'error');
                return;
            }

            const response = await fetch(`${this.baseUrl}/floors/${buildingId}/${floorId}/permissions/bulk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(permissionsData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`Granted ${result.total} permissions successfully`, 'success');
                form.reset();
                await this.loadFloorAccessSummary();
            } else {
                this.showNotification(result.message, 'error');
            }
        } catch (error) {
            console.error('Failed to grant bulk permissions:', error);
            this.showNotification('Failed to grant bulk permissions', 'error');
        }
    }

    handleRealTimeUpdate(data) {
        switch (data.type) {
            case 'permission_granted':
                this.showNotification(`Permission granted to ${data.role}`, 'info');
                this.loadPermissions();
                break;
            case 'permission_revoked':
                this.showNotification(`Permission revoked from ${data.role}`, 'info');
                this.loadPermissions();
                break;
            case 'user_created':
                this.showNotification(`User ${data.username} created`, 'info');
                this.loadUsers();
                break;
            case 'audit_log':
                this.showNotification(`New activity: ${data.action}`, 'info');
                this.loadAuditLogs();
                break;
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="message">${message}</span>
            <button class="close-btn" onclick="this.parentElement.remove()">&times;</button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Utility methods
    hasPermission(resourceType, action, resourceId = null) {
        const key = `${resourceType}:${resourceId || 'global'}`;
        const permissionLevel = this.userPermissions.get(key);

        if (!permissionLevel) return false;

        const requiredLevel = this.getRequiredPermissionLevel(action);
        return permissionLevel >= requiredLevel;
    }

    getRequiredPermissionLevel(action) {
        const actionLevels = {
            'read': 1,
            'create': 2,
            'update': 2,
            'delete': 3,
            'export': 1,
            'import': 2,
            'merge': 2,
            'branch': 2,
            'annotate': 2,
            'comment': 2,
            'approve': 3,
            'reject': 3,
            'assign': 3,
            'transfer': 3
        };
        return actionLevels[action] || 3;
    }

    logActivity(action, resourceType, resourceId, details = {}) {
        if (!this.currentUser) return;

        const activityData = {
            user_id: this.currentUser.user_id,
            action: action,
            resource_type: resourceType,
            resource_id: resourceId,
            details: details,
            ip_address: this.getClientIP(),
            user_agent: navigator.userAgent
        };

        fetch(`${this.baseUrl}/audit-logs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(activityData)
        }).catch(error => {
            console.error('Failed to log activity:', error);
        });
    }

    getClientIP() {
        // This would typically be provided by your backend
        return 'unknown';
    }
}

// Initialize the access control manager
const accessControlManager = new AccessControlManager();

// Export for use in other modules
window.accessControlManager = accessControlManager;
