import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Message, Doctor, AppointmentData, RouterResponse, TestRecommendation, DiagnosticQuestion, SmartWelcomeResponse, PatientProfile } from '../types';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import WelcomeScreen from './WelcomeScreen';
import { SessionStorageManager } from '../utils/sessionStorage';
import { useProgress } from '../contexts/ProgressContext';
import { useHospital } from '../contexts/HospitalContext';
import { apiFetch } from '../utils/api';

interface ChatContainerProps {
  isCalendarConnected?: boolean;
  clearChatFlag?: boolean;
  onClearChatHandled?: () => void;
  slug?: string;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ isCalendarConnected = false, clearChatFlag, onClearChatHandled, slug }) => {
  const { hospital } = useHospital();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [diagnosticState, setDiagnosticState] = useState<{
    sessionId: string | null;
    isDiagnosing: boolean;
    symptoms: string;
    currentQuestionId: number | null;
    currentQuestion: DiagnosticQuestion | null;
  }>({ sessionId: null, isDiagnosing: false, symptoms: '', currentQuestionId: null, currentQuestion: null });

  const [phoneRecognitionState, setPhoneRecognitionState] = useState<{
    isCollectingPhone: boolean;
    currentSymptoms: string;
    conversationHistory: string;
    pendingDoctors: Doctor[];
    patientProfile: PatientProfile | null;
    smartWelcomeData: SmartWelcomeResponse | null;
  }>({
    isCollectingPhone: false, 
    currentSymptoms: '', 
    conversationHistory: '',
    pendingDoctors: [],
    patientProfile: null,
    smartWelcomeData: null
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { setCurrentStep, updateStep, resetProgress } = useProgress();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize progress when component mounts
  useEffect(() => {
    setCurrentStep('symptoms');
  }, [setCurrentStep]);

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
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
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setDiagnosticState({
      sessionId: null,
      isDiagnosing: false,
      symptoms: '',
      currentQuestionId: null,
      currentQuestion: null
    });
    SessionStorageManager.clearConversationHistory();
    // Reset progress when chat is cleared
    resetProgress();
    setCurrentStep('symptoms');
  }, [resetProgress, setCurrentStep]);

  // Clear chat flag handler - must be after clearChat is defined
  useEffect(() => {
    if (clearChatFlag) {
      clearChat();
      onClearChatHandled?.();
    }
  }, [clearChatFlag, onClearChatHandled, clearChat]);

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
            type: entry.type || 'text',
            ...entry.metadata
          }));
          setMessages(formattedMessages);
        } else {
          // No messages in storage, add initial assistant message and persist it
          const initialMessage = {
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            content: "Let's start with some questions to better understand your symptoms.",
            role: 'assistant' as const,
            type: 'text' as const,
            timestamp: new Date(),
          };
          setMessages([initialMessage]);
          SessionStorageManager.addConversationEntry({
            role: initialMessage.role,
            content: initialMessage.content,
            type: initialMessage.type,
            metadata: {}
          });
        }
      } catch (error) {
        console.error('Error loading conversation history:', error);
      }
    };
    loadConversationHistory();
  }, []); // Remove addMessage dependency to prevent infinite loop



  const handleSendMessage = async (content: string, quickReply = false) => {
    if (!quickReply) {
      addMessage({ content, role: 'user', type: 'text' });
    }
    
    setIsLoading(true);

    // Check if user wants to book tests after diagnosis
    if (content.toLowerCase().includes('book medical tests') || content.toLowerCase().includes('i want to book medical tests')) {
      // Update progress to booking step
      setCurrentStep('booking');
      updateStep('diagnosis', 'completed');
      
    try {
      // Get test recommendations using LLM, scoped to hospital
      const tests = await apiFetch(`/tests/recommendations/${encodeURIComponent(diagnosticState.symptoms)}`, { slug: '' });
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
      // Update progress to booking step
      setCurrentStep('booking');
      updateStep('diagnosis', 'completed');
      
      try {
        // Get doctor recommendations using LLM, scoped to hospital
        const doctors = await apiFetch('/recommend-doctors', {
          slug: '',
          method: 'POST',
          body: { symptoms: diagnosticState.symptoms }
        });
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
      // Update progress to show we're in the diagnosis phase
      setCurrentStep('diagnosis');
      updateStep('symptoms', 'completed');
      updateStep('questions', 'active');
      
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
      
      const result: RouterResponse = await apiFetch(`/v2/h/${hospital?.slug || slug || ''}/answer-adaptive-question?${urlParams.toString()}`, {
        method: 'POST',
        slug: ''
      });
      
      if ((result.next_step === 'answer_question' || result.next_step === 'continue_diagnostic') && result.current_question) {
        addMessage({ content: result.message, role: 'assistant', type: 'text' });
        addMessage({ content: '', role: 'assistant', type: 'diagnostic_question', question: result.current_question });
        setDiagnosticState(prev => ({ 
          ...prev, 
          currentQuestionId: result.current_question?.question_id || null,
          currentQuestion: result.current_question || null
        }));
      } else if (result.next_step === 'provide_diagnosis' || result.next_step === 'review_diagnosis' || result.next_step === 'emergency_referral') {
        // Update progress to show diagnosis is complete
        updateStep('questions', 'completed');
        updateStep('analysis', 'completed');
        updateStep('prediction', 'completed');
        updateStep('diagnosis', 'completed');
        
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
        // Update progress to show symptoms are being processed
        updateStep('symptoms', 'active');
        
        // Start diagnostic session with critical questions for proper symptoms
        try {
          const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          const result: RouterResponse = await apiFetch(`/v2/h/${hospital?.slug || slug || ''}/start-adaptive-diagnostic?symptoms=${encodeURIComponent(content)}&session_id=${newSessionId}`, {
            method: 'POST',
            slug: ''
          });

          setDiagnosticState({ 
            sessionId: result.session_id, 
            isDiagnosing: true, 
            symptoms: content,
            currentQuestionId: result.current_question?.question_id || null,
            currentQuestion: result.current_question || null
          });
          
          // Update progress to show symptoms are complete and diagnosis is starting
          updateStep('symptoms', 'completed');
          setCurrentStep('diagnosis');
          
          if (result.message) {
            addMessage({ content: result.message, role: 'assistant', type: 'text' });
          }
          if (result.current_question) {
            addMessage({ content: '', role: 'assistant', type: 'diagnostic_question', question: result.current_question });
          }
        } catch (error) {
          console.error('Error starting diagnostic session:', error);
          updateStep('symptoms', 'error');
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
    // Always show the appointment form, phone recognition will happen during form submission
      addMessage({
        content: `You've selected Dr. ${doctor.name}. Please provide the details to book your appointment.`,
        role: 'assistant',
        type: 'appointment-form',
        selectedDoctor: doctor,
      patientProfile: phoneRecognitionState.patientProfile || undefined,
      symptoms: phoneRecognitionState.currentSymptoms || diagnosticState.symptoms,
    });
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
    
    try {
    const result = await apiFetch(`/h/${hospital?.slug || slug || ''}/book-appointment`, {
      slug: '',
      method: 'POST',
      body: enhancedAppointmentData
    });
      console.log('Appointment booking result:', result); // Debug log
    setMessages(prev => prev.filter(m => m.type !== 'appointment-form'));
    
    // Generate personalized success message
    let successMessage = result.message || '✅ Appointment booked successfully!';
    if (phoneRecognitionState.patientProfile && phoneRecognitionState.smartWelcomeData) {
      const { patient_profile } = phoneRecognitionState.smartWelcomeData;
      if (patient_profile.total_visits > 1) {
        successMessage += ` Welcome back, ${patient_profile.first_name}! This is your ${patient_profile.total_visits}${getOrdinalSuffix(patient_profile.total_visits)} visit with us.`;
      }
    }
    
    // Update progress to show booking is complete and confirmation is active
    updateStep('booking', 'completed');
    setCurrentStep('confirmation');
    updateStep('confirmation', 'active');
    
    addMessage({
      content: successMessage,
      role: 'assistant',
      type: 'appointment-success',
      appointment: { 
        ...enhancedAppointmentData, 
        id: result.id || result.appointment_id || Date.now(), // Fallback ID generation
        doctor_name: result.doctor_name || result.doctor?.name || 'Unknown Doctor', 
        status: result.status || 'confirmed' 
      }
    });
    
      // Mark confirmation as completed after a short delay
      setTimeout(() => {
        updateStep('confirmation', 'completed');
      }, 2000);
      
    } catch (error) {
      console.error('Error booking appointment:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addMessage({
        content: `❌ Error booking appointment: ${errorMessage}`,
        role: 'assistant',
        type: 'text'
      });
    } finally {
    setIsLoading(false);
    }
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
    // Always show the test form, phone recognition will happen during form submission
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
      const result = await apiFetch(`/h/${hospital?.slug || slug || ''}/book-tests`, {
        slug: '',
        method: 'POST',
        body: bookingData
      });

      // Remove the test form message
      setMessages(prev => prev.filter(m => m.type !== 'test_form'));
      
      // Update progress to show booking is complete and confirmation is active
      updateStep('booking', 'completed');
      setCurrentStep('confirmation');
      updateStep('confirmation', 'active');
      
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
      
      // Mark confirmation as completed after a short delay
      setTimeout(() => {
        updateStep('confirmation', 'completed');
      }, 2000);
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
    // Validate appointment ID
    if (!appointmentId || appointmentId === 0) {
      addMessage({
        content: '❌ Cannot reschedule appointment: Invalid appointment ID',
        role: 'assistant',
        type: 'text'
      });
      return;
    }
    
    setIsLoading(true);
    try {
      const result = await apiFetch('/reschedule-appointment', {
        slug: hospital?.slug || slug || '',
        method: 'PUT',
        body: {
          appointment_id: appointmentId,
          new_date: newDate,
          new_time: newTime
        }
      });

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
    
    // Validate appointment ID
    if (!appointmentId || appointmentId === 0) {
      addMessage({
        content: '❌ Cannot cancel appointment: Invalid appointment ID',
        role: 'assistant',
        type: 'text'
      });
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/h/${slug}/cancel-appointment/${appointmentId}`, {
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
      
      // Remove the test success message from chat
      setMessages(prev => prev.filter(m => !(m.type === 'test-success' && m.testBooking?.booking_id === bookingId)));
      
      addMessage({
        content: result.message || '✅ Test booking cancelled successfully',
        role: 'assistant',
        type: 'text'
      });
    } catch (error) {
      console.error('Error cancelling test:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      addMessage({
        content: `❌ Error cancelling test: ${errorMessage}`,
        role: 'assistant',
        type: 'text'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Phone recognition handlers
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
  };

  return (
    <div className="h-full flex flex-col bg-chat-bg">
      {messages.length <= 1 ? (
        <div className="flex flex-col h-full px-2 sm:px-4 lg:px-8 py-4 lg:py-8">
          <div className="flex-1 flex flex-col justify-center">
            <WelcomeScreen onExampleClick={handleSendMessage} />
          </div>
          {/* Fixed input at bottom for welcome screen */}
          <div className="flex-shrink-0 px-2 sm:px-4 lg:px-6 pb-3 lg:pb-4">
            <div className="max-w-2xl mx-auto">
              <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} disabled={isLoading} />
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Scrollable messages area with fixed height calculation */}
          <div className="flex-1 overflow-y-auto overflow-x-hidden px-2 sm:px-4 lg:px-6 pt-3 lg:pt-4 pb-2 min-h-0">
            <div className="pb-4"> {/* Extra padding to ensure last message is visible and input never overlaps */}
              {messages.map((message, idx) => (
                <MessageBubble 
                  key={message.id}
                  message={message}
                  onDoctorSelect={handleDoctorSelect}
                  onAppointmentSubmit={handleAppointmentSubmit}
                  onTestsSelect={handleTestsSelect}
                  onTestSubmit={handleTestSubmit}
                  onQuickReply={handleSendMessage}
                  onBookAppointment={handleBookAppointment}
                  onBookTests={handleBookTests}
                  onRescheduleAppointment={handleRescheduleAppointment}
                  onRescheduleSubmit={handleRescheduleSubmit}
                  onRescheduleCancel={handleRescheduleCancel}
                  onCancelAppointment={handleCancelAppointment}
                  onCancelTest={handleCancelTest}
                  onPatientRecognized={handlePatientRecognized}
                  isLoading={isLoading}
                  hospitalSlug={slug || 'demo1'}
                />
              ))}
            </div>
            <div ref={messagesEndRef} />
          </div>
          
          {/* Fixed input area at bottom - ALWAYS stays at bottom regardless of content */}
          <div className="flex-shrink-0 border-t border-gray-600/30 bg-gradient-to-t from-chat-bg via-chat-bg to-transparent px-2 sm:px-4 lg:px-8 py-2 lg:py-3 backdrop-blur-sm">
            <div className="max-w-2xl mx-auto">
              <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} disabled={isLoading} />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ChatContainer; 