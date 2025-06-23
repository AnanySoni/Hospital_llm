import React, { useState } from 'react';
import ChatContainer from './components/ChatContainer';
import GoogleCalendarConnect from './components/GoogleCalendarConnect';

function App() {
  const [isCalendarConnected, setIsCalendarConnected] = useState(false);

  return (
    <div className="h-screen bg-chat-bg text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-chat-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 rounded-lg p-2">
              <i className="fas fa-stethoscope text-white"></i>
            </div>
            <div>
              <h1 className="text-xl font-semibold">Hospital AI Assistant</h1>
              <p className="text-gray-400 text-sm">Your medical consultation companion</p>
            </div>
          </div>
          
          {/* Google Calendar Connect Button */}
          <GoogleCalendarConnect onConnectionChange={setIsCalendarConnected} />
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-hidden">
        <ChatContainer isCalendarConnected={isCalendarConnected} />
      </main>
    </div>
  );
}

export default App; 