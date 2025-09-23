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

        // Show immediate thinking state
        showClassificationThinking();

        // Debounce classification requests (reduced delay)
        classificationTimeout = setTimeout(() => {
            classifyStatement(statement);
        }, 300);
    });

    /**
     * Show immediate classification thinking state
     */
    function showClassificationThinking() {
        statementType.textContent = 'Analyzing...';
        classificationDescription.textContent = 'Determining statement type and appropriate agents';
        classificationPreview.style.display = 'block';

        // Update alert class to show thinking state
        const alertDiv = classificationPreview.querySelector('.alert');
        alertDiv.className = 'alert alert-light';

        // Add spinner icon
        statementType.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
    }

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
        e.preventDefault(); // Prevent form submission

        // Add loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing Statement...';
        document.body.classList.add('loading');

        // Show progress indicator
        showProgressIndicator();

        // Submit via AJAX
        submitFormViaAjax(form);
    });

    /**
     * Submit form via AJAX to avoid page refresh
     */
    function submitFormViaAjax(form) {
        const formData = new FormData(form);

        fetch('/fact-check', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            // Hide thinking overlay
            const overlay = document.getElementById('thinking-overlay');
            if (overlay) overlay.remove();

            // Parse response and update results section
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newResults = doc.querySelector('.card.shadow-sm:last-child');
            const errorAlert = doc.querySelector('.alert-danger');

            // Remove existing results
            const existingResults = document.querySelector('.card.shadow-sm:last-child');
            if (existingResults && existingResults.querySelector('.card-title').textContent.includes('Fact-Check Results')) {
                existingResults.remove();
            }

            // Add new results or error
            const container = document.querySelector('.col-lg-8');
            if (newResults) {
                container.appendChild(newResults);
            } else if (errorAlert) {
                container.appendChild(errorAlert);
            }

            // Reset form
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-search me-2"></i>Fact-Check Statement';
            document.body.classList.remove('loading');
        })
        .catch(error => {
            console.error('Fact-check request failed:', error);

            // Hide overlay and show error
            const overlay = document.getElementById('thinking-overlay');
            if (overlay) overlay.remove();

            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-search me-2"></i>Fact-Check Statement';
            document.body.classList.remove('loading');

            showToast('Fact-check request failed. Please try again.', 'danger');
        });
    }
}

/**
 * Show progress indicator during fact-checking
 */
function showProgressIndicator() {
    // Create persistent overlay
    const overlay = document.createElement('div');
    overlay.id = 'thinking-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        z-index: 10000;
        display: flex;
        justify-content: center;
        align-items: center;
    `;

    overlay.innerHTML = `
        <div class="card border-0 shadow-lg" style="min-width: 300px;">
            <div class="card-body text-center py-4">
                <div class="mb-3">
                    <i class="fas fa-search fa-3x text-primary"></i>
                </div>
                <p class="card-text text-muted mb-3">
                    Analyzing your statement using AI agents
                </p>
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
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