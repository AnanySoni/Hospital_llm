export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  type: 'text' | 'doctors' | 'appointment-form' | 'appointment-success' | 'reschedule-form' | 'diagnostic_question' | 'diagnostic_result' | 'tests' | 'test_form' | 'test-success';
  doctors?: Doctor[];
  selectedDoctor?: Doctor;
  appointment?: Appointment;
  diagnosticResult?: RouterResponse;
  question?: DiagnosticQuestion;
  tests?: TestRecommendation[];
  selectedTests?: TestRecommendation[];
  testBooking?: TestBooking;
  // Phase 2: Phone recognition data
  patientProfile?: PatientProfile;
  symptoms?: string;
  // Phase 1: Consequence messaging fields
  consequenceMessage?: ConsequenceMessage;
  riskProgression?: RiskProgression;
  persuasionMetrics?: PersuasionMetrics;
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
  phone_number: string;
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
  confidence_score?: number;
  diagnostic_confidence?: ConfidenceScore;
}

export interface RouterDecision {
  action_type: string;
  reasoning: string;
  recommended_tests: TestRecommendation[];
  recommended_doctors: DoctorRecommendation[];
  urgency_message: string;
  decision_confidence?: ConfidenceScore;
}

export interface ConfidenceScore {
  score: number;
  level: string;
  reasoning: string;
  uncertainty_factors: string[];
}

export interface RiskFactor {
  factor_type: string;
  severity: number;
  description: string;
  weight?: number;
}

export interface RedFlag {
  symptom: string;
  category: string;
  urgency_level: string;
  reasoning: string;
}

export interface TriageAssessment {
  level: 'emergency' | 'urgent' | 'soon' | 'routine';
  confidence_score: number;
  time_urgency: string;
  risk_factors: RiskFactor[];
  red_flags: RedFlag[];
  reasoning: string;
  emergency_override: boolean;
  recommendations: string[];
}

export interface UrgencyAssessmentRequest {
  symptoms: string;
  patient_age?: number;
  medical_history: string[];
  current_medications: string[];
  vital_signs?: { [key: string]: any };
  answers: { [key: string]: any };
}

export interface EmergencyCheckRequest {
  symptoms: string;
  age?: number;
}

export interface TriageResponse {
  assessment: TriageAssessment;
  next_steps: string[];
  emergency_contacts?: { [key: string]: string };
  follow_up_timeframe: string;
}

export interface RouterResponse {
  session_id: string;
  current_question?: DiagnosticQuestion;
  questions_remaining: number;
  diagnosis?: PredictiveDiagnosis;
  decision?: RouterDecision;
  message: string;
  next_step: string;
  confidence?: ConfidenceScore;
  triage_assessment?: TriageAssessment;
  urgency_override?: boolean;
  // Phase 1: Consequence Messaging (New Fields)
  consequence_message?: ConsequenceMessage;
  risk_progression?: RiskProgression;
  persuasion_metrics?: PersuasionMetrics;
}

// New interfaces for consequence messaging
export interface ConsequenceMessage {
  primary_consequence: string;
  risk_level: string;
  timeframe: string;
  escalation_risks: string[];
  opportunity_cost?: string;
  social_proof?: string;
  regret_prevention?: string;
  action_benefits: string;
}

export interface RiskProgression {
  immediate_risk: string;
  short_term_risk: string;
  long_term_risk: string;
  prevention_window: string;
}

export interface PersuasionMetrics {
  urgency_score: number;
  fear_appeal_strength: string;
  message_type: string;
  expected_conversion?: number;
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

export interface TestBooking {
  booking_id: string;
  tests_booked: string[];
  appointment_date: string;
  appointment_time: string;
  total_cost: string;
  patient_name: string;
  status: string;
  preparation_instructions?: string[];
}

// Session-based user tracking interfaces (Phase 1)
export interface SessionUserInfo {
  sessionId: string;
  firstName?: string;
  age?: number;
  gender?: string;
  createdAt: string;
  lastActive: string;
}

export interface PatientHistoryEntry {
  id: string;
  entryType: 'symptom' | 'diagnosis' | 'appointment' | 'test' | 'medication';
  symptoms?: string[];
  diagnosis?: string;
  doctorRecommendations?: any[];
  testRecommendations?: any[];
  severityLevel?: 'mild' | 'moderate' | 'severe' | 'emergency';
  urgencyLevel?: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: string;
  sessionContext?: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  conversation_count: number;
  recent_symptoms: string[];
  recent_diagnoses: string[];
  chronic_conditions: string[];
  allergies: string[];
  appointment_history: Array<{
    id: number;
    doctor_name: string;
    date: string;
    time: string;
    status: string;
    notes?: string;
  }>;
  test_history: Array<{
    id: number;
    test_name: string;
    test_type: string;
    date: string;
    time: string;
    status: string;
    cost?: string;
  }>;
  last_visit?: string;
}

export interface EnhancedChatRequest {
  message: string;
  session_id: string;
  user_info?: {
    first_name?: string;
    age?: number;
    gender?: string;
  };
  include_history?: boolean;
}

export interface SessionStats {
  session_id: string;
  is_new_user: boolean;
  total_conversations: number;
  returning_user: boolean;
  has_chronic_conditions?: boolean;
  recent_visit_count?: number;
  last_visit?: string;
}

// Phase 2: Phone-based recognition types
export interface PatientProfile {
  id: number;
  phone_number: string;
  first_name: string;
  last_name?: string;
  age?: number;
  gender?: string;
  family_member_type: string;
  total_visits: number;
  last_visit_date?: string;
  last_visit_symptoms?: string;
  chronic_conditions: string[];
  allergies: string[];
}

export interface SmartWelcomeResponse {
  patient_profile: PatientProfile;
  is_new_patient: boolean;
  welcome_message: string;
  symptom_analysis: {
    category: string;
    relatedness: {
      is_related: boolean;
      relationship_type: string;
      message: string;
      reference_previous: boolean;
      relevant_history?: any;
    };
  };
  next_action: string;
}

export interface PhoneRecognitionData {
  phone_number: string;
  first_name?: string;
  family_member_type?: string;
}

export interface PhoneBasedChatRequest {
  message: string;
  session_id: string;
  phone_number?: string;
  patient_name?: string;
  include_history?: boolean;
  is_booking_flow?: boolean;
}

// Phase 1: Triage & Risk Stratification Types
export interface RedFlag {
  symptom: string;
  severity: string;
  immediate_action: string;
  escalation_reason: string;
}

export interface RiskFactor {
  factor_type: string;
  factor_value: any;
  risk_weight: number;
  description: string;
}

export interface EmergencyEscalation {
  triggered_by: string[];
  emergency_level: string;
  recommended_action: string;
  contact_info: string;
  timestamp: string;
}

export interface TriageAssessment {
  triage_level: 'emergency' | 'urgent' | 'soon' | 'routine';
  urgency_score: number;
  timeframe: string;
  action_required: string;
  red_flags_detected: RedFlag[];
  risk_factors: RiskFactor[];
  confidence_score: number;
  escalation_required: boolean;
  emergency_contact_info?: string;
  reasoning: string;
}

export interface UrgencyResponse {
  triage_assessment: TriageAssessment;
  doctor_recommendations: DoctorRecommendation[];
  appointment_priority: string;
  follow_up_instructions: string;
  emergency_escalation?: EmergencyEscalation;
}

export interface TriageRequest {
  symptoms: string;
  patient_age?: number;
  chronic_conditions?: string[];
  current_medications?: string[];
  previous_diagnoses?: string[];
  pain_level?: number;
  symptom_duration?: string;
  vital_signs?: Record<string, any>;
} 