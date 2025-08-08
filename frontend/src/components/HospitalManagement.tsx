import React, { useState, useEffect } from 'react';
import { useHospital } from '../contexts/HospitalContext';
import { apiFetch } from '../utils/api';
import { 
  Hospital, 
  Plus, 
  Search, 
  Edit3, 
  Trash2, 
  Settings, 
  Users, 
  Calendar,
  Activity,
  Globe,
  Mail,
  Phone,
  MapPin,
  CreditCard,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react';

interface HospitalData {
  id: number;
  hospital_id: string;
  name: string;
  display_name: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  subscription_plan: string;
  subscription_status: string;
  subscription_expires: string | null;
  max_doctors: number;
  max_patients: number;
  google_workspace_domain: string | null;
  features_enabled: string[];
  created_at: string;
  updated_at: string;
  admin_users_count: number;
  doctors_count: number;
  patients_count: number;
}

interface HospitalManagementProps {
  currentUser?: {
    id: number;
    is_super_admin: boolean;
    hospital_id: number;
  };
}

const HospitalManagement: React.FC<HospitalManagementProps> = ({ currentUser }) => {
  const [hospitals, setHospitals] = useState<HospitalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedHospital, setSelectedHospital] = useState<HospitalData | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const { hospital } = useHospital();

  useEffect(() => {
    fetchHospitals();
  }, [hospital]);

  const fetchHospitals = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_access_token');
      // For superadmin, fetch all hospitals; for hospital admin, fetch only their hospital
      let hospitalsData = [];
      if (hospital?.slug) {
        hospitalsData = await apiFetch('/admin/hospitals', {
          slug: hospital.slug,
        token: token || undefined
        });
      }
      setHospitals(Array.isArray(hospitalsData) ? hospitalsData : hospitalsData.hospitals || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch hospitals');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateHospital = async (hospitalData: any) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      await apiFetch('/admin/hospitals', {
        slug: hospital?.slug || '',
        token: token ?? undefined,
        method: 'POST',
        body: hospitalData
      });
      await fetchHospitals();
      setShowCreateModal(false);
    } catch (err: any) {
      setError(err.message || 'Failed to create hospital');
    }
  };

  const handleUpdateHospital = async (hospitalId: number, hospitalData: any) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      await apiFetch(`/admin/hospitals/${hospitalId}`, {
        slug: hospital?.slug || '',
        token: token ?? undefined,
        method: 'PUT',
        body: hospitalData
      });
      await fetchHospitals();
      setShowEditModal(false);
      setSelectedHospital(null);
    } catch (err: any) {
      setError(err.message || 'Failed to update hospital');
    }
  };

  const handleDeleteHospital = async (hospitalId: number) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      await apiFetch(`/admin/hospitals/${hospitalId}`, {
        slug: hospital?.slug || '',
        token: token ?? undefined,
        method: 'DELETE'
      });
      await fetchHospitals();
      setShowDeleteModal(false);
      setSelectedHospital(null);
    } catch (err: any) {
      setError(err.message || 'Failed to delete hospital');
    }
  };

  const filteredHospitals = hospitals.filter(hospital => {
    return !searchTerm || 
      hospital.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hospital.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      hospital.hospital_id.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const getSubscriptionStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'expired':
        return 'bg-red-100 text-red-800';
      case 'trial':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSubscriptionStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
        return <CheckCircle className="h-4 w-4" />;
      case 'expired':
        return <XCircle className="h-4 w-4" />;
      case 'trial':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (!currentUser?.is_super_admin) {
    return (
      <div className="text-center py-12">
        <Hospital className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-500">
          Only super administrators can access hospital management.
        </p>
      </div>
    );
  }

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
          <h1 className="text-2xl font-bold text-gray-800">Hospital Management</h1>
          <p className="text-gray-600">Manage hospitals, subscriptions, and configurations</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Add Hospital</span>
        </button>
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

      {/* Search */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search hospitals..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={fetchHospitals}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Hospitals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 admin-scrollbar" style={{maxHeight: '60vh', overflowY: 'auto'}}>
        {filteredHospitals.map((hospital) => (
          <div key={hospital.id} className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div className="p-6">
              {/* Hospital Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Hospital className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{hospital.display_name}</h3>
                    <p className="text-sm text-gray-500">ID: {hospital.hospital_id}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => {
                      setSelectedHospital(hospital);
                      setShowDetailsModal(true);
                    }}
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                    title="View details"
                  >
                    <Activity className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedHospital(hospital);
                      setShowEditModal(true);
                    }}
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Edit hospital"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedHospital(hospital);
                      setShowDeleteModal(true);
                    }}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete hospital"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Hospital Info */}
              <div className="space-y-2 mb-4">
                {hospital.address && (
                  <div className="flex items-center text-sm text-gray-600">
                    <MapPin className="h-4 w-4 mr-2" />
                    <span className="truncate">{hospital.address}</span>
                  </div>
                )}
                {hospital.email && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Mail className="h-4 w-4 mr-2" />
                    <span className="truncate">{hospital.email}</span>
                  </div>
                )}
                {hospital.phone && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="h-4 w-4 mr-2" />
                    <span>{hospital.phone}</span>
                  </div>
                )}
                {hospital.website && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Globe className="h-4 w-4 mr-2" />
                    <a href={hospital.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 truncate">
                      {hospital.website}
                    </a>
                  </div>
                )}
              </div>

              {/* Subscription Status */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Subscription</span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSubscriptionStatusColor(hospital.subscription_status)}`}>
                    {getSubscriptionStatusIcon(hospital.subscription_status)}
                    <span className="ml-1 capitalize">{hospital.subscription_status}</span>
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Plan:</span>
                    <span className="font-medium capitalize">{hospital.subscription_plan}</span>
                  </div>
                  {hospital.subscription_expires && (
                    <div className="flex justify-between">
                      <span>Expires:</span>
                      <span className="font-medium">{formatDate(hospital.subscription_expires)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Usage Stats */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{hospital.admin_users_count}</div>
                  <div className="text-xs text-gray-500">Admin Users</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{hospital.doctors_count}</div>
                  <div className="text-xs text-gray-500">Doctors</div>
                </div>
              </div>

              {/* Limits */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Doctor Limit:</span>
                  <span className="font-medium">{hospital.doctors_count} / {hospital.max_doctors}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Patient Limit:</span>
                  <span className="font-medium">{hospital.patients_count} / {hospital.max_patients}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredHospitals.length === 0 && !loading && (
        <div className="text-center py-12">
          <Hospital className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No hospitals found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm ? 'Try adjusting your search terms' : 'Get started by adding a new hospital'}
          </p>
        </div>
      )}

      {/* Modals - Placeholder implementations */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Add New Hospital</h3>
            <p className="text-gray-600 mb-4">Hospital creation form will be implemented here.</p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {showEditModal && selectedHospital && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Edit Hospital: {selectedHospital.display_name}</h3>
            <p className="text-gray-600 mb-4">Hospital editing form will be implemented here.</p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedHospital(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteModal && selectedHospital && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Delete Hospital</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete {selectedHospital.display_name}? This action cannot be undone and will remove all associated data.
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setSelectedHospital(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteHospital(selectedHospital.id)}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {showDetailsModal && selectedHospital && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Hospital Details: {selectedHospital.display_name}</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Name:</span> {selectedHospital.name}</div>
                  <div><span className="font-medium">Display Name:</span> {selectedHospital.display_name}</div>
                  <div><span className="font-medium">ID:</span> {selectedHospital.hospital_id}</div>
                  <div><span className="font-medium">Created:</span> {formatDate(selectedHospital.created_at)}</div>
                  <div><span className="font-medium">Updated:</span> {formatDate(selectedHospital.updated_at)}</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Subscription</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Plan:</span> {selectedHospital.subscription_plan}</div>
                  <div><span className="font-medium">Status:</span> {selectedHospital.subscription_status}</div>
                  {selectedHospital.subscription_expires && (
                    <div><span className="font-medium">Expires:</span> {formatDate(selectedHospital.subscription_expires)}</div>
                  )}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Limits & Usage</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Max Doctors:</span> {selectedHospital.max_doctors}</div>
                  <div><span className="font-medium">Max Patients:</span> {selectedHospital.max_patients}</div>
                  <div><span className="font-medium">Admin Users:</span> {selectedHospital.admin_users_count}</div>
                  <div><span className="font-medium">Doctors:</span> {selectedHospital.doctors_count}</div>
                  <div><span className="font-medium">Patients:</span> {selectedHospital.patients_count}</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Features</h4>
                <div className="flex flex-wrap gap-1">
                  {selectedHospital.features_enabled.map((feature, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setShowDetailsModal(false);
                  setSelectedHospital(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HospitalManagement; 