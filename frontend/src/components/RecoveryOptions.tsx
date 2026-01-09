import React from 'react';

interface RecoveryOptionsProps {
  errorType: 'email_verification' | 'slug_taken' | 'rate_limit' | 'token_expired';
  onResendEmail?: () => void;
  onSuggestSlug?: () => void;
  onRetry?: () => void;
  retryAfter?: number;
}

const RecoveryOptions: React.FC<RecoveryOptionsProps> = ({
  errorType,
  onResendEmail,
  onSuggestSlug,
  onRetry,
  retryAfter,
}) => {
  const renderRecovery = () => {
    switch (errorType) {
      case 'email_verification':
        return (
          <div className="mt-3 p-3 bg-gray-800 rounded border border-gray-700">
            <p className="text-xs text-gray-400 mb-2">
              Didn't receive the email?
            </p>
            <button
              onClick={onResendEmail}
              className="text-xs text-blue-400 hover:text-blue-300 underline"
            >
              Resend verification email
            </button>
            <p className="text-xs text-gray-500 mt-2">
              Check your spam folder if you don't see it.
            </p>
          </div>
        );

      case 'slug_taken':
        return (
          <div className="mt-3 p-3 bg-gray-800 rounded border border-gray-700">
            <p className="text-xs text-gray-400 mb-2">
              Need help choosing a slug?
            </p>
            <button
              onClick={onSuggestSlug}
              className="text-xs text-blue-400 hover:text-blue-300 underline"
            >
              Get suggestions
            </button>
          </div>
        );

      case 'token_expired':
        return (
          <div className="mt-3 p-3 bg-gray-800 rounded border border-gray-700">
            <p className="text-xs text-gray-400 mb-2">
              Verification link expired?
            </p>
            <button
              onClick={onResendEmail}
              className="text-xs text-blue-400 hover:text-blue-300 underline"
            >
              Send new verification email
            </button>
          </div>
        );

      case 'rate_limit':
        return (
          <div className="mt-3 p-3 bg-gray-800 rounded border border-gray-700">
            <p className="text-xs text-gray-400 mb-2">
              {retryAfter
                ? `Too many requests. Try again in ${retryAfter} seconds.`
                : 'Too many requests?'}
            </p>
            {onRetry && !retryAfter && (
              <button
                onClick={onRetry}
                className="text-xs text-blue-400 hover:text-blue-300 underline"
              >
                Try again later
              </button>
            )}
            {retryAfter && (
              <p className="text-xs text-gray-500 mt-2">
                Or{' '}
                <a
                  href="mailto:support@example.com"
                  className="text-blue-400 hover:text-blue-300 underline"
                >
                  contact support
                </a>{' '}
                if this persists.
              </p>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return <>{renderRecovery()}</>;
};

export default RecoveryOptions;

