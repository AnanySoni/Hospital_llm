import React from 'react';
import { ProgressStep as ProgressStepType } from '../types';

interface ProgressStepProps {
  step: ProgressStepType;
  isActive: boolean;
  isLast: boolean;
}

const ProgressStep: React.FC<ProgressStepProps> = ({ step, isActive, isLast }) => {
  const getStatusIcon = () => {
    switch (step.status) {
      case 'completed':
        return (
          <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center checkmark-appear">
            <i className="fas fa-check text-white text-xs"></i>
          </div>
        );
      case 'active':
        return (
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center progress-pulse">
            <i className="fas fa-spinner fa-spin text-white text-xs"></i>
          </div>
        );
      case 'error':
        return (
          <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
            <i className="fas fa-exclamation text-white text-xs"></i>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
            <i className={`${step.icon} text-gray-400 text-xs`}></i>
          </div>
        );
    }
  };

  const getStatusColor = () => {
    switch (step.status) {
      case 'completed':
        return 'text-green-400';
      case 'active':
        return 'text-blue-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className={`flex items-start space-x-3 p-2 rounded-lg transition-all duration-200 ${
      isActive ? 'bg-gray-700' : ''
    }`}>
      {/* Step Icon */}
      <div className="flex-shrink-0">
        {getStatusIcon()}
      </div>

      {/* Step Content */}
      <div className="flex-1 min-w-0">
        <div className={`font-medium text-sm ${getStatusColor()}`}>
          {step.title}
        </div>
        {step.description && (
          <div className="text-gray-500 text-xs mt-1">
            {step.description}
          </div>
        )}
        {step.timestamp && step.status === 'completed' && (
          <div className="text-gray-600 text-xs mt-1">
            {step.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
        
        {/* Sub-steps */}
        {step.subSteps && step.subSteps.length > 0 && (
          <div className="mt-2 space-y-1">
            {step.subSteps.map((subStep, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  subStep.status === 'completed' ? 'bg-green-400' :
                  subStep.status === 'active' ? 'bg-blue-400' :
                  subStep.status === 'error' ? 'bg-red-400' : 'bg-gray-500'
                }`}></div>
                <span className={`text-xs ${
                  subStep.status === 'completed' ? 'text-green-400' :
                  subStep.status === 'active' ? 'text-blue-400' :
                  subStep.status === 'error' ? 'text-red-400' : 'text-gray-500'
                }`}>
                  {subStep.title}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressStep; 