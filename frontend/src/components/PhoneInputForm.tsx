/**
 * Phone Input Form Component
 * Handles phone number collection and patient recognition
 */

import React, { useState } from 'react';
import { PhoneRecognitionService } from '../utils/phoneRecognitionService';
import { PatientProfile, SmartWelcomeResponse } from '../types';

interface PhoneInputFormProps {
  onPatientRecognized: (response: SmartWelcomeResponse) => void;
  onCancel: () => void;
  symptoms: string;
  sessionId: string;
  conversationHistory?: string;
}

const PhoneInputForm: React.FC<PhoneInputFormProps> = ({
  onPatientRecognized,
  onCancel,
  symptoms,
  sessionId,
  conversationHistory = ''
}) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [firstName, setFirstName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showNameInput, setShowNameInput] = useState(false);
  const [familyType, setFamilyType] = useState('self');

  const handlePhoneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!PhoneRecognitionService.validatePhoneNumber(phoneNumber)) {
      setError('Please enter a valid phone number (at least 10 digits)');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // First, try to recognize existing patient
      const patientProfile = await PhoneRecognitionService.recognizePatient({
        phone_number: phoneNumber,
        first_name: firstName || undefined,
        family_member_type: familyType
      });

      // If patient exists but no name provided for new patient, ask for name
      if (!patientProfile.first_name || patientProfile.first_name === 'Patient') {
        setShowNameInput(true);
        setIsLoading(false);
        return;
      }

      // Get smart welcome with symptom analysis
      const smartWelcome = await PhoneRecognitionService.getSmartWelcome(
        phoneNumber,
        symptoms,
        sessionId,
        conversationHistory
      );

      onPatientRecognized(smartWelcome);

    } catch (error) {
      console.error('Error with phone recognition:', error);
      setError('Unable to process phone number. Please try again.');
      setIsLoading(false);
    }
  };

  const handleNameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!firstName.trim()) {
      setError('Please enter your first name');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Detect family booking
      const familyDetection = PhoneRecognitionService.detectFamilyBooking(
        firstName,
        conversationHistory
      );

      const finalFamilyType = familyDetection.isFamilyBooking 
        ? familyDetection.familyMemberType 
        : familyType;

      // Create/update patient profile with name
      const patientProfile = await PhoneRecognitionService.recognizePatient({
        phone_number: phoneNumber,
        first_name: firstName.trim(),
        family_member_type: finalFamilyType
      });

      // Get smart welcome
      const smartWelcome = await PhoneRecognitionService.getSmartWelcome(
        phoneNumber,
        symptoms,
        sessionId,
        conversationHistory
      );

      onPatientRecognized(smartWelcome);

    } catch (error) {
      console.error('Error creating patient profile:', error);
      setError('Unable to create profile. Please try again.');
      setIsLoading(false);
    }
  };

  const formatPhoneDisplay = (value: string) => {
    // Remove all non-digit characters
    const digits = value.replace(/\D/g, '');
    
    // Format as (123) 456-7890
    if (digits.length >= 6) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`;
    } else if (digits.length >= 3) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
    } else {
      return digits;
    }
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setPhoneNumber(value);
    setError('');
  };

  if (showNameInput) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-bold text-white mb-4">
          Welcome! Let's get you set up
        </h3>
        
        <p className="text-gray-300 mb-4">
          We found your phone number but need a few more details to personalize your experience.
        </p>

        <form onSubmit={handleNameSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              First Name *
            </label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Enter your first name"
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500"
              required
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Booking for
            </label>
            <select
              value={familyType}
              onChange={(e) => setFamilyType(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="self">Myself</option>
              <option value="child">My Child</option>
              <option value="parent">My Parent</option>
              <option value="spouse">My Spouse</option>
              <option value="sibling">My Sibling</option>
            </select>
          </div>

          {error && (
            <div className="text-red-400 text-sm">{error}</div>
          )}

          <div className="flex space-x-3">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              {isLoading ? 'Setting up...' : 'Continue'}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-xl font-bold text-white mb-4">
        📱 Phone Number for Booking
      </h3>
      
      <p className="text-gray-300 mb-4">
        To proceed with booking, please provide your phone number. We'll use this to:
      </p>

      <ul className="text-gray-300 text-sm mb-6 space-y-1">
        <li>• Recognize you for future visits</li>
        <li>• Send appointment confirmations</li>
        <li>• Keep track of your medical history</li>
        <li>• Provide personalized care recommendations</li>
      </ul>

      <form onSubmit={handlePhoneSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Phone Number *
          </label>
          <input
            type="tel"
            value={phoneNumber}
            onChange={handlePhoneChange}
            placeholder="(123) 456-7890"
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white focus:ring-blue-500 focus:border-blue-500"
            required
            autoFocus
          />
          <p className="text-xs text-gray-400 mt-1">
            We'll format this automatically as you type
          </p>
        </div>

        {error && (
          <div className="text-red-400 text-sm">{error}</div>
        )}

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={isLoading || !phoneNumber.trim()}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
          >
            {isLoading ? 'Checking...' : 'Continue'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>

      <div className="mt-4 p-3 bg-gray-700 rounded-md">
        <p className="text-xs text-gray-400">
          🔒 Your phone number is secure and will only be used for medical appointments and communication.
        </p>
      </div>
    </div>
  );
};

export default PhoneInputForm; 