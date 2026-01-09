import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateEmailFormat } from '../utils/emailValidation';
import ErrorDisplay from './ErrorDisplay';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [emailTouched, setEmailTouched] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleEmailChange = (value: string) => {
    setEmail(value);
    setEmailTouched(true);
    
    if (value) {
      const validation = validateEmailFormat(value);
      setEmailError(validation.message);
    } else {
      setEmailError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Validate email
    if (!email.trim()) {
      setEmailError('Email is required');
      setEmailTouched(true);
      return;
    }

    const emailValidation = validateEmailFormat(email);
    if (!emailValidation.valid) {
      setEmailError(emailValidation.message);
      setEmailTouched(true);
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/onboarding/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send password reset email');
      }

      // Show success message (generic for security)
      setSuccess(data.message || 'If an account exists with this email, a password reset email has been sent.');
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/admin/login');
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to send password reset email. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
      <div className="max-w-md w-full bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-semibold text-white">
              Forgot Password
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Enter your email address and we'll send you a link to reset your password.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/admin/login')}
            className="text-xs text-gray-400 hover:text-gray-200"
          >
            ← Back to Login
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Email address
            </label>
            <div className="relative">
              <input
                type="email"
                value={email}
                onChange={(e) => handleEmailChange(e.target.value)}
                onBlur={() => setEmailTouched(true)}
                required
                className={`w-full px-3 py-2 pr-10 rounded-lg bg-gray-900 border text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  emailError
                    ? 'border-red-500'
                    : emailTouched && email && !emailError
                    ? 'border-green-500'
                    : 'border-gray-700'
                }`}
                placeholder="admin@hospital.com"
              />
              {emailTouched && email && !emailError && (
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

          <ErrorDisplay
            error={error}
            onDismiss={() => setError(null)}
          />

          {success && (
            <div className="text-sm text-green-400 bg-emerald-950/40 border border-emerald-800 px-3 py-2 rounded-lg">
              {success}
              <p className="text-xs text-gray-400 mt-1">
                Redirecting to login page...
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !!emailError || !email.trim()}
            className="w-full mt-2 inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Sending...' : 'Send Reset Link'}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => navigate('/admin/login')}
              className="text-xs text-gray-400 hover:text-gray-200"
            >
              Remember your password? Sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ForgotPassword;

