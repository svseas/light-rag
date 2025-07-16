/**
 * Firebase Authentication Manager for LightRAG
 * Handles Firebase authentication through backend REST API
 */

class AuthManager {
    constructor() {
        this.token = localStorage.getItem('authToken');
        this.user = null;
        this.baseURL = '/api/auth';
        this.refreshToken = localStorage.getItem('refreshToken');
    }

    /**
     * Authenticate user with email and password via Firebase
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise<Object>} Authentication result
     */
    async login(email, password) {
        try {
            const response = await fetch(`${this.baseURL}/signin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store Firebase ID token
                this.token = data.token;
                this.user = data.user;
                
                localStorage.setItem('authToken', this.token);
                if (data.refreshToken) {
                    localStorage.setItem('refreshToken', data.refreshToken);
                }
                
                // Redirect to main app
                setTimeout(() => {
                    window.location.href = '/main';
                }, 500);
                
                return { success: true, message: 'Login successful' };
            } else {
                // Handle Firebase error messages
                let errorMessage = 'Login failed';
                
                if (data.message) {
                    switch (data.message) {
                        case 'EMAIL_NOT_FOUND':
                            errorMessage = 'No account found with this email address';
                            break;
                        case 'INVALID_PASSWORD':
                            errorMessage = 'Invalid password';
                            break;
                        case 'USER_DISABLED':
                            errorMessage = 'This account has been disabled';
                            break;
                        case 'TOO_MANY_ATTEMPTS_TRY_LATER':
                            errorMessage = 'Too many failed attempts. Please try again later';
                            break;
                        case 'INVALID_LOGIN_CREDENTIALS':
                            errorMessage = 'Invalid email or password';
                            break;
                        default:
                            errorMessage = data.message;
                    }
                }
                
                return { 
                    success: false, 
                    message: errorMessage 
                };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { 
                success: false, 
                message: 'Network error. Please check your connection and try again.' 
            };
        }
    }

    /**
     * Register new user account via Firebase
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise<Object>} Registration result
     */
    async register(email, password) {
        try {
            console.log('Attempting to register with:', { email, password: '***' });
            
            const response = await fetch(`${this.baseURL}/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            console.log('Registration response status:', response.status);
            const data = await response.json();
            console.log('Registration response data:', data);

            if (response.ok && data.success) {
                // Don't store token or redirect automatically for registration
                // User needs to verify email first
                return { 
                    success: true, 
                    message: data.message || 'Registration successful',
                    requiresVerification: true 
                };
            } else {
                // Handle Firebase error messages
                let errorMessage = 'Registration failed';
                
                if (data.message) {
                    switch (data.message) {
                        case 'EMAIL_EXISTS':
                            errorMessage = 'An account with this email already exists. You may need to verify your email.';
                            break;
                        case 'WEAK_PASSWORD':
                            errorMessage = 'Password is too weak. Please choose a stronger password';
                            break;
                        case 'INVALID_EMAIL':
                            errorMessage = 'Invalid email address';
                            break;
                        default:
                            errorMessage = data.message;
                    }
                }
                
                return { 
                    success: false, 
                    message: errorMessage,
                    originalError: data.message 
                };
            }
        } catch (error) {
            console.error('Registration error:', error);
            return { 
                success: false, 
                message: 'Network error. Please check your connection and try again.' 
            };
        }
    }

    /**
     * Verify current Firebase ID token
     * @returns {Promise<boolean>} True if token is valid
     */
    async verifyToken() {
        if (!this.token) {
            return false;
        }

        try {
            const response = await fetch(`${this.baseURL}/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: this.token })
            });

            if (response.ok) {
                const userData = await response.json();
                this.user = userData;
                return true;
            } else {
                // Token is invalid or expired
                await this.logout();
                return false;
            }
        } catch (error) {
            console.error('Token verification error:', error);
            await this.logout();
            return false;
        }
    }

    /**
     * Get current user profile
     * @returns {Promise<Object|null>} User profile data
     */
    async getProfile() {
        if (!this.token) {
            return null;
        }

        try {
            const response = await fetch(`${this.baseURL}/profile`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                this.user = userData;
                return userData;
            } else if (response.status === 401) {
                // Token expired, try to refresh or logout
                await this.logout();
                return null;
            } else {
                return null;
            }
        } catch (error) {
            console.error('Profile fetch error:', error);
            return null;
        }
    }

    /**
     * Log out current user
     */
    logout() {
        try {
            // Clear local storage
            this.token = null;
            this.user = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('refreshToken');
            
            // Show logout message
            if (typeof showToast === 'function') {
                showToast('Logged out successfully', 'success');
            }
            
            // Redirect to login page after a brief delay
            setTimeout(() => {
                window.location.href = '/login';
            }, 500);
        } catch (error) {
            console.error('Logout error:', error);
            // Force redirect even if error occurs
            window.location.href = '/login';
        }
    }

    /**
     * Check if user is authenticated
     * @returns {boolean} True if authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Get current user data
     * @returns {Object|null} User data or null
     */
    getCurrentUser() {
        return this.user;
    }

    /**
     * Get Firebase ID token
     * @returns {string|null} Firebase ID token
     */
    getToken() {
        return this.token;
    }

    /**
     * Make authenticated API request with Firebase token
     * @param {string} url - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Response>} Fetch response
     */
    async authenticatedFetch(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        if (this.token) {
            defaultOptions.headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            ...defaultOptions
        });

        // Handle authentication errors
        if (response.status === 401) {
            await this.logout();
            throw new Error('Authentication required');
        }

        return response;
    }

    /**
     * Get user display name or email
     * @returns {string} User display name or email
     */
    getDisplayName() {
        if (this.user) {
            return this.user.email || 'User';
        }
        return 'User';
    }

    /**
     * Check if user's email is verified
     * @returns {boolean} True if email is verified
     */
    isEmailVerified() {
        return this.user?.email_verified || false;
    }
}

// Create global instance
window.AuthManager = new AuthManager();
// Also create global reference for direct access
globalThis.AuthManager = window.AuthManager;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.AuthManager;
}

// Auto-verify token on page load for authenticated pages
document.addEventListener('DOMContentLoaded', async function() {
    // Skip verification on login page
    if (window.location.pathname === '/login') {
        return;
    }

    // For protected pages, verify authentication
    if (window.AuthManager.isAuthenticated()) {
        const isValid = await window.AuthManager.verifyToken();
        if (!isValid) {
            // Token is invalid, will be redirected by logout()
            return;
        }
    } else {
        // No token, redirect to login
        window.location.href = '/login';
        return;
    }

    // Load user profile for authenticated users
    await window.AuthManager.getProfile();
});

// Handle token expiration globally
window.addEventListener('storage', function(e) {
    if (e.key === 'authToken' && !e.newValue) {
        // Token was removed from another tab
        window.location.href = '/login';
    }
});

// Enhanced fetch interceptor for Firebase token handling
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    // Only add auth header to our API requests
    if (url.startsWith('/api/') && window.AuthManager.isAuthenticated()) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${window.AuthManager.getToken()}`;
    }
    
    return originalFetch(url, options)
        .then(response => {
            // Handle global authentication errors
            if (response.status === 401 && window.AuthManager.isAuthenticated()) {
                window.AuthManager.logout();
                throw new Error('Authentication expired');
            }
            return response;
        })
        .catch(error => {
            // Handle network errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                console.error('Network error:', error);
                throw new Error('Network error. Please check your connection.');
            }
            throw error;
        });
};

// Utility function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        console.log(`Toast: ${message} (${type})`);
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Remove toast after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

// Make showToast globally available
window.showToast = showToast;