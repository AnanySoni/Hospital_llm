import React from 'react';
import { ProgressStep } from '../types';
import ProgressStepComponent from './ProgressStep';

interface ProgressSidebarProps {
  steps: ProgressStep[];
  currentStep: string;
  isVisible: boolean;
  onClearChat?: () => void;
}

const ProgressSidebar: React.FC<ProgressSidebarProps> = ({ steps, currentStep, isVisible, onClearChat }) => {
  if (!isVisible) return null;

  return (
    <div className="w-56 lg:w-64 bg-chat-glass backdrop-blur-md border-r border-chat-border/20 flex flex-col rounded-2xl shadow-xl m-1 lg:m-2 flex-shrink-0">
      {/* Progress Header */}
      <div className="p-3 lg:p-4 border-b border-chat-border/10">
        <div className="flex items-center space-x-2">
          <div className="bg-chat-accent rounded-lg p-1.5 lg:p-2 shadow">
            <i className="fas fa-clipboard-list text-white text-xs lg:text-sm"></i>
          </div>
          <div className="min-w-0">
            <h3 className="text-white font-semibold text-xs lg:text-sm truncate">Progress</h3>
            <p className="text-gray-400 text-xs truncate">Medical Consultation</p>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex-1 p-3 lg:p-4 space-y-2 lg:space-y-3 overflow-y-auto">
        {steps.map((step, index) => (
          <div key={step.id} className="relative">
            <ProgressStepComponent 
              step={step} 
              isActive={currentStep === step.id}
              isLast={index === steps.length - 1}
            />
            
            {/* Connecting Line */}
            {index < steps.length - 1 && (
              <div className="absolute left-5 lg:left-6 top-10 lg:top-12 w-0.5 h-6 lg:h-8 bg-chat-border/20"></div>
            )}
          </div>
        ))}
      </div>

      {/* Progress Footer */}
      <div className="p-3 lg:p-4 border-t border-chat-border/10 flex flex-col items-center">
        <div className="text-center mb-2 w-full">
          <div className="text-gray-400 text-xs mb-1">
            {steps.filter(s => s.status === 'completed').length} of {steps.length} completed
          </div>
          <div className="w-full bg-chat-border/20 rounded-full h-1">
            <div 
              className="bg-chat-accent-green h-1 rounded-full transition-all duration-300"
              style={{ 
                width: `${(steps.filter(s => s.status === 'completed').length / steps.length) * 100}%` 
              }}
            ></div>
          </div>
        </div>
        {onClearChat && (
          <button
            onClick={onClearChat}
            className="mt-2 lg:mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1.5 lg:py-2 px-3 lg:px-4 rounded-lg shadow transition-colors duration-200 text-xs lg:text-sm"
          >
            <i className="fas fa-trash mr-1 lg:mr-2"></i>
            Clear Chat
          </button>
        )}
      </div>
    </div>
  );
};

export default ProgressSidebar; 