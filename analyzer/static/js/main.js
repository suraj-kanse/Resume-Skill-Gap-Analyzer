// Main JavaScript for Resume Skill Gap Analyzer

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // File upload progress
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var files = this.files;
            if (files.length > 0) {
                var totalSize = 0;
                for (var i = 0; i < files.length; i++) {
                    totalSize += files[i].size;
                }
                
                // Check total size (2MB per file limit)
                var maxSize = 2 * 1024 * 1024; // 2MB
                for (var i = 0; i < files.length; i++) {
                    if (files[i].size > maxSize) {
                        alert('File "' + files[i].name + '" is too large. Maximum size is 2MB.');
                        this.value = '';
                        return;
                    }
                }
                
                // Show file info
                var fileInfo = document.getElementById('fileInfo');
                if (fileInfo) {
                    fileInfo.innerHTML = files.length + ' file(s) selected (' + 
                        (totalSize / 1024 / 1024).toFixed(2) + ' MB total)';
                }
            }
        });
    });

    // Smooth scrolling for anchor links
    var anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form validation enhancement
    var forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Dynamic search/filter
    var searchInputs = document.querySelectorAll('[data-search-target]');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var targetSelector = this.getAttribute('data-search-target');
            var targets = document.querySelectorAll(targetSelector);
            
            targets.forEach(function(target) {
                var text = target.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    target.style.display = '';
                } else {
                    target.style.display = 'none';
                }
            });
        });
    });

    // Progress bar animations
    var progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(function(bar) {
        var width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function() {
            bar.style.width = width;
            bar.style.transition = 'width 1s ease-in-out';
        }, 100);
    });

    // Copy to clipboard functionality
    var copyButtons = document.querySelectorAll('[data-copy-target]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var targetSelector = this.getAttribute('data-copy-target');
            var target = document.querySelector(targetSelector);
            
            if (target) {
                var text = target.textContent || target.value;
                navigator.clipboard.writeText(text).then(function() {
                    // Show success feedback
                    var originalText = button.textContent;
                    button.textContent = 'Copied!';
                    button.classList.add('btn-success');
                    
                    setTimeout(function() {
                        button.textContent = originalText;
                        button.classList.remove('btn-success');
                    }, 2000);
                });
            }
        });
    });

    // Auto-refresh for real-time updates
    var autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
    autoRefreshElements.forEach(function(element) {
        var interval = parseInt(element.getAttribute('data-auto-refresh')) * 1000;
        if (interval > 0) {
            setInterval(function() {
                location.reload();
            }, interval);
        }
    });

    // Skill badge interactions
    var skillBadges = document.querySelectorAll('.skill-badge');
    skillBadges.forEach(function(badge) {
        badge.addEventListener('click', function() {
            this.classList.toggle('selected');
        });
    });

    // Table row selection
    var selectableRows = document.querySelectorAll('tr[data-selectable]');
    selectableRows.forEach(function(row) {
        row.addEventListener('click', function() {
            var checkbox = this.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                this.classList.toggle('table-active', checkbox.checked);
            }
        });
    });

    // Bulk actions
    var selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            var checkboxes = document.querySelectorAll('tbody input[type="checkbox"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = selectAllCheckbox.checked;
                var row = checkbox.closest('tr');
                if (row) {
                    row.classList.toggle('table-active', checkbox.checked);
                }
            });
            updateBulkActionButtons();
        });
    }

    // Update bulk action buttons based on selection
    function updateBulkActionButtons() {
        var checkedBoxes = document.querySelectorAll('tbody input[type="checkbox"]:checked');
        var bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
        
        bulkActionButtons.forEach(function(button) {
            button.disabled = checkedBoxes.length === 0;
        });
    }

    // Individual checkbox change handler
    var individualCheckboxes = document.querySelectorAll('tbody input[type="checkbox"]');
    individualCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            var row = this.closest('tr');
            if (row) {
                row.classList.toggle('table-active', this.checked);
            }
            updateBulkActionButtons();
        });
    });

    // Loading states for forms
    var submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        var form = button.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                button.disabled = true;
                var originalText = button.innerHTML;
                button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(function() {
                    button.disabled = false;
                    button.innerHTML = originalText;
                }, 10000);
            });
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+S to save (prevent default and trigger form submit)
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            var form = document.querySelector('form');
            if (form) {
                form.submit();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            var modals = document.querySelectorAll('.modal.show');
            modals.forEach(function(modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });

    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
});

// Chart initialization function
function initializeCharts() {
    // Skill gap chart
    var skillGapChart = document.getElementById('skillGapChart');
    if (skillGapChart) {
        var ctx = skillGapChart.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Matched Skills', 'Missing Skills'],
                datasets: [{
                    data: [70, 30],
                    backgroundColor: ['#28a745', '#dc3545'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Match score trend chart
    var trendChart = document.getElementById('trendChart');
    if (trendChart) {
        var ctx = trendChart.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Average Match Score',
                    data: [65, 70, 68, 75, 72, 78],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

// Utility functions
function showToast(message, type = 'info') {
    var toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    var toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    var bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    var k = 1024;
    var sizes = ['Bytes', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function debounce(func, wait) {
    var timeout;
    return function executedFunction(...args) {
        var later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}