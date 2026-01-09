import React, { useEffect, useState } from 'react';
import { useHospital } from '../contexts/HospitalContext';
import { apiFetch } from '../utils/api';
import { Plus, Search, Edit3, Trash2, RefreshCw } from 'lucide-react';

interface Department {
  id: number;
  name: string;
  hospital_id: number;
  doctor_count: number;
}

const DepartmentsManagement: React.FC = () => {
  const { hospital } = useHospital();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState<Department | null>(null);
  const [departmentName, setDepartmentName] = useState('');

  useEffect(() => {
    fetchDepartments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hospital]);

  const fetchDepartments = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_access_token');
      const slug = hospital?.slug || '';
      const endpoint = slug ? `/admin/departments?slug=${encodeURIComponent(slug)}` : '/admin/departments';
      const result = await apiFetch(endpoint, {
        slug: '',
        token: token || undefined,
      });
      setDepartments(Array.isArray(result) ? result : result.departments || []);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch departments');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_access_token');
      const slug = hospital?.slug || '';
      const endpoint = slug ? `/admin/departments?slug=${encodeURIComponent(slug)}` : '/admin/departments';
      await apiFetch(endpoint, {
        slug: '',
        token: token || undefined,
        method: 'POST',
        body: { name: departmentName },
      });
      setDepartmentName('');
      setShowCreateModal(false);
      await fetchDepartments();
    } catch (err: any) {
      setError(err.message || 'Failed to create department');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedDepartment) return;
    try {
      setLoading(true);
      const token = localStorage.getItem('admin_access_token');
      const slug = hospital?.slug || '';
      const endpoint = slug
        ? `/admin/departments/${selectedDepartment.id}?slug=${encodeURIComponent(slug)}`
        : `/admin/departments/${selectedDepartment.id}`;
      await apiFetch(endpoint, {
        slug: '',
        token: token || undefined,
        method: 'DELETE',
      });
      setShowDeleteModal(false);
      setSelectedDepartment(null);
      await fetchDepartments();
    } catch (err: any) {
      setError(err.message || 'Failed to delete department');
    } finally {
      setLoading(false);
    }
  };

  const filteredDepartments = departments.filter((dept) =>
    dept.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Departments</h1>
          <p className="text-gray-600">Manage departments for this hospital</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchDepartments}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Add Department</span>
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
          <span className="text-red-700 text-sm">{error}</span>
          <button
            className="text-red-600 hover:text-red-800"
            onClick={() => setError('')}
          >
            ×
          </button>
        </div>
      )}

      {/* Search */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search departments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Departments list */}
      <div
        className="bg-white rounded-lg shadow-sm admin-scrollbar"
        style={{ maxHeight: '60vh', overflowY: 'auto' }}
      >
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Doctors
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredDepartments.map((dept) => (
              <tr key={dept.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {dept.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {dept.doctor_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm space-x-2">
                  <button
                    className="px-2 py-1 border rounded hover:bg-gray-50 inline-flex items-center space-x-1 text-gray-700"
                    onClick={() => {
                      setSelectedDepartment(dept);
                      setShowDeleteModal(true);
                    }}
                    disabled={dept.doctor_count > 0}
                    title={
                      dept.doctor_count > 0
                        ? 'Reassign or remove doctors before deleting'
                        : 'Delete department'
                    }
                  >
                    <Trash2 className="h-4 w-4" />
                    <span>Delete</span>
                  </button>
                </td>
              </tr>
            ))}
            {filteredDepartments.length === 0 && (
              <tr>
                <td
                  colSpan={3}
                  className="px-6 py-4 text-center text-sm text-gray-500"
                >
                  No departments found. Create your first department to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Create modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">Add Department</h2>
            <input
              type="text"
              value={departmentName}
              onChange={(e) => setDepartmentName(e.target.value)}
              placeholder="Department name"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setDepartmentName('');
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!departmentName.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete modal */}
      {showDeleteModal && selectedDepartment && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">Delete Department</h2>
            <p className="text-sm text-gray-600">
              Are you sure you want to delete{' '}
              <span className="font-semibold">{selectedDepartment.name}</span>? This
              action cannot be undone.
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setSelectedDepartment(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DepartmentsManagement;


