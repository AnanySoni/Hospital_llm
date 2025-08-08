import React, { useState } from 'react';
import { Message, Doctor, AppointmentData, TestRecommendation, SmartWelcomeResponse } from '../types';
import DoctorCard from './DoctorCard';
import AppointmentForm from './AppointmentForm';
import RescheduleForm from './RescheduleForm';
import TestCard from './TestCard';
import TestBookingForm from './TestBookingForm';
import ConfidenceIndicator from './ConfidenceIndicator';
import ConsequenceAlert from './ConsequenceAlert';

interface MessageBubbleProps {
  message: Message;
  onDoctorSelect?: (doctor: Doctor) => void;
  onAppointmentSubmit?: (appointmentData: AppointmentData) => void;
  onTestsSelect?: (tests: TestRecommendation[]) => void;
  onTestSubmit?: (bookingData: any) => void;
  onQuickReply?: (reply: string) => void;
  onBookAppointment?: (doctors: Doctor[]) => void;
  onBookTests?: (tests: TestRecommendation[]) => void;
  onRescheduleAppointment?: (appointmentId: number) => void;
  onRescheduleSubmit?: (appointmentId: number, newDate: string, newTime: string) => void;
  onRescheduleCancel?: () => void;
  onCancelAppointment?: (appointmentId: number) => void;
  onCancelTest?: (bookingId: string) => void;
  onPatientRecognized?: (smartWelcomeResponse: SmartWelcomeResponse) => void;
  isLoading?: boolean;
  hospitalSlug?: string;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message, 
  onDoctorSelect,
  onAppointmentSubmit,
  onTestsSelect,
  onTestSubmit,
  onQuickReply,
  onBookAppointment,
  onBookTests,
  onRescheduleAppointment,
  onRescheduleSubmit,
  onRescheduleCancel,
  onCancelAppointment,
  onCancelTest,
  onPatientRecognized,
  isLoading = false,
  hospitalSlug = 'demo1',
}) => {
  const isUser = message.role === 'user';
  const [selectedTests, setSelectedTests] = useState<Set<string>>(new Set());

  const handleTestSelection = (testId: string, selected: boolean) => {
    setSelectedTests(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(testId);
      } else {
        newSet.delete(testId);
      }
      return newSet;
    });
  };

  const handleBookSelectedTests = () => {
    if (selectedTests.size === 0) {
      return; // Don't proceed if no tests selected
    }
    
    const testsToBook = message.tests?.filter(test => selectedTests.has(test.test_id)) || [];
    onTestsSelect?.(testsToBook);
  };

  const renderContent = () => {
    // Safety check for tests property
    if (message.tests && !Array.isArray(message.tests)) {
      console.error('message.tests is not an array:', message.tests);
      message.tests = []; // Convert to empty array if not an array
    }
    
    switch (message.type) {
      case 'diagnostic_question':
        if (!message.question) return null;
    return (
          <div className="bg-chat-assistant rounded-xl px-3 py-2">
            <p className="text-sm leading-relaxed text-gray-100 mb-2">{message.question.question}</p>
            {message.question.options && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {message.question.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => onQuickReply?.(option)}
                    className="bg-chat-accent text-white text-sm font-medium rounded-full px-3 py-1.5 shadow transition-transform duration-150 hover:scale-105 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-chat-accent"
                  >
                    {option}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      
      case 'diagnostic_result':
        if (!message.diagnosticResult) return null;
        const { diagnosis, confidence } = message.diagnosticResult;
        return (
          <div className="space-y-4 w-full">
            {/* Main message content */}
            <div className="w-full px-4 md:px-6 py-3 bg-chat-assistant/80 rounded-xl">
              <p className="text-sm leading-relaxed text-gray-100 mb-3">{message.content}</p>
            {confidence && (
              <div className="mb-3">
                <ConfidenceIndicator confidence={confidence} showDetails={true} />
              </div>
            )}
            </div>
            
            {diagnosis && (
              <div className="w-full px-4 md:px-6 py-4 bg-chat-assistant/90 rounded-xl">
                <h4 className="text-base font-semibold text-white mb-3 flex items-center">
                  <i className="fas fa-stethoscope text-blue-400 mr-2 text-sm"></i>
                  Diagnostic Assessment
                </h4>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="text-sm font-medium text-blue-400 mb-2">Possible Conditions</h5>
                    <ul className="space-y-1">
                      {diagnosis.possible_conditions?.map((condition, i) => (
                        <li key={i} className="text-gray-300 flex items-start text-sm">
                          <span className="text-blue-400 mr-2">•</span>
                          {condition}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h5 className="text-sm font-medium text-green-400 mb-2">Assessment Details</h5>
                    <div className="space-y-1">
                      <div className="text-sm">
                        <span className="text-gray-400">Confidence Level:</span>
                        <span className="text-gray-300 ml-2">{diagnosis.confidence_level}</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-400">Urgency Level:</span>
                        <span className="text-gray-300 ml-2">{diagnosis.urgency_level}</span>
                      </div>
                  {diagnosis.diagnostic_confidence && (
                        <div className="mt-2">
                    <ConfidenceIndicator confidence={diagnosis.diagnostic_confidence} compact={true} />
                        </div>
                  )}
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                  <h6 className="text-sm font-medium text-gray-300 mb-2">Medical Explanation</h6>
                  <p className="text-xs text-gray-400 leading-relaxed">{diagnosis.explanation}</p>
                </div>
              </div>
            )}
            
            {/* Consequence Messaging */}
            {message.diagnosticResult?.consequence_message && (
              <div className="mt-4">
                <ConsequenceAlert
                  consequenceMessage={message.diagnosticResult.consequence_message}
                  riskProgression={message.diagnosticResult.risk_progression}
                  persuasionMetrics={message.diagnosticResult.persuasion_metrics}
                />
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="bg-gray-700 rounded-lg p-3">
              <h5 className="text-sm font-medium text-white mb-3">What would you like to do next?</h5>
              <div className="flex flex-wrap gap-2">
                <button 
                  onClick={() => onQuickReply?.('I want to book medical tests')} 
                  className="bg-chat-accent-green hover:bg-emerald-400 text-white text-sm font-semibold rounded-full px-3 py-1.5 shadow transition-transform duration-150 hover:scale-105 flex items-center gap-1.5"
                >
                  <i className="fas fa-flask text-xs"></i>
                  Book Medical Tests
                </button>
                <button 
                  onClick={() => onQuickReply?.('I want to book an appointment with a doctor')} 
                  className="bg-chat-accent hover:bg-blue-500 text-white text-sm font-semibold rounded-full px-3 py-1.5 shadow transition-transform duration-150 hover:scale-105 flex items-center gap-1.5"
                >
                  <i className="fas fa-user-md text-xs"></i>
                  Book Doctor Appointment
                </button>
              </div>
            </div>
          </div>
        );

      case 'doctors':
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-white mb-2 flex items-center">
                <i className="fas fa-user-md text-blue-400 mr-2"></i>
                Recommended Specialists
              </h4>
              <p className="text-gray-300">{message.content}</p>
            </div>
            
            {/* Doctor Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {message.doctors?.map(doc => (
                <DoctorCard key={doc.id} doctor={doc} onSelect={() => onDoctorSelect?.(doc)} />
              ))}
        </div>
      </div>
    );

      case 'appointment-form':
        return message.selectedDoctor && onAppointmentSubmit ? (
          <div className="flex justify-center py-8">
            <div className="bg-gray-800/90 rounded-2xl shadow-xl p-12 max-w-4xl w-full">
              <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                <i className="fas fa-calendar-plus text-blue-400 mr-2"></i>
                Book Appointment
              </h4>
            <AppointmentForm
              doctor={message.selectedDoctor}
            onSubmit={onAppointmentSubmit} 
            onCancel={()=>{}} 
            patientProfile={message.patientProfile}
            symptoms={message.symptoms}
                onPatientRecognized={onPatientRecognized}
                hospitalSlug={hospitalSlug}
          />
            </div>
          </div>
        ) : null;

      case 'appointment-success':
        return message.appointment ? (
          <div className="bg-green-900/30 border border-green-600/50 rounded-lg p-6 text-white">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i className="fas fa-check text-white"></i>
          </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-green-400 mb-2">Appointment Confirmed!</h4>
                <p className="text-gray-300">{message.content}</p>
        </div>
      </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
              <h5 className="font-medium text-white mb-3">Appointment Details</h5>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Doctor:</span>
                  <span className="text-gray-300 ml-2">{message.appointment.doctor_name}</span>
                </div>
                <div>
                  <span className="text-gray-400">Date:</span>
                  <span className="text-gray-300 ml-2">{message.appointment.appointment_date}</span>
                </div>
                <div>
                  <span className="text-gray-400">Time:</span>
                  <span className="text-gray-300 ml-2">{message.appointment.appointment_time}</span>
                </div>
                <div>
                  <span className="text-gray-400">Status:</span>
                  <span className="text-green-400 ml-2 capitalize">{message.appointment.status}</span>
                </div>
              </div>
              {message.appointment.notes && (
                <div className="mt-3">
                  <span className="text-gray-400">Notes:</span>
                  <span className="text-gray-300 ml-2">{message.appointment.notes}</span>
                </div>
              )}
          </div>

            <div className="flex gap-3">
              <button 
                onClick={() => onRescheduleAppointment?.(message.appointment!.id)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors duration-200"
              >
                <i className="fas fa-calendar-alt"></i>
                Reschedule
              </button>
              <button 
                onClick={() => onCancelAppointment?.(message.appointment!.id)}
                className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors duration-200"
              >
                <i className="fas fa-times"></i>
                Cancel
              </button>
      </div>
          </div>
        ) : null;

      case 'reschedule-form':
        return message.appointment ? (
          <div className="bg-gray-800 rounded-lg p-6">
            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
              <i className="fas fa-calendar-edit text-blue-400 mr-2"></i>
              Reschedule Appointment
            </h4>
            <RescheduleForm
              appointment={message.appointment}
              onSubmit={onRescheduleSubmit || (() => {})}
              onCancel={onRescheduleCancel || (() => {})}
            isLoading={isLoading}
          />
          </div>
        ) : null;

      case 'tests':
        return (
          <div className="space-y-6">
            {/* Header */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h4 className="text-lg font-semibold text-white mb-2 flex items-center">
                <i className="fas fa-flask text-blue-400 mr-2"></i>
                Recommended Medical Tests
              </h4>
              <p className="text-gray-300">{message.content}</p>
            </div>
            
            {/* Test Cards */}
            <div className="space-y-4">
              {message.tests?.map(test => (
                <TestCard 
                  key={test.test_id} 
                  test={test} 
                  isSelected={selectedTests.has(test.test_id)}
                  onSelect={handleTestSelection}
                />
              ))}
            </div>
            
            {/* Selection Summary */}
            {message.tests && (
              <div className="bg-gray-700 rounded-lg p-4 flex items-center justify-between">
                <div className="text-gray-300">
                  {selectedTests.size > 0 ? (
                    <span>{selectedTests.size} test{selectedTests.size !== 1 ? 's' : ''} selected</span>
                  ) : (
                    <span>Select tests to book</span>
                  )}
                </div>
                <button 
                  onClick={handleBookSelectedTests}
                  disabled={selectedTests.size === 0}
                  className={`px-6 py-3 font-medium rounded-lg transition-colors duration-200 flex items-center gap-2 ${
                    selectedTests.size > 0 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <i className="fas fa-calendar-check"></i>
                  Book Selected Tests ({selectedTests.size})
                </button>
              </div>
            )}
          </div>
        );
      
      case 'test_form':
          return message.selectedTests && onTestSubmit ? (
          <div className="bg-gray-800 rounded-lg p-6">
            <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
              <i className="fas fa-calendar-plus text-blue-400 mr-2"></i>
              Book Medical Tests
            </h4>
              <TestBookingForm 
                selectedTests={message.selectedTests} 
                onSubmit={onTestSubmit} 
                onCancel={() => {}}
                patientProfile={message.patientProfile}
                symptoms={message.symptoms}
              onPatientRecognized={onPatientRecognized}
              />
          </div>
          ) : null;

      case 'test-success':
        return message.testBooking ? (
          <div className="bg-green-900/30 border border-green-600/50 rounded-lg p-6 text-white">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i className="fas fa-check text-white"></i>
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-green-400 mb-2">Tests Booked Successfully!</h4>
                <p className="text-gray-300">{message.content}</p>
              </div>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
              <h5 className="font-medium text-white mb-3">Booking Details</h5>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Booking ID:</span>
                  <span className="text-gray-300 ml-2">{message.testBooking.booking_id}</span>
                </div>
                <div>
                  <span className="text-gray-400">Patient:</span>
                  <span className="text-gray-300 ml-2">{message.testBooking.patient_name}</span>
                </div>
                <div>
                  <span className="text-gray-400">Date:</span>
                  <span className="text-gray-300 ml-2">{message.testBooking.appointment_date}</span>
                </div>
                <div>
                  <span className="text-gray-400">Time:</span>
                  <span className="text-gray-300 ml-2">{message.testBooking.appointment_time}</span>
                </div>
                <div>
                  <span className="text-gray-400">Total Cost:</span>
                  <span className="text-gray-300 ml-2">{message.testBooking.total_cost}</span>
                </div>
                <div>
                  <span className="text-gray-400">Status:</span>
                  <span className="text-green-400 ml-2 capitalize">{message.testBooking.status}</span>
                </div>
              </div>
              
              <div className="mt-4">
                <h6 className="font-medium text-gray-300 mb-2">Tests Booked:</h6>
                <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                  {message.testBooking.tests_booked.map((test, index) => (
                    <li key={index}>{test}</li>
                  ))}
                </ul>
              </div>

              {message.testBooking.preparation_instructions && message.testBooking.preparation_instructions.length > 0 && (
                <div className="mt-4">
                  <h6 className="font-medium text-gray-300 mb-2">Preparation Instructions:</h6>
                  <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                    {message.testBooking.preparation_instructions.map((instruction, index) => (
                      <li key={index}>{instruction}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button 
                onClick={() => onCancelTest?.(message.testBooking!.booking_id)}
                className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors duration-200"
              >
                <i className="fas fa-times"></i>
                Cancel Booking
              </button>
            </div>
          </div>
        ) : null;

      default:
        return (
            <div className={`rounded-xl px-3 py-2 ${isUser ? 'bg-blue-600 text-white' : 'bg-chat-assistant text-gray-100'}`}>
                <p className="text-sm leading-relaxed">{message.content}</p>
      </div>
    );
  }
  };

  // Render different layouts for user vs assistant messages
  if (isUser) {
    // User messages remain compact and right-aligned
  return (
      <div className="flex items-start gap-2 justify-end mb-1">
        <div className="max-w-lg">
          <div className="text-white rounded-2xl px-4 py-2 max-w-full ml-auto">
            {renderContent()}
          </div>
        </div>
        <div className="w-7 h-7 rounded-full flex-shrink-0 bg-chat-user flex items-center justify-center shadow">
          <i className="fas fa-user text-white text-xs"></i>
        </div>
      </div>
    );
  } else {
    // Assistant messages: use nearly full width, no max-w, just padding
    return (
      <div className="w-full mb-1">
        <div className="w-full px-2 md:px-6">
          <div className="text-sm text-gray-100 leading-relaxed w-full">
            {renderContent()}
          </div>
        </div>
    </div>
  );
  }
};

export default MessageBubble; 