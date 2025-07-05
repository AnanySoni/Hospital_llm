import React, { useState } from 'react';
import { TestRecommendation } from '../types';

interface TestBookingFormProps {
  selectedTests: TestRecommendation[];
  onSubmit: (bookingData: any) => void;
  onCancel: () => void;
  patientProfile?: any;
  symptoms?: string;
}

const TestBookingForm: React.FC<TestBookingFormProps> = ({
  selectedTests,
  onSubmit,
  onCancel,
  patientProfile,
  symptoms
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

  const getTotalCost = () => {
    return selectedTests.reduce((total, test) => total + (test.cost || 0), 0);
  };

  const getMinDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

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
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter contact number"
            />
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
            disabled={isSubmitting}
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