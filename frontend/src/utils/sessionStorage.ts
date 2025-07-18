/**
 * Session Storage Utilities
 * Phase 1: Simple session-based tracking with localStorage
 */

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

export interface ConversationEntry {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type?: string;
  metadata?: any;
}

const SESSION_STORAGE_KEYS = {
  SESSION_ID: 'hospital_llm_session_id',
  USER_INFO: 'hospital_llm_user_info',
  PATIENT_HISTORY: 'hospital_llm_patient_history',
  CONVERSATION_HISTORY: 'hospital_llm_conversation_history',
  CURRENT_SESSION: 'hospital_llm_current_session'
};

export class SessionStorageManager {
  
  // Session ID Management
  static getSessionId(): string {
    let sessionId = localStorage.getItem(SESSION_STORAGE_KEYS.SESSION_ID);
    if (!sessionId) {
      sessionId = this.generateSessionId();
      localStorage.setItem(SESSION_STORAGE_KEYS.SESSION_ID, sessionId);
    }
    return sessionId;
  }
  
  static generateSessionId(): string {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
  
  static resetSession(): string {
    const newSessionId = this.generateSessionId();
    localStorage.setItem(SESSION_STORAGE_KEYS.SESSION_ID, newSessionId);
    
    // Clear existing data
    localStorage.removeItem(SESSION_STORAGE_KEYS.USER_INFO);
    localStorage.removeItem(SESSION_STORAGE_KEYS.PATIENT_HISTORY);
    localStorage.removeItem(SESSION_STORAGE_KEYS.CONVERSATION_HISTORY);
    localStorage.removeItem(SESSION_STORAGE_KEYS.CURRENT_SESSION);
    
    return newSessionId;
  }
  
  // User Info Management
  static getUserInfo(): SessionUserInfo | null {
    const userInfoStr = localStorage.getItem(SESSION_STORAGE_KEYS.USER_INFO);
    if (!userInfoStr) return null;
    
    try {
      return JSON.parse(userInfoStr);
    } catch (error) {
      console.error('Error parsing user info:', error);
      return null;
    }
  }
  
  static setUserInfo(userInfo: Partial<SessionUserInfo>): SessionUserInfo {
    const sessionId = this.getSessionId();
    const existingInfo = this.getUserInfo();
    
    const updatedInfo: SessionUserInfo = {
      sessionId,
      firstName: userInfo.firstName || existingInfo?.firstName,
      age: userInfo.age || existingInfo?.age,
      gender: userInfo.gender || existingInfo?.gender,
      createdAt: existingInfo?.createdAt || new Date().toISOString(),
      lastActive: new Date().toISOString()
    };
    
    localStorage.setItem(SESSION_STORAGE_KEYS.USER_INFO, JSON.stringify(updatedInfo));
    return updatedInfo;
  }
  
  static updateLastActive(): void {
    const userInfo = this.getUserInfo();
    if (userInfo) {
      userInfo.lastActive = new Date().toISOString();
      localStorage.setItem(SESSION_STORAGE_KEYS.USER_INFO, JSON.stringify(userInfo));
    }
  }
  
  // Patient History Management
  static getPatientHistory(): PatientHistoryEntry[] {
    const historyStr = localStorage.getItem(SESSION_STORAGE_KEYS.PATIENT_HISTORY);
    if (!historyStr) return [];
    
    try {
      return JSON.parse(historyStr);
    } catch (error) {
      console.error('Error parsing patient history:', error);
      return [];
    }
  }
  
  static addPatientHistoryEntry(entry: Omit<PatientHistoryEntry, 'id' | 'timestamp'>): PatientHistoryEntry {
    const history = this.getPatientHistory();
    const newEntry: PatientHistoryEntry = {
      ...entry,
      id: 'hist_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
      timestamp: new Date().toISOString()
    };
    
    history.unshift(newEntry); // Add to beginning
    
    // Keep only last 50 entries
    const trimmedHistory = history.slice(0, 50);
    localStorage.setItem(SESSION_STORAGE_KEYS.PATIENT_HISTORY, JSON.stringify(trimmedHistory));
    
    this.updateLastActive();
    return newEntry;
  }
  
  static getRecentSymptoms(limit: number = 10): string[] {
    const history = this.getPatientHistory();
    const symptoms = new Set<string>();
    
    for (const entry of history) {
      if (entry.symptoms) {
        entry.symptoms.forEach(symptom => symptoms.add(symptom));
      }
      if (symptoms.size >= limit) break;
    }
    
    return Array.from(symptoms).slice(0, limit);
  }
  
  static getRecentDiagnoses(limit: number = 5): string[] {
    const history = this.getPatientHistory();
    const diagnoses = new Set<string>();
    
    for (const entry of history) {
      if (entry.diagnosis) {
        diagnoses.add(entry.diagnosis);
      }
      if (diagnoses.size >= limit) break;
    }
    
    return Array.from(diagnoses).slice(0, limit);
  }
  
  static getChronicConditions(): string[] {
    const history = this.getPatientHistory();
    const conditions = new Set<string>();
    
    // Look for chronic conditions in diagnosis entries
    for (const entry of history) {
      if (entry.diagnosis) {
        // Look for keywords that suggest chronic conditions
        const chronicKeywords = ['chronic', 'diabetes', 'hypertension', 'asthma', 'arthritis', 'migraine'];
        const diagnosis = entry.diagnosis.toLowerCase();
        
        if (chronicKeywords.some(keyword => diagnosis.includes(keyword))) {
          conditions.add(entry.diagnosis);
        }
      }
    }
    
    return Array.from(conditions);
  }
  
  // Conversation History Management
  static getConversationHistory(): ConversationEntry[] {
    const historyStr = localStorage.getItem(SESSION_STORAGE_KEYS.CONVERSATION_HISTORY);
    if (!historyStr) return [];
    
    try {
      return JSON.parse(historyStr);
    } catch (error) {
      console.error('Error parsing conversation history:', error);
      return [];
    }
  }
  
  static addConversationEntry(entry: Omit<ConversationEntry, 'id' | 'timestamp'>): ConversationEntry {
    const history = this.getConversationHistory();
    const newEntry: ConversationEntry = {
      ...entry,
      id: 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
      timestamp: new Date().toISOString()
    };
    
    history.push(newEntry);
    
    // Keep only last 100 conversation entries
    const trimmedHistory = history.slice(-100);
    localStorage.setItem(SESSION_STORAGE_KEYS.CONVERSATION_HISTORY, JSON.stringify(trimmedHistory));
    
    this.updateLastActive();
    return newEntry;
  }
  
  static clearConversationHistory(): void {
    localStorage.removeItem(SESSION_STORAGE_KEYS.CONVERSATION_HISTORY);
  }
  
  // Context Generation for LLM
  static generatePatientContext(): string {
    const userInfo = this.getUserInfo();
    const recentSymptoms = this.getRecentSymptoms(5);
    const recentDiagnoses = this.getRecentDiagnoses(3);
    const chronicConditions = this.getChronicConditions();
    const history = this.getPatientHistory();
    
    if (!userInfo || history.length === 0) {
      return "New patient - no previous history available.";
    }
    
    const contextParts = [];
    
    // Basic info
    if (userInfo.firstName) {
      contextParts.push(`Patient: ${userInfo.firstName}`);
    }
    if (userInfo.age) {
      contextParts.push(`Age: ${userInfo.age}`);
    }
    if (userInfo.gender) {
      contextParts.push(`Gender: ${userInfo.gender}`);
    }
    
    // Visit history
    const lastVisit = new Date(userInfo.lastActive);
    const daysSince = Math.floor((Date.now() - lastVisit.getTime()) / (1000 * 60 * 60 * 24));
    contextParts.push(`Last visit: ${daysSince} days ago`);
    contextParts.push(`Total visits: ${history.length}`);
    
    // Medical history
    if (chronicConditions.length > 0) {
      contextParts.push(`Chronic conditions: ${chronicConditions.join(', ')}`);
    }
    
    if (recentSymptoms.length > 0) {
      contextParts.push(`Recent symptoms: ${recentSymptoms.join(', ')}`);
    }
    
    if (recentDiagnoses.length > 0) {
      contextParts.push(`Recent diagnoses: ${recentDiagnoses.join(', ')}`);
    }
    
    return contextParts.join('\n');
  }
  
  // Data Export/Import for debugging
  static exportSessionData(): any {
    return {
      sessionId: this.getSessionId(),
      userInfo: this.getUserInfo(),
      patientHistory: this.getPatientHistory(),
      conversationHistory: this.getConversationHistory()
    };
  }
  
  static importSessionData(data: any): void {
    if (data.sessionId) {
      localStorage.setItem(SESSION_STORAGE_KEYS.SESSION_ID, data.sessionId);
    }
    if (data.userInfo) {
      localStorage.setItem(SESSION_STORAGE_KEYS.USER_INFO, JSON.stringify(data.userInfo));
    }
    if (data.patientHistory) {
      localStorage.setItem(SESSION_STORAGE_KEYS.PATIENT_HISTORY, JSON.stringify(data.patientHistory));
    }
    if (data.conversationHistory) {
      localStorage.setItem(SESSION_STORAGE_KEYS.CONVERSATION_HISTORY, JSON.stringify(data.conversationHistory));
    }
  }
  
  // Storage size management
  static getStorageSize(): number {
    let total = 0;
    for (let key in localStorage) {
      if (key.startsWith('hospital_llm_')) {
        total += localStorage[key].length;
      }
    }
    return total;
  }
  
  static cleanupOldData(daysToKeep: number = 30): void {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);
    
    // Clean patient history
    const history = this.getPatientHistory();
    const filteredHistory = history.filter(entry => 
      new Date(entry.timestamp) > cutoffDate
    );
    localStorage.setItem(SESSION_STORAGE_KEYS.PATIENT_HISTORY, JSON.stringify(filteredHistory));
    
    // Clean conversation history
    const conversations = this.getConversationHistory();
    const filteredConversations = conversations.filter(entry => 
      new Date(entry.timestamp) > cutoffDate
    );
    localStorage.setItem(SESSION_STORAGE_KEYS.CONVERSATION_HISTORY, JSON.stringify(filteredConversations));
  }
}

export default SessionStorageManager; 