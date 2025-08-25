// ARXOS Buildings Module

// Building management functions
function createBuilding(formData) {
    fetch('/api/buildings', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('arxos_token')
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to create building');
        }
        return response.json();
    })
    .then(data => {
        // Redirect to new building
        window.location.href = `/buildings/${data.id}`;
    })
    .catch(error => {
        console.error('Error creating building:', error);
        showError('Failed to create building. Please try again.');
    });
}

function updateBuilding(buildingId, data) {
    fetch(`/api/buildings/${buildingId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + localStorage.getItem('arxos_token')
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update building');
        }
        return response.json();
    })
    .then(data => {
        showSuccess('Building updated successfully');
        // Refresh the page content
        loadBuildingDetail(buildingId);
    })
    .catch(error => {
        console.error('Error updating building:', error);
        showError('Failed to update building. Please try again.');
    });
}

function deleteBuilding(buildingId) {
    if (!confirm('Are you sure you want to delete this building? This action cannot be undone.')) {
        return;
    }
    
    fetch(`/api/buildings/${buildingId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('arxos_token')
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete building');
        }
        // Redirect to buildings list
        window.location.href = '/buildings';
    })
    .catch(error => {
        console.error('Error deleting building:', error);
        showError('Failed to delete building. Please try again.');
    });
}

function starBuilding(buildingId) {
    fetch(`/api/buildings/${buildingId}/star`, {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('arxos_token')
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to star building');
        }
        return response.json();
    })
    .then(data => {
        // Update star icon
        const starIcon = document.querySelector(`[data-building-id="${buildingId}"] .star-icon`);
        if (starIcon) {
            starIcon.classList.toggle('starred', data.starred);
        }
    })
    .catch(error => {
        console.error('Error starring building:', error);
    });
}

// PDF Upload handling
function initPDFUpload() {
    const dropZone = document.getElementById('pdf-drop-zone');
    const fileInput = document.getElementById('pdf-file-input');
    
    if (!dropZone || !fileInput) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);
    
    // Handle file input change
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    // Click to select file
    dropZone.addEventListener('click', () => fileInput.click());
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    e.currentTarget.classList.add('drag-over');
}

function unhighlight(e) {
    e.currentTarget.classList.remove('drag-over');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    ([...files]).forEach(uploadFile);
}

function uploadFile(file) {
    // Check if file is PDF
    if (file.type !== 'application/pdf') {
        showError('Please upload only PDF files');
        return;
    }
    
    // Check file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
        showError('File size must be less than 50MB');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Show progress
    showProgress('Uploading and processing PDF...');
    
    fetch('/upload/pdf', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('arxos_token')
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        return response.json();
    })
    .then(data => {
        hideProgress();
        showSuccess('PDF processed successfully');
        
        // Display results
        displayPDFResults(data);
    })
    .catch(error => {
        hideProgress();
        console.error('Upload error:', error);
        showError('Failed to process PDF. Please try again.');
    });
}

function displayPDFResults(data) {
    const resultsDiv = document.getElementById('pdf-results');
    if (!resultsDiv) return;
    
    let html = `
        <div class="pdf-results">
            <h3>Processing Results</h3>
            <p class="text-muted">Found ${data.arxobjects.length} objects in ${data.filename}</p>
            
            <div class="results-grid">
    `;
    
    // Group objects by type
    const objectsByType = {};
    data.arxobjects.forEach(obj => {
        const type = obj.type || 'unknown';
        if (!objectsByType[type]) {
            objectsByType[type] = [];
        }
        objectsByType[type].push(obj);
    });
    
    // Display grouped objects
    for (const [type, objects] of Object.entries(objectsByType)) {
        html += `
            <div class="result-group">
                <h4>${type} (${objects.length})</h4>
                <ul class="object-list">
        `;
        
        objects.slice(0, 5).forEach(obj => {
            html += `
                <li>
                    <span class="object-id">${obj.id}</span>
                    <span class="object-confidence">${(obj.confidence * 100).toFixed(0)}%</span>
                </li>
            `;
        });
        
        if (objects.length > 5) {
            html += `<li class="text-muted">... and ${objects.length - 5} more</li>`;
        }
        
        html += `
                </ul>
            </div>
        `;
    }
    
    html += `
            </div>
            
            <div class="results-actions">
                <button class="btn btn-primary" onclick="saveToBuilding('${data.id}')">
                    Save to Building
                </button>
                <button class="btn btn-default" onclick="viewDetailed('${data.id}')">
                    View Detailed Results
                </button>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Utility functions for notifications
function showError(message) {
    showNotification(message, 'error');
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showProgress(message) {
    const progressDiv = document.getElementById('progress-indicator') || createProgressIndicator();
    progressDiv.textContent = message;
    progressDiv.style.display = 'block';
}

function hideProgress() {
    const progressDiv = document.getElementById('progress-indicator');
    if (progressDiv) {
        progressDiv.style.display = 'none';
    }
}

function createProgressIndicator() {
    const div = document.createElement('div');
    div.id = 'progress-indicator';
    div.className = 'progress-indicator';
    document.body.appendChild(div);
    return div;
}

function showNotification(message, type = 'info') {
    const notificationDiv = document.createElement('div');
    notificationDiv.className = `notification notification-${type}`;
    notificationDiv.textContent = message;
    
    document.body.appendChild(notificationDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notificationDiv.remove();
    }, 5000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize PDF upload if on new building page
    if (window.location.pathname === '/buildings/new') {
        initPDFUpload();
    }
});

// Export functions
window.buildings = {
    createBuilding,
    updateBuilding,
    deleteBuilding,
    starBuilding,
    uploadFile,
    initPDFUpload
};