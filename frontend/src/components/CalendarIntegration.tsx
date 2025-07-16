import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Plus, 
  AlertCircle, 
  CheckCircle, 
  XCircle, 
  Settings, 
  Link, 
  Unlink, 
  Clock, 
  Users, 
  RefreshCw,
  Chrome,
  Shield,
  Activity,
  Eye,
  Download,
  Upload
} from 'lucide-react';

interface CalendarConnection {
  id: number;
  doctor_id: number;
  doctor_name: string;
  doctor_email: string;
  google_calendar_id: string;
  calendar_name: string;
  connection_status: 'connected' | 'disconnected' | 'error' | 'syncing';
  last_sync: string | null;
  sync_status: 'success' | 'failed' | 'pending';
  events_synced: number;
  created_at: string;
  updated_at: string;
}

interface CalendarIntegrationProps {
  currentUser?: {
    id: number;
    is_super_admin: boolean;
    hospital_id: number;
  };
}

const CalendarIntegration: React.FC<CalendarIntegrationProps> = ({ currentUser }) => {
  const [connections, setConnections] = useState<CalendarConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConnection, setSelectedConnection] = useState<CalendarConnection | null>(null);
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [showBulkSetupModal, setShowBulkSetupModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [syncingAll, setSyncingAll] = useState(false);

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration
      const mockConnections: CalendarConnection[] = [
        {
          id: 1,
          doctor_id: 1,
          doctor_name: "Dr. Sarah Johnson",
          doctor_email: "sarah.johnson@hospital.com",
          google_calendar_id: "sarah.johnson@hospital.com",
          calendar_name: "Dr. Sarah Johnson - Appointments",
          connection_status: "connected",
          last_sync: "2024-01-20T10:30:00Z",
          sync_status: "success",
          events_synced: 45,
          created_at: "2024-01-15T08:00:00Z",
          updated_at: "2024-01-20T10:30:00Z"
        },
        {
          id: 2,
          doctor_id: 2,
          doctor_name: "Dr. Michael Chen",
          doctor_email: "michael.chen@hospital.com",
          google_calendar_id: "",
          calendar_name: "",
          connection_status: "disconnected",
          last_sync: null,
          sync_status: "pending",
          events_synced: 0,
          created_at: "2024-01-10T08:00:00Z",
          updated_at: "2024-01-10T08:00:00Z"
        },
        {
          id: 3,
          doctor_id: 3,
          doctor_name: "Dr. Emily Rodriguez",
          doctor_email: "emily.rodriguez@hospital.com",
          google_calendar_id: "emily.rodriguez@hospital.com",
          calendar_name: "Dr. Emily Rodriguez - Pediatrics",
          connection_status: "connected",
          last_sync: "2024-01-19T14:15:00Z",
          sync_status: "success",
          events_synced: 67,
          created_at: "2024-01-12T08:00:00Z",
          updated_at: "2024-01-19T14:15:00Z"
        }
      ];

      setConnections(mockConnections);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch calendar connections');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectCalendar = async (doctorId: number) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      
      // Open Google OAuth flow
      const authUrl = `http://localhost:8000/auth/google/login?doctor_id=${doctorId}`;
      const authWindow = window.open(authUrl, 'google-auth', 'width=500,height=600');
      
      // Listen for auth completion
      const checkClosed = setInterval(() => {
        if (authWindow?.closed) {
          clearInterval(checkClosed);
          fetchConnections(); // Refresh connections
        }
      }, 1000);
      
    } catch (err: any) {
      setError(err.message || 'Failed to connect calendar');
    }
  };

  const handleDisconnectCalendar = async (connectionId: number) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      
      // API call to disconnect calendar
      const response = await fetch(`http://localhost:8000/admin/calendar/disconnect/${connectionId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to disconnect calendar');
      }

      await fetchConnections();
    } catch (err: any) {
      setError(err.message || 'Failed to disconnect calendar');
    }
  };

  const handleSyncCalendar = async (connectionId: number) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      
      // Update connection status to syncing
      setConnections(prev => 
        prev.map(conn => 
          conn.id === connectionId 
            ? { ...conn, connection_status: 'syncing' as const }
            : conn
        )
      );

      const response = await fetch(`http://localhost:8000/admin/calendar/sync/${connectionId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to sync calendar');
      }

      await fetchConnections();
    } catch (err: any) {
      setError(err.message || 'Failed to sync calendar');
      await fetchConnections();
    }
  };

  const handleSyncAllCalendars = async () => {
    try {
      setSyncingAll(true);
      const token = localStorage.getItem('admin_access_token');
      
      const response = await fetch('http://localhost:8000/admin/calendar/sync-all', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to sync all calendars');
      }

      await fetchConnections();
    } catch (err: any) {
      setError(err.message || 'Failed to sync all calendars');
    } finally {
      setSyncingAll(false);
    }
  };

  const filteredConnections = connections.filter(connection => {
    const matchesSearch = !searchTerm || 
      connection.doctor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      connection.doctor_email.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = filterStatus === 'all' || connection.connection_status === filterStatus;

    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-100 text-green-800';
      case 'disconnected':
        return 'bg-red-100 text-red-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'syncing':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-4 w-4" />;
      case 'disconnected':
        return <XCircle className="h-4 w-4" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      case 'syncing':
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getSyncStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'pending':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const connectedCount = connections.filter(conn => conn.connection_status === 'connected').length;
  const totalCount = connections.length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Calendar Integration</h1>
          <p className="text-gray-600">Manage Google Calendar connections and synchronization</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowBulkSetupModal(true)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
          >
            <Settings className="h-4 w-4" />
            <span>Bulk Setup</span>
          </button>
          <button
            onClick={handleSyncAllCalendars}
            disabled={syncingAll}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${syncingAll ? 'animate-spin' : ''}`} />
            <span>Sync All</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Connected</p>
              <p className="text-2xl font-bold text-green-600">{connectedCount}</p>
            </div>
            <div className="p-3 rounded-full bg-green-100">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Disconnected</p>
              <p className="text-2xl font-bold text-red-600">{totalCount - connectedCount}</p>
            </div>
            <div className="p-3 rounded-full bg-red-100">
              <XCircle className="h-6 w-6 text-red-600" />
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Events</p>
              <p className="text-2xl font-bold text-blue-600">
                {connections.reduce((sum, conn) => sum + conn.events_synced, 0)}
              </p>
            </div>
            <div className="p-3 rounded-full bg-blue-100">
              <Calendar className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Sync Rate</p>
              <p className="text-2xl font-bold text-purple-600">
                {totalCount > 0 ? Math.round((connectedCount / totalCount) * 100) : 0}%
              </p>
            </div>
            <div className="p-3 rounded-full bg-purple-100">
              <Activity className="h-6 w-6 text-purple-600" />
            </div>
          </div>
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

      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <AlertCircle className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search doctors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center space-x-2">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="connected">Connected</option>
              <option value="disconnected">Disconnected</option>
              <option value="error">Error</option>
              <option value="syncing">Syncing</option>
            </select>
            <button
              onClick={fetchConnections}
              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Connections Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Doctor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Calendar
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Sync
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Events
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredConnections.map((connection) => (
                <tr key={connection.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm font-medium">
                          {connection.doctor_name.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {connection.doctor_name}
                        </div>
                        <div className="text-sm text-gray-500">{connection.doctor_email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {connection.calendar_name || 'Not connected'}
                    </div>
                    {connection.google_calendar_id && (
                      <div className="text-sm text-gray-500 flex items-center">
                        <Chrome className="h-4 w-4 mr-1" />
                        {connection.google_calendar_id}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(connection.connection_status)}`}>
                      {getStatusIcon(connection.connection_status)}
                      <span className="ml-1 capitalize">{connection.connection_status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {connection.last_sync ? (
                      <div>
                        <div>{formatDate(connection.last_sync)}</div>
                        <div className={`text-xs ${getSyncStatusColor(connection.sync_status)}`}>
                          {connection.sync_status}
                        </div>
                      </div>
                    ) : (
                      'Never'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {connection.events_synced}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      {connection.connection_status === 'connected' ? (
                        <>
                          <button
                            onClick={() => handleSyncCalendar(connection.id)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Sync calendar"
                          >
                            <RefreshCw className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => {
                              setSelectedConnection(connection);
                              setShowDetailsModal(true);
                            }}
                            className="text-gray-600 hover:text-gray-800"
                            title="View details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDisconnectCalendar(connection.id)}
                            className="text-red-600 hover:text-red-800"
                            title="Disconnect calendar"
                          >
                            <Unlink className="h-4 w-4" />
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handleConnectCalendar(connection.doctor_id)}
                          className="text-green-600 hover:text-green-800"
                          title="Connect calendar"
                        >
                          <Link className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty State */}
      {filteredConnections.length === 0 && !loading && (
        <div className="text-center py-12">
          <Calendar className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No calendar connections found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm ? 'Try adjusting your search terms' : 'Calendar connections will appear here'}
          </p>
        </div>
      )}

      {/* Modals */}
      {showBulkSetupModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Bulk Calendar Setup</h3>
            <p className="text-gray-600 mb-4">Setup Google Calendar for multiple doctors at once.</p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Google Workspace Domain
                </label>
                <input
                  type="text"
                  placeholder="hospital.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Calendar Naming Pattern
                </label>
                <input
                  type="text"
                  placeholder="Dr. {name} - {department}"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => setShowBulkSetupModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Setup
              </button>
            </div>
          </div>
        </div>
      )}

      {showDetailsModal && selectedConnection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">
              Calendar Details: {selectedConnection.doctor_name}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Connection Info</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Doctor:</span> {selectedConnection.doctor_name}</div>
                  <div><span className="font-medium">Email:</span> {selectedConnection.doctor_email}</div>
                  <div><span className="font-medium">Calendar ID:</span> {selectedConnection.google_calendar_id || 'N/A'}</div>
                  <div><span className="font-medium">Calendar Name:</span> {selectedConnection.calendar_name || 'N/A'}</div>
                  <div><span className="font-medium">Status:</span> {selectedConnection.connection_status}</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Sync Information</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Last Sync:</span> {selectedConnection.last_sync ? formatDate(selectedConnection.last_sync) : 'Never'}</div>
                  <div><span className="font-medium">Sync Status:</span> {selectedConnection.sync_status}</div>
                  <div><span className="font-medium">Events Synced:</span> {selectedConnection.events_synced}</div>
                  <div><span className="font-medium">Created:</span> {formatDate(selectedConnection.created_at)}</div>
                  <div><span className="font-medium">Updated:</span> {formatDate(selectedConnection.updated_at)}</div>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => {
                  setShowDetailsModal(false);
                  setSelectedConnection(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
              {selectedConnection.connection_status === 'connected' && (
                <button
                  onClick={() => handleSyncCalendar(selectedConnection.id)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Sync Now
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarIntegration; 