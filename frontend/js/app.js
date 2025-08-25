// ARXOS Main Application JavaScript

// Initialize HTMX configuration
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    document.body.addEventListener('htmx:configRequest', function(evt) {
        // Add auth token to all requests
        const token = localStorage.getItem('arxos_token');
        if (token) {
            evt.detail.headers['Authorization'] = 'Bearer ' + token;
        }
    });

    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(evt) {
        if (evt.detail.xhr.status === 401) {
            // Redirect to login on auth failure
            window.location.href = '/login';
        }
    });

    // Initialize the app
    initApp();
});

function initApp() {
    // Check authentication status
    checkAuth();
    
    // Set up navigation
    setupNavigation();
    
    // Set up search functionality
    setupSearch();
    
    // Load initial content based on URL
    loadCurrentPage();
}

function setupNavigation() {
    // Handle navigation links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Handle browser back/forward
    window.addEventListener('popstate', function(e) {
        loadCurrentPage();
    });
}

function setupSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchDropdown = document.querySelector('#search-results');
    
    if (searchInput) {
        // Show/hide dropdown based on content
        document.body.addEventListener('htmx:afterRequest', function(evt) {
            if (evt.detail.target.id === 'search-results') {
                if (evt.detail.xhr.responseText.trim()) {
                    searchDropdown.classList.add('active');
                } else {
                    searchDropdown.classList.remove('active');
                }
            }
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.classList.remove('active');
            }
        });
    }
}

function loadCurrentPage() {
    const path = window.location.pathname;
    const mainContent = document.getElementById('main-content');
    
    // Map paths to content loaders
    switch(path) {
        case '/dashboard':
            loadDashboard();
            break;
        case '/buildings':
            loadBuildings();
            break;
        case '/profile':
            loadProfile();
            break;
        case '/settings':
            loadSettings();
            break;
        default:
            if (path.startsWith('/buildings/')) {
                const buildingId = path.split('/')[2];
                if (buildingId === 'new') {
                    loadNewBuilding();
                } else {
                    loadBuildingDetail(buildingId);
                }
            }
            break;
    }
    
    // Update active nav link
    updateActiveNav(path);
}

function updateActiveNav(path) {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === path || (path.startsWith('/buildings') && href === '/buildings')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

function loadDashboard() {
    const mainContent = document.getElementById('main-content');
    
    // Fetch dashboard content with HTMX
    htmx.ajax('GET', '/api/dashboard', {
        target: '#main-content',
        swap: 'innerHTML'
    }).then(() => {
        // Additional dashboard initialization if needed
        initDashboardCharts();
    });
}

function loadBuildings() {
    htmx.ajax('GET', '/api/buildings', {
        target: '#main-content',
        swap: 'innerHTML'
    });
}

function loadBuildingDetail(buildingId) {
    htmx.ajax('GET', `/api/buildings/${buildingId}`, {
        target: '#main-content',
        swap: 'innerHTML'
    }).then(() => {
        // Initialize 3D viewer if present
        if (window.initBuildingViewer) {
            window.initBuildingViewer(buildingId);
        }
    });
}

function loadNewBuilding() {
    htmx.ajax('GET', '/api/buildings/new', {
        target: '#main-content',
        swap: 'innerHTML'
    });
}

function loadProfile() {
    htmx.ajax('GET', '/api/profile', {
        target: '#main-content',
        swap: 'innerHTML'
    });
}

function loadSettings() {
    htmx.ajax('GET', '/api/settings', {
        target: '#main-content',
        swap: 'innerHTML'
    });
}

// Dashboard specific functions
function initDashboardCharts() {
    // Initialize any charts or visualizations
    // This would integrate with Chart.js or similar if needed
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than a minute
    if (diff < 60000) {
        return 'just now';
    }
    
    // Less than an hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    }
    
    // Less than a day
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    
    // Less than a week
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days} day${days > 1 ? 's' : ''} ago`;
    }
    
    // Default to date string
    return date.toLocaleDateString();
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Export functions for use in other modules
window.arxos = {
    formatDate,
    formatNumber,
    loadDashboard,
    loadBuildings,
    loadBuildingDetail
};