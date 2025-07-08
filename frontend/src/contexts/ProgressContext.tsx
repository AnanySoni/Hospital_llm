import React, { createContext, useContext, useState, useCallback } from 'react';
import { ProgressState, ProgressStep, ProgressContextType } from '../types';

const defaultSteps: ProgressStep[] = [
  {
    id: 'symptoms',
    title: 'Symptoms',
    icon: 'fas fa-stethoscope',
    status: 'waiting',
    description: 'Describe your symptoms'
  },
  {
    id: 'diagnosis',
    title: 'Diagnosis',
    icon: 'fas fa-search',
    status: 'waiting',
    description: 'AI analysis and prediction',
    subSteps: [
      { id: 'questions', title: 'Questions', icon: 'fas fa-question', status: 'waiting' },
      { id: 'analysis', title: 'Analysis', icon: 'fas fa-brain', status: 'waiting' },
      { id: 'prediction', title: 'Prediction', icon: 'fas fa-chart-line', status: 'waiting' }
    ]
  },
  {
    id: 'booking',
    title: 'Booking',
    icon: 'fas fa-calendar-alt',
    status: 'waiting',
    description: 'Appointment or test booking'
  },
  {
    id: 'confirmation',
    title: 'Confirmation',
    icon: 'fas fa-check-circle',
    status: 'waiting',
    description: 'Booking confirmation'
  }
];

const defaultProgressState: ProgressState = {
  currentStep: 'symptoms',
  steps: defaultSteps,
  isVisible: true,
  startTime: new Date()
};

const ProgressContext = createContext<ProgressContextType | undefined>(undefined);

export const useProgress = () => {
  const context = useContext(ProgressContext);
  if (!context) {
    throw new Error('useProgress must be used within a ProgressProvider');
  }
  return context;
};

interface ProgressProviderProps {
  children: React.ReactNode;
}

export const ProgressProvider: React.FC<ProgressProviderProps> = ({ children }) => {
  const [progressState, setProgressState] = useState<ProgressState>(defaultProgressState);

  const updateStep = useCallback((stepId: string, status: ProgressStep['status']) => {
    setProgressState(prev => {
      const updatedSteps = prev.steps.map(step => {
        if (step.id === stepId) {
          return { ...step, status, timestamp: status === 'completed' ? new Date() : step.timestamp };
        }
        
        // Update sub-steps if they exist
        if (step.subSteps) {
          const updatedSubSteps = step.subSteps.map(subStep => {
            if (subStep.id === stepId) {
              return { ...subStep, status, timestamp: status === 'completed' ? new Date() : subStep.timestamp };
            }
            return subStep;
          });
          
          // Update parent step status based on sub-steps
          const allCompleted = updatedSubSteps.every(s => s.status === 'completed');
          const hasActive = updatedSubSteps.some(s => s.status === 'active');
          const hasError = updatedSubSteps.some(s => s.status === 'error');
          
          let newStatus: ProgressStep['status'] = 'waiting';
          if (hasError) newStatus = 'error';
          else if (hasActive) newStatus = 'active';
          else if (allCompleted) newStatus = 'completed';
          
          return { ...step, status: newStatus, subSteps: updatedSubSteps };
        }
        
        return step;
      });
      
      return { ...prev, steps: updatedSteps };
    });
  }, []);

  const setCurrentStep = useCallback((stepId: string) => {
    setProgressState(prev => ({
      ...prev,
      currentStep: stepId
    }));
    
    // Automatically set the step to active when it becomes current
    updateStep(stepId, 'active');
  }, [updateStep]);

  const resetProgress = useCallback(() => {
    setProgressState({
      ...defaultProgressState,
      startTime: new Date()
    });
  }, []);

  const toggleVisibility = useCallback(() => {
    setProgressState(prev => ({
      ...prev,
      isVisible: !prev.isVisible
    }));
  }, []);

  const value: ProgressContextType = {
    progressState,
    updateStep,
    setCurrentStep,
    resetProgress,
    toggleVisibility
  };

  return (
    <ProgressContext.Provider value={value}>
      {children}
    </ProgressContext.Provider>
  );
}; 