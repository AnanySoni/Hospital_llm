import React, { useState, useEffect, useRef } from 'react';
import { Message, Doctor, AppointmentData, RouterResponse, TestRecommendation, SmartWelcomeResponse, PatientProfile, DiagnosticQuestion } from '../types';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import WelcomeScreen from './WelcomeScreen';
import PhoneInputForm from './PhoneInputForm';
import { SessionStorageManager } from '../utils/sessionStorage';

interface ChatContainerProps {
  isCalendarConnected?: boolean;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ isCalendarConnected = false }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => SessionStorageManager.getSessionId());
  const [diagnosticState, setDiagnosticState] = useState<{
    sessionId: string | null;
    isDiagnosing: boolean;
    symptoms: string;
    currentQuestionId: number | null;
    currentQuestion: DiagnosticQuestion | null;
  }>({ sessionId: null, isDiagnosing: false, symptoms: '', currentQuestionId: null, currentQuestion: null });

  const [phoneRecognitionState, setPhoneRecognitionState] = useState({
    isCollectingPhone: false, 
    currentSymptoms: '', 
    conversationHistory: '',
    pendingDoctors: [] as Doctor[],
    patientProfile: null as PatientProfile | null,
    smartWelcomeData: null as SmartWelcomeResponse | null
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load conversation history on component mount
  useEffect(() => {
    const loadConversationHistory = () => {
      try {
        const recentMessages = SessionStorageManager.getConversationHistory();
          if (recentMessages.length > 0) {
            // Convert to Message format and add to state
          const formattedMessages = recentMessages.map((entry: any) => ({
            id: entry.id || Date.now() + Math.random(),
            content: entry.content || '',
              role: entry.role as 'user' | 'assistant',
              timestamp: new Date(entry.timestamp),
            type: 'text' as const
          }));
            
            setMessages(formattedMessages);
          }
      } catch (error) {
        console.error('Error loading conversation history:', error);
      }
    };
    
    loadConversationHistory();
  }, []);

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date(),
    } as Message;
    setMessages(prev => [...prev, newMessage]);
    
    // Save to localStorage for session continuity
    SessionStorageManager.addConversationEntry({
      role: newMessage.role,
      content: newMessage.content,
      type: newMessage.type,
      metadata: { 
        doctors: newMessage.doctors,
        appointment: newMessage.appointment,
        diagnosticResult: newMessage.diagnosticResult,
        question: newMessage.question,
        tests: newMessage.tests 
      }
    });
  };

  const clearChat = () => {
    setMessages([]);
    setDiagnosticState({
      sessionId: null,
      isDiagnosing: false,
      symptoms: '',
      currentQuestionId: null,
      currentQuestion: null
    });
    SessionStorageManager.clearConversationHistory();
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
      const urlParams = new URLSearchParams({
        session_id: diagnosticState.sessionId,
        question_id: diagnosticState.currentQuestionId.toString(),
        answer_value: content
      });
      
      // Add question details if available
      if (diagnosticState.currentQuestion) {
        urlParams.append('question_text', diagnosticState.currentQuestion.question);
        urlParams.append('question_type', diagnosticState.currentQuestion.question_type || 'text');
        if (diagnosticState.currentQuestion.options) {
          urlParams.append('question_options', JSON.stringify(diagnosticState.currentQuestion.options));
        }
      }
      
      const response = await fetch(`http://localhost:8000/v2/answer-adaptive-question?${urlParams.toString()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const result: RouterResponse = await response.json();
      
      if ((result.next_step === 'answer_question' || result.next_step === 'continue_diagnostic') && result.current_question) {
        addMessage({ content: result.message, role: 'assistant', type: 'text' });
        addMessage({ content: '', role: 'assistant', type: 'diagnostic_question', question: result.current_question });
        setDiagnosticState(prev => ({ 
          ...prev, 
          currentQuestionId: result.current_question?.question_id || null,
          currentQuestion: result.current_question || null
        }));
      } else if (result.next_step === 'provide_diagnosis' || result.next_step === 'review_diagnosis' || result.next_step === 'emergency_referral') {
        addMessage({ content: result.message, role: 'assistant', type: 'diagnostic_result', diagnosticResult: result });
        
        // Note: Consequence message is now included within the diagnostic_result type in MessageBubble
        // No need to create a separate consequence_alert message
        
        setDiagnosticState(prev => ({ 
          ...prev, 
          isDiagnosing: false, 
          currentQuestionId: null, 
          currentQuestion: null 
        }));
      }
    } else {
      // Check if this is conversational input or actual symptoms
      const lowerContent = content.toLowerCase().trim();
      const isConversationalInput = 
        lowerContent.length <= 3 ||
        ['hi', 'hello', 'hey', 'help', 'what', 'how', 'ok', 'okay', 'yes', 'no', 'thanks', 'thank you'].some(word => 
          lowerContent === word || lowerContent.startsWith(word + ' ')
        );

      if (isConversationalInput) {
        addMessage({
          content: "Hello! 👋 I'm here to help you find the right doctor for your health concerns. To provide you with the best recommendations, I'll need to ask you a few questions about your symptoms. Please describe any symptoms or health issues you're experiencing. For example, you could say 'I have a headache and fever' or 'I'm experiencing chest pain'.",
          role: 'assistant',
          type: 'text'
        });
      } else {
        // Start diagnostic session with critical questions for proper symptoms
        try {
          const response = await fetch(`http://localhost:8000/v2/start-adaptive-diagnostic?symptoms=${encodeURIComponent(content)}&session_id=${Date.now()}`, {
            method: 'POST',
          });
          const result: RouterResponse = await response.json();

          setDiagnosticState({ 
            sessionId: result.session_id, 
            isDiagnosing: true, 
            symptoms: content,
            currentQuestionId: result.current_question?.question_id || null,
            currentQuestion: result.current_question || null
          });
          
          if (result.message) {
            addMessage({ content: result.message, role: 'assistant', type: 'text' });
          }
          if (result.current_question) {
            addMessage({ content: '', role: 'assistant', type: 'diagnostic_question', question: result.current_question });
          }
        } catch (error) {
          console.error('Error starting diagnostic session:', error);
          addMessage({
            content: "I'm sorry, there was an error starting the diagnostic session. Please try again.",
            role: 'assistant',
            type: 'text'
          });
        }
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
    // Get conversation history for phone recognition
    const conversationHistory = messages
      .filter(m => m.role === 'user')
      .map(m => m.content)
      .join(' ');

    // Check if we already have patient profile from phone recognition
    if (phoneRecognitionState.patientProfile) {
      // Skip phone collection, go directly to appointment form
      addMessage({
        content: `You've selected Dr. ${doctor.name}. Please provide the details to book your appointment.`,
        role: 'assistant',
        type: 'appointment-form',
        selectedDoctor: doctor,
      });
    } else {
      // Start phone recognition flow
      setPhoneRecognitionState(prev => ({
        ...prev,
        isCollectingPhone: true,
        currentSymptoms: diagnosticState.symptoms || 'general consultation',
        conversationHistory,
        pendingDoctors: [doctor]
      }));

      addMessage({
        content: `Great choice! Dr. ${doctor.name} is an excellent doctor for your condition. To proceed with booking, I'll need to collect some information first.`,
        role: 'assistant',
        type: 'text'
      });
    }
  };

  const handleAppointmentSubmit = async (appointmentData: AppointmentData) => {
    setIsLoading(true);
    
    // Enhance appointment data with patient profile information if available
    let enhancedAppointmentData = { ...appointmentData };
    if (phoneRecognitionState.patientProfile) {
      enhancedAppointmentData = {
        ...appointmentData,
        patient_name: appointmentData.patient_name || phoneRecognitionState.patientProfile.first_name,
        phone_number: appointmentData.phone_number || phoneRecognitionState.patientProfile.phone_number,
        symptoms: appointmentData.symptoms || phoneRecognitionState.currentSymptoms
      };
    }
    
    const response = await fetch('http://localhost:8000/book-appointment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(enhancedAppointmentData),
    });
    const result = await response.json();
    setMessages(prev => prev.filter(m => m.type !== 'appointment-form'));
    
    // Generate personalized success message
    let successMessage = result.message || '✅ Appointment booked successfully!';
    if (phoneRecognitionState.patientProfile && phoneRecognitionState.smartWelcomeData) {
      const { patient_profile } = phoneRecognitionState.smartWelcomeData;
      if (patient_profile.total_visits > 1) {
        successMessage += ` Welcome back, ${patient_profile.first_name}! This is your ${patient_profile.total_visits}${getOrdinalSuffix(patient_profile.total_visits)} visit with us.`;
      }
    }
    
    addMessage({
      content: successMessage,
      role: 'assistant',
      type: 'appointment-success',
      appointment: { ...enhancedAppointmentData, id: result.id, doctor_name: result.doctor_name, status: 'confirmed' }
    });
    setIsLoading(false);
  };

  // Helper function for ordinal numbers
  const getOrdinalSuffix = (num: number): string => {
    const j = num % 10;
    const k = num % 100;
    if (j === 1 && k !== 11) return 'st';
    if (j === 2 && k !== 12) return 'nd';
    if (j === 3 && k !== 13) return 'rd';
    return 'th';
  };
  
  const handleTestsSelect = (tests: TestRecommendation[]) => {
      addMessage({
        content: `You've selected ${tests.length} test${tests.length !== 1 ? 's' : ''}. Please provide the details to book your tests.`,
        role: 'assistant',
        type: 'test_form',
        selectedTests: tests,
        patientProfile: phoneRecognitionState.patientProfile || undefined,
        symptoms: phoneRecognitionState.currentSymptoms || diagnosticState.symptoms
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
      
      // Add success message with booking details (like appointment-success)
      addMessage({
        content: result.message || '✅ Tests booked successfully!',
        role: 'assistant',
        type: 'test-success',
        testBooking: {
          booking_id: result.booking_id,
          tests_booked: result.tests_booked,
          appointment_date: result.appointment_date,
          appointment_time: result.appointment_time,
          total_cost: result.total_cost,
          patient_name: bookingData.patient_name,
          status: 'confirmed',
          preparation_instructions: result.preparation_instructions
        }
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

  const handleCancelTest = async (bookingId: string) => {
    if (isLoading) return; // Prevent multiple simultaneous requests
    
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/tests/cancel/${bookingId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to cancel test booking');
      }
      
      const result = await response.json();
      
      addMessage({
        content: result.message || '✅ Test booking cancelled successfully.',
        role: 'assistant',
        type: 'text'
      });
    } catch (error) {
      console.error('Error cancelling test booking:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addMessage({
        content: `❌ Error cancelling test booking: ${errorMessage}`,
        role: 'assistant',
        type: 'text'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Phase 2: Phone recognition handlers
  const handlePatientRecognized = (smartWelcomeResponse: SmartWelcomeResponse) => {
    const { patient_profile, welcome_message } = smartWelcomeResponse;
    
    setPhoneRecognitionState(prev => ({
      ...prev,
      isCollectingPhone: false,
      patientProfile: patient_profile,
      smartWelcomeData: smartWelcomeResponse
    }));

    // Add personalized welcome message
    addMessage({
      content: welcome_message,
      role: 'assistant',
      type: 'text'
    });

    // Continue with appointment booking flow
    if (phoneRecognitionState.pendingDoctors.length > 0) {
      const selectedDoctor = phoneRecognitionState.pendingDoctors[0];
      addMessage({
        content: `Perfect! Now let's book your appointment with Dr. ${selectedDoctor.name}. Please provide the appointment details.`,
        role: 'assistant',
        type: 'appointment-form',
        selectedDoctor: selectedDoctor,
        patientProfile: patient_profile,
        symptoms: phoneRecognitionState.currentSymptoms,
      });
    }
  };

  const handlePhoneRecognitionCancel = () => {
    setPhoneRecognitionState(prev => ({
      ...prev,
      isCollectingPhone: false,
      currentSymptoms: '',
      conversationHistory: '',
      pendingDoctors: []
    }));

    addMessage({
      content: "No problem! You can continue browsing our services. If you'd like to book an appointment later, just let me know.",
      role: 'assistant',
      type: 'text'
    });
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
                onCancelTest={handleCancelTest}
                isLoading={isLoading}
              />
            ))}
            
            {/* Phase 2: Phone Recognition Form */}
            {phoneRecognitionState.isCollectingPhone && (
              <div className="flex justify-start">
                <div className="w-8 h-8 rounded-full flex-shrink-0 bg-green-600 flex items-center justify-center">
                  <i className="fas fa-robot text-white text-sm"></i>
                </div>
                <div className="ml-3 max-w-lg">
                  <PhoneInputForm
                    onPatientRecognized={handlePatientRecognized}
                    onCancel={handlePhoneRecognitionCancel}
                    symptoms={phoneRecognitionState.currentSymptoms}
                    sessionId={sessionId}
                    conversationHistory={phoneRecognitionState.conversationHistory}
                  />
                </div>
              </div>
            )}
            
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
            <div className="flex items-center gap-3 mb-3">
              <button
                onClick={clearChat}
                className="text-xs text-gray-400 hover:text-white transition-colors duration-200 flex items-center gap-1"
                disabled={isLoading}
              >
                <i className="fas fa-trash text-xs"></i>
                Clear Chat
              </button>
              <div className="text-xs text-gray-500">
                {messages.length} messages
              </div>
            </div>
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} disabled={isLoading} />
      </div>
        </>
      )}
    </div>
  );
};

export default ChatContainer; 