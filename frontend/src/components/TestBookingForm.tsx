import React, { useState } from 'react';
import { TestRecommendation } from '../types';

interface TestBookingFormProps {
  recommendedTests: TestRecommendation[];
  onBookingComplete: (bookingDetails: any) => void;
  onBack: () => void;
}

const TestBookingForm: React.FC<TestBookingFormProps> = ({ recommendedTests, onBookingComplete, onBack }) => {
  const [patientName, setPatientName] = useState('');
  const [preferredDate, setPreferredDate] = useState('');
  const [preferredTime, setPreferredTime] = useState('');
  const [contactNumber, setContactNumber] = useState('');
  const [notes, setNotes] = useState('');

  const totalCost = recommendedTests.reduce((acc, test) => acc + (test.cost || 0), 0);

  // Get tomorrow's date as minimum date
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split('T')[0];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onBookingComplete({
      patient_name: patientName,
      test_ids: recommendedTests.map(test => test.test_id),
      preferred_date: preferredDate,
      preferred_time: preferredTime,
      contact_number: contactNumber,
      notes: notes || undefined
    });
  };

  return (
    <div className="bg-chat-assistant-muted rounded-lg p-4 text-white w-full max-w-lg">
      <h3 className="text-lg font-bold mb-3 text-gray-100">Book Diagnostic Tests</h3>
      
      <div className="mb-4">
        <h4 className="font-semibold text-gray-300 mb-2">Selected Tests:</h4>
        <ul className="space-y-1 text-sm">
          {recommendedTests.map(test => (
            <li key={test.test_id} className="flex justify-between">
              <span>{test.test_name}</span>
              <span className="text-gray-400">₹{test.cost || 0}</span>
            </li>
          ))}
        </ul>
        <div className="flex justify-between font-bold mt-2 pt-2 border-t border-gray-600">
          <span>Total Cost:</span>
          <span>₹{totalCost.toLocaleString()}</span>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="space-y-3">
          <input 
            type="text" 
            value={patientName} 
            onChange={e => setPatientName(e.target.value)} 
            placeholder="Full Name"
            required 
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
          <input 
            type="tel" 
            value={contactNumber} 
            onChange={e => setContactNumber(e.target.value)} 
            placeholder="Contact Number (e.g., +91 9876543210)"
            required 
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="grid grid-cols-2 gap-3">
            <input 
              type="date" 
              value={preferredDate} 
              onChange={e => setPreferredDate(e.target.value)}
              min={minDate}
              required
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            />
            <select 
              value={preferredTime} 
              onChange={e => setPreferredTime(e.target.value)}
              required
              className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select Time</option>
              <option value="09:00">9:00 AM</option>
              <option value="10:00">10:00 AM</option>
              <option value="11:00">11:00 AM</option>
              <option value="14:00">2:00 PM</option>
              <option value="15:00">3:00 PM</option>
              <option value="16:00">4:00 PM</option>
            </select>
          </div>
          <textarea 
            value={notes} 
            onChange={e => setNotes(e.target.value)} 
            placeholder="Additional notes (optional)"
            rows={2}
            className="w-full bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div className="flex justify-end gap-3 mt-4">
          <button type="button" onClick={onBack} className="text-sm text-gray-400 hover:text-white">Cancel</button>
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg text-sm">
            Confirm Booking
          </button>
        </div>
      </form>
    </div>
  );
};

export default TestBookingForm; 