/**
 * CSRF token utility for secure form submissions
 */

const CSRF_TOKEN_KEY = 'csrf_token';
const SESSION_ID_KEY = 'session_id';

/**
 * Get CSRF token from backend
 * Call this before making state-changing requests (POST, PUT, DELETE, PATCH)
 */
export const getCSRFToken = async (): Promise<string | null> => {
  try {
    const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
    const response = await fetch(`${API_BASE}/onboarding/csrf-token`, {
      method: 'GET',
      credentials: 'include', // Include cookies
    });

    if (!response.ok) {
      console.error('Failed to get CSRF token');
      return null;
    }

    const data = await response.json();
    
    // Store in sessionStorage for this session
    if (data.token) {
      sessionStorage.setItem(CSRF_TOKEN_KEY, data.token);
    }
    if (data.session_id) {
      sessionStorage.setItem(SESSION_ID_KEY, data.session_id);
    }

    return data.token || null;
  } catch (error) {
    console.error('Error fetching CSRF token:', error);
    return null;
  }
};

/**
 * Get stored CSRF token (from sessionStorage)
 */
export const getStoredCSRFToken = (): string | null => {
  return sessionStorage.getItem(CSRF_TOKEN_KEY);
};

/**
 * Get stored session ID
 */
export const getSessionId = (): string | null => {
  return sessionStorage.getItem(SESSION_ID_KEY);
};

/**
 * Clear CSRF token and session ID
 */
export const clearCSRFToken = (): void => {
  sessionStorage.removeItem(CSRF_TOKEN_KEY);
  sessionStorage.removeItem(SESSION_ID_KEY);
};

/**
 * Add CSRF token to fetch headers
 * Use this helper when making API calls
 */
export const addCSRFHeader = async (headers: HeadersInit = {}): Promise<HeadersInit> => {
  let token = getStoredCSRFToken();
  
  // If no token, fetch one
  if (!token) {
    token = await getCSRFToken();
  }

  const headersWithCSRF: HeadersInit = {
    ...headers,
  };

  if (token) {
    (headersWithCSRF as Record<string, string>)['X-CSRF-Token'] = token;
  }

  const sessionId = getSessionId();
  if (sessionId) {
    (headersWithCSRF as Record<string, string>)['X-Session-ID'] = sessionId;
  }

  return headersWithCSRF;
};

/**
 * Example usage:
 * 
 * const headers = await addCSRFHeader({
 *   'Content-Type': 'application/json',
 * });
 * 
 * fetch('/onboarding/register', {
 *   method: 'POST',
 *   headers,
 *   credentials: 'include',
 *   body: JSON.stringify(data),
 * });
 */

