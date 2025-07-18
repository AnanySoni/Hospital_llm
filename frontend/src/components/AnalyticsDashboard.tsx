import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Calendar, 
  Clock, 
  Activity, 
  DollarSign,
  Download,
  Filter,
  RefreshCw,
  Eye,
  AlertCircle,
  CheckCircle,
  Star,
  UserPlus,
  Hospital,
  Stethoscope
} from 'lucide-react';

interface AnalyticsData {
  hospital_analytics: {
    total_doctors: number;
    total_patients: number;
    total_appointments: number;
    appointments_today: number;
    appointments_this_week: number;
    appointments_this_month: number;
    active_sessions: number;
    diagnostic_sessions: number;
    revenue_this_month: number;
    top_departments: Array<{
      name: string;
      appointments: number;
      revenue: number;
    }>;
    recent_activities: Array<{
      action: string;
      user: string;
      timestamp: string;
    }>;
  };
  system_analytics: {
    total_hospitals: number;
    total_admin_users: number;
    system_health: {
      uptime: number;
      response_time: number;
      error_rate: number;
    };
  };
  trends: {
    appointments_trend: Array<{
      date: string;
      count: number;
    }>;
    revenue_trend: Array<{
      date: string;
      amount: number;
    }>;
    patient_satisfaction: Array<{
      month: string;
      rating: number;
    }>;
  };
}

