import React, { useState } from 'react';
import { Appointment } from '../types';

interface RescheduleFormProps {
  appointment: Appointment;
  onSubmit: (appointmentId: number, newDate: string, newTime: string) => void;
  onCancel: () => void;
  isLoading: boolean;
}

const RescheduleForm: React.FC<RescheduleFormProps> = ({
  appointment,
  onSubmit,
  onCancel,
  isLoading
}) => {
  const [formData, setFormData] = useState({
    appointment_date: appointment.appointment_date,
    appointment_time: appointment.appointment_time
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Get tomorrow's date as minimum date
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split('T')[0];

  // Generate available time slots
  const generateTimeSlots = () => {
    const slots = [];
    const startHour = 9; // 9 AM
    const endHour = 17; // 5 PM
    
    for (let hour = startHour; hour < endHour; hour++) {
      const hourStr = hour.toString().padStart(2, '0');
      slots.push(`${hourStr}:00`);
      slots.push(`${hourStr}:30`);
    }
    
    return slots;
  };

  const timeSlots = generateTimeSlots();

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.appointment_date) {
      newErrors.appointment_date = 'New appointment date is required';
    }

    if (!formData.appointment_time) {
      newErrors.appointment_time = 'New appointment time is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    onSubmit(appointment.id, formData.appointment_date, formData.appointment_time);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Format current appointment time for display
  const formatCurrentTime = (timeString: string) => {
    if (!timeString) return 'Not specified';
    
    try {
      // Handle both "HH:MM" and "HH:MM-HH:MM" formats
      const timePart = timeString.includes('-') ? timeString.split('-')[0] : timeString;
      const [hours, minutes] = timePart.split(':');
      
      if (!hours || !minutes) return timeString;
      
      const date = new Date();
      date.setHours(parseInt(hours), parseInt(minutes));
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return timeString || 'Not specified';
    }
  };

  return (
    <div className="bg-chat-assistant border border-chat-border rounded-lg p-4 mb-3">
      <div className="flex items-center space-x-3 mb-3">
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
          <i className="fas fa-edit text-white text-sm"></i>
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">Reschedule Appointment</h3>
          <p className="text-blue-400 text-xs">with {appointment.doctor_name}</p>
        </div>
      </div>

      {/* Current Appointment Info */}
      <div className="bg-chat-input rounded-md p-3 mb-3">
        <p className="text-xs font-medium text-gray-300 mb-2">Current Appointment:</p>
        <div className="space-y-1">
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <i className="fas fa-calendar w-3"></i>
            <span>{new Date(appointment.appointment_date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}</span>
          </div>
          <div className="flex items-center space-x-2 text-xs text-gray-400">
            <i className="fas fa-clock w-3"></i>
            <span>{formatCurrentTime(appointment.appointment_time)}</span>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        {/* New Date and Time */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              New Date *
            </label>
            <input
              type="date"
              value={formData.appointment_date}
              onChange={(e) => handleInputChange('appointment_date', e.target.value)}
              min={minDate}
              className="w-full px-3 py-2 bg-chat-input border border-chat-border rounded-md text-white focus:outline-none focus:border-blue-500 text-sm"
              disabled={isLoading}
            />
            {errors.appointment_date && (
              <p className="text-red-400 text-xs mt-1">{errors.appointment_date}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              New Time Slot *
            </label>
            <select
              value={formData.appointment_time}
              onChange={(e) => handleInputChange('appointment_time', e.target.value)}
              className="w-full px-3 py-2 bg-chat-input border border-chat-border rounded-md text-white focus:outline-none focus:border-blue-500 text-sm"
              disabled={isLoading}
              style={{ 
                colorScheme: 'dark',
                WebkitAppearance: 'none',
                MozAppearance: 'none',
                appearance: 'none'
              }}
            >
              <option value="" style={{ backgroundColor: '#2f2f2f', color: 'white' }}>
                Select new time slot
              </option>
              {timeSlots.map((slot) => (
                <option 
                  key={slot} 
                  value={slot} 
                  style={{ backgroundColor: '#2f2f2f', color: 'white' }}
                >
                  {new Date(`2000-01-01T${slot}:00`).toLocaleTimeString([], {
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true
                  })}
                </option>
              ))}
            </select>
            {errors.appointment_time && (
              <p className="text-red-400 text-xs mt-1">{errors.appointment_time}</p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex space-x-2 pt-1">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center space-x-2 text-sm"
          >
            {isLoading ? (
              <>
                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Rescheduling...</span>
              </>
            ) : (
              <>
                <i className="fas fa-check text-xs"></i>
                <span>Confirm Reschedule</span>
              </>
            )}
          </button>
          
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-700 text-white font-medium py-2 px-3 rounded-md transition-colors duration-200 flex items-center justify-center space-x-1 text-sm"
          >
            <i className="fas fa-times text-xs"></i>
            <span>Cancel</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default RescheduleForm; 