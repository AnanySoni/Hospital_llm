import React, { useState, useEffect, useCallback } from 'react';
import { Doctor, AppointmentData } from '../types';

interface TimeSlot {
  id: number;
  time_24: string;
  time_12: string;
  is_available: boolean;
}

interface AppointmentFormProps {
  doctor: Doctor;
  onSubmit: (data: AppointmentData) => void;
  onCancel: () => void;
}

const AppointmentForm: React.FC<AppointmentFormProps> = ({ doctor, onSubmit, onCancel }) => {
  const [patientName, setPatientName] = useState('');
  const [appointmentDate, setAppointmentDate] = useState('');
  const [appointmentTime, setAppointmentTime] = useState('');
  const [notes, setNotes] = useState('');
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);

  // Fetch available slots when date changes
  const fetchAvailableSlots = useCallback(async () => {
    if (!appointmentDate || !doctor.id) return;
    
    setIsLoadingSlots(true);
    try {
      const response = await fetch(`http://localhost:8000/doctors/${doctor.id}/available-slots?date=${appointmentDate}`);
      if (response.ok) {
        const slots = await response.json();
        setAvailableSlots(slots);
      } else {
        console.error('Failed to fetch available slots');
        setAvailableSlots([]);
    }
    } catch (error) {
      console.error('Error fetching available slots:', error);
      setAvailableSlots([]);
    } finally {
      setIsLoadingSlots(false);
    }
  }, [appointmentDate, doctor.id]);

  useEffect(() => {
    fetchAvailableSlots();
  }, [fetchAvailableSlots]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      doctor_id: doctor.id,
      patient_name: patientName,
      appointment_date: appointmentDate,
      appointment_time: appointmentTime,
      notes: notes,
      symptoms: '', // This might need to be sourced from the diagnostic session state
    });
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="bg-chat-assistant-muted rounded-lg p-4 text-white w-full max-w-lg">
      <h3 className="text-lg font-bold mb-3 text-gray-100">Book with {doctor.name}</h3>
      <p className="text-sm text-gray-400 mb-4">{doctor.specialization} - {doctor.location}</p>

      <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
          value={patientName}
          onChange={(e) => setPatientName(e.target.value)}
          placeholder="Full Name"
          required
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
        />
        
        <div className="space-y-3">
            <input
              type="date"
            value={appointmentDate}
            onChange={(e) => {
              setAppointmentDate(e.target.value);
              setAppointmentTime(''); // Reset time when date changes
            }}
            min={today}
            required
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            />
          
          {appointmentDate && (
          <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Available Time Slots
            </label>
              {isLoadingSlots ? (
                <div className="text-sm text-gray-400">Loading available slots...</div>
              ) : availableSlots.length > 0 ? (
                <div className="grid grid-cols-2 gap-2">
                  {availableSlots.map((slot) => (
                    <button
                      key={slot.id}
                      type="button"
                      onClick={() => {
                        // Send the 12-hour format time as requested
                        setAppointmentTime(slot.time_12);
                      }}
                      className={`p-2 text-sm rounded-md border transition-colors ${
                        appointmentTime === slot.time_12
                          ? 'bg-blue-600 border-blue-500 text-white'
                          : 'bg-gray-700 border-gray-600 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {slot.time_12}
                    </button>
              ))}
                </div>
              ) : (
                <div className="text-sm text-gray-400">No available slots for this date</div>
            )}
          </div>
          )}
        </div>

          <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Reason for visit (optional)"
            rows={2}
          className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
        ></textarea>
        
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onCancel} className="text-sm text-gray-400 hover:text-white">Cancel</button>
          <button
            type="submit"
            disabled={!appointmentTime}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg text-sm"
          >
            Confirm Appointment
          </button>
        </div>
      </form>
    </div>
  );
};

export default AppointmentForm; 