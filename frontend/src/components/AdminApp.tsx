import React, { useState, useEffect } from 'react';
import AdminLogin from './AdminLogin';
import AdminDashboard from './AdminDashboard';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  hospital_id: number;
  is_super_admin: boolean;
}

interface LoginCredentials {
  username: string;
  password: string;
  twoFactorCode?: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_info: User;
}

const AdminApp: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    try {
      const token = localStorage.getItem('admin_access_token');
      if (token) {
        const response = await fetch('http://localhost:8000/admin/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          // Token is invalid, remove it
          localStorage.removeItem('admin_access_token');
          localStorage.removeItem('admin_refresh_token');
        }
      }
    } catch (error) {
      console.error('Error checking existing session:', error);
      localStorage.removeItem('admin_access_token');
      localStorage.removeItem('admin_refresh_token');
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const handleLogin = async (credentials: LoginCredentials): Promise<void> => {
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data: LoginResponse = await response.json();
      
      // Store tokens
      localStorage.setItem('admin_access_token', data.access_token);
      localStorage.setItem('admin_refresh_token', data.refresh_token);
      
      // Set user data
      setUser(data.user_info);
      
      console.log('Login successful:', data.user_info);
      
    } catch (error: any) {
      console.error('Login error:', error);
      setError(error.message || 'Login failed. Please try again.');
      throw error; // Re-throw to handle 2FA in login component
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('admin_access_token');
      if (token) {
        // Call logout endpoint
        await fetch('http://localhost:8000/admin/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage and state
      localStorage.removeItem('admin_access_token');
      localStorage.removeItem('admin_refresh_token');
      setUser(null);
      setError('');
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshToken = localStorage.getItem('admin_refresh_token');
      if (!refreshToken) {
        return false;
      }

      const response = await fetch('http://localhost:8000/admin/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        return false;
      }

      const data: LoginResponse = await response.json();
      
      // Update tokens
      localStorage.setItem('admin_access_token', data.access_token);
      localStorage.setItem('admin_refresh_token', data.refresh_token);
      
      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  };

  // Auto-refresh token before expiry
  useEffect(() => {
    if (user) {
      const interval = setInterval(async () => {
        const success = await refreshToken();
        if (!success) {
          handleLogout();
        }
      }, 25 * 60 * 1000); // Refresh every 25 minutes (tokens expire in 30 minutes)

      return () => clearInterval(interval);
    }
  }, [user]);

  // Show loading spinner while checking authentication
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login if user is not authenticated
  if (!user) {
    return (
      <AdminLogin 
        onLogin={handleLogin}
        isLoading={isLoading}
        error={error}
      />
    );
  }

  // Show dashboard if user is authenticated
  return (
    <AdminDashboard 
      user={user}
      onLogout={handleLogout}
    />
  );
};

export default AdminApp; 