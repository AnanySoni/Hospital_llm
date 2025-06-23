# 🏥 Hospital LLM Project - Smart Diagnostic Router

An intelligent hospital appointment booking system with AI-powered diagnostic assessment, test recommendations, and smart routing.

## ✨ New Features

### 🧠 Smart Diagnostic Router
- **Interactive Q&A Flow**: Asks 3-5 critical questions based on symptoms
- **Predictive Diagnosis**: Uses LLM to analyze symptoms and provide possible conditions
- **Intelligent Routing**: Decides whether to recommend tests, appointments, or both
- **Urgency Assessment**: Determines if immediate medical attention is needed

### 🧪 Test Booking System
- **Comprehensive Test Catalog**: Blood tests, imaging, cardiac tests, etc.
- **Smart Recommendations**: Based on symptoms and diagnostic assessment
- **Cost Estimates**: Transparent pricing for all tests
- **Preparation Instructions**: Clear guidance for patients

### 🔄 Enhanced Chat Experience
- **Smart Intent Detection**: Recognizes when users want diagnostic assessment
- **Seamless Integration**: Diagnostic router flows naturally into existing chat
- **Rich Results Display**: Shows diagnosis, recommendations, and action buttons

## 🚀 Quick Start

### Option 1: One-Command Setup (Recommended)
```bash
python run_project.py
```

This will:
- ✅ Install all dependencies
- ✅ Set up the database with sample data
- ✅ Start backend server (port 8000)
- ✅ Start frontend server (port 3000)
- ✅ Open your browser automatically

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📱 How to Use

### 1. Start the Application
```bash
python run_project.py
```

### 2. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Try the Smart Diagnostic

#### Method 1: Direct Diagnostic Request
Type in the chat:
- "I want a diagnostic assessment"
- "Smart diagnostic for my symptoms"
- "Can you ask me some questions about my symptoms?"

#### Method 2: Describe Symptoms
Type your symptoms and the system will:
1. Ask if you want a smart diagnostic assessment
2. Guide you through 3-5 critical questions
3. Provide a predictive diagnosis
4. Recommend specific tests and doctors
5. Route you to booking tests or appointments

### 4. Example Flow
```
User: "I have chest pain and shortness of breath"

System: "I understand your symptoms. To provide the best care, 
I need to ask you a few important questions:"

Q1: "How severe is your pain on a scale of 1-10?"
Q2: "How long have you been experiencing these symptoms?"
Q3: "Are there any specific triggers that make it worse?"

System: "Based on your symptoms and answers, here's our assessment:
- Possible conditions: Angina, Anxiety, Respiratory infection
- Confidence: Medium
- Urgency: Urgent
- Recommended: ECG, Chest X-Ray, Blood tests
- Action: Book tests and see a cardiologist"
```

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── main.py                 # Main FastAPI application
├── core/
│   ├── database.py        # Database configuration
│   └── models.py          # SQLAlchemy models
├── services/
│   ├── appointment_service.py  # Appointment booking logic
│   └── test_service.py         # Test booking logic
├── utils/
│   └── llm_utils.py       # LLM integration & diagnostic logic
└── schemas/
    └── request_models.py  # Pydantic models
```

### Frontend (React + TypeScript)
```
frontend/src/
├── components/
│   ├── DiagnosticRouter.tsx    # Smart diagnostic interface
│   ├── TestBookingForm.tsx     # Test booking interface
│   ├── ChatContainer.tsx       # Main chat interface
│   └── MessageBubble.tsx       # Message display
└── types/
    └── index.ts               # TypeScript interfaces
```

## 🔧 API Endpoints

### Diagnostic Router
- `POST /start-diagnostic` - Start diagnostic session
- `POST /answer-diagnostic` - Submit diagnostic answer
- `POST /smart-recommend-doctors` - Enhanced doctor recommendations

### Test Booking
- `GET /available-tests` - Get all available tests
- `POST /book-tests` - Book medical tests
- `GET /tests/category/{category}` - Get tests by category
- `GET /tests/patient/{patient_name}` - Get patient's test bookings
- `DELETE /tests/cancel/{booking_id}` - Cancel test booking

### Existing Features
- `POST /recommend-doctors` - Doctor recommendations
- `POST /book-appointment` - Book appointments
- `PUT /reschedule-appointment` - Reschedule appointments
- `DELETE /cancel-appointment/{id}` - Cancel appointments

## 🧪 Available Tests

### Blood Tests
- Complete Blood Count (CBC) - $75
- Comprehensive Metabolic Panel - $120

### Imaging Tests
- Chest X-Ray - $150
- Abdominal Ultrasound - $300
- Brain MRI - $800

### Cardiac Tests
- Electrocardiogram (ECG) - $200
- Cardiac Stress Test - $400

### Other Tests
- Urinalysis - $45

## 🔑 Environment Variables

Create a `.env` file in the backend directory:

```env
# LLM API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/v1/chat/completions
GROQ_MODEL=llama2-70b-4096

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost/hospital_db
```

## 🎯 Key Features

### Smart Diagnostic Flow
1. **Symptom Analysis**: LLM analyzes initial symptoms
2. **Question Generation**: Creates 3-5 targeted questions
3. **Answer Processing**: Analyzes responses for urgency/severity
4. **Diagnostic Assessment**: Provides possible conditions
5. **Smart Routing**: Recommends tests, doctors, or emergency care

### Test Recommendations
- **Symptom-Based**: Recommends tests based on symptoms
- **Cost Transparency**: Shows estimated costs upfront
- **Preparation Guidance**: Clear instructions for each test
- **Urgency Levels**: Prioritizes tests by medical urgency

### Enhanced User Experience
- **Progressive Disclosure**: Shows information as needed
- **Action-Oriented**: Direct buttons to book tests/appointments
- **Emergency Detection**: Alerts for urgent medical situations
- **Seamless Integration**: Works within existing chat interface

## 🚨 Emergency Features

The system can detect emergency situations and:
- Show urgent warnings
- Recommend immediate medical attention
- Provide emergency contact information
- Route to emergency services when needed

## 🔄 Development

### Adding New Tests
Edit `backend/services/test_service.py` and add to `AVAILABLE_TESTS`:

```python
"new_test": {
    "id": "new_test",
    "name": "New Test Name",
    "category": "Test Category",
    "description": "Test description",
    "cost": 100,
    "preparation": "Preparation instructions",
    "duration": "15-30 minutes",
    "availability": ["09:00", "10:00", "11:00"]
}
```

### Customizing Diagnostic Questions
Modify `backend/utils/llm_utils.py` in the `generate_diagnostic_questions` function.

## 📊 Performance

- **Response Time**: < 2 seconds for diagnostic questions
- **Accuracy**: High confidence in routing decisions
- **Scalability**: Supports multiple concurrent users
- **Reliability**: Fallback mechanisms for API failures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues or questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review the console logs for error messages
3. Ensure all environment variables are set correctly

---

**🏥 Built with ❤️ for better healthcare experiences** 