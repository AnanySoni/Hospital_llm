import React, { useState, useEffect, useRef } from 'react';
import { Message, Doctor, AppointmentData, Appointment, RouterResponse, DiagnosticQuestion, TestRecommendation } from '../types';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import WelcomeScreen from './WelcomeScreen';

interface ChatContainerProps {
  isCalendarConnected?: boolean;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ isCalendarConnected = false }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [diagnosticState, setDiagnosticState] = useState<{
    sessionId: string | null;
    isDiagnosing: boolean;
    symptoms: string;
    currentQuestionId: number | null;
  }>({ sessionId: null, isDiagnosing: false, symptoms: '', currentQuestionId: null });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    setMessages([{
      id: 'welcome-1',
      content: "👋 Hi! I'm your medical assistant. To get started, please describe your symptoms.",
      role: 'assistant',
      timestamp: new Date(),
      type: 'text'
    }]);
  }, []);

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date(),
    } as Message;
    setMessages(prev => [...prev, newMessage]);
  };

  const handleSendMessage = async (content: string, quickReply = false) => {
    if (!quickReply) {
      addMessage({ content, role: 'user', type: 'text' });
    }
    
    setIsLoading(true);

    // Check if user wants to book tests after diagnosis
    if (content.toLowerCase().includes('book medical tests') || content.toLowerCase().includes('i want to book medical tests')) {
    try {
        // Get test recommendations using LLM
        const response = await fetch(`http://localhost:8000/tests/recommendations/${encodeURIComponent(diagnosticState.symptoms)}`, {
          method: 'GET',
        });
        const tests = await response.json();
        
        addMessage({
          content: "Based on your diagnosis, here are the recommended medical tests:",
          role: 'assistant',
          type: 'tests',
          tests: tests,
        });
      } catch (error) {
        console.error('Error getting test recommendations:', error);
        addMessage({
          content: "I'm sorry, there was an error getting test recommendations. Please try again.",
          role: 'assistant',
          type: 'text'
        });
      }
      setIsLoading(false);
      return;
    }

    // Check if user wants to book appointment after diagnosis  
    if (content.toLowerCase().includes('book an appointment') || content.toLowerCase().includes('i want to book an appointment')) {
      try {
        // Get doctor recommendations using LLM
      const response = await fetch('http://localhost:8000/recommend-doctors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symptoms: diagnosticState.symptoms }),
        });
        const doctors = await response.json();
        
        addMessage({
          content: "Based on your diagnosis, here are the recommended doctors:",
          role: 'assistant',
          type: 'doctors',
          doctors: doctors,
        });
      } catch (error) {
        console.error('Error getting doctor recommendations:', error);
        addMessage({
          content: "I'm sorry, there was an error getting doctor recommendations. Please try again.",
          role: 'assistant',
          type: 'text'
        });
      }
      setIsLoading(false);
      return;
    }

    if (diagnosticState.isDiagnosing && diagnosticState.sessionId && diagnosticState.currentQuestionId !== null) {
      // Handle answer to a diagnostic question
      const response = await fetch('http://localhost:8000/answer-diagnostic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          session_id: diagnosticState.sessionId, 
          answer: content, 
          question_id: diagnosticState.currentQuestionId 
        }),
      });
      const result: RouterResponse = await response.json();
      
      if (result.next_step === 'answer_question' && result.current_question) {
        addMessage({ content: result.message, role: 'assistant', type: 'text' });
        addMessage({ content: '', role: 'assistant', type: 'diagnostic_question', question: result.current_question });
        setDiagnosticState(prev => ({ ...prev, currentQuestionId: result.current_question?.question_id || null }));
      } else if (result.next_step === 'review_diagnosis') {
        addMessage({ content: result.message, role: 'assistant', type: 'diagnostic_result', diagnosticResult: result });
        setDiagnosticState(prev => ({ ...prev, isDiagnosing: false, currentQuestionId: null }));
      }
    } else {
      // Start a new diagnostic session
      const response = await fetch(`http://localhost:8000/start-diagnostic?symptoms=${encodeURIComponent(content)}`, {
        method: 'POST',
      });
      const result: RouterResponse = await response.json();

      setDiagnosticState({ 
        sessionId: result.session_id, 
        isDiagnosing: true, 
        symptoms: content,
        currentQuestionId: result.current_question?.question_id || null
      });
      
      if (result.message) {
        addMessage({ content: result.message, role: 'assistant', type: 'text' });
      }
      if (result.current_question) {
        addMessage({ content: '', role: 'assistant', type: 'diagnostic_question', question: result.current_question });
      }
    }
    setIsLoading(false);
  };

  const handleBookAppointment = (doctors: Doctor[]) => {
    addMessage({
      content: "Excellent. Here are the recommended specialists. Please choose one to proceed with booking.",
            role: 'assistant',
            type: 'doctors',
      doctors,
    });
  };

  const handleBookTests = (tests: TestRecommendation[]) => {
    addMessage({
      content: "Certainly. Here are the recommended tests. Please review and confirm to book.",
        role: 'assistant',
      type: 'tests',
      tests,
    });
  };

  const handleDoctorSelect = (doctor: Doctor) => {
    addMessage({
      content: `You've selected Dr. ${doctor.name}. Please provide the details to book your appointment.`,
      role: 'assistant',
      type: 'appointment-form',
      selectedDoctor: doctor,
    });
  };

  const handleAppointmentSubmit = async (appointmentData: AppointmentData) => {
    setIsLoading(true);
    const response = await fetch('http://localhost:8000/book-appointment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(appointmentData),
    });
    const result = await response.json();
    setMessages(prev => prev.filter(m => m.type !== 'appointment-form'));
    addMessage({
      content: result.message || '✅ Appointment booked successfully!',
      role: 'assistant',
      type: 'appointment-success',
      appointment: { ...appointmentData, id: result.id, doctor_name: result.doctor_name, status: 'confirmed' }
    });
    setIsLoading(false);
  };
  
  const handleTestsSelect = (tests: TestRecommendation[]) => {
      addMessage({
        content: `You've selected ${tests.length} test${tests.length !== 1 ? 's' : ''}. Please provide the details to book your tests.`,
        role: 'assistant',
        type: 'test_form',
        selectedTests: tests,
    });
  }

  const handleTestSubmit = async (bookingData: any) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/book-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to book tests');
      }

      const result = await response.json();

      // Remove the test form message
      setMessages(prev => prev.filter(m => m.type !== 'test_form'));
      
      addMessage({
        content: result.message || '✅ Tests booked successfully!',
        role: 'assistant',
        type: 'text'
      });
    } catch (error) {
      console.error('Error booking tests:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addMessage({
        content: `❌ Error booking tests: ${errorMessage}`,
        role: 'assistant',
        type: 'text'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRescheduleAppointment = async (appointmentId: number) => {
    // Find the appointment from messages to get complete data
    const appointmentMessage = messages.find(m => 
      m.type === 'appointment-success' && m.appointment?.id === appointmentId
    );
    
    if (!appointmentMessage?.appointment) {
      addMessage({
        content: '❌ Could not find appointment details for rescheduling.',
      role: 'assistant',
      type: 'text'
      });
      return;
    }

    // Add reschedule form message with complete appointment data
    addMessage({
      content: `Please select a new date and time for your appointment with ${appointmentMessage.appointment.doctor_name}.`,
      role: 'assistant',
      type: 'reschedule-form',
      appointment: appointmentMessage.appointment,
    });
  };

  const handleRescheduleSubmit = async (appointmentId: number, newDate: string, newTime: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/reschedule-appointment', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appointment_id: appointmentId,
          new_date: newDate,
          new_time: newTime
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reschedule appointment');
      }

      const result = await response.json();

      // Remove the reschedule form message
      setMessages(prev => prev.filter(m => m.type !== 'reschedule-form'));

      // Find the original appointment to get missing fields
      const originalAppointment = messages.find(m => 
        m.type === 'appointment-success' && m.appointment?.id === appointmentId
      )?.appointment;
      
      addMessage({
        content: result.message || '✅ Appointment rescheduled successfully!',
        role: 'assistant',
        type: 'appointment-success',
        appointment: {
          id: result.id,
          doctor_name: result.doctor_name,
          doctor_id: originalAppointment?.doctor_id || 0,
          patient_name: result.patient_name,
          appointment_date: result.appointment_date,
          appointment_time: result.appointment_time,
          notes: result.notes || '',
          symptoms: originalAppointment?.symptoms || '',
          status: result.status
        }
      });
    } catch (error) {
      console.error('Error rescheduling appointment:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addMessage({
        content: `❌ Error rescheduling appointment: ${errorMessage}`,
        role: 'assistant',
        type: 'text'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRescheduleCancel = () => {
    // Remove the reschedule form message
    setMessages(prev => prev.filter(m => m.type !== 'reschedule-form'));
    addMessage({
      content: 'Reschedule cancelled.',
      role: 'assistant',
      type: 'text'
    });
  };

  const handleCancelAppointment = async (appointmentId: number) => {
    if (isLoading) return; // Prevent multiple simultaneous requests
    
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/cancel-appointment/${appointmentId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to cancel appointment');
      }
      
      const result = await response.json();
      
      addMessage({
        content: result.message || '✅ Appointment cancelled successfully.',
        role: 'assistant',
        type: 'text'
      });
    } catch (error) {
      console.error('Error cancelling appointment:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addMessage({
        content: `❌ Error cancelling appointment: ${errorMessage}`,
        role: 'assistant',
        type: 'text'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-chat-bg text-white">
      {messages.length <= 1 ? (
        <div className="flex flex-col h-full">
          <div className="flex-1 flex flex-col justify-center">
            <WelcomeScreen onExampleClick={handleSendMessage} />
            <div className="px-4 md:px-6 pb-8">
              <div className="max-w-3xl mx-auto">
                <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} disabled={isLoading} />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
            {messages.map((msg) => (
              <MessageBubble 
                key={msg.id}
                message={msg}
                onQuickReply={handleSendMessage}
                onBookAppointment={handleBookAppointment}
                onBookTests={handleBookTests}
                onDoctorSelect={handleDoctorSelect}
                onAppointmentSubmit={handleAppointmentSubmit}
                onTestsSelect={handleTestsSelect}
                onTestSubmit={handleTestSubmit}
                onRescheduleAppointment={handleRescheduleAppointment}
                onRescheduleSubmit={handleRescheduleSubmit}
                onRescheduleCancel={handleRescheduleCancel}
                onCancelAppointment={handleCancelAppointment}
                isLoading={isLoading}
              />
            ))}
            {isLoading && (
              <div className="flex justify-start">
                  <div className="w-8 h-8 rounded-full flex-shrink-0 bg-green-600 flex items-center justify-center">
                    <i className="fas fa-robot text-white text-sm"></i>
                  </div>
                  <div className="ml-3 bg-chat-assistant rounded-2xl px-4 py-3 text-sm text-gray-300">
                      Typing...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="p-4 md:p-6 border-t border-chat-border">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} disabled={isLoading} />
      </div>
        </>
      )}
    </div>
  );
};

export default ChatContainer; 