interface AnalyticsDashboardProps {
  currentUser?: {
    id: number;
    is_super_admin: boolean;
    hospital_id: number;
  };
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ currentUser }) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [selectedTimeRange, setSelectedTimeRange] = useState<'week' | 'month' | 'quarter' | 'year'>('month');
  const [selectedMetric, setSelectedMetric] = useState<'appointments' | 'revenue' | 'patients'>('appointments');

  useEffect(() => {
    fetchAnalytics();
  }, [selectedTimeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration
      const mockData: AnalyticsData = {
        hospital_analytics: {
          total_doctors: 24,
          total_patients: 1234,
          total_appointments: 5678,
          appointments_today: 56,
          appointments_this_week: 342,
          appointments_this_month: 1456,
          active_sessions: 12,
          diagnostic_sessions: 89,
          revenue_this_month: 125000,
          top_departments: [
            { name: 'Cardiology', appointments: 245, revenue: 36750 },
            { name: 'Pediatrics', appointments: 312, revenue: 37440 },
            { name: 'Neurology', appointments: 189, revenue: 37800 },
            { name: 'Orthopedics', appointments: 156, revenue: 23400 },
            { name: 'Dermatology', appointments: 98, revenue: 14700 }
          ],
          recent_activities: [
            { action: 'New appointment booked', user: 'Dr. Sarah Johnson', timestamp: '2024-01-20T10:30:00Z' },
            { action: 'Patient consultation completed', user: 'Dr. Michael Chen', timestamp: '2024-01-20T09:15:00Z' },
            { action: 'Calendar updated', user: 'Dr. Emily Rodriguez', timestamp: '2024-01-20T08:45:00Z' },
            { action: 'New patient registered', user: 'System', timestamp: '2024-01-20T08:30:00Z' }
          ]
        },
        system_analytics: {
          total_hospitals: 3,
          total_admin_users: 12,
          system_health: {
            uptime: 99.9,
            response_time: 145,
            error_rate: 0.1
          }
        },
        trends: {
          appointments_trend: [
            { date: '2024-01-14', count: 45 },
            { date: '2024-01-15', count: 52 },
            { date: '2024-01-16', count: 38 },
            { date: '2024-01-17', count: 61 },
            { date: '2024-01-18', count: 48 },
            { date: '2024-01-19', count: 55 },
            { date: '2024-01-20', count: 56 }
          ],
          revenue_trend: [
            { date: '2024-01-14', amount: 6750 },
            { date: '2024-01-15', amount: 7800 },
            { date: '2024-01-16', amount: 5700 },
            { date: '2024-01-17', amount: 9150 },
            { date: '2024-01-18', amount: 7200 },
            { date: '2024-01-19', amount: 8250 },
            { date: '2024-01-20', amount: 8400 }
          ],
          patient_satisfaction: [
            { month: 'Sep', rating: 4.6 },
            { month: 'Oct', rating: 4.7 },
            { month: 'Nov', rating: 4.8 },
            { month: 'Dec', rating: 4.9 },
            { month: 'Jan', rating: 4.8 }
          ]
        }
      };

      setAnalyticsData(mockData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = () => {
    // Generate and download report
    const reportData = {
      generated_at: new Date().toISOString(),
      time_range: selectedTimeRange,
      ...analyticsData
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hospital-analytics-${selectedTimeRange}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getChangeIndicator = (current: number, previous: number) => {
    const change = ((current - previous) / previous) * 100;
    const isPositive = change > 0;
    
    return (
      <div className={`flex items-center ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="h-4 w-4 mr-1" /> : <TrendingDown className="h-4 w-4 mr-1" />}
        <span className="text-sm font-medium">{Math.abs(change).toFixed(1)}%</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No analytics data available</h3>
        <p className="mt-1 text-sm text-gray-500">Analytics data will appear here once available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 admin-scrollbar" style={{maxHeight: '70vh', overflowY: 'auto'}}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Analytics Dashboard</h1>
          <p className="text-gray-600">Monitor hospital performance and system metrics</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value as any)}
            className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
            <option value="year">This Year</option>
          </select>
          <button
            onClick={exportReport}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
          <button
            onClick={fetchAnalytics}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <div className="text-red-600 text-sm">{error}</div>
            <button
              onClick={() => setError('')}
              className="text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Doctors</p>
              <p className="text-2xl font-bold text-blue-600">{analyticsData.hospital_analytics.total_doctors}</p>
              <p className="text-sm text-gray-500">Active practitioners</p>
            </div>
            <div className="p-3 rounded-full bg-blue-100">
              <Stethoscope className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Patients</p>
              <p className="text-2xl font-bold text-green-600">{analyticsData.hospital_analytics.total_patients}</p>
              <p className="text-sm text-gray-500">Registered patients</p>
            </div>
            <div className="p-3 rounded-full bg-green-100">
              <Users className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">This Month</p>
              <p className="text-2xl font-bold text-purple-600">{analyticsData.hospital_analytics.appointments_this_month}</p>
              <p className="text-sm text-gray-500">Appointments</p>
            </div>
            <div className="p-3 rounded-full bg-purple-100">
              <Calendar className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Revenue</p>
              <p className="text-2xl font-bold text-emerald-600">
                {formatCurrency(analyticsData.hospital_analytics.revenue_this_month)}
              </p>
              <p className="text-sm text-gray-500">This month</p>
            </div>
            <div className="p-3 rounded-full bg-emerald-100">
              <DollarSign className="h-6 w-6 text-emerald-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Today's Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Today's Activity</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Appointments Today</span>
              <span className="text-lg font-bold text-blue-600">{analyticsData.hospital_analytics.appointments_today}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Active Sessions</span>
              <span className="text-lg font-bold text-green-600">{analyticsData.hospital_analytics.active_sessions}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Diagnostic Sessions</span>
              <span className="text-lg font-bold text-purple-600">{analyticsData.hospital_analytics.diagnostic_sessions}</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">System Health</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Uptime</span>
              <span className="text-lg font-bold text-green-600">{analyticsData.system_analytics.system_health.uptime}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Response Time</span>
              <span className="text-lg font-bold text-blue-600">{analyticsData.system_analytics.system_health.response_time}ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Error Rate</span>
              <span className="text-lg font-bold text-red-600">{analyticsData.system_analytics.system_health.error_rate}%</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Patient Satisfaction</h3>
          <div className="space-y-3">
            {analyticsData.trends.patient_satisfaction.slice(-3).map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{item.month}</span>
                <div className="flex items-center space-x-2">
                  <Star className="h-4 w-4 text-yellow-400 fill-current" />
                  <span className="text-sm font-medium">{item.rating}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Appointments Trend</h3>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value as any)}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value="appointments">Appointments</option>
              <option value="revenue">Revenue</option>
              <option value="patients">Patients</option>
            </select>
          </div>
          <div className="h-64 flex items-end space-x-2">
            {analyticsData.trends.appointments_trend.map((item, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div 
                  className="w-full bg-blue-500 rounded-t"
                  style={{ height: `${(item.count / 70) * 100}%` }}
                  title={`${item.count} appointments`}
                ></div>
                <span className="text-xs text-gray-500 mt-1">
                  {new Date(item.date).getDate()}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Departments</h3>
          <div className="space-y-3">
            {analyticsData.hospital_analytics.top_departments.map((dept, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{dept.name}</div>
                    <div className="text-sm text-gray-500">{dept.appointments} appointments</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900">{formatCurrency(dept.revenue)}</div>
                  <div className="text-sm text-gray-500">Revenue</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activities */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Activities</h3>
        <div className="space-y-3">
          {analyticsData.hospital_analytics.recent_activities.map((activity, index) => (
            <div key={index} className="flex items-center space-x-3 py-2">
              <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">{activity.action}</p>
                <p className="text-xs text-gray-500">{activity.user} • {formatDate(activity.timestamp)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Super Admin Analytics */}
      {currentUser?.is_super_admin && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">System Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{analyticsData.system_analytics.total_hospitals}</div>
              <div className="text-sm text-gray-500">Total Hospitals</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{analyticsData.system_analytics.total_admin_users}</div>
              <div className="text-sm text-gray-500">Admin Users</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">{analyticsData.hospital_analytics.total_doctors}</div>
              <div className="text-sm text-gray-500">Total Doctors</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard; 