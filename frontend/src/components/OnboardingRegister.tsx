import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDebounce } from '../hooks/useDebounce';
import { validateEmailFormat, checkEmailDuplicate } from '../utils/emailValidation';
import { parseError, getErrorType, ERROR_MESSAGES } from '../utils/errorMessages';
import ErrorDisplay from './ErrorDisplay';
import RecoveryOptions from './RecoveryOptions';
import PasswordStrengthMeter from './PasswordStrengthMeter';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

type SignupMethod = 'email' | 'google';

interface RegisterResponse {
  user_id: number;
  onboarding_session_id: number;
  signup_method: SignupMethod;
  email: string;
  company_name: string;
  requires_email_verification?: boolean;
  email_verified?: boolean;
}

const OnboardingRegister: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Field validation states
  const [emailError, setEmailError] = useState<string>('');
  const [emailTouched, setEmailTouched] = useState(false);
  const [emailDuplicateChecked, setEmailDuplicateChecked] = useState(false);
  const [passwordError, setPasswordError] = useState<string>('');
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [companyNameError, setCompanyNameError] = useState<string>('');
  const [companyNameTouched, setCompanyNameTouched] = useState(false);
  const [confirmPasswordError, setConfirmPasswordError] = useState<string>('');
  const [confirmPasswordTouched, setConfirmPasswordTouched] = useState(false);
  
  // Debounced values
  const debouncedEmail = useDebounce(email, 300);

  // Check if user was redirected here after email verification
  useEffect(() => {
    if (searchParams.get('email_verified') === 'true') {
      setSuccessMessage('Email verified successfully! You can now continue with hospital setup.');
      // Remove query parameter from URL
      window.history.replaceState({}, '', '/onboarding/register');
    }
  }, [searchParams]);

  // Real-time email format validation
  useEffect(() => {
    if (emailTouched && email) {
      const validation = validateEmailFormat(email);
      setEmailError(validation.message);
      setEmailDuplicateChecked(false); // Reset duplicate check when email changes
    } else if (!email && emailTouched) {
      setEmailError('Email is required');
    } else {
      setEmailError('');
    }
  }, [email, emailTouched]);

  // Email duplicate check on blur (debounced)
  useEffect(() => {
    if (emailTouched && debouncedEmail && !emailError) {
      const checkDuplicate = async () => {
        const result = await checkEmailDuplicate(debouncedEmail, API_BASE);
        if (!result.valid) {
          setEmailError(result.message);
        }
        setEmailDuplicateChecked(true);
      };
      checkDuplicate();
    }
  }, [debouncedEmail, emailTouched, emailError]);

  // Password validation
  useEffect(() => {
    if (passwordTouched) {
      if (!password) {
        setPasswordError('Password is required');
      } else if (password.length < 8) {
        setPasswordError('Password must be at least 8 characters long');
      } else {
        setPasswordError('');
      }
    }
  }, [password, passwordTouched]);

  // Confirm password validation
  useEffect(() => {
    if (confirmPasswordTouched) {
      if (password && confirmPassword && password !== confirmPassword) {
        setConfirmPasswordError('Passwords do not match');
      } else {
        setConfirmPasswordError('');
      }
    }
  }, [password, confirmPassword, confirmPasswordTouched]);

  // Company name validation
  useEffect(() => {
    if (companyNameTouched) {
      if (!companyName.trim()) {
        setCompanyNameError('Company name is required');
      } else if (companyName.trim().length < 2) {
        setCompanyNameError('Company name must be at least 2 characters');
      } else {
        setCompanyNameError('');
      }
    }
  }, [companyName, companyNameTouched]);

  const handleGoogleSignup = () => {
    // Redirect directly to backend Google OAuth start endpoint
    window.location.href = `${API_BASE}/onboarding/google/login`;
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    // Mark all fields as touched
    setCompanyNameTouched(true);
    setEmailTouched(true);
    setPasswordTouched(true);
    setConfirmPasswordTouched(true);

    // Validate all fields
    const errors: string[] = [];
    
    if (!companyName.trim()) {
      setCompanyNameError('Company name is required');
      errors.push('Company name');
    }
    
    if (!email.trim()) {
      setEmailError('Email is required');
      errors.push('Email');
    } else {
      const emailValidation = validateEmailFormat(email);
      if (!emailValidation.valid) {
        setEmailError(emailValidation.message);
        errors.push('Email');
      }
    }
    
    if (!password) {
      setPasswordError('Password is required');
      errors.push('Password');
    } else if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      errors.push('Password');
    }
    
    if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
      errors.push('Password confirmation');
    }

    if (!agreeTerms) {
      errors.push('Terms agreement');
    }

    if (errors.length > 0) {
      setError(`Please fix the following: ${errors.join(', ')}`);
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/onboarding/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          company_name: companyName,
          signup_method: 'email',
          password,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        const errorMsg = parseError(data);
        throw new Error(errorMsg);
      }

      const parsed: RegisterResponse = data;

      if (parsed.requires_email_verification) {
        setSuccessMessage(
          'Account created. Please check your email for a verification link before continuing onboarding.'
        );
      } else {
        setSuccessMessage('Account created successfully. You can continue to hospital setup.');
      }
    } catch (err: any) {
      const errorMsg = parseError(err);
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendEmail = async () => {
    // This will be implemented when resend verification is available
    setError('Resend email functionality coming soon');
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
      <div className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Left side: marketing / explanation */}
        <div className="text-gray-100">
          <h1 className="text-3xl sm:text-4xl font-semibold mb-4">
            Onboard your hospital to{' '}
            <span className="text-blue-500">Hospital AI Platform</span>
          </h1>
          <p className="text-gray-400 mb-6 text-sm sm:text-base">
            Create an admin account, connect your departments and doctors, and get a
            ready-to-use AI assistant that you can embed on your website in minutes.
          </p>
          <div className="space-y-3 text-sm text-gray-300">
            <div className="flex items-start gap-3">
              <span className="mt-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-xs">
                1
              </span>
              <div>
                <p className="font-medium">Create your admin account</p>
                <p className="text-gray-400">
                  Use Google or email to securely create your admin login and start onboarding.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="mt-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-xs">
                2
              </span>
              <div>
                <p className="font-medium">Set up hospital details</p>
                <p className="text-gray-400">
                  Add your hospital info, departments, and doctors in a guided step-by-step flow.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="mt-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-xs">
                3
              </span>
              <div>
                <p className="font-medium">Integrate on your website</p>
                <p className="text-gray-400">
                  Copy a small code snippet or iframe to launch the assistant on your site.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right side: registration card */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl p-6 sm:p-8">
          <h2 className="text-xl font-semibold text-white mb-2">
            Create your admin account
          </h2>
          <p className="text-gray-400 text-sm mb-6">
            Use Google for a one-click sign up or continue with email.
          </p>

          {/* Google sign-up button */}
          <button
            onClick={handleGoogleSignup}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg border border-gray-700 bg-gray-900 hover:bg-gray-800 transition-colors mb-5"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span className="text-sm font-medium text-white">
              Continue with Google
            </span>
          </button>

          <div className="flex items-center my-4">
            <div className="flex-1 h-px bg-gray-800" />
            <span className="px-3 text-xs text-gray-500 uppercase tracking-wider">
              or continue with email
            </span>
            <div className="flex-1 h-px bg-gray-800" />
          </div>

          <form className="space-y-4" onSubmit={handleEmailSubmit}>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Company / Hospital name
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => {
                    setCompanyName(e.target.value);
                    setCompanyNameTouched(true);
                  }}
                  onBlur={() => setCompanyNameTouched(true)}
                  required
                  className={`w-full px-3 py-2 pr-10 rounded-lg bg-gray-900 border text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    companyNameError
                      ? 'border-red-500'
                      : companyNameTouched && companyName
                      ? 'border-green-500'
                      : 'border-gray-700'
                  }`}
                  placeholder="City General Hospital"
                />
                {companyNameTouched && companyName && !companyNameError && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <svg
                      className="h-4 w-4 text-green-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                )}
              </div>
              {companyNameError && (
                <p className="mt-1 text-xs text-red-400">{companyNameError}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Work email
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setEmailTouched(true);
                  }}
                  onBlur={() => {
                    setEmailTouched(true);
                    if (email && !emailError) {
                      // Trigger duplicate check
                      setEmailDuplicateChecked(false);
                    }
                  }}
                  required
                  className={`w-full px-3 py-2 pr-10 rounded-lg bg-gray-900 border text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    emailError
                      ? 'border-red-500'
                      : emailTouched && email && !emailError && emailDuplicateChecked
                      ? 'border-green-500'
                      : 'border-gray-700'
                  }`}
                  placeholder="admin@hospital.com"
                />
                {emailTouched && email && !emailError && emailDuplicateChecked && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <svg
                      className="h-4 w-4 text-green-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  </div>
                )}
                {emailError && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <svg
                      className="h-4 w-4 text-red-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </div>
                )}
              </div>
              {emailError && (
                <p className="mt-1 text-xs text-red-400">{emailError}</p>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Password
                </label>
                <div className="relative">
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setPasswordTouched(true);
                    }}
                    onFocus={() => {
                      setPasswordTouched(true);
                    }}
                    onBlur={() => setPasswordTouched(true)}
                    required
                    className={`w-full px-3 py-2 pr-10 rounded-lg bg-gray-900 border text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      passwordError
                        ? 'border-red-500'
                        : passwordTouched && password && !passwordError
                        ? 'border-green-500'
                        : 'border-gray-700'
                    }`}
                    placeholder="••••••••"
                  />
                  {passwordTouched && password && !passwordError && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <svg
                        className="h-4 w-4 text-green-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </div>
                  )}
                </div>
                {passwordError && (
                  <p className="mt-1 text-xs text-red-400">{passwordError}</p>
                )}
                <PasswordStrengthMeter password={password} />
                <p className="mt-1 text-xs text-gray-500">
                  At least 8 characters. Use a strong, unique password.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Confirm password
                </label>
                <div className="relative">
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      setConfirmPasswordTouched(true);
                    }}
                    onBlur={() => setConfirmPasswordTouched(true)}
                    required
                    className={`w-full px-3 py-2 pr-10 rounded-lg bg-gray-900 border text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      confirmPasswordError
                        ? 'border-red-500'
                        : confirmPasswordTouched &&
                          confirmPassword &&
                          !confirmPasswordError
                        ? 'border-green-500'
                        : 'border-gray-700'
                    }`}
                    placeholder="••••••••"
                  />
                  {confirmPasswordTouched &&
                    confirmPassword &&
                    !confirmPasswordError && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        <svg
                          className="h-4 w-4 text-green-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    )}
                </div>
                {confirmPasswordError && (
                  <p className="mt-1 text-xs text-red-400">
                    {confirmPasswordError}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-2">
              <input
                id="agree"
                type="checkbox"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-gray-700 bg-gray-900 text-blue-600 focus:ring-blue-500"
              />
              <label
                htmlFor="agree"
                className="text-xs text-gray-400 leading-relaxed"
              >
                I agree to the Terms & Conditions and understand this is an early
                access onboarding experience.
              </label>
            </div>

            <ErrorDisplay
              error={error}
              onDismiss={() => setError(null)}
              recoveryAction={
                getErrorType(error || '')
                  ? {
                      label: 'Get help',
                      onClick: () => {
                        // Could navigate to help page or show recovery options
                      },
                    }
                  : undefined
              }
            />

            {successMessage && (
              <ErrorDisplay
                error={successMessage}
                onDismiss={() => setSuccessMessage(null)}
                autoDismiss={true}
                dismissDelay={10000}
              />
            )}

            {error && getErrorType(error) && (
              <RecoveryOptions
                errorType={getErrorType(error) as any}
                onResendEmail={handleResendEmail}
              />
            )}

            <button
              type="submit"
              disabled={
                isSubmitting ||
                !!companyNameError ||
                !!emailError ||
                !!passwordError ||
                !!confirmPasswordError ||
                !companyName.trim() ||
                !email.trim() ||
                !password ||
                !confirmPassword ||
                !agreeTerms
              }
              className="w-full mt-2 inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Creating account...' : 'Create account with email'}
            </button>
          </form>

          <p className="mt-4 text-xs text-gray-500 text-center">
            Already have an account? {/* TODO: link to admin login or future onboarding login */}
          </p>
        </div>
      </div>
    </div>
  );
};

export default OnboardingRegister;


