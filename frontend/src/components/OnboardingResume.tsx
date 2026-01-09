import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const OnboardingResume: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const run = async () => {
      const token = window.localStorage.getItem('access_token');
      if (!token) {
        navigate('/onboarding/register');
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/onboarding/session/resume`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error('Failed to load onboarding session.');
        }

        const data = await res.json();
        const route = data.route || '/onboarding/register';
        navigate(route, { replace: true });
      } catch {
        navigate('/onboarding/register', { replace: true });
      }
    };

    run();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-400 text-sm">Loading your onboarding progress...</p>
      </div>
    </div>
  );
};

export default OnboardingResume;






