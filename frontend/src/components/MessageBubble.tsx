import React, { useState, useEffect } from 'react';
import { Message, Doctor, AppointmentData, TestRecommendation } from '../types';
import DoctorCard from './DoctorCard';
import AppointmentForm from './AppointmentForm';
import RescheduleForm from './RescheduleForm';
import TestCard from './TestCard';
import TestBookingForm from './TestBookingForm';

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
  isLoading?: boolean;
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
  isLoading = false,
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
    switch (message.type) {
      case 'diagnostic_question':
        if (!message.question) return null;
        return (
          <div className="bg-chat-assistant rounded-2xl px-4 py-3">
            <p className="text-sm leading-relaxed text-gray-100 mb-3">{message.question.question}</p>
            {message.question.options && (
              <div className="flex flex-wrap gap-2">
                {message.question.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => onQuickReply?.(option)}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-1.5 px-3 rounded-lg"
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
        const { diagnosis, decision } = message.diagnosticResult;
        return (
          <div className="bg-chat-assistant rounded-2xl p-4 text-white">
            <p className="text-sm leading-relaxed text-gray-100 mb-3">{message.content}</p>
            {diagnosis && (
              <div className="bg-gray-800 rounded-lg p-3 mb-3">
                <h4 className="font-bold mb-2 text-gray-100">Preliminary Diagnosis</h4>
                <p className="text-sm text-gray-300 mb-2">{diagnosis.explanation}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <p><strong className="text-gray-400">Conditions:</strong> {diagnosis.possible_conditions.join(', ')}</p>
                  <p><strong className="text-gray-400">Urgency:</strong> {diagnosis.urgency_level}</p>
                </div>
              </div>
            )}
            
            {/* Ask user what they want to do next */}
            <div className="bg-gray-700 rounded-lg p-3 mb-3">
              <p className="text-sm text-gray-300 mb-3">What would you like to do next?</p>
              <div className="flex flex-wrap gap-2">
                <button 
                  onClick={() => onQuickReply?.('I want to book medical tests')} 
                  className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-lg"
                >
                  Book Medical Tests
                </button>
                <button 
                  onClick={() => onQuickReply?.('I want to book an appointment with a doctor')} 
                  className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-4 rounded-lg"
                >
                  Book Doctor Appointment
                </button>
              </div>
            </div>
          </div>
        );

      case 'doctors':
        return (
          <div>
            <div className="bg-chat-assistant rounded-2xl px-4 py-3 mb-3"><p>{message.content}</p></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {message.doctors?.map(doc => <DoctorCard key={doc.id} doctor={doc} onSelect={() => onDoctorSelect?.(doc)} />)}
            </div>
          </div>
        );

      case 'appointment-form':
        return message.selectedDoctor && onAppointmentSubmit ? (
          <AppointmentForm doctor={message.selectedDoctor} onSubmit={onAppointmentSubmit} onCancel={()=>{}} />
        ) : null;

      case 'appointment-success':
        return message.appointment ? (
          <div className="bg-green-900/30 border border-green-600/50 rounded-2xl p-4 text-white">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i className="fas fa-check text-white text-sm"></i>
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-green-400 mb-1">Appointment Confirmed!</h4>
                <p className="text-sm text-gray-300">{message.content}</p>
              </div>
            </div>
            
            <div className="bg-gray-800/50 rounded-lg p-3 mb-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <p><strong className="text-gray-400">Doctor:</strong> {message.appointment.doctor_name}</p>
                <p><strong className="text-gray-400">Date:</strong> {message.appointment.appointment_date}</p>
                <p><strong className="text-gray-400">Time:</strong> {message.appointment.appointment_time}</p>
                <p><strong className="text-gray-400">Status:</strong> <span className="text-green-400 capitalize">{message.appointment.status}</span></p>
              </div>
              {message.appointment.notes && (
                <p className="text-sm text-gray-300 mt-2">
                  <strong className="text-gray-400">Notes:</strong> {message.appointment.notes}
                </p>
              )}
            </div>
            
            <div className="flex gap-2">
              <button 
                onClick={() => onRescheduleAppointment?.(message.appointment!.id)}
                className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-1.5 px-3 rounded-lg flex items-center gap-1"
              >
                <i className="fas fa-calendar-alt text-xs"></i>
                Reschedule
              </button>
              <button 
                onClick={() => onCancelAppointment?.(message.appointment!.id)}
                className="bg-red-600 hover:bg-red-700 text-white text-sm font-medium py-1.5 px-3 rounded-lg flex items-center gap-1"
              >
                <i className="fas fa-times text-xs"></i>
                Cancel
              </button>
            </div>
          </div>
        ) : null;

      case 'reschedule-form':
        return message.appointment ? (
          <RescheduleForm 
            appointment={message.appointment} 
            onSubmit={onRescheduleSubmit || (() => {})} 
            onCancel={onRescheduleCancel || (() => {})} 
            isLoading={isLoading}
          />
        ) : null;

      case 'tests':
        return (
          <div>
            <div className="bg-chat-assistant rounded-2xl px-4 py-3 mb-3">
              <p>{message.content}</p>
            </div>
            <div className="space-y-3">
              {message.tests?.map(test => (
                <TestCard 
                  key={test.test_id} 
                  test={test} 
                  isSelected={selectedTests.has(test.test_id)}
                  onSelect={handleTestSelection}
                />
              ))}
            </div>
            {message.tests && (
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm text-gray-400">
                  {selectedTests.size > 0 ? (
                    <span>{selectedTests.size} test{selectedTests.size !== 1 ? 's' : ''} selected</span>
                  ) : (
                    <span>Select tests to book</span>
                  )}
                </div>
                <button 
                  onClick={handleBookSelectedTests}
                  disabled={selectedTests.size === 0}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${
                    selectedTests.size > 0 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                      : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  Book Selected Tests ({selectedTests.size})
                </button>
              </div>
            )}
          </div>
        );
      
      case 'test_form':
          return message.selectedTests && onTestSubmit ? (
              <TestBookingForm recommendedTests={message.selectedTests} onBookingComplete={onTestSubmit} onBack={() => {}} />
          ) : null;

      default:
        return (
            <div className={`rounded-2xl px-4 py-3 ${isUser ? 'bg-blue-600 text-white' : 'bg-chat-assistant text-gray-100'}`}>
                <p className="text-sm leading-relaxed">{message.content}</p>
            </div>
        );
    }
  };

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full flex-shrink-0 bg-green-600 flex items-center justify-center">
          <i className="fas fa-robot text-white text-sm"></i>
        </div>
      )}
      <div className={`max-w-xl ${isUser ? '' : 'flex-grow'}`}>{renderContent()}</div>
      {isUser && (
        <div className="w-8 h-8 rounded-full flex-shrink-0 bg-blue-600 flex items-center justify-center">
          <i className="fas fa-user text-white text-sm"></i>
        </div>
      )}
    </div>
  );
};

export default MessageBubble; 