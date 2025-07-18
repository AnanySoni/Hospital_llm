import React from 'react';
import { Appointment } from '../types';

interface AppointmentCardProps {
  appointment: Appointment;
  onReschedule: (appointment: Appointment) => void;
  onCancel: (appointmentId: number) => void;
  isLoading?: boolean;
}

const AppointmentCard: React.FC<AppointmentCardProps> = ({
  appointment,
  onReschedule,
  onCancel,
  isLoading = false
}) => {
  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Format time for display
  const formatTime = (timeString: string) => {
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const handleCancel = () => {
    if (isLoading) return; // Prevent multiple clicks
    if (window.confirm('Are you sure you want to cancel this appointment?')) {
      onCancel(appointment.id);
    }
  };

  return (
    <div className="bg-green-900/20 border border-green-600/30 rounded-lg p-4 mb-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center">
            <i className="fas fa-calendar-check text-white text-sm"></i>
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Appointment Confirmed</h3>
            <p className="text-green-400 text-xs">ID: #{appointment.id}</p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          appointment.status === 'confirmed' 
            ? 'bg-green-600/20 text-green-400' 
            : 'bg-yellow-600/20 text-yellow-400'
        }`}>
          {appointment.status}
        </span>
      </div>

      {/* Appointment Details */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center space-x-3">
          <i className="fas fa-user-md text-blue-400 w-4"></i>
          <span className="text-white text-sm font-medium">{appointment.doctor_name}</span>
        </div>
        
        <div className="flex items-center space-x-3">
          <i className="fas fa-user text-gray-400 w-4"></i>
          <span className="text-gray-300 text-sm">{appointment.patient_name}</span>
        </div>

        <div className="flex items-center space-x-3">
          <i className="fas fa-calendar text-gray-400 w-4"></i>
          <span className="text-gray-300 text-sm">{formatDate(appointment.appointment_date)}</span>
        </div>

        <div className="flex items-center space-x-3">
          <i className="fas fa-clock text-gray-400 w-4"></i>
          <span className="text-gray-300 text-sm">{formatTime(appointment.appointment_time)}</span>
        </div>

        {appointment.symptoms && (
          <div className="flex items-start space-x-3">
            <i className="fas fa-notes-medical text-gray-400 w-4 mt-0.5"></i>
            <span className="text-gray-300 text-sm">
              <span className="font-medium">Symptoms:</span> {appointment.symptoms}
            </span>
          </div>
        )}

        {appointment.notes && (
          <div className="flex items-start space-x-3">
            <i className="fas fa-comment text-gray-400 w-4 mt-0.5"></i>
            <span className="text-gray-300 text-sm">
              <span className="font-medium">Notes:</span> {appointment.notes}
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={() => onReschedule(appointment)}
          disabled={isLoading}
          className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center space-x-2 text-sm"
        >
          <i className="fas fa-edit text-xs"></i>
          <span>Reschedule</span>
        </button>
        
        <button
          onClick={handleCancel}
          disabled={isLoading}
          className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white font-medium py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center space-x-2 text-sm"
        >
          <i className="fas fa-times text-xs"></i>
          <span>Cancel</span>
        </button>
      </div>
    </div>
  );
};

export default AppointmentCard; 