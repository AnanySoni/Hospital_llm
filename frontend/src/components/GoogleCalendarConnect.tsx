import React, { useState, useEffect } from 'react';

interface GoogleCalendarConnectProps {
  onConnectionChange?: (connected: boolean) => void;
}

const GoogleCalendarConnect: React.FC<GoogleCalendarConnectProps> = ({ onConnectionChange }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [doctorId, setDoctorId] = useState<number | null>(null);
  const [showDoctorSelect, setShowDoctorSelect] = useState(false);
  const [doctors, setDoctors] = useState<any[]>([]);

  // Load doctors on component mount
  useEffect(() => {
    fetchDoctors();
    
    // Check if we're returning from OAuth
    handleOAuthCallback();
  }, []);

  const fetchDoctors = async () => {
    try {
      const response = await fetch('http://localhost:8000/doctors');
      if (response.ok) {
        const doctorList = await response.json();
        setDoctors(doctorList);
      }
    } catch (error) {
      console.error('Error fetching doctors:', error);
    }
  };

  // Handle OAuth callback when returning from Google
  const handleOAuthCallback = async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const oauthInProgress = localStorage.getItem('oauth_in_progress');
    const connectingDoctorId = localStorage.getItem('connecting_doctor_id');
    
    if (code && oauthInProgress && connectingDoctorId) {
      setIsLoading(true);
      
      try {
        // Clear localStorage
        localStorage.removeItem('oauth_in_progress');
        localStorage.removeItem('connecting_doctor_id');
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Check connection status for the doctor
        const doctorId = parseInt(connectingDoctorId);
        await checkConnectionStatus(doctorId);
        
      } catch (error) {
        console.error('Error handling OAuth callback:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleConnect = () => {
    if (!isConnected) {
      setShowDoctorSelect(true);
    } else {
      // Disconnect
      setIsConnected(false);
      setDoctorId(null);
      onConnectionChange?.(false);
    }
  };

  const handleDoctorSelect = async (selectedDoctorId: number) => {
    console.log('Doctor selected:', selectedDoctorId);
    setIsLoading(true);
    setShowDoctorSelect(false);
    
    try {
      // Check if doctor already has calendar connected
      const selectedDoctor = doctors.find(d => d.id === selectedDoctorId);
      console.log('Selected doctor:', selectedDoctor);
      
      if (selectedDoctor?.has_calendar_connected) {
        console.log('Doctor already has calendar connected');
        setIsConnected(true);
        setDoctorId(selectedDoctorId);
        onConnectionChange?.(true);
        setIsLoading(false);
      } else {
        console.log('Doctor needs calendar connection, initiating OAuth flow');
        
        // Store doctor ID for when we return from OAuth
        localStorage.setItem('connecting_doctor_id', selectedDoctorId.toString());
        localStorage.setItem('oauth_in_progress', 'true');
        
        // Redirect directly to OAuth endpoint with doctor_id as query param
        const authUrl = `http://localhost:8000/auth/google/login?doctor_id=${selectedDoctorId}`;
        console.log('Redirecting to auth URL:', authUrl);
        
        window.location.href = authUrl;
      }
    } catch (error) {
      console.error('Error connecting to Google Calendar:', error);
      setIsLoading(false);
    }
  };

  const checkConnectionStatus = async (doctorId: number) => {
    try {
      // Re-fetch doctors to check if the selected doctor now has calendar connected
      const response = await fetch('http://localhost:8000/doctors');
      if (response.ok) {
        const doctorList = await response.json();
        const updatedDoctor = doctorList.find((d: any) => d.id === doctorId);
        
        if (updatedDoctor?.has_calendar_connected) {
          setIsConnected(true);
          setDoctorId(doctorId);
          setDoctors(doctorList); // Update the doctors list
          onConnectionChange?.(true);
        }
      }
    } catch (error) {
      console.error('Error checking connection status:', error);
    }
  };

  if (showDoctorSelect) {
    return (
      <div className="relative">
        <div className="absolute right-0 top-12 bg-chat-assistant border border-chat-border rounded-lg shadow-lg p-4 w-80 z-50">
          <h3 className="text-sm font-medium text-white mb-3">Select Doctor Account</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {doctors.map((doctor) => (
              <button
                key={doctor.id}
                onClick={() => handleDoctorSelect(doctor.id)}
                className="w-full text-left p-3 bg-chat-input hover:bg-gray-600 rounded-md transition-colors"
                disabled={isLoading}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white text-sm font-medium">{doctor.name}</div>
                    <div className="text-gray-400 text-xs">{doctor.department}</div>
                  </div>
                  {doctor.has_calendar_connected && (
                    <div className="flex items-center space-x-1">
                      <i className="fas fa-check-circle text-green-500 text-xs"></i>
                      <span className="text-green-500 text-xs">Connected</span>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
          <button
            onClick={() => setShowDoctorSelect(false)}
            className="mt-3 w-full bg-gray-600 hover:bg-gray-700 text-white text-sm py-2 rounded-md transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={handleConnect}
      disabled={isLoading}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors text-sm ${
        isConnected
          ? 'bg-green-600 hover:bg-green-700 text-white'
          : 'bg-blue-600 hover:bg-blue-700 text-white'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {isLoading ? (
        <>
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>Connecting...</span>
        </>
      ) : isConnected ? (
        <>
          <i className="fab fa-google text-sm"></i>
          <span>Calendar Connected</span>
          <i className="fas fa-check-circle text-sm"></i>
        </>
      ) : (
        <>
          <i className="fab fa-google text-sm"></i>
          <span>Connect Calendar</span>
        </>
      )}
    </button>
  );
};

export default GoogleCalendarConnect; 