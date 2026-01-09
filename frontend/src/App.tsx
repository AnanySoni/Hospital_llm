import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useParams, Navigate, useLocation } from 'react-router-dom';
import ChatContainer from './components/ChatContainer';
import { HospitalProvider, useHospital } from './contexts/HospitalContext';
import GoogleCalendarConnect from './components/GoogleCalendarConnect';
import ProgressSidebar from './components/ProgressSidebar';
import ProgressToggle from './components/ProgressToggle';
import MobileProgressBar from './components/MobileProgressBar';
import AdminApp from './components/AdminApp';
import { ProgressProvider, useProgress } from './contexts/ProgressContext';
import OnboardingRegister from './components/OnboardingRegister';
import OnboardingGoogleCallback from './components/OnboardingGoogleCallback';
import OnboardingVerifyEmail from './components/OnboardingVerifyEmail';
import OnboardingHospitalInfo from './components/OnboardingHospitalInfo';
import OnboardingResume from './components/OnboardingResume';
import OnboardingComplete from './components/OnboardingComplete';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';

// Removed stray untyped function signature for AppContent
function AppContent({ slug }: { slug?: string }) {
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
            slug={slug}
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

function ChatRouteWrapper() {
  const { slug } = useParams();
  return (
    <HospitalProvider slug={slug!}>
      <HospitalGuard>
        <ProgressProvider>
          <AppContent slug={slug} />
        </ProgressProvider>
      </HospitalGuard>
    </HospitalProvider>
  );
}

function AdminRouteWrapper() {
  const { slug } = useParams();
  return (
    <HospitalProvider slug={slug!}>
      <HospitalGuard>
        <AdminApp slug={slug} />
      </HospitalGuard>
    </HospitalProvider>
  );
}
// Guard component to redirect if hospital is invalid
function HospitalGuard({ children }: { children: React.ReactNode }) {
  const { hospital, loading } = useHospital();
  const location = useLocation();
  
  console.log(`[HospitalGuard] Loading: ${loading}, Hospital:`, hospital);
  console.log(`[HospitalGuard] Current location:`, location.pathname);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading hospital...</p>
      </div>
    );
  }
  if (!hospital) {
    console.log(`[HospitalGuard] Hospital not found, showing error page`);
    // Show error instead of redirecting to demo1
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Hospital Not Found</h1>
          <p className="text-gray-600 mb-4">The hospital you're looking for doesn't exist or is not available.</p>
          <button 
            onClick={() => window.location.href = '/h/demo1'} 
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Go to Demo Hospital
          </button>
        </div>
      </div>
    );
  }
  console.log(`[HospitalGuard] Hospital found, rendering children`);
  return <>{children}</>;
}

function App() {
  return (
    <Router>
      <Routes>
        {/* Public onboarding routes (no hospital slug required) */}
        <Route path="/onboarding" element={<OnboardingResume />} />
        <Route path="/onboarding/register" element={<OnboardingRegister />} />
        <Route path="/onboarding/google/callback" element={<OnboardingGoogleCallback />} />
        <Route path="/onboarding/verify-email" element={<OnboardingVerifyEmail />} />
        <Route path="/onboarding/hospital-info" element={<OnboardingHospitalInfo />} />
        <Route path="/onboarding/complete" element={<OnboardingComplete />} />
        <Route path="/onboarding/forgot-password" element={<ForgotPassword />} />
        <Route path="/onboarding/reset-password" element={<ResetPassword />} />

        <Route path="/h/:slug" element={<ChatRouteWrapper />} />
        <Route path="/h/:slug/admin" element={<AdminRouteWrapper />} />
        {/* Fallback: redirect to /h/demo1 or show 404 */}
        <Route path="*" element={<Navigate to="/h/demo1" replace />} />
      </Routes>
    </Router>
  );
}

export default App; 