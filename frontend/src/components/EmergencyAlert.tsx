import React, { useState, useEffect } from 'react';

interface EmergencyAlertProps {
  isVisible: boolean;
  urgencyLevel: 'emergency' | 'urgent';
  redFlags: string[];
  reasoning: string;
  timeUrgency: string;
  recommendations: string[];
  onAcknowledge: () => void;
  onCallEmergency?: () => void;
  autoShow?: boolean;
}

const EmergencyAlert: React.FC<EmergencyAlertProps> = ({
  isVisible,
  urgencyLevel,
  redFlags,
  reasoning,
  timeUrgency,
  recommendations,
  onAcknowledge,
  onCallEmergency,
  autoShow = true
}) => {
  const [isShowing, setIsShowing] = useState(false);
  const [countdown, setCountdown] = useState(10);

  useEffect(() => {
    if (isVisible && autoShow) {
      setIsShowing(true);
      
      // Auto-close countdown for emergency alerts
      if (urgencyLevel === 'emergency') {
        const timer = setInterval(() => {
          setCountdown((prev) => {
            if (prev <= 1) {
              clearInterval(timer);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);

        return () => clearInterval(timer);
      }
    }
  }, [isVisible, autoShow, urgencyLevel]);

  const handleAcknowledge = () => {
    setIsShowing(false);
    onAcknowledge();
  };

  const handleCallEmergency = () => {
    if (onCallEmergency) {
      onCallEmergency();
    } else {
      // Attempt to open phone dialer
      window.location.href = 'tel:911';
    }
  };

  if (!isShowing) return null;

  const isEmergency = urgencyLevel === 'emergency';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
      <div className={`max-w-md w-full mx-4 rounded-lg shadow-2xl ${
        isEmergency ? 'bg-red-50 border-4 border-red-600' : 'bg-orange-50 border-4 border-orange-500'
      }`}>
        
        {/* Header */}
        <div className={`p-4 rounded-t-lg ${
          isEmergency ? 'bg-red-600' : 'bg-orange-500'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {isEmergency ? (
                <i className="fas fa-exclamation-triangle text-white text-2xl animate-pulse"></i>
              ) : (
                <i className="fas fa-clock text-white text-2xl"></i>
              )}
              <h2 className="text-white text-xl font-bold">
                {isEmergency ? 'MEDICAL EMERGENCY' : 'URGENT MEDICAL ATTENTION'}
              </h2>
            </div>
            
            {isEmergency && countdown > 0 && (
              <div className="bg-white bg-opacity-20 rounded-full px-3 py-1">
                <span className="text-white text-sm font-bold">{countdown}s</span>
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          
          {/* Time Urgency */}
          <div className="mb-4">
            <div className={`p-3 rounded-lg border-l-4 ${
              isEmergency ? 'bg-red-100 border-red-500' : 'bg-orange-100 border-orange-500'
            }`}>
              <div className="flex items-center space-x-2 mb-2">
                <i className={`fas fa-clock ${isEmergency ? 'text-red-600' : 'text-orange-600'}`}></i>
                <span className={`font-semibold ${isEmergency ? 'text-red-800' : 'text-orange-800'}`}>
                  Time Frame:
                </span>
              </div>
              <p className={`text-sm ${isEmergency ? 'text-red-700' : 'text-orange-700'}`}>
                {timeUrgency}
              </p>
            </div>
          </div>

          {/* Medical Reasoning */}
          <div className="mb-4">
            <h3 className={`font-semibold mb-2 ${isEmergency ? 'text-red-800' : 'text-orange-800'}`}>
              Medical Assessment:
            </h3>
            <p className={`text-sm ${isEmergency ? 'text-red-700' : 'text-orange-700'}`}>
              {reasoning}
            </p>
          </div>

          {/* Red Flags */}
          {redFlags.length > 0 && (
            <div className="mb-4">
              <h3 className={`font-semibold mb-2 ${isEmergency ? 'text-red-800' : 'text-orange-800'}`}>
                Critical Symptoms Detected:
              </h3>
              <ul className="space-y-1">
                {redFlags.map((flag, index) => (
                  <li key={index} className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${isEmergency ? 'bg-red-600' : 'bg-orange-500'}`}></div>
                    <span className={`text-sm ${isEmergency ? 'text-red-700' : 'text-orange-700'}`}>
                      {flag}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          <div className="mb-6">
            <h3 className={`font-semibold mb-2 ${isEmergency ? 'text-red-800' : 'text-orange-800'}`}>
              Immediate Actions Required:
            </h3>
            <ul className="space-y-1">
              {recommendations.map((rec, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <div className={`w-2 h-2 rounded-full mt-2 ${isEmergency ? 'bg-red-600' : 'bg-orange-500'}`}></div>
                  <span className={`text-sm ${isEmergency ? 'text-red-700' : 'text-orange-700'}`}>
                    {rec}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            {isEmergency && (
              <button
                onClick={handleCallEmergency}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
              >
                <i className="fas fa-phone"></i>
                <span>CALL 911 NOW</span>
              </button>
            )}
            
            <button
              onClick={handleAcknowledge}
              className={`w-full font-semibold py-2 px-4 rounded-lg transition-colors duration-200 ${
                isEmergency 
                  ? 'bg-gray-600 hover:bg-gray-700 text-white' 
                  : 'bg-orange-600 hover:bg-orange-700 text-white'
              }`}
            >
              I Understand - Continue
            </button>
          </div>

          {/* Disclaimer */}
          <div className="mt-4 p-3 bg-gray-100 rounded-lg">
            <p className="text-xs text-gray-600 text-center">
              <i className="fas fa-info-circle mr-1"></i>
              This assessment is for informational purposes only. Always consult with a healthcare professional for medical advice.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmergencyAlert; 