import React from 'react';
import { useProgress } from '../contexts/ProgressContext';

const ProgressToggle: React.FC = () => {
  const { progressState, toggleVisibility } = useProgress();

  return (
    <button
      onClick={toggleVisibility}
      className="bg-gray-700 hover:bg-gray-600 rounded-lg p-2 transition-colors duration-200"
      title={progressState.isVisible ? "Hide Progress" : "Show Progress"}
    >
      <i className={`fas fa-${progressState.isVisible ? 'eye-slash' : 'eye'} text-white text-sm`}></i>
    </button>
  );
};

export default ProgressToggle; 