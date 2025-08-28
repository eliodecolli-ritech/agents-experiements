// Fact-Checker Application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize components
    initializeStatementClassification();
    initializeFormSubmission();
    initializeTooltips();
    
    console.log('Fact-Checker UI initialized');
});

/**
 * Initialize real-time statement classification
 */
function initializeStatementClassification() {
    const statementTextarea = document.getElementById('statement');
    const classificationPreview = document.getElementById('classificationPreview');
    const statementType = document.getElementById('statementType');
    const classificationDescription = document.getElementById('classificationDescription');
    
    if (!statementTextarea || !classificationPreview) return;
    
    let classificationTimeout;
    
    statementTextarea.addEventListener('input', function() {
        const statement = this.value.trim();
        
        // Clear previous timeout
        clearTimeout(classificationTimeout);
        
        // Hide preview if statement is too short
        if (statement.length < 10) {
            classificationPreview.style.display = 'none';
            return;
        }
        
        // Debounce classification requests
        classificationTimeout = setTimeout(() => {
            classifyStatement(statement);
        }, 1000);
    });
    
    /**
     * Classify statement via AJAX
     */
    function classifyStatement(statement) {
        fetch('/classify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ statement: statement })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.warn('Classification error:', data.error);
                classificationPreview.style.display = 'none';
                return;
            }
            
            // Update UI with classification result
            const type = data.statement_type || 'unknown';
            const method = data.classification_method || 'unknown';
            
            statementType.textContent = formatStatementType(type);
            classificationDescription.textContent = getClassificationDescription(type, method);
            classificationPreview.style.display = 'block';
            
            // Update alert class based on type
            const alertDiv = classificationPreview.querySelector('.alert');
            alertDiv.className = 'alert ' + getClassificationAlertClass(type);
        })
        .catch(error => {
            console.error('Classification request failed:', error);
            classificationPreview.style.display = 'none';
        });
    }
    
    /**
     * Format statement type for display
     */
    function formatStatementType(type) {
        const typeMap = {
            'private_data': 'Private Data',
            'public_knowledge': 'Public Knowledge',
            'mixed': 'Mixed (Private + Public)',
            'unknown': 'Unknown'
        };
        return typeMap[type] || type;
    }
    
    /**
     * Get description for statement type
     */
    function getClassificationDescription(type, method) {
        const descriptions = {
            'private_data': 'Will use RAG agent to search company/employee database',
            'public_knowledge': 'Will use Wikipedia agent to verify public facts',
            'mixed': 'Will use both RAG and Wikipedia agents for comprehensive analysis',
            'unknown': 'Classification uncertain - will use all available agents'
        };
        return descriptions[type] + ` (${method} classification)`;
    }
    
    /**
     * Get Bootstrap alert class for statement type
     */
    function getClassificationAlertClass(type) {
        const classMap = {
            'private_data': 'alert-primary',
            'public_knowledge': 'alert-info',
            'mixed': 'alert-warning',
            'unknown': 'alert-secondary'
        };
        return classMap[type] || 'alert-secondary';
    }
}

/**
 * Initialize form submission with loading states
 */
function initializeFormSubmission() {
    const form = document.querySelector('form[action="/fact-check"]');
    const submitBtn = document.getElementById('factCheckBtn');
    
    if (!form || !submitBtn) return;
    
    form.addEventListener('submit', function(e) {
        // Add loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing Statement...';
        document.body.classList.add('loading');
        
        // Show progress indicator
        showProgressIndicator();
    });
}

/**
 * Show progress indicator during fact-checking
 */
function showProgressIndicator() {
    // Create progress modal or toast
    const progressToast = document.createElement('div');
    progressToast.className = 'toast align-items-center text-white bg-primary border-0';
    progressToast.style.position = 'fixed';
    progressToast.style.top = '20px';
    progressToast.style.right = '20px';
    progressToast.style.zIndex = '9999';
    
    progressToast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-spinner fa-spin me-2"></i>
                Fact-checking in progress...
            </div>
        </div>
    `;
    
    document.body.appendChild(progressToast);
    
    // Initialize and show toast
    const toast = new bootstrap.Toast(progressToast, {
        autohide: false
    });
    toast.show();
    
    // Remove toast after form submission completes
    setTimeout(() => {
        toast.hide();
        setTimeout(() => {
            if (document.body.contains(progressToast)) {
                document.body.removeChild(progressToast);
            }
        }, 300);
    }, 1000);
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Text copied to clipboard!', 'success');
    }, function(err) {
        console.error('Could not copy text: ', err);
        showToast('Failed to copy text', 'danger');
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-white bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement, {
        delay: 3000
    });
    toast.show();
    
    // Remove element after hide
    toastElement.addEventListener('hidden.bs.toast', function() {
        if (toastContainer.contains(toastElement)) {
            toastContainer.removeChild(toastElement);
        }
    });
}

/**
 * Get or create toast container
 */
function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Expand/collapse evidence content
 */
function toggleEvidence(button) {
    const card = button.closest('.card');
    const content = card.querySelector('.evidence-content');
    const icon = button.querySelector('i');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fas fa-chevron-up';
        button.textContent = ' Collapse';
        button.prepend(icon);
    } else {
        content.style.display = 'none';
        icon.className = 'fas fa-chevron-down';
        button.textContent = ' Expand';
        button.prepend(icon);
    }
}

/**
 * Format confidence as progress bar
 */
function formatConfidenceBar(confidence, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const percentage = Math.round(confidence * 100);
    const barClass = percentage > 80 ? 'bg-success' : 
                    percentage > 60 ? 'bg-info' : 
                    percentage > 40 ? 'bg-warning' : 'bg-danger';
    
    container.innerHTML = `
        <div class="progress" style="height: 20px;">
            <div class="progress-bar ${barClass}" 
                 style="width: ${percentage}%" 
                 aria-valuenow="${percentage}" 
                 aria-valuemin="0" 
                 aria-valuemax="100">
                ${percentage}%
            </div>
        </div>
    `;
}

// Export functions for global access
window.copyToClipboard = copyToClipboard;
window.toggleEvidence = toggleEvidence;
window.formatConfidenceBar = formatConfidenceBar;