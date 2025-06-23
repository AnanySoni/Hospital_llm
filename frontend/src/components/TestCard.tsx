import React from 'react';
import { TestRecommendation } from '../types';

interface TestCardProps {
  test: TestRecommendation;
  isSelected?: boolean;
  onSelect?: (testId: string, selected: boolean) => void;
}

const TestCard: React.FC<TestCardProps> = ({ test, isSelected = false, onSelect }) => {
  const handleSelectionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onSelect?.(test.test_id, e.target.checked);
  };

  return (
    <div className={`bg-chat-assistant-muted border rounded-lg p-3 text-white transition-all duration-200 ${
      isSelected ? 'border-blue-500 bg-blue-900/20' : 'border-gray-700'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={handleSelectionChange}
            className="mt-1 w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-2"
          />
          <div className="flex-1">
            <div className="flex justify-between items-start">
              <h5 className="font-bold text-gray-100">{test.test_name}</h5>
              <span className="text-sm font-semibold text-green-400">₹{test.cost}</span>
            </div>
            <p className="text-sm text-gray-300 mt-1 mb-2">{test.description}</p>
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="bg-gray-700 px-2 py-1 rounded-full">{test.category}</span>
              <span className="bg-red-800 px-2 py-1 rounded-full">Prep: {test.preparation}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestCard; 