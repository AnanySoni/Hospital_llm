import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface GoogleUserInfo {
  email: string;
  name?: string;
  given_name?: string;
  family_name?: string;
  picture?: string;
  google_id: string;
  verified_email?: boolean;
}

interface GoogleCallbackResponse {
  message: string;
  user_info: GoogleUserInfo;
  action: string;
}

interface RegisterResponse {
  user_id: number;
  onboarding_session_id: number;
  signup_method: 'google';
  email: string;
  company_name: string;
  requires_email_verification?: boolean;
  email_verified?: boolean;
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  expires_in?: number;
}

const OnboardingGoogleCallback: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [exchangeError, setExchangeError] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState<GoogleUserInfo | null>(null);

  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [creatingAccount, setCreatingAccount] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Use ref to persist across re-renders (prevents duplicate requests in React Strict Mode)
  const hasExchangedCode = useRef(false);
  const processedCodeRef = useRef<string | null>(null); // Track which code we've processed
  const successfulUserInfoRef = useRef<GoogleUserInfo | null>(null); // Persist successful userInfo even if component unmounts

  // Step 1: on load, read ?code from URL and ask backend to exchange it
  useEffect(() => {
    // #region agent log
    const logDebug = (message: string, data: any, hypothesisId: string) => {
      fetch('http://127.0.0.1:7242/ingest/89aa9015-f616-4ba3-aa20-47578ae7295f', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: 'OnboardingGoogleCallback.tsx:useEffect',
          message,
          data,
          timestamp: Date.now(),
          sessionId: 'debug-session',
          runId: 'oauth-debug',
          hypothesisId
        })
      }).catch(() => {});
    };
    // #endregion

    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');

    // #region agent log
    logDebug('useEffect started', {
      has_code: !!code,
      code_preview: code ? code.substring(0, 20) + '...' : null,
      code_length: code?.length || 0,
      has_state: !!state,
      state_value: state || null,
      url: window.location.href,
      has_exchanged_already: hasExchangedCode.current,
      processed_code: processedCodeRef.current,
      has_user_info: !!userInfo
    }, 'A');
    // #endregion

    if (!code) {
      setExchangeError('Missing authorization code from Google.');
      setLoading(false);
      return;
    }

    // If we already processed this exact code, skip
    if (processedCodeRef.current === code || hasExchangedCode.current) {
      // #region agent log
      logDebug('DUPLICATE REQUEST PREVENTED (useRef)', {
        code_preview: code.substring(0, 20) + '...',
        timestamp: Date.now()
      }, 'A');
      // #endregion
      setLoading(false);
      return;
    }

    // If we already have userInfo from a previous successful exchange, restore it
    if (successfulUserInfoRef.current && !userInfo) {
      // #region agent log
      logDebug('Restoring userInfo from ref', {
        user_email: successfulUserInfoRef.current.email
      }, 'A');
      // #endregion
      setUserInfo(successfulUserInfoRef.current);
      setEmail(successfulUserInfoRef.current.email);
      setLoading(false);
      return;
    }

    // If we already have userInfo in state, don't process again
    if (userInfo) {
      // #region agent log
      logDebug('Already have userInfo, skipping', {
        user_email: userInfo.email
      }, 'A');
      // #endregion
      setLoading(false);
      return;
    }

    // Mark that we're about to exchange the code
    hasExchangedCode.current = true;
    processedCodeRef.current = code;

    // Prevent duplicate calls (React strict mode or page refresh)
    let isMounted = true;
    const exchangeCode = async () => {
      const requestStartTime = Date.now();
      // #region agent log
      logDebug('Starting token exchange request', {
        code_preview: code.substring(0, 20) + '...',
        state: state || null,
        request_start_time: requestStartTime
      }, 'A');
      // #endregion

      try {
        const res = await fetch(
          `${API_BASE}/onboarding/google/callback?code=${encodeURIComponent(
            code
          )}${state ? `&state=${encodeURIComponent(state)}` : ''}`
        );
        
        // #region agent log
        const requestEndTime = Date.now();
        const requestDuration = requestEndTime - requestStartTime;
        logDebug('Received response from backend', {
          status: res.status,
          status_ok: res.ok,
          request_duration_ms: requestDuration,
          timestamp: requestEndTime
        }, 'A');
        // #endregion

        const data: GoogleCallbackResponse | { detail?: string } = await res.json();

        // #region agent log
        logDebug('Parsed response data', {
          has_user_info: !!(data as any).user_info,
          has_detail: !!(data as any).detail,
          detail_preview: (data as any).detail ? String((data as any).detail).substring(0, 100) : null,
          is_mounted: isMounted,
          res_ok: res.ok,
          res_status: res.status
        }, 'A');
        // #endregion

        if (!res.ok) {
          throw new Error(
            (data as any).detail || 'Failed to complete Google sign-in. Please try again.'
          );
        }

        const payload = data as GoogleCallbackResponse;
        
        // #region agent log
        logDebug('About to set state', {
          user_email: payload.user_info.email,
          has_google_id: !!payload.user_info.google_id,
          is_mounted: isMounted,
          payload_keys: Object.keys(payload)
        }, 'A');
        // #endregion
        
        // Store in ref first to persist even if component unmounts
        successfulUserInfoRef.current = payload.user_info;
        
        // Set state immediately - don't check isMounted here as it might be false due to React Strict Mode
        // The state update will be safe even if component unmounts
        try {
          setUserInfo(payload.user_info);
          setEmail(payload.user_info.email);
          setLoading(false); // Explicitly set loading to false on success

          // #region agent log
          logDebug('Token exchange successful - state set', {
            user_email: payload.user_info.email,
            has_google_id: !!payload.user_info.google_id,
            state_set_called: true,
            stored_in_ref: true
          }, 'A');
          // #endregion
        } catch (stateError: any) {
          // #region agent log
          logDebug('Error setting state', {
            error: stateError.message || String(stateError)
          }, 'A');
          // #endregion
          throw stateError;
        }
      } catch (err: any) {
        // #region agent log
        logDebug('Token exchange error', {
          error_message: err.message || String(err),
          error_type: err.constructor?.name || typeof err,
          is_mounted: isMounted
        }, 'A');
        // #endregion

        if (!isMounted) return; // Component unmounted, ignore error
        
        // Reset the flag on error so user can retry
        hasExchangedCode.current = false;
        setExchangeError(err.message || 'Failed to complete Google sign-in.');
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    exchangeCode();
    
    return () => {
      isMounted = false; // Cleanup: prevent state updates if component unmounts
    };
  }, []); // Empty dependency array - only run once on mount

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInfo) return;

    // Validate company name
    if (!companyName.trim()) {
      setCreateError('Company name is required.');
      return;
    }

    // Validate password (now required for Google signup)
    if (!password || password.trim().length < 8) {
      setCreateError('Password is required and must be at least 8 characters long.');
      return;
    }

    setCreateError(null);
    setSuccessMessage(null);
    setCreatingAccount(true);

    // #region agent log
    const logDebug = (message: string, data: any, hypothesisId: string) => {
      fetch('http://127.0.0.1:7242/ingest/89aa9015-f616-4ba3-aa20-47578ae7295f', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: 'OnboardingGoogleCallback.tsx:handleCreateAccount',
          message,
          data,
          timestamp: Date.now(),
          sessionId: 'debug-session',
          runId: 'oauth-debug',
          hypothesisId
        })
      }).catch(() => {});
    };
    logDebug('Starting account creation', {
      email,
      company_name: companyName,
      has_google_id: !!userInfo?.google_id
    }, 'E');
    // #endregion

    try {
      const res = await fetch(`${API_BASE}/onboarding/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          company_name: companyName,
          signup_method: 'google',
          google_id: userInfo.google_id,
          password: password, // Required for all signup methods
        }),
      });

      const data: RegisterResponse | { detail?: string } = await res.json();
      
      // #region agent log
      logDebug('Registration response received', {
        status: res.status,
        status_ok: res.ok,
        has_access_token: !!(data as any).access_token,
        email_verified: !!(data as any).email_verified
      }, 'E');
      // #endregion
      
      if (!res.ok) {
        throw new Error((data as any).detail || 'Failed to finalize registration.');
      }

      const payload = data as RegisterResponse;
      
      // #region agent log
      logDebug('Registration successful, checking redirect conditions', {
        email_verified: payload.email_verified,
        has_access_token: !!payload.access_token
      }, 'E');
      // #endregion
      
      if (payload.email_verified && payload.access_token) {
        // Store tokens so we can call authenticated onboarding endpoints
        window.localStorage.setItem('access_token', payload.access_token);
        if (payload.refresh_token) {
          window.localStorage.setItem('refresh_token', payload.refresh_token);
        }
        if (payload.expires_in) {
          window.localStorage.setItem('access_token_expires_in', String(payload.expires_in));
        }

        setSuccessMessage(
          'Your admin account is ready. Redirecting to hospital setup...'
        );
        // #region agent log
        logDebug('About to redirect to hospital-info', {
          will_navigate: true,
          target_route: '/onboarding/hospital-info'
        }, 'E');
        // #endregion
        // Small delay before navigating to hospital info step
        setTimeout(() => {
          // #region agent log
          logDebug('Executing navigation', {
            route: '/onboarding/hospital-info'
          }, 'E');
          // #endregion
          navigate('/onboarding/hospital-info');
        }, 800);
      } else {
        setSuccessMessage(
          'Account created. Please verify your email, then continue onboarding.'
        );
        // #region agent log
        logDebug('Registration successful but email not verified', {
          requires_verification: true
        }, 'E');
        // #endregion
      }
    } catch (err: any) {
      // #region agent log
      logDebug('Registration error', {
        error_message: err.message || String(err),
        error_type: err.constructor?.name || typeof err
      }, 'E');
      // #endregion
      setCreateError(err.message || 'Failed to finalize registration.');
    } finally {
      setCreatingAccount(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-400 text-sm">Completing Google sign-in...</p>
        </div>
      </div>
    );
  }

  if (exchangeError) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-gray-900 border border-red-800/60 rounded-2xl p-6">
          <h1 className="text-xl font-semibold text-red-400 mb-2">
            Google sign-in failed
          </h1>
          <p className="text-sm text-gray-300 mb-4">{exchangeError}</p>
          <button
            onClick={() => (window.location.href = '/onboarding/register')}
            className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500"
          >
            Back to onboarding
          </button>
        </div>
      </div>
    );
  }

  if (!userInfo && !loading && !exchangeError) {
    // This shouldn't happen, but show a message if it does
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-gray-400 text-sm">Processing your sign-in...</p>
          <button
            onClick={() => (window.location.href = '/onboarding/register')}
            className="mt-4 text-blue-400 hover:text-blue-300 underline"
          >
            Back to onboarding
          </button>
        </div>
      </div>
    );
  }

  if (!userInfo) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
      <div className="max-w-lg w-full bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-4">
          {userInfo.picture && (
            <img
              src={userInfo.picture}
              alt={userInfo.name || 'Google profile'}
              className="w-10 h-10 rounded-full border border-gray-700"
            />
          )}
          <div>
            <h1 className="text-xl font-semibold text-white">
              Welcome{userInfo.given_name ? `, ${userInfo.given_name}` : ''} 👋
            </h1>
            <p className="text-xs text-gray-400">
              We’ve confirmed your Google account. Now tell us about your hospital.
            </p>
          </div>
        </div>

        <form className="space-y-4" onSubmit={handleCreateAccount}>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Work email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              You can adjust this if you prefer a different admin email.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Company / Hospital name
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="City General Hospital"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Create a password <span className="text-red-400">*</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter a password (minimum 8 characters)"
            />
            <p className="mt-1 text-xs text-gray-500">
              Required for logging into the admin panel. Must be at least 8 characters long.
            </p>
          </div>

          {createError && (
            <div className="text-sm text-red-400 bg-red-950/40 border border-red-800 px-3 py-2 rounded-lg">
              {createError}
            </div>
          )}

          {successMessage && (
            <div className="text-sm text-green-400 bg-emerald-950/40 border border-emerald-800 px-3 py-2 rounded-lg">
              {successMessage}
            </div>
          )}

          <button
            type="submit"
            disabled={creatingAccount}
            className="w-full mt-2 inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            {creatingAccount ? 'Creating your admin account...' : 'Continue to hospital setup'}
          </button>
        </form>

        <p className="mt-4 text-xs text-gray-500 text-center">
          If anything looks wrong, you can cancel and restart from{' '}
          <button
            onClick={() => (window.location.href = '/onboarding/register')}
            className="text-blue-400 hover:text-blue-300 underline"
          >
            the onboarding start page
          </button>
          .
        </p>
      </div>
    </div>
  );
};

export default OnboardingGoogleCallback;


