import React from 'react';

interface UrgencyIndicatorProps {
  urgencyLevel: 'emergency' | 'urgent' | 'soon' | 'routine';
  urgencyScore: number;
  timeframe: string;
  actionRequired: string;
  redFlags?: Array<{
    symptom: string;
    severity: string;
    immediate_action: string;
    escalation_reason: string;
  }>;
  escalationRequired?: boolean;
  emergencyContact?: string;
}

const UrgencyIndicator: React.FC<UrgencyIndicatorProps> = ({
  urgencyLevel,
  urgencyScore,
  timeframe,
  actionRequired,
  redFlags = [],
  escalationRequired = false,
  emergencyContact
}) => {
  const getUrgencyConfig = (level: string) => {
    switch (level) {
      case 'emergency':
        return {
          bgColor: 'bg-red-100 border-red-500',
          textColor: 'text-red-800',
          iconColor: 'text-red-600',
          icon: 'fas fa-exclamation-triangle',
          label: 'EMERGENCY',
          badgeColor: 'bg-red-600'
        };
      case 'urgent':
        return {
          bgColor: 'bg-orange-100 border-orange-500',
          textColor: 'text-orange-800',
          iconColor: 'text-orange-600',
          icon: 'fas fa-clock',
          label: 'URGENT',
          badgeColor: 'bg-orange-600'
        };
      case 'soon':
        return {
          bgColor: 'bg-yellow-100 border-yellow-500',
          textColor: 'text-yellow-800',
          iconColor: 'text-yellow-600',
          icon: 'fas fa-calendar-alt',
          label: 'SOON',
          badgeColor: 'bg-yellow-600'
        };
      case 'routine':
        return {
          bgColor: 'bg-green-100 border-green-500',
          textColor: 'text-green-800',
          iconColor: 'text-green-600',
          icon: 'fas fa-check-circle',
          label: 'ROUTINE',
          badgeColor: 'bg-green-600'
        };
      default:
        return {
          bgColor: 'bg-gray-100 border-gray-500',
          textColor: 'text-gray-800',
          iconColor: 'text-gray-600',
          icon: 'fas fa-info-circle',
          label: 'UNKNOWN',
          badgeColor: 'bg-gray-600'
        };
    }
  };

  const config = getUrgencyConfig(urgencyLevel);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-600';
    if (score >= 60) return 'text-orange-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className={`border-l-4 rounded-lg p-4 mb-4 ${config.bgColor} ${config.textColor}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <i className={`${config.icon} ${config.iconColor} text-xl`}></i>
          <span className={`px-3 py-1 rounded-full text-white text-sm font-bold ${config.badgeColor}`}>
            {config.label}
          </span>
          <span className={`text-sm font-semibold ${getScoreColor(urgencyScore)}`}>
            Score: {urgencyScore.toFixed(1)}/100
          </span>
        </div>
        
        {escalationRequired && (
          <div className="flex items-center space-x-1 bg-red-600 text-white px-2 py-1 rounded-full text-xs">
            <i className="fas fa-phone"></i>
            <span>CALL NOW</span>
          </div>
        )}
      </div>

      {/* Timeframe */}
      <div className="mb-3">
        <div className="flex items-center space-x-2 mb-1">
          <i className={`fas fa-clock ${config.iconColor}`}></i>
          <span className="font-semibold">Recommended Timeframe:</span>
        </div>
        <p className="text-sm ml-6">{timeframe}</p>
      </div>

      {/* Action Required */}
      <div className="mb-3">
        <div className="flex items-center space-x-2 mb-1">
          <i className={`fas fa-tasks ${config.iconColor}`}></i>
          <span className="font-semibold">Action Required:</span>
        </div>
        <p className="text-sm ml-6">{actionRequired}</p>
      </div>

      {/* Emergency Contact */}
      {emergencyContact && (
        <div className="mb-3 bg-red-50 border border-red-200 rounded p-3">
          <div className="flex items-center space-x-2 mb-1">
            <i className="fas fa-phone text-red-600"></i>
            <span className="font-semibold text-red-800">Emergency Contact:</span>
          </div>
          <p className="text-sm text-red-700 ml-6 font-mono">{emergencyContact}</p>
        </div>
      )}

      {/* Red Flags */}
      {redFlags.length > 0 && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
          <div className="flex items-center space-x-2 mb-2">
            <i className="fas fa-flag text-red-600"></i>
            <span className="font-semibold text-red-800">Critical Symptoms Detected:</span>
          </div>
          <div className="space-y-2">
            {redFlags.map((flag, index) => (
              <div key={index} className="text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-600 rounded-full"></div>
                  <span className="font-medium text-red-800">{flag.symptom}</span>
                  <span className="text-xs bg-red-600 text-white px-2 py-1 rounded">
                    {flag.severity}
                  </span>
                </div>
                <p className="text-red-700 ml-4 text-xs mt-1">{flag.escalation_reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Level Visual */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-xs mb-1">
          <span>Risk Level</span>
          <span className={getScoreColor(urgencyScore)}>{urgencyScore.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              urgencyScore >= 80 ? 'bg-red-600' :
              urgencyScore >= 60 ? 'bg-orange-500' :
              urgencyScore >= 40 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(urgencyScore, 100)}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

export default UrgencyIndicator; 