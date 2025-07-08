import React, { useState } from 'react';
import ChatContainer from './components/ChatContainer';
import GoogleCalendarConnect from './components/GoogleCalendarConnect';
import ProgressSidebar from './components/ProgressSidebar';
import ProgressToggle from './components/ProgressToggle';
import MobileProgressBar from './components/MobileProgressBar';
import { ProgressProvider, useProgress } from './contexts/ProgressContext';

function AppContent() {
  const [isCalendarConnected, setIsCalendarConnected] = useState(false);
  const { progressState } = useProgress();
  const [clearChatFlag, setClearChatFlag] = useState(false);
  const handleClearChat = () => setClearChatFlag(true);

  return (
    <div className="h-screen bg-chat-bg text-white flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-chat-border px-2 sm:px-4 py-2 sm:py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
            <div className="bg-blue-600 rounded-lg p-1.5 sm:p-2 flex-shrink-0">
              <i className="fas fa-stethoscope text-white text-sm"></i>
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl font-semibold truncate">Hospital AI Assistant</h1>
              <p className="text-gray-400 text-xs sm:text-sm truncate">Your medical consultation companion</p>
            </div>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center space-x-1 sm:space-x-2 flex-shrink-0">
            <ProgressToggle />
            <GoogleCalendarConnect onConnectionChange={setIsCalendarConnected} />
          </div>
        </div>
      </header>

      {/* Main Content Area with Sidebar */}
      <main className="flex-1 overflow-hidden flex min-h-0">
        {/* Progress Sidebar */}
        <ProgressSidebar 
          steps={progressState.steps}
          currentStep={progressState.currentStep}
          isVisible={progressState.isVisible}
          onClearChat={handleClearChat}
        />
        
        {/* Chat Container */}
        <div className="flex-1 min-w-0 overflow-hidden">
          <ChatContainer 
            isCalendarConnected={isCalendarConnected} 
            clearChatFlag={clearChatFlag} 
            onClearChatHandled={() => setClearChatFlag(false)} 
          />
        </div>
      </main>
      
      {/* Mobile Progress Bar */}
      <MobileProgressBar 
        steps={progressState.steps}
        currentStep={progressState.currentStep}
        isVisible={progressState.isVisible}
      />
    </div>
  );
}

function App() {
  return (
    <ProgressProvider>
      <AppContent />
    </ProgressProvider>
  );
}

export default App; 