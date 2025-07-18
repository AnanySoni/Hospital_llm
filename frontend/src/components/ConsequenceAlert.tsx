import React from 'react';

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
}

const ConsequenceAlert: React.FC<ConsequenceAlertProps> = ({
  consequenceMessage,
  riskProgression,
  persuasionMetrics
}) => {
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
      {/* Compact main message */}
      <div className="flex items-start space-x-3">
        <div className={`text-xl ${styling.iconColor} flex-shrink-0`}>
          {styling.icon}
        </div>
        <div className="flex-1">
          {/* Urgency indicator */}
          <div className={`text-sm font-bold ${styling.textColor} mb-2`}>
            {styling.urgencyText}
          </div>
          
          {/* Primary consequence message */}
          <div className={`text-base font-semibold ${styling.textColor} mb-2`}>
            {consequenceMessage.primary_consequence}
          </div>
          
          {/* Timeframe */}
          <div className={`text-sm ${styling.textColor} mb-2`}>
            ⏰ Action needed: {consequenceMessage.timeframe}
          </div>
          
          {/* Action benefits - single line */}
          <div className={`text-sm ${styling.textColor} mb-3`}>
            ✅ {consequenceMessage.action_benefits}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsequenceAlert; 