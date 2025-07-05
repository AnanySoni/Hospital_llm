import React, { useState } from 'react';

interface ConsequenceMessage {
  primary_consequence: string;
  risk_level: string;
  timeframe: string;
  escalation_risks: string[];
  opportunity_cost?: string;
  social_proof?: string;
  regret_prevention?: string;
  action_benefits: string;
}

interface RiskProgression {
  immediate_risk: string;
  short_term_risk: string;
  long_term_risk: string;
  prevention_window: string;
}

interface PersuasionMetrics {
  urgency_score: number;
  fear_appeal_strength: string;
  message_type: string;
  expected_conversion?: number;
}

interface ConsequenceAlertProps {
  consequenceMessage?: ConsequenceMessage;
  riskProgression?: RiskProgression;
  persuasionMetrics?: PersuasionMetrics;
  onActionClick?: () => void;
}

const ConsequenceAlert: React.FC<ConsequenceAlertProps> = ({
  consequenceMessage,
  riskProgression,
  persuasionMetrics,
  onActionClick
}) => {
  const [showDetails, setShowDetails] = useState(false);

  if (!consequenceMessage) return null;

  const getRiskLevelStyling = (riskLevel: string) => {
    switch (riskLevel) {
      case 'emergency':
        return {
          container: 'bg-red-50 border-red-200 border-l-4 border-l-red-500',
          icon: '🚨',
          iconColor: 'text-red-600',
          textColor: 'text-red-800',
          buttonColor: 'bg-red-600 hover:bg-red-700',
          urgencyText: 'URGENT ACTION NEEDED'
        };
      case 'urgent':
        return {
          container: 'bg-orange-50 border-orange-200 border-l-4 border-l-orange-500',
          icon: '⚠️',
          iconColor: 'text-orange-600',
          textColor: 'text-orange-800',
          buttonColor: 'bg-orange-600 hover:bg-orange-700',
          urgencyText: 'PROMPT ACTION RECOMMENDED'
        };
      default:
        return {
          container: 'bg-blue-50 border-blue-200 border-l-4 border-l-blue-500',
          icon: '💡',
          iconColor: 'text-blue-600',
          textColor: 'text-blue-800',
          buttonColor: 'bg-blue-600 hover:bg-blue-700',
          urgencyText: 'EARLY ACTION BENEFICIAL'
        };
    }
  };

  const styling = getRiskLevelStyling(consequenceMessage.risk_level);

  return (
    <div className={`p-4 rounded-lg ${styling.container} my-4 shadow-md`}>
      {/* Main consequence header */}
      <div className="flex items-start space-x-3">
        <div className={`text-2xl ${styling.iconColor}`}>
          {styling.icon}
        </div>
        <div className="flex-1">
          {/* Urgency indicator */}
          <div className={`text-sm font-bold ${styling.textColor} mb-2`}>
            {styling.urgencyText}
          </div>
          
          {/* Primary consequence message */}
          <div className={`text-lg font-semibold ${styling.textColor} mb-3`}>
            {consequenceMessage.primary_consequence}
          </div>
          
          {/* Timeframe */}
          <div className={`text-md ${styling.textColor} mb-3 font-medium`}>
            ⏰ Action needed: {consequenceMessage.timeframe}
          </div>
          
          {/* Action benefits */}
          <div className={`text-md ${styling.textColor} mb-4`}>
            ✅ {consequenceMessage.action_benefits}
          </div>
          
          {/* Escalation risks preview */}
          {consequenceMessage.escalation_risks.length > 0 && (
            <div className={`text-sm ${styling.textColor} mb-3`}>
              <span className="font-medium">Risks if delayed:</span>
              <ul className="list-disc list-inside mt-1">
                <li>{consequenceMessage.escalation_risks[0]}</li>
                {consequenceMessage.escalation_risks.length > 1 && (
                  <li>
                    and {consequenceMessage.escalation_risks.length - 1} more...
                    <button
                      onClick={() => setShowDetails(!showDetails)}
                      className={`ml-1 underline ${styling.textColor} hover:opacity-75`}
                    >
                      {showDetails ? 'show less' : 'see all'}
                    </button>
                  </li>
                )}
              </ul>
            </div>
          )}
          
          {/* Expandable details */}
          {showDetails && (
            <div className={`mt-4 p-3 bg-white bg-opacity-50 rounded-md ${styling.textColor}`}>
              {/* Complete risk list */}
              {consequenceMessage.escalation_risks.length > 1 && (
                <div className="mb-3">
                  <h4 className="font-semibold mb-2">Complete risk assessment:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {consequenceMessage.escalation_risks.slice(1).map((risk, index) => (
                      <li key={index}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Risk progression timeline */}
              {riskProgression && (
                <div className="mb-3">
                  <h4 className="font-semibold mb-2">Risk timeline:</h4>
                  <div className="space-y-2 text-sm">
                    <div>📍 <strong>Immediate:</strong> {riskProgression.immediate_risk}</div>
                    <div>📈 <strong>Short-term:</strong> {riskProgression.short_term_risk}</div>
                    <div>📊 <strong>Long-term:</strong> {riskProgression.long_term_risk}</div>
                    <div>🎯 <strong>Optimal window:</strong> {riskProgression.prevention_window}</div>
                  </div>
                </div>
              )}
              
              {/* Social proof */}
              {consequenceMessage.social_proof && (
                <div className="mb-3">
                  <h4 className="font-semibold mb-1">Medical evidence:</h4>
                  <p className="text-sm italic">{consequenceMessage.social_proof}</p>
                </div>
              )}
              
              {/* Regret prevention */}
              {consequenceMessage.regret_prevention && (
                <div className="mb-3">
                  <h4 className="font-semibold mb-1">Patient experience:</h4>
                  <p className="text-sm italic">{consequenceMessage.regret_prevention}</p>
                </div>
              )}
              
              {/* Opportunity cost */}
              {consequenceMessage.opportunity_cost && (
                <div className="mb-3">
                  <h4 className="font-semibold mb-1">Cost of waiting:</h4>
                  <p className="text-sm">{consequenceMessage.opportunity_cost}</p>
                </div>
              )}
            </div>
          )}
          
          {/* Action button */}
          <div className="mt-4">
            <button
              onClick={onActionClick}
              className={`w-full ${styling.buttonColor} text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 shadow-md hover:shadow-lg`}
            >
              {consequenceMessage.risk_level === 'emergency' 
                ? 'Get Emergency Care Now' 
                : consequenceMessage.risk_level === 'urgent'
                ? 'Book Appointment Today'
                : 'Schedule Consultation'}
            </button>
          </div>
          
          {/* Reassurance text */}
          <div className={`mt-2 text-xs ${styling.textColor} text-center opacity-75`}>
            {consequenceMessage.risk_level === 'emergency' 
              ? 'Taking immediate action is the best choice for your health'
              : 'Early action leads to better outcomes and peace of mind'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsequenceAlert; 