import React, { useState, useEffect } from 'react';
import { useHospital } from '../contexts/HospitalContext';
import { apiFetch } from '../utils/api';
import { 
  UserPlus, 
  Plus, 
  Search, 
  Edit3, 
  Trash2, 
  Calendar, 
  Mail, 
  Phone, 
  MapPin,
  Stethoscope,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Upload,
  Download,
  Filter,
  Star,
  Award
} from 'lucide-react';

interface Doctor {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  specialization: string;
  department: string;
  experience_years: number;
  qualification: string;
  consultation_fee: number;
  languages: string[];
  availability_status: 'available' | 'busy' | 'offline';
  calendar_connected: boolean;
  google_calendar_id: string | null;
  rating: number;
  total_consultations: number;
  created_at: string;
  updated_at: string;
  working_hours: {
    [key: string]: {
      start: string;
      end: string;
      is_available: boolean;
    };
  };
}

interface DoctorManagementProps {
  currentUser?: {
    id: number;
    is_super_admin: boolean;
    hospital_id: number;
  };
}

const DoctorManagement: React.FC<DoctorManagementProps> = ({ currentUser }) => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showBulkUploadModal, setShowBulkUploadModal] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [filterDepartment, setFilterDepartment] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterCalendar, setFilterCalendar] = useState<string>('all');

  const pageSize = 12;
  const departments = ['Cardiology', 'Neurology', 'Pediatrics', 'Orthopedics', 'Dermatology', 'General Medicine'];
  const specializations = ['Cardiologist', 'Neurologist', 'Pediatrician', 'Orthopedic Surgeon', 'Dermatologist', 'General Physician'];

  const { hospital } = useHospital();

  useEffect(() => {
    fetchDoctors();
  }, [currentPage, searchTerm, filterDepartment, filterStatus, filterCalendar, hospital]);

  const fetchDoctors = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_access_token');
      // Use hospital slug for API call
      const doctors = await apiFetch('/admin/doctors', {
        slug: hospital?.slug || '',
        token: token || undefined
      });
      setDoctors(Array.isArray(doctors) ? doctors : doctors.doctors || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch doctors');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectCalendar = async (doctorId: number) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      // This would typically redirect to Google OAuth
      window.open(`http://localhost:8000/auth/google/login?doctor_id=${doctorId}`, '_blank');
    } catch (err: any) {
      setError(err.message || 'Failed to connect calendar');
    }
  };

  const handleCreateDoctor = async (doctorData: any) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      // API call would go here
      await fetchDoctors();
      setShowCreateModal(false);
    } catch (err: any) {
      setError(err.message || 'Failed to create doctor');
    }
  };

  const handleUpdateDoctor = async (doctorId: number, doctorData: any) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      // API call would go here
      await fetchDoctors();
      setShowEditModal(false);
      setSelectedDoctor(null);
    } catch (err: any) {
      setError(err.message || 'Failed to update doctor');
    }
  };

  const handleDeleteDoctor = async (doctorId: number) => {
    try {
      const token = localStorage.getItem('admin_access_token');
      // API call would go here
      await fetchDoctors();
      setShowDeleteModal(false);
      setSelectedDoctor(null);
    } catch (err: any) {
      setError(err.message || 'Failed to delete doctor');
    }
  };

  const filteredDoctors = doctors.filter(doctor => {
    const matchesSearch = !searchTerm || 
      doctor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doctor.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doctor.specialization.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doctor.department.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDepartment = filterDepartment === 'all' || doctor.department === filterDepartment;
    const matchesStatus = filterStatus === 'all' || doctor.availability_status === filterStatus;
    const matchesCalendar = filterCalendar === 'all' || 
      (filterCalendar === 'connected' && doctor.calendar_connected) ||
      (filterCalendar === 'not_connected' && !doctor.calendar_connected);

    return matchesSearch && matchesDepartment && matchesStatus && matchesCalendar;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available':
        return 'bg-green-100 text-green-800';
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'offline':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available':
        return <CheckCircle className="h-4 w-4" />;
      case 'busy':
        return <AlertCircle className="h-4 w-4" />;
      case 'offline':
        return <XCircle className="h-4 w-4" />;
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
          <h1 className="text-2xl font-bold text-gray-800">Doctor Management</h1>
          <p className="text-gray-600">Manage doctors, their profiles, and calendar integrations</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowBulkUploadModal(true)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
          >
            <Upload className="h-4 w-4" />
            <span>Bulk Upload</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Add Doctor</span>
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

      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search doctors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              value={filterDepartment}
              onChange={(e) => setFilterDepartment(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Departments</option>
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="available">Available</option>
              <option value="busy">Busy</option>
              <option value="offline">Offline</option>
            </select>
            <select
              value={filterCalendar}
              onChange={(e) => setFilterCalendar(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Calendar</option>
              <option value="connected">Connected</option>
              <option value="not_connected">Not Connected</option>
            </select>
            <button
              onClick={fetchDoctors}
              className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Doctors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 admin-scrollbar" style={{maxHeight: '60vh', overflowY: 'auto'}}>
        {filteredDoctors.map((doctor) => (
          <div key={doctor.id} className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div className="p-6">
              {/* Doctor Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Stethoscope className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{doctor.name}</h3>
                    <p className="text-sm text-gray-500">{doctor.specialization}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => {
                      setSelectedDoctor(doctor);
                      setShowDetailsModal(true);
                    }}
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                    title="View details"
                  >
                    <UserPlus className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedDoctor(doctor);
                      setShowEditModal(true);
                    }}
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Edit doctor"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedDoctor(doctor);
                      setShowDeleteModal(true);
                    }}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                    title="Delete doctor"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Doctor Info */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <Mail className="h-4 w-4 mr-2" />
                  <span className="truncate">{doctor.email}</span>
                </div>
                {doctor.phone && (
                  <div className="flex items-center text-sm text-gray-600">
                    <Phone className="h-4 w-4 mr-2" />
                    <span>{doctor.phone}</span>
                  </div>
                )}
                <div className="flex items-center text-sm text-gray-600">
                  <Award className="h-4 w-4 mr-2" />
                  <span>{doctor.qualification}</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Clock className="h-4 w-4 mr-2" />
                  <span>{doctor.experience_years} years experience</span>
                </div>
              </div>

              {/* Status and Calendar */}
              <div className="flex items-center justify-between mb-4">
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(doctor.availability_status)}`}>
                  {getStatusIcon(doctor.availability_status)}
                  <span className="ml-1 capitalize">{doctor.availability_status}</span>
                </span>
                <div className="flex items-center space-x-2">
                  {doctor.calendar_connected ? (
                    <div className="flex items-center text-green-600">
                      <Calendar className="h-4 w-4 mr-1" />
                      <span className="text-xs">Connected</span>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleConnectCalendar(doctor.id)}
                      className="flex items-center text-blue-600 hover:text-blue-800 text-xs"
                    >
                      <Calendar className="h-4 w-4 mr-1" />
                      <span>Connect</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Rating and Stats */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-1">
                  <Star className="h-4 w-4 text-yellow-400 fill-current" />
                  <span className="text-sm font-medium">{doctor.rating}</span>
                </div>
                <div className="text-sm text-gray-500">
                  {doctor.total_consultations} consultations
                </div>
              </div>

              {/* Fee */}
              <div className="mt-2 text-center">
                <span className="text-lg font-bold text-green-600">${doctor.consultation_fee}</span>
                <span className="text-sm text-gray-500 ml-1">per consultation</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredDoctors.length === 0 && !loading && (
        <div className="text-center py-12">
          <Stethoscope className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No doctors found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm ? 'Try adjusting your search terms' : 'Get started by adding a new doctor'}
          </p>
        </div>
      )}

      {/* Modals - Placeholder implementations */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Add New Doctor</h3>
            <p className="text-gray-600 mb-4">Doctor creation form will be implemented here.</p>
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

      {showBulkUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Bulk Upload Doctors</h3>
            <p className="text-gray-600 mb-4">Upload a CSV file with doctor information.</p>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">Drop your CSV file here or click to browse</p>
              <button className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Select File
              </button>
            </div>
            <div className="flex justify-end space-x-2 mt-4">
              <button
                onClick={() => setShowBulkUploadModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Upload
              </button>
            </div>
          </div>
        </div>
      )}

      {showDetailsModal && selectedDoctor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Doctor Details: {selectedDoctor.name}</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Name:</span> {selectedDoctor.name}</div>
                  <div><span className="font-medium">Email:</span> {selectedDoctor.email}</div>
                  <div><span className="font-medium">Phone:</span> {selectedDoctor.phone || 'N/A'}</div>
                  <div><span className="font-medium">Specialization:</span> {selectedDoctor.specialization}</div>
                  <div><span className="font-medium">Department:</span> {selectedDoctor.department}</div>
                  <div><span className="font-medium">Experience:</span> {selectedDoctor.experience_years} years</div>
                  <div><span className="font-medium">Qualification:</span> {selectedDoctor.qualification}</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-900 mb-2">Professional Details</h4>
                <div className="space-y-2 text-sm">
                  <div><span className="font-medium">Consultation Fee:</span> ${selectedDoctor.consultation_fee}</div>
                  <div><span className="font-medium">Languages:</span> {selectedDoctor.languages.join(', ')}</div>
                  <div><span className="font-medium">Rating:</span> {selectedDoctor.rating}/5</div>
                  <div><span className="font-medium">Total Consultations:</span> {selectedDoctor.total_consultations}</div>
                  <div><span className="font-medium">Calendar Connected:</span> {selectedDoctor.calendar_connected ? 'Yes' : 'No'}</div>
                  <div><span className="font-medium">Status:</span> {selectedDoctor.availability_status}</div>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <h4 className="font-medium text-gray-900 mb-2">Working Hours</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                {Object.entries(selectedDoctor.working_hours).map(([day, hours]) => (
                  <div key={day} className="flex justify-between">
                    <span className="capitalize font-medium">{day}:</span>
                    <span>
                      {hours.is_available ? `${hours.start} - ${hours.end}` : 'Closed'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => {
                  setShowDetailsModal(false);
                  setSelectedDoctor(null);
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

export default DoctorManagement; 