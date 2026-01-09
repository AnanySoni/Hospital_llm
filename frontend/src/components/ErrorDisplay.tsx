import React, { useEffect } from 'react';

interface ErrorDisplayProps {
  error: string | null;
  onDismiss?: () => void;
  recoveryAction?: {
    label: string;
    onClick: () => void;
  };
  autoDismiss?: boolean;
  dismissDelay?: number;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onDismiss,
  recoveryAction,
  autoDismiss = false,
  dismissDelay = 10000,
}) => {
  useEffect(() => {
    if (autoDismiss && error && onDismiss) {
      const timer = setTimeout(() => {
        onDismiss();
      }, dismissDelay);
      return () => clearTimeout(timer);
    }
  }, [autoDismiss, error, dismissDelay, onDismiss]);

  if (!error) return null;

  return (
    <div className="bg-red-950/40 border border-red-800 rounded-lg p-4 mb-4">
      <div className="flex items-start gap-3">
        <svg
          className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5"
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
        <div className="flex-1">
          <p className="text-sm text-red-400">{error}</p>
          {recoveryAction && (
            <button
              onClick={recoveryAction.onClick}
              className="mt-2 text-xs text-red-300 hover:text-red-200 underline"
            >
              {recoveryAction.label}
            </button>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-red-400 hover:text-red-300 flex-shrink-0"
            aria-label="Dismiss error"
          >
            <svg
              className="h-4 w-4"
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
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorDisplay;

