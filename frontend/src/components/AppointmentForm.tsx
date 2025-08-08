import React, { useState, useEffect, useCallback } from 'react';
import { Doctor, AppointmentData, PatientProfile, SmartWelcomeResponse } from '../types';

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
  patientProfile?: PatientProfile | null;
  symptoms?: string;
  onPatientRecognized?: (smartWelcomeResponse: SmartWelcomeResponse) => void;
  hospitalSlug?: string;
}

const AppointmentForm: React.FC<AppointmentFormProps> = ({ doctor, onSubmit, onCancel, patientProfile, symptoms, onPatientRecognized, hospitalSlug = 'demo1' }) => {
  const [patientName, setPatientName] = useState(patientProfile?.first_name || '');
  const [phoneNumber, setPhoneNumber] = useState(patientProfile?.phone_number || '');
  const [appointmentDate, setAppointmentDate] = useState('');
  const [appointmentTime, setAppointmentTime] = useState('');
  const [notes, setNotes] = useState(symptoms || '');
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [phoneError, setPhoneError] = useState('');
  const [isPhoneValidated, setIsPhoneValidated] = useState(!!patientProfile?.phone_number);
  const [recognizedPatient, setRecognizedPatient] = useState<PatientProfile | null>(patientProfile || null);

  // Validate Indian phone numbers
  const validateIndianPhone = (phone: string): boolean => {
    // Remove any spaces, dashes, or parentheses
    const cleanPhone = phone.replace(/[\s\-()]/g, '');
    
    // Check if it starts with +91 or 91 or is 10 digits starting with 6,7,8,9
    const indianPhoneRegex = /^(?:\+91|91)?[6-9]\d{9}$/;
    return indianPhoneRegex.test(cleanPhone);
  };

  // Format phone number to standard Indian format
  const formatIndianPhone = (phone: string): string => {
    const cleanPhone = phone.replace(/[\s\-()]/g, '');
    if (cleanPhone.startsWith('+91')) {
      return cleanPhone.substring(3);
    } else if (cleanPhone.startsWith('91') && cleanPhone.length === 12) {
      return cleanPhone.substring(2);
    }
    return cleanPhone;
  };

  // Handle phone number validation and recognition
  const handlePhoneBlur = async () => {
    if (!phoneNumber) return;

    const isValid = validateIndianPhone(phoneNumber);
    if (!isValid) {
      setPhoneError('Please enter a valid Indian mobile number (10 digits starting with 6, 7, 8, or 9)');
      setIsPhoneValidated(false);
      return;
    }

    setPhoneError('');
    const formattedPhone = formatIndianPhone(phoneNumber);
    setPhoneNumber(formattedPhone);

    // If we already have a patient profile with this phone number, skip recognition
    if (recognizedPatient?.phone_number === formattedPhone) {
      setIsPhoneValidated(true);
      return;
    }

    try {
      // Call phone recognition API
      const response = await fetch('http://localhost:8000/phone-recognition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: formattedPhone }),
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.patient_found && result.patient_profile) {
          // Found existing patient
          setRecognizedPatient(result.patient_profile);
          setPatientName(result.patient_profile.first_name);
          setIsPhoneValidated(true);
          
          // Generate smart welcome if handler provided
          if (onPatientRecognized) {
            try {
              const smartWelcomeResponse = await fetch('http://localhost:8000/smart-welcome', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  phone_number: formattedPhone,
                  symptoms: symptoms || '',
                  session_id: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
                }),
              });

              if (smartWelcomeResponse.ok) {
                const smartWelcomeData = await smartWelcomeResponse.json();
                onPatientRecognized(smartWelcomeData);
              }
            } catch (error) {
              console.error('Smart welcome error:', error);
            }
          }
        } else {
          // New patient
          setIsPhoneValidated(true);
          setRecognizedPatient(null);
        }
      } else {
        setIsPhoneValidated(true); // Allow booking even if recognition fails
      }
    } catch (error) {
      console.error('Phone recognition error:', error);
      setIsPhoneValidated(true); // Allow booking even if recognition fails
    }
  };

  // Fetch available slots when date changes
  const fetchAvailableSlots = useCallback(async () => {
    if (!appointmentDate || !doctor.id) return;
    
    setIsLoadingSlots(true);
    try {
      const response = await fetch(`http://localhost:8000/h/${hospitalSlug}/doctors/${doctor.id}/available-slots?date=${appointmentDate}`);
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
    
    // Final validation
    if (!isPhoneValidated || phoneError) {
      setPhoneError('Please enter a valid phone number');
      return;
    }
    
    onSubmit({
      doctor_id: doctor.id,
      patient_name: patientName,
      phone_number: phoneNumber,
      appointment_date: appointmentDate,
      appointment_time: appointmentTime,
      notes: notes,
      symptoms: symptoms || notes, // Use provided symptoms or notes
    });
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="bg-chat-assistant-muted rounded-lg p-8 text-white w-full max-w-3xl">
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
        
        <div>
        <input
          type="tel"
          value={phoneNumber}
            onChange={(e) => {
              setPhoneNumber(e.target.value);
              setPhoneError(''); // Clear error on typing
            }}
          placeholder="Phone Number"
          required
            className={`w-full bg-gray-700 border rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 ${
              phoneError ? 'border-red-500' : 'border-gray-600'
            }`}
            onBlur={handlePhoneBlur}
          />
          {phoneError && (
            <p className="text-red-400 text-xs mt-1">{phoneError}</p>
          )}
          {recognizedPatient && (
            <p className="text-green-400 text-xs mt-1">
              ✓ Welcome back, {recognizedPatient.first_name}! (Visit #{recognizedPatient.total_visits})
            </p>
          )}
        </div>
        
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
            disabled={!appointmentTime || !isPhoneValidated || !!phoneError}
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