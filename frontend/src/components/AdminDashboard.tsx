import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Hospital, 
  Calendar, 
  BarChart3, 
  Settings, 
  LogOut, 
  Menu, 
  X, 
  UserPlus, 
  Shield,
  Activity,
  Bell
} from 'lucide-react';

// Import the management components
import AdminUsersManagement from './AdminUsersManagement';
import HospitalManagement from './HospitalManagement';
import DoctorManagement from './DoctorManagement';
import CalendarIntegration from './CalendarIntegration';
import AnalyticsDashboard from './AnalyticsDashboard';

interface AdminDashboardProps {
  user?: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    hospital_id: number;
    is_super_admin: boolean;
  };
  onLogout: () => void;
}

interface NavigationItem {
  id: string;
  name: string;
  icon: React.ComponentType<any>;
  path: string;
  permission?: string;
  superAdminOnly?: boolean;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notifications, setNotifications] = useState(3);

  const navigationItems: NavigationItem[] = [
    {
      id: 'dashboard',
      name: 'Dashboard',
      icon: BarChart3,
      path: '/admin/dashboard',
    },
    {
      id: 'users',
      name: 'Admin Users',
      icon: Users,
      path: '/admin/users',
      permission: 'admin:read',
    },
    {
      id: 'hospitals',
      name: 'Hospitals',
      icon: Hospital,
      path: '/admin/hospitals',
      permission: 'hospital:read',
      superAdminOnly: true,
    },
    {
      id: 'doctors',
      name: 'Doctors',
      icon: UserPlus,
      path: '/admin/doctors',
      permission: 'doctor:read',
    },
    {
      id: 'calendar',
      name: 'Calendar Setup',
      icon: Calendar,
      path: '/admin/calendar',
      permission: 'calendar:manage',
    },
    {
      id: 'analytics',
      name: 'Analytics',
      icon: Activity,
      path: '/admin/analytics',
      permission: 'analytics:read',
    },
    {
      id: 'roles',
      name: 'Roles & Permissions',
      icon: Shield,
      path: '/admin/roles',
      permission: 'role:read',
    },
    {
      id: 'settings',
      name: 'Settings',
      icon: Settings,
      path: '/admin/settings',
    },
  ];

  const filteredNavItems = navigationItems.filter(item => {
    if (item.superAdminOnly && !user?.is_super_admin) {
      return false;
    }
    return true;
  });

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardContent user={user} />;
      case 'users':
        return <UsersContent user={user} />;
      case 'hospitals':
        return <HospitalsContent user={user} />;
      case 'doctors':
        return <DoctorsContent user={user} />;
      case 'calendar':
        return <CalendarContent user={user} />;
      case 'analytics':
        return <AnalyticsContent user={user} />;
      case 'roles':
        return <RolesContent user={user} />;
      case 'settings':
        return <SettingsContent user={user} />;
      default:
        return <DashboardContent user={user} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white shadow-lg transition-all duration-300 ease-in-out`}>
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className={`${sidebarOpen ? 'block' : 'hidden'} flex items-center space-x-2`}>
              <Hospital className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-800">Hospital Admin</span>
            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        <nav className="mt-8">
          {filteredNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center px-4 py-3 text-left hover:bg-blue-50 transition-colors ${
                  activeTab === item.id ? 'bg-blue-50 border-r-2 border-blue-600 text-blue-600' : 'text-gray-600'
                }`}
              >
                <Icon className="h-5 w-5 mr-3" />
                {sidebarOpen && <span className="font-medium">{item.name}</span>}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 capitalize">
                {activeTab === 'dashboard' ? 'Dashboard' : activeTab}
              </h1>
              <p className="text-sm text-gray-600">
                Welcome back, {user?.first_name} {user?.last_name}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <div className="relative">
                <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                  <Bell className="h-5 w-5 text-gray-600" />
                  {notifications > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                      {notifications}
                    </span>
                  )}
                </button>
              </div>

              {/* User Info */}
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-800">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {user?.is_super_admin ? 'Super Admin' : 'Admin'}
                  </p>
                </div>
                <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
                  </span>
                </div>
              </div>

              {/* Logout */}
              <button
                onClick={onLogout}
                className="p-2 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors text-gray-600"
                title="Logout"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 p-6 overflow-y-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};

// Dashboard Content Component
const DashboardContent: React.FC<{ user?: any }> = ({ user }) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Doctors"
          value="24"
          change="+2 this month"
          icon={UserPlus}
          color="blue"
        />
        <StatCard
          title="Active Patients"
          value="1,234"
          change="+15% this week"
          icon={Users}
          color="green"
        />
        <StatCard
          title="Appointments Today"
          value="56"
          change="+8 from yesterday"
          icon={Calendar}
          color="purple"
        />
        <StatCard
          title="System Health"
          value="99.9%"
          change="All systems operational"
          icon={Activity}
          color="emerald"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            <ActivityItem
              action="New doctor registered"
              user="Dr. Sarah Johnson"
              time="2 hours ago"
            />
            <ActivityItem
              action="Calendar connected"
              user="Dr. Mike Chen"
              time="4 hours ago"
            />
            <ActivityItem
              action="Patient appointment booked"
              user="John Smith"
              time="6 hours ago"
            />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <QuickActionButton
              title="Add New Doctor"
              description="Register a new doctor in the system"
              icon={UserPlus}
              onClick={() => {}}
            />
            <QuickActionButton
              title="Setup Calendar"
              description="Configure Google Calendar integration"
              icon={Calendar}
              onClick={() => {}}
            />
            <QuickActionButton
              title="View Analytics"
              description="Check system performance metrics"
              icon={BarChart3}
              onClick={() => {}}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// Content components using the management interfaces
const UsersContent: React.FC<{ user?: any }> = ({ user }) => (
  <AdminUsersManagement currentUser={user} />
);

const HospitalsContent: React.FC<{ user?: any }> = ({ user }) => (
  <HospitalManagement currentUser={user} />
);

const DoctorsContent: React.FC<{ user?: any }> = ({ user }) => (
  <DoctorManagement currentUser={user} />
);

const CalendarContent: React.FC<{ user?: any }> = ({ user }) => (
  <CalendarIntegration currentUser={user} />
);

const AnalyticsContent: React.FC<{ user?: any }> = ({ user }) => (
  <AnalyticsDashboard currentUser={user} />
);

const RolesContent: React.FC<{ user?: any }> = ({ user }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm">
    <h2 className="text-xl font-semibold text-gray-800 mb-4">Roles & Permissions</h2>
    <p className="text-gray-600">Role-based access control interface will be implemented here.</p>
  </div>
);

const SettingsContent: React.FC<{ user?: any }> = ({ user }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm">
    <h2 className="text-xl font-semibold text-gray-800 mb-4">System Settings</h2>
    <p className="text-gray-600">System configuration interface will be implemented here.</p>
  </div>
);

// Helper Components
const StatCard: React.FC<{
  title: string;
  value: string;
  change: string;
  icon: React.ComponentType<any>;
  color: string;
}> = ({ title, value, change, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    emerald: 'bg-emerald-100 text-emerald-600',
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-800">{value}</p>
          <p className="text-sm text-gray-500">{change}</p>
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color as keyof typeof colorClasses]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
};

const ActivityItem: React.FC<{
  action: string;
  user: string;
  time: string;
}> = ({ action, user, time }) => (
  <div className="flex items-center space-x-3 py-2">
    <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
    <div className="flex-1">
      <p className="text-sm font-medium text-gray-800">{action}</p>
      <p className="text-xs text-gray-500">{user} • {time}</p>
    </div>
  </div>
);

const QuickActionButton: React.FC<{
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  onClick: () => void;
}> = ({ title, description, icon: Icon, onClick }) => (
  <button
    onClick={onClick}
    className="w-full p-4 text-left border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
  >
    <div className="flex items-center space-x-3">
      <div className="p-2 bg-blue-100 rounded-lg">
        <Icon className="h-5 w-5 text-blue-600" />
      </div>
      <div>
        <h4 className="font-medium text-gray-800">{title}</h4>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
    </div>
  </button>
);

export default AdminDashboard; 