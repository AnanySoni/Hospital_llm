import React, { useState, useEffect } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface PasswordStrengthMeterProps {
  password: string;
  showStrength?: boolean;
  onStrengthChange?: (strength: { score: number; level: string } | null) => void;
}

interface StrengthInfo {
  score: number;
  level: 'weak' | 'fair' | 'good' | 'strong';
}

const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({
  password,
  showStrength = true,
  onStrengthChange,
}) => {
  const [strength, setStrength] = useState<StrengthInfo | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!password || password.length < 8) {
      setStrength(null);
      if (onStrengthChange) onStrengthChange(null);
      return;
    }

    const checkStrength = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/onboarding/password/strength`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password }),
        });
        const data = await res.json();
        if (data.strength) {
          setStrength(data.strength);
          if (onStrengthChange) onStrengthChange(data.strength);
        }
      } catch (error) {
        console.error('Error checking password strength:', error);
      } finally {
        setLoading(false);
      }
    };

    const debounceTimer = setTimeout(checkStrength, 300);
    return () => clearTimeout(debounceTimer);
  }, [password, onStrengthChange]);

  // Only show when has content
  if (!showStrength || !password) return null;

  const getStrengthColor = () => {
    if (!strength) return 'bg-gray-500';
    switch (strength.level) {
      case 'weak':
        return 'bg-red-500';
      case 'fair':
        return 'bg-yellow-500';
      case 'good':
        return 'bg-blue-500';
      case 'strong':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStrengthText = () => {
    if (!strength) return '';
    switch (strength.level) {
      case 'weak':
        return 'Weak';
      case 'fair':
        return 'Fair';
      case 'good':
        return 'Good';
      case 'strong':
        return 'Strong';
      default:
        return '';
    }
  };

  const getTextColor = () => {
    if (!strength) return 'text-gray-400';
    switch (strength.level) {
      case 'weak':
        return 'text-red-400';
      case 'fair':
        return 'text-yellow-400';
      case 'good':
        return 'text-blue-400';
      case 'strong':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 mb-1">
        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getStrengthColor()}`}
            style={{
              width: strength
                ? `${(strength.score / 4) * 100}%`
                : password.length >= 8
                ? '25%'
                : '0%',
            }}
          />
        </div>
        {loading ? (
          <span className="text-xs text-gray-400">Checking...</span>
        ) : (
          strength && (
            <span className={`text-xs font-medium ${getTextColor()}`}>
              {getStrengthText()}
            </span>
          )
        )}
      </div>
      {strength && (
        <p className="text-xs text-gray-400">
          Score: {strength.score}/4
        </p>
      )}
    </div>
  );
};

export default PasswordStrengthMeter;

