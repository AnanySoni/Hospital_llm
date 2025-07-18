/**
 * Phone Recognition Service
 * Handles phone-based patient recognition and smart welcome functionality
 */

import { PatientProfile, SmartWelcomeResponse, PhoneRecognitionData } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export class PhoneRecognitionService {
  
  /**
   * Recognize patient by phone number
   */
  static async recognizePatient(phoneData: PhoneRecognitionData): Promise<PatientProfile> {
    try {
      const response = await fetch(`${API_BASE_URL}/phone-recognition`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(phoneData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error recognizing patient:', error);
      throw error;
    }
  }

  /**
   * Get smart welcome with symptom analysis
   */
  static async getSmartWelcome(
    phoneNumber: string,
    symptoms: string,
    sessionId: string,
    conversationHistory?: string
  ): Promise<SmartWelcomeResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/smart-welcome`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          symptoms: symptoms,
          session_id: sessionId,
          conversation_history: conversationHistory || '',
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting smart welcome:', error);
      throw error;
    }
  }

  /**
   * Update patient profile information
   */
  static async updatePatientProfile(
    phoneNumber: string,
    updateData: Partial<PatientProfile>
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/update-patient-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          update_data: updateData,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await response.json();
    } catch (error) {
      console.error('Error updating patient profile:', error);
      throw error;
    }
  }

  /**
   * Validate phone number format
   */
  static validatePhoneNumber(phoneNumber: string): boolean {
    // Remove all non-digit characters
    const digits = phoneNumber.replace(/\D/g, '');
    
    // Check if it has at least 10 digits
    return digits.length >= 10;
  }

  /**
   * Format phone number for display
   */
  static formatPhoneNumber(phoneNumber: string): string {
    // Remove all non-digit characters
    const digits = phoneNumber.replace(/\D/g, '');
    
    if (digits.length === 10) {
      // US format: (123) 456-7890
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    } else if (digits.length === 11 && digits.startsWith('1')) {
      // US format with country code: +1 (123) 456-7890
      return `+1 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
    } else {
      // International format
      return `+${digits}`;
    }
  }

  /**
   * Detect family member booking from text
   */
  static detectFamilyBooking(patientName: string, conversationContext: string): {
    isFamilyBooking: boolean;
    familyMemberType: string;
  } {
    const name = patientName.toLowerCase();
    const context = conversationContext.toLowerCase();
    const fullText = `${name} ${context}`;

    // Family indicators
    const familyPatterns = {
      child: ['my son', 'my daughter', 'my child', 'my kid', 'for my baby'],
      parent: ['my mother', 'my father', 'my mom', 'my dad', 'my parent'],
      spouse: ['my husband', 'my wife', 'my partner'],
      sibling: ['my sister', 'my brother'],
    };

    for (const [type, patterns] of Object.entries(familyPatterns)) {
      if (patterns.some(pattern => fullText.includes(pattern))) {
        return {
          isFamilyBooking: true,
          familyMemberType: type,
        };
      }
    }

    return {
      isFamilyBooking: false,
      familyMemberType: 'self',
    };
  }

  /**
   * Generate smart welcome message based on patient data
   */
  static generateContextualMessage(
    patientProfile: PatientProfile,
    isNewPatient: boolean,
    symptomCategory: string,
    isRelated: boolean
  ): string {
    const name = patientProfile.first_name;
    
    if (isNewPatient) {
      return `Welcome to our hospital, ${name}! I'm here to help you with your ${symptomCategory.replace('_', ' ')} concerns.`;
    }

    if (isRelated) {
      return `Welcome back, ${name}! I see you're here about ${symptomCategory.replace('_', ' ')} again. Let's continue from where we left off.`;
    }

    if (patientProfile.total_visits > 1) {
      return `Welcome back, ${name}! I see you have a new concern today. What's bothering you?`;
    }

    return `Welcome back, ${name}! How can I help you today?`;
  }

  /**
   * Check if symptoms are urgent
   */
  static isUrgentSymptom(symptoms: string): boolean {
    const urgentKeywords = [
      'chest pain', 'difficulty breathing', 'severe pain', 'bleeding',
      'unconscious', 'seizure', 'stroke', 'heart attack', 'emergency',
      'severe headache', 'high fever', 'allergic reaction'
    ];

    const symptomsLower = symptoms.toLowerCase();
    return urgentKeywords.some(keyword => symptomsLower.includes(keyword));
  }
} 