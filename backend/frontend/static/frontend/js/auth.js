/**
 * Authentication utility functions for frontend.
 */

/**
 * Check if JWT token exists and is valid.
 * @returns {boolean} True if token exists and is valid, false otherwise.
 */
function hasValidToken() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
        return false;
    }
    
    try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        const exp = payload.exp * 1000; // exp is in seconds, convert to milliseconds
        return exp > Date.now();
    } catch (e) {
        // Token parsing failed, remove invalid tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return false;
    }
}

/**
 * Redirect to login page if no valid token.
 */
function requireAuth() {
    if (!hasValidToken()) {
        window.location.href = '/login/';
        return false;
    }
    return true;
}

/**
 * Redirect to my page if valid token exists.
 * Used on login/signup/index pages.
 * Note: This function redirects to /me/ which will handle role-based redirection server-side.
 */
function redirectIfAuthenticated() {
    if (hasValidToken()) {
        // サーバー側でロールに応じたリダイレクトが行われるため、/me/にリダイレクト
        window.location.href = '/me/';
        return true;
    }
    return false;
}

/**
 * Clear authentication tokens.
 */
function clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

/**
 * Get access token from localStorage.
 * @returns {string|null} Access token or null if not found.
 */
function getAccessToken() {
    return localStorage.getItem('access_token');
}

/**
 * Set access token in localStorage.
 * @param {string} token Access token.
 */
function setAccessToken(token) {
    localStorage.setItem('access_token', token);
}

/**
 * Get refresh token from localStorage.
 * @returns {string|null} Refresh token or null if not found.
 */
function getRefreshToken() {
    return localStorage.getItem('refresh_token');
}

/**
 * Set refresh token in localStorage.
 * @param {string} token Refresh token.
 */
function setRefreshToken(token) {
    localStorage.setItem('refresh_token', token);
}

