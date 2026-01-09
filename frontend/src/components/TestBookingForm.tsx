import React, { useState } from 'react';
import { TestRecommendation, PatientProfile, SmartWelcomeResponse } from '../types';

interface TestBookingFormProps {
  selectedTests: TestRecommendation[];
  onSubmit: (bookingData: any) => void;
  onCancel: () => void;
  patientProfile?: PatientProfile;
  symptoms?: string;
  onPatientRecognized?: (smartWelcomeResponse: SmartWelcomeResponse) => void;
}

const TestBookingForm: React.FC<TestBookingFormProps> = ({
  selectedTests,
  onSubmit,
  onCancel,
  patientProfile,
  symptoms,
  onPatientRecognized
}) => {
  const [formData, setFormData] = useState({
    patient_name: patientProfile?.first_name || '',
    contact_number: patientProfile?.phone_number || '',
    preferred_date: '',
    preferred_time: '09:00',
    notes: symptoms ? `Related symptoms: ${symptoms}` : ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [phoneError, setPhoneError] = useState('');
  const [isPhoneValidated, setIsPhoneValidated] = useState(!!patientProfile?.phone_number);
  const [recognizedPatient, setRecognizedPatient] = useState<PatientProfile | null>(patientProfile || null);

  const getTotalCost = () => {
    return selectedTests.reduce((total, test) => total + (test.cost || 0), 0);
  };

  const getMinDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  // Validate Indian phone numbers
  const validateIndianPhone = (phone: string): boolean => {
    const cleanPhone = phone.replace(/[\s\-()]/g, '');
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
    if (!formData.contact_number) return;

    const isValid = validateIndianPhone(formData.contact_number);
    if (!isValid) {
      setPhoneError('Please enter a valid Indian mobile number (10 digits starting with 6, 7, 8, or 9)');
      setIsPhoneValidated(false);
      return;
    }

    setPhoneError('');
    const formattedPhone = formatIndianPhone(formData.contact_number);
    setFormData(prev => ({ ...prev, contact_number: formattedPhone }));

    // If we already have a patient profile with this phone number, skip recognition
    if (recognizedPatient?.phone_number === formattedPhone) {
      setIsPhoneValidated(true);
      return;
    }

    try {
      // Call phone recognition API
      const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/phone-recognition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: formattedPhone }),
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.patient_found && result.patient_profile) {
          // Found existing patient
          setRecognizedPatient(result.patient_profile);
          setFormData(prev => ({ 
            ...prev, 
            patient_name: result.patient_profile.first_name 
          }));
          setIsPhoneValidated(true);
          
          // Generate smart welcome if handler provided
          if (onPatientRecognized) {
            try {
              const smartWelcomeResponse = await fetch(`${API_BASE}/smart-welcome`, {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    // Final validation
    if (!isPhoneValidated || phoneError) {
      setError('Please enter a valid phone number');
      setIsSubmitting(false);
      return;
    }

    try {
      const testIds = selectedTests.map(test => test.test_id);
      
      await onSubmit({
        ...formData,
        test_ids: testIds
      });
    } catch (error: any) {
      setError(error.message || 'Failed to book tests');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-gray-800/50 rounded-2xl p-4 text-white">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
          <i className="fas fa-flask text-white text-sm"></i>
        </div>
        <div className="flex-1">
          <h4 className="font-bold text-blue-400 mb-1">Book Selected Tests</h4>
          <p className="text-sm text-gray-300">Please provide your details to complete the booking</p>
        </div>
      </div>

      {/* Selected Tests Summary */}
      <div className="bg-gray-700/50 rounded-lg p-3 mb-4">
        <h5 className="font-medium text-gray-300 mb-2">Selected Tests ({selectedTests.length})</h5>
        <div className="space-y-2">
          {selectedTests.map(test => (
            <div key={test.test_id} className="flex justify-between items-center text-sm">
              <span className="text-gray-300">{test.test_name}</span>
              <span className="text-green-400 font-medium">₹{test.cost?.toLocaleString()}</span>
            </div>
          ))}
        </div>
        <div className="border-t border-gray-600 pt-2 mt-2 flex justify-between items-center font-medium">
          <span className="text-gray-300">Total Cost:</span>
          <span className="text-green-400 text-lg">₹{getTotalCost().toLocaleString()}</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Patient Name *
            </label>
            <input
              type="text"
              required
              value={formData.patient_name}
              onChange={(e) => setFormData({...formData, patient_name: e.target.value})}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter patient name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Contact Number *
            </label>
            <input
              type="tel"
              required
              value={formData.contact_number}
              onChange={(e) => setFormData({...formData, contact_number: e.target.value})}
              onBlur={handlePhoneBlur}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter contact number"
            />
            {phoneError && (
              <div className="text-red-400 text-sm mt-1">
                {phoneError}
              </div>
            )}
            {recognizedPatient && (
              <div className="text-green-400 text-sm mt-1">
                ✓ Welcome back, {recognizedPatient.first_name}! (Visit #{recognizedPatient.total_visits})
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Preferred Date *
            </label>
            <input
              type="date"
              required
              min={getMinDate()}
              value={formData.preferred_date}
              onChange={(e) => setFormData({...formData, preferred_date: e.target.value})}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Preferred Time *
            </label>
            <select
              value={formData.preferred_time}
              onChange={(e) => setFormData({...formData, preferred_time: e.target.value})}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="09:00">9:00 AM</option>
              <option value="10:00">10:00 AM</option>
              <option value="11:00">11:00 AM</option>
              <option value="14:00">2:00 PM</option>
              <option value="15:00">3:00 PM</option>
              <option value="16:00">4:00 PM</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Additional Notes
          </label>
          <textarea
            value={formData.notes}
            onChange={(e) => setFormData({...formData, notes: e.target.value})}
            rows={3}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Any special instructions or notes..."
          />
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-600/50 text-red-400 px-3 py-2 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !isPhoneValidated || !!phoneError}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            {isSubmitting ? 'Booking...' : `Book Tests (₹${getTotalCost().toLocaleString()})`}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TestBookingForm; 