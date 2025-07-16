/**
 * Main Application JavaScript for LightRAG
 * Handles global app functionality and utilities
 */

// Global app configuration
const AppConfig = {
    apiBaseURL: '/api',
    maxFileSize: 5 * 1024 * 1024, // 5MB
    maxFiles: 5,
    allowedFileTypes: ['.pdf', '.docx', '.txt', '.md'],
    toastDuration: 5000
};

// Application state management
class AppState {
    constructor() {
        this.user = null;
        this.project = null;
        this.documents = [];
        this.entities = [];
        this.relationships = [];
        this.chatHistory = [];
        this.isProcessing = false;
        this.status = 'Idle';
    }

    setState(newState) {
        Object.assign(this, newState);
        this.notifyStateChange();
    }

    notifyStateChange() {
        // Emit custom event for components to listen to
        document.dispatchEvent(new CustomEvent('appStateChanged', {
            detail: { state: this }
        }));
    }

    getState() {
        return { ...this };
    }
}

// Global app state
const appState = new AppState();

// Utility functions
const Utils = {
    /**
     * Format file size in human readable format
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted size string
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Format date in human readable format
     * @param {string|Date} date - Date to format
     * @returns {string} Formatted date string
     */
    formatDate(date) {
        const d = new Date(date);
        return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
    },

    /**
     * Truncate text to specified length
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text
     */
    truncateText(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    /**
     * Validate file type
     * @param {File} file - File to validate
     * @returns {boolean} True if valid
     */
    validateFileType(file) {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        return AppConfig.allowedFileTypes.includes(extension);
    },

    /**
     * Validate file size
     * @param {File} file - File to validate
     * @returns {boolean} True if valid
     */
    validateFileSize(file) {
        return file.size <= AppConfig.maxFileSize;
    },

    /**
     * Generate unique ID
     * @returns {string} Unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} delay - Delay in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, delay) {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    },

    /**
     * Escape HTML characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>} True if successful
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy text:', err);
            return false;
        }
    }
};

// Toast notification system
class ToastManager {
    constructor() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.createContainer();
        }
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = AppConfig.toastDuration) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        this.container.appendChild(toast);

        // Auto-remove toast
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }
        }, duration);

        // Allow manual dismissal
        toast.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });

        return toast;
    }

    success(message, duration) {
        return this.show(message, 'success', duration);
    }

    error(message, duration) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Global toast manager
const toastManager = new ToastManager();

// Make toast manager globally available
window.showToast = (message, type, duration) => {
    toastManager.show(message, type, duration);
};

// Loading state management
class LoadingManager {
    constructor() {
        this.overlay = document.getElementById('loading-overlay');
        this.activeRequests = new Set();
    }

    show(requestId = null) {
        if (requestId) {
            this.activeRequests.add(requestId);
        }
        
        if (this.overlay) {
            this.overlay.style.display = 'flex';
        }
        
        appState.setState({ isProcessing: true });
    }

    hide(requestId = null) {
        if (requestId) {
            this.activeRequests.delete(requestId);
        }
        
        // Only hide if no active requests
        if (this.activeRequests.size === 0) {
            if (this.overlay) {
                this.overlay.style.display = 'none';
            }
            appState.setState({ isProcessing: false });
        }
    }

    isLoading() {
        return this.activeRequests.size > 0;
    }
}

// Global loading manager
const loadingManager = new LoadingManager();

// API helper functions
const API = {
    /**
     * Make authenticated API request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise<Response>} Response object
     */
    async request(endpoint, options = {}) {
        const url = `${AppConfig.apiBaseURL}${endpoint}`;
        const requestId = Utils.generateId();
        
        loadingManager.show(requestId);
        
        try {
            const response = await window.AuthManager.authenticatedFetch(url, options);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        } finally {
            loadingManager.hide(requestId);
        }
    },

    /**
     * GET request
     * @param {string} endpoint - API endpoint
     * @returns {Promise<Object>} Response data
     */
    async get(endpoint) {
        const response = await this.request(endpoint, { method: 'GET' });
        return response.json();
    },

    /**
     * POST request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request data
     * @returns {Promise<Object>} Response data
     */
    async post(endpoint, data) {
        const response = await this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response.json();
    },

    /**
     * PUT request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request data
     * @returns {Promise<Object>} Response data
     */
    async put(endpoint, data) {
        const response = await this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return response.json();
    },

    /**
     * DELETE request
     * @param {string} endpoint - API endpoint
     * @returns {Promise<Object>} Response data
     */
    async delete(endpoint) {
        const response = await this.request(endpoint, { method: 'DELETE' });
        return response.json();
    },

    /**
     * Upload file
     * @param {string} endpoint - API endpoint
     * @param {FormData} formData - Form data with file
     * @returns {Promise<Object>} Response data
     */
    async upload(endpoint, formData) {
        const url = `${AppConfig.apiBaseURL}${endpoint}`;
        const requestId = Utils.generateId();
        
        loadingManager.show(requestId);
        
        try {
            const response = await AuthManager.authenticatedFetch(url, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            return response.json();
        } catch (error) {
            console.error('Upload failed:', error);
            throw error;
        } finally {
            loadingManager.hide(requestId);
        }
    }
};

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    // Don't show toast for navigation errors
    if (e.error && e.error.message && e.error.message.includes('Navigation')) {
        return;
    }
    toastManager.error('An unexpected error occurred. Please try again.');
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    // Don't show toast for authentication errors
    if (e.reason && e.reason.message && e.reason.message.includes('Authentication')) {
        return;
    }
    toastManager.error('An unexpected error occurred. Please try again.');
});

// Initialize app on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize HTMX error handling
    if (typeof htmx !== 'undefined') {
        htmx.on('htmx:responseError', function(evt) {
            const xhr = evt.detail.xhr;
            if (xhr.status === 401) {
                AuthManager.logout();
            } else {
                toastManager.error('Request failed. Please try again.');
            }
        });

        htmx.on('htmx:sendError', function(evt) {
            toastManager.error('Network error. Please check your connection.');
        });
    }

    // Initialize keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('message-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.active');
            modals.forEach(modal => {
                modal.classList.remove('active');
            });
        }
    });

    console.log('LightRAG App initialized');
});

// Export utilities for global use
window.Utils = Utils;
window.API = API;
window.appState = appState;
window.loadingManager = loadingManager;
window.toastManager = toastManager;