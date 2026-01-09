import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import PasswordStrengthMeter from './PasswordStrengthMeter';
import ErrorDisplay from './ErrorDisplay';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const status = searchParams.get('status') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [confirmPasswordTouched, setConfirmPasswordTouched] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);

  // Check token validity on mount
  useEffect(() => {
    if (!token) {
      setTokenValid(false);
      setError('No reset token provided. Please request a new password reset.');
      return;
    }

    // Check status from URL
    if (status === 'invalid' || status === 'expired' || status === 'already_used') {
      setTokenValid(false);
      const errorParam = searchParams.get('error') || 'Invalid or expired reset token';
      setError(errorParam);
      return;
    }

    if (status === 'valid') {
      setTokenValid(true);
      return;
    }

    // If no status, assume valid (will be validated on submit)
    setTokenValid(true);
  }, [token, status, searchParams]);

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    setPasswordTouched(true);
    
    if (value.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
    } else {
      setPasswordError('');
    }

    // Check confirm password match
    if (confirmPassword && value !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
    } else if (confirmPassword) {
      setConfirmPasswordError('');
    }
  };

  const handleConfirmPasswordChange = (value: string) => {
    setConfirmPassword(value);
    setConfirmPasswordTouched(true);
    
    if (password && value !== password) {
      setConfirmPasswordError('Passwords do not match');
    } else {
      setConfirmPasswordError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Validate
    if (!password) {
      setPasswordError('Password is required');
      setPasswordTouched(true);
      return;
    }

    if (password.length < 8) {
      setPasswordError('Password must be at least 8 characters long');
      setPasswordTouched(true);
      return;
    }

    if (password !== confirmPassword) {
      setConfirmPasswordError('Passwords do not match');
      setConfirmPasswordTouched(true);
      return;
    }

    if (!token) {
      setError('No reset token provided. Please request a new password reset.');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/onboarding/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token,
          new_password: password,
        }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to reset password');
      }

      setSuccess(data.message || 'Password has been reset successfully.');
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/admin/login', { state: { message: 'Password reset successful. Please log in with your new password.' } });
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to reset password. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (tokenValid === false) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
        <div className="max-w-md w-full bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl p-6 sm:p-8">
          <div className="text-center">
            <div className="mb-4">
              <svg
                className="h-12 w-12 text-red-400 mx-auto"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h1 className="text-xl sm:text-2xl font-semibold text-white mb-2">
              Invalid Reset Link
            </h1>
            <p className="text-gray-400 text-sm mb-6">
              {error || 'This password reset link is invalid or has expired.'}
            </p>
            <button
              onClick={() => navigate('/onboarding/forgot-password')}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 transition-colors"
            >
              Request New Reset Link
            </button>
            <div className="mt-4">
              <button
                onClick={() => navigate('/admin/login')}
                className="text-xs text-gray-400 hover:text-gray-200"
              >
                Back to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
      <div className="max-w-md w-full bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl p-6 sm:p-8">
        <div className="mb-4">
          <h1 className="text-xl sm:text-2xl font-semibold text-white">
            Reset Password
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Enter your new password below.
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              New Password
            </label>
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => handlePasswordChange(e.target.value)}
                onFocus={() => setPasswordTouched(true)}
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
            <PasswordStrengthMeter password={password} showStrength={true} />
            <p className="mt-1 text-xs text-gray-500">
              At least 8 characters. Use a strong, unique password.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Confirm Password
            </label>
            <div className="relative">
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => handleConfirmPasswordChange(e.target.value)}
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
            disabled={
              isSubmitting ||
              !!passwordError ||
              !!confirmPasswordError ||
              !password ||
              !confirmPassword
            }
            className="w-full mt-2 inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Resetting Password...' : 'Reset Password'}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => navigate('/admin/login')}
              className="text-xs text-gray-400 hover:text-gray-200"
            >
              Back to Login
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;

