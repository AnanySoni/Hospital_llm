/**
 * Email validation utilities
 */

const TEMP_EMAIL_DOMAINS = [
  'tempmail.com',
  '10minutemail.com',
  'guerrillamail.com',
  'mailinator.com',
  'throwaway.email',
  'temp-mail.org',
  'mohmal.com',
  'fakeinbox.com',
  'trashmail.com',
];

export interface EmailValidationResult {
  valid: boolean;
  message: string;
  isTemporary?: boolean;
}

/**
 * Validate email format (client-side)
 */
export const validateEmailFormat = (email: string): EmailValidationResult => {
  if (!email) {
    return { valid: false, message: '' };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return {
      valid: false,
      message: 'Please enter a valid email address',
    };
  }

  // Check for temporary email domains
  const domain = email.split('@')[1]?.toLowerCase();
  if (domain && TEMP_EMAIL_DOMAINS.includes(domain)) {
    return {
      valid: false,
      message: 'Temporary email addresses are not allowed',
      isTemporary: true,
    };
  }

  return { valid: true, message: '' };
};

/**
 * Check if email is duplicate (requires API call)
 */
export const checkEmailDuplicate = async (
  email: string,
  apiBase: string
): Promise<EmailValidationResult> => {
  try {
    const response = await fetch(
      `${apiBase}/onboarding/check-email?email=${encodeURIComponent(email)}`
    );
    const data = await response.json();
    
    if (data.exists) {
      return {
        valid: false,
        message: 'This email is already registered. Please log in instead.',
      };
    }
    
    return { valid: true, message: '' };
  } catch (error) {
    // Don't block on network errors, let backend handle it
    return { valid: true, message: '' };
  }
};

