import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Copy, ArrowRight } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const PUBLIC_BASE_URL = process.env.REACT_APP_PUBLIC_BASE_URL || 'https://yourdomain.com';

interface CompletionData {
  hospital_slug: string;
  hospital_name: string;
  admin_panel_url: string;
  chat_url: string;
}

const OnboardingComplete: React.FC = () => {
  const navigate = useNavigate();
  const [completionData, setCompletionData] = useState<CompletionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

  useEffect(() => {
    // Get hospital slug from localStorage or fetch from backend
    const token = window.localStorage.getItem('access_token');
    if (!token) {
      navigate('/onboarding/register');
      return;
    }

    // Fetch completion status from backend
    const fetchCompletionData = async () => {
      try {
        const response = await fetch(`${API_BASE}/onboarding/complete/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to load completion data' }));
          throw new Error(errorData.detail || 'Failed to load completion data');
        }

        const data = await response.json();
        if (data.hospital_slug) {
          setCompletionData({
            hospital_slug: data.hospital_slug,
            hospital_name: data.hospital_name || 'Your Hospital',
            admin_panel_url: data.admin_panel_url,
            chat_url: data.chat_url,
          });
        } else {
          setError('Hospital information not found. Please complete hospital setup.');
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load completion data.');
      } finally {
        setLoading(false);
      }
    };

    fetchCompletionData();
  }, [navigate]);

  const handleCopyUrl = (url: string, type: string) => {
    navigator.clipboard.writeText(url).then(() => {
      setCopiedUrl(type);
      setTimeout(() => setCopiedUrl(null), 2000);
    }).catch(() => {
      // Fallback for browsers without clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = url;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopiedUrl(type);
      setTimeout(() => setCopiedUrl(null), 2000);
    });
  };

  const checklistItems = [
    { label: 'Account created', completed: true },
    { label: 'Email verified', completed: true },
    { label: 'Hospital information saved', completed: true },
    { label: 'URL created', completed: true },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !completionData) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Error</h1>
          <p className="text-gray-300 mb-6">{error || 'Failed to load completion data'}</p>
          <button
            onClick={() => navigate('/onboarding/hospital-info')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
      <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500 rounded-full mb-4">
            <CheckCircle className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">🎉 Your Hospital is Ready!</h1>
          <p className="text-gray-400">Congratulations! You've completed the initial setup.</p>
        </div>

        {/* Checklist */}
        <div className="bg-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Completion Checklist</h2>
          <div className="space-y-3">
            {checklistItems.map((item, index) => (
              <div key={index} className="flex items-center space-x-3">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* URLs */}
        <div className="bg-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Your Hospital URLs</h2>
          
          <div className="space-y-4">
            {/* Chat URL */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Patient Chat URL
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={completionData.chat_url}
                  readOnly
                  className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg border border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => handleCopyUrl(completionData.chat_url, 'chat')}
                  className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
                  title="Copy URL"
                >
                  <Copy className="w-4 h-4" />
                  <span className="text-sm">{copiedUrl === 'chat' ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Use this URL on your kiosk or website
              </p>
            </div>

            {/* Admin Panel URL */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Admin Panel URL
              </label>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={completionData.admin_panel_url}
                  readOnly
                  className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg border border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={() => handleCopyUrl(completionData.admin_panel_url, 'admin')}
                  className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
                  title="Copy URL"
                >
                  <Copy className="w-4 h-4" />
                  <span className="text-sm">{copiedUrl === 'admin' ? 'Copied!' : 'Copy'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Next Steps */}
        <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Next Steps (in Admin Panel)</h2>
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start space-x-2">
              <span className="text-blue-400 mt-1">•</span>
              <span>Add departments (Admin → Departments)</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-blue-400 mt-1">•</span>
              <span>Add doctors - CSV upload or manual entry (Admin → Doctors)</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-blue-400 mt-1">•</span>
              <span>Connect Google Calendar (Admin → Calendar) - Optional</span>
            </li>
            <li className="flex items-start space-x-2">
              <span className="text-blue-400 mt-1">•</span>
              <span>Configure kiosk: Use <code className="bg-gray-700 px-2 py-1 rounded text-sm">{completionData.chat_url}</code> in full-screen browser</span>
            </li>
          </ul>
        </div>

        {/* Action Button */}
        <div className="text-center">
          <button
            onClick={() => window.location.href = completionData.admin_panel_url}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-lg inline-flex items-center space-x-2 text-lg transition-colors"
          >
            <span>Go to Admin Panel</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* Credentials Reminder */}
        <div className="mt-6 p-4 bg-yellow-900/30 border border-yellow-700 rounded-lg">
          <p className="text-sm text-yellow-200">
            <strong>Remember:</strong> Your login credentials were sent to your email. Use your username and password to access the admin panel in the future.
          </p>
        </div>
      </div>
    </div>
  );
};

export default OnboardingComplete;

