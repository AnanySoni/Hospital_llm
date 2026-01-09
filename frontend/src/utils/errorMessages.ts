/**
 * Centralized error message mapping and parsing
 */

export const ERROR_MESSAGES = {
  // Registration errors
  EMAIL_ALREADY_REGISTERED: 'This email is already registered. Please log in instead.',
  COMPANY_NAME_TAKEN: 'This company name is already registered. Please use a different name.',
  GOOGLE_ACCOUNT_EXISTS: 'This Google account is already registered. Please log in instead.',

  // Slug errors
  SLUG_TAKEN: (suggestions: string[]) =>
    `This slug is already taken. ${
      suggestions.length > 0
        ? `Try: ${suggestions[0]}`
        : 'Please choose another.'
    }`,
  SLUG_RESERVED: (slug: string) =>
    `"${slug}" is a reserved word and cannot be used. Please choose another.`,
  SLUG_INVALID_FORMAT:
    'Slug can only contain lowercase letters, numbers, and hyphens.',

  // Verification errors
  TOKEN_EXPIRED: "Verification link expired. We'll send a new one.",
  TOKEN_ALREADY_USED: 'This verification link has already been used.',
  TOKEN_INVALID: 'Invalid verification link. Please request a new one.',

  // Rate limiting
  RATE_LIMIT_EXCEEDED: (retryAfter?: number) =>
    `Too many requests. ${
      retryAfter
        ? `Please try again in ${retryAfter} seconds.`
        : 'Please try again later.'
    }`,

  // Network errors
  NETWORK_ERROR:
    'Network error. Please check your connection and try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
};

/**
 * Parse error from API response or error object
 */
export const parseError = (error: any): string => {
  if (typeof error === 'string') return error;
  if (error?.detail) return error.detail;
  if (error?.message) return error.message;
  return ERROR_MESSAGES.SERVER_ERROR;
};

/**
 * Get error type for recovery options
 */
export const getErrorType = (error: string): string | null => {
  const lowerError = error.toLowerCase();
  
  if (lowerError.includes('verification') || lowerError.includes('token')) {
    return 'email_verification';
  }
  if (lowerError.includes('slug') && lowerError.includes('taken')) {
    return 'slug_taken';
  }
  if (lowerError.includes('rate limit') || lowerError.includes('too many')) {
    return 'rate_limit';
  }
  if (lowerError.includes('expired')) {
    return 'token_expired';
  }
  
  return null;
};

