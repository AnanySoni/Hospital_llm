import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

type VerificationStatus = 'loading' | 'success' | 'expired' | 'invalid' | 'already_verified' | 'error';

const OnboardingVerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<VerificationStatus>('loading');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(3);
  const [resending, setResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendError, setResendError] = useState<string | null>(null);
  const [email, setEmail] = useState<string>('');

  const token = searchParams.get('token');
  const statusParam = searchParams.get('status');
  const errorParam = searchParams.get('error');
  const accessToken = searchParams.get('access_token');
  const refreshToken = searchParams.get('refresh_token');
  const expiresIn = searchParams.get('expires_in');

  useEffect(() => {
    // Backend redirects to this page with status parameter, so read from URL
    if (statusParam) {
      if (statusParam === 'success') {
        setStatus('success');

        // Store tokens for subsequent authenticated onboarding steps
        if (accessToken) {
          window.localStorage.setItem('access_token', accessToken);
        }
        if (refreshToken) {
          window.localStorage.setItem('refresh_token', refreshToken);
        }
        if (expiresIn) {
          window.localStorage.setItem('access_token_expires_in', expiresIn);
        }

        // Start countdown
        const timer = setInterval(() => {
          setCountdown((prev) => {
            if (prev <= 1) {
              clearInterval(timer);
              // Redirect directly to hospital info step
              navigate('/onboarding/hospital-info');
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
        return () => clearInterval(timer);
      } else if (statusParam === 'expired') {
        setStatus('expired');
        setErrorMessage(errorParam || 'This verification link has expired.');
      } else if (statusParam === 'already_verified') {
        setStatus('already_verified');
      } else if (statusParam === 'invalid') {
        setStatus('invalid');
        setErrorMessage(errorParam || 'This verification link is invalid or has already been used.');
      } else if (statusParam === 'error') {
        setStatus('error');
        setErrorMessage(errorParam || 'Something went wrong. Please try again.');
      }
      return;
    }

    // If no status in URL and we have a token, redirect to backend (which will redirect back with status)
    if (token) {
      window.location.href = `${API_BASE}/onboarding/verify-email?token=${encodeURIComponent(token)}`;
      return;
    }

    // No token and no status - invalid state
    setStatus('invalid');
    setErrorMessage('No verification token provided.');
  }, [token, statusParam, errorParam, navigate]);

  const handleResend = async () => {
    if (!email.trim()) {
      setResendError('Please enter your email address.');
      return;
    }

    setResending(true);
    setResendError(null);
    setResendSuccess(false);

    try {
      const response = await fetch(`${API_BASE}/onboarding/resend-verification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to resend verification email.');
      }

      setResendSuccess(true);
      setResendError(null);
    } catch (err: any) {
      setResendError(err.message || 'Failed to resend verification email. Please try again.');
      setResendSuccess(false);
    } finally {
      setResending(false);
    }
  };

  const handleContinue = () => {
    if (status === 'success' || status === 'already_verified') {
      navigate('/onboarding/hospital-info');
    } else {
      navigate('/onboarding/register');
    }
  };

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-400 text-sm">Verifying your email...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
      <div className="max-w-lg w-full bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl p-6 sm:p-8">
        {status === 'success' && (
          <>
            <div className="text-center mb-6">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-500/20 mb-4">
                <svg
                  className="h-8 w-8 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h1 className="text-2xl font-semibold text-white mb-2">
                Email Verified Successfully!
              </h1>
              <p className="text-gray-400 text-sm">
                Your email address has been verified. You can now continue with the onboarding process.
              </p>
            </div>

            <div className="bg-blue-950/40 border border-blue-800 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-300 text-center">
                Redirecting to next step in {countdown} second{countdown !== 1 ? 's' : ''}...
              </p>
            </div>

            <button
              onClick={handleContinue}
              className="w-full inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 transition-colors"
            >
              Continue to Hospital Setup
            </button>
          </>
        )}

        {status === 'already_verified' && (
          <>
            <div className="text-center mb-6">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-blue-500/20 mb-4">
                <svg
                  className="h-8 w-8 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h1 className="text-2xl font-semibold text-white mb-2">
                Email Already Verified
              </h1>
              <p className="text-gray-400 text-sm">
                This email address has already been verified. You can continue with the onboarding process.
              </p>
            </div>

            <button
              onClick={handleContinue}
              className="w-full inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 transition-colors"
            >
              Continue to Hospital Setup
            </button>
          </>
        )}

        {(status === 'expired' || status === 'invalid' || status === 'error') && (
          <>
            <div className="text-center mb-6">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-500/20 mb-4">
                <svg
                  className="h-8 w-8 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h1 className="text-2xl font-semibold text-white mb-2">
                {status === 'expired' ? 'Verification Link Expired' : 'Verification Failed'}
              </h1>
              <p className="text-gray-400 text-sm mb-4">
                {errorMessage ||
                  (status === 'expired'
                    ? 'This verification link has expired. Please request a new one.'
                    : 'This verification link is invalid or has already been used.')}
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Email address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {resendSuccess && (
                <div className="text-sm text-green-400 bg-emerald-950/40 border border-emerald-800 px-3 py-2 rounded-lg">
                  New verification email sent! Please check your inbox.
                </div>
              )}

              {resendError && (
                <div className="text-sm text-red-400 bg-red-950/40 border border-red-800 px-3 py-2 rounded-lg">
                  {resendError}
                </div>
              )}

              <button
                onClick={handleResend}
                disabled={resending || !email.trim()}
                className="w-full inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
              >
                {resending ? 'Sending...' : 'Resend Verification Email'}
              </button>

              <button
                onClick={() => navigate('/onboarding/register')}
                className="w-full inline-flex items-center justify-center px-4 py-2 rounded-lg border border-gray-700 bg-gray-900 text-gray-300 text-sm font-medium hover:bg-gray-800 transition-colors"
              >
                Back to Registration
              </button>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-800">
              <p className="text-xs text-gray-500 text-center">
                Need help? Contact our support team or{' '}
                <a
                  href="mailto:support@hospitalai.com"
                  className="text-blue-400 hover:text-blue-300 underline"
                >
                  send us an email
                </a>
                .
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default OnboardingVerifyEmail;

