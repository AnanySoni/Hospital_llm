import React from 'react';

interface WelcomeScreenProps {
  onExampleClick: (symptom: string) => void;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onExampleClick }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      {/* Logo and Title */}
      <div className="mb-8">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-green-500 rounded-2xl flex items-center justify-center mb-4 mx-auto">
          <i className="fas fa-stethoscope text-white text-2xl"></i>
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">
          Hospital AI Assistant
        </h1>
        <p className="text-gray-400 text-lg">
          Describe your symptoms and get expert medical recommendations
        </p>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 max-w-4xl">
        <div className="bg-chat-assistant rounded-xl p-4 text-left">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mb-3">
            <i className="fas fa-user-md text-white text-sm"></i>
          </div>
          <h3 className="text-white font-semibold mb-2">Expert Recommendations</h3>
          <p className="text-gray-400 text-sm">
            Get matched with the right specialists based on your symptoms
          </p>
        </div>

        <div className="bg-chat-assistant rounded-xl p-4 text-left">
          <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center mb-3">
            <i className="fas fa-calendar-alt text-white text-sm"></i>
          </div>
          <h3 className="text-white font-semibold mb-2">Easy Scheduling</h3>
          <p className="text-gray-400 text-sm">
            Book appointments directly through our integrated system
          </p>
        </div>

        <div className="bg-chat-assistant rounded-xl p-4 text-left">
          <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center mb-3">
            <i className="fas fa-shield-alt text-white text-sm"></i>
          </div>
          <h3 className="text-white font-semibold mb-2">Secure & Private</h3>
          <p className="text-gray-400 text-sm">
            Your medical information is protected and confidential
          </p>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen; 