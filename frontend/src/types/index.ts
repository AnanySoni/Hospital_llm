export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  type: 'text' | 'doctors' | 'appointment-form' | 'appointment-success' | 'reschedule-form' | 'diagnostic_question' | 'diagnostic_result' | 'tests' | 'test_form';
  doctors?: Doctor[];
  selectedDoctor?: Doctor;
  appointment?: Appointment;
  diagnosticResult?: RouterResponse;
  question?: DiagnosticQuestion;
  tests?: TestRecommendation[];
  selectedTests?: TestRecommendation[];
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export interface ApiResponse {
  doctors?: Doctor[];
  message?: string;
  error?: string;
}

export interface Doctor {
  id: number;
  name: string;
  specialization: string;
  experience: string;
  reason: string;
  expertise: string[];
  rating?: number;
  availability?: string;
  location?: string;
}

export interface AppointmentData {
  doctor_id: number;
  patient_name: string;
  appointment_date: string;
  appointment_time: string;
  notes: string;
  symptoms: string;
}

export interface Appointment {
  id: number;
  doctor_name: string;
  doctor_id: number;
  patient_name: string;
  appointment_date: string;
  appointment_time: string;
  notes: string;
  symptoms: string;
  status: string;
}

export interface TestRecommendation {
  test_id: string;
  test_name: string;
  description: string;
  cost: number;
  category: string;
  preparation: string;
  urgency: string;
}

export interface DoctorRecommendation {
  id: number;
  name: string;
  specialization: string;
  reason: string;
  experience: string;
  expertise: string[];
}

export interface DiagnosticQuestion {
  question_id: number;
  question: string;
  question_type: string;
  options?: string[];
  required: boolean;
}

export interface PredictiveDiagnosis {
  possible_conditions: string[];
  confidence_level: string;
  urgency_level: string;
  recommended_action: string;
  explanation: string;
}

export interface RouterDecision {
  action_type: string;
  reasoning: string;
  recommended_tests: TestRecommendation[];
  recommended_doctors: DoctorRecommendation[];
  urgency_message: string;
}

export interface RouterResponse {
  session_id: string;
  current_question?: DiagnosticQuestion;
  questions_remaining: number;
  diagnosis?: PredictiveDiagnosis;
  decision?: RouterDecision;
  message: string;
  next_step: string;
}

export interface TestBookingRequest {
  patient_name: string;
  test_ids: string[];
  preferred_date: string;
  preferred_time: string;
  contact_number: string;
  notes?: string;
}

export interface TestBookingResponse {
  booking_id: string;
  message: string;
  tests_booked: string[];
  appointment_date: string;
  appointment_time: string;
  total_cost?: string;
  preparation_instructions: string[];
} 