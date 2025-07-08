import React from 'react';
import { ProgressStep } from '../types';

interface MobileProgressBarProps {
  steps: ProgressStep[];
  currentStep: string;
  isVisible: boolean;
}

const MobileProgressBar: React.FC<MobileProgressBarProps> = ({ steps, currentStep, isVisible }) => {
  if (!isVisible) return null;

  const completedSteps = steps.filter(s => s.status === 'completed').length;
  const totalSteps = steps.length;
  const progressPercentage = (completedSteps / totalSteps) * 100;

  const currentStepData = steps.find(s => s.id === currentStep);

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 p-3 z-50">
      {/* Progress Bar */}
      <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
        <div 
          className="bg-green-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progressPercentage}%` }}
        ></div>
      </div>
      
      {/* Current Step Info */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            currentStepData?.status === 'completed' ? 'bg-green-500' :
            currentStepData?.status === 'active' ? 'bg-blue-500 animate-pulse' :
            currentStepData?.status === 'error' ? 'bg-red-500' : 'bg-gray-500'
          }`}></div>
          <span className="text-white font-medium">
            {currentStepData?.title || 'Progress'}
          </span>
        </div>
        
        <span className="text-gray-400">
          {completedSteps} of {totalSteps}
        </span>
      </div>
    </div>
  );
};

export default MobileProgressBar; 