# Hospital LLM Project - Master Test Suite

## Overview
The `master_test_suite.py` is the **single comprehensive test file** for the entire Hospital LLM project. It contains all tests for every feature, ensuring complete system validation in one place.

## 🚀 Quick Start

### Run All Tests
```bash
cd tests
python master_test_suite.py
```

### Run Specific Section
```bash
python master_test_suite.py --section infrastructure
python master_test_suite.py --section core_features
python master_test_suite.py --section validation
```

### Enable Verbose Logging
```bash
python master_test_suite.py --verbose
```

## 📋 Test Sections

### 1. Infrastructure Tests
- **Backend Health Check**: Verifies server is running
- **Database Connectivity**: Tests database connection
- **API Documentation**: Validates OpenAPI docs endpoint

### 2. Core Features Tests
- **Doctor Recommendations**: Symptom-based doctor matching
- **Smart Doctor Recommendations**: Enhanced recommendation logic
- **Departments**: Department listing functionality
- **Doctor Available Slots**: Availability checking
- **Appointment Booking**: Full booking workflow
- **Appointment Rescheduling**: Rescheduling functionality
- **Appointment Cancellation**: Cancellation process
- **Appointment Retrieval**: Fetching appointments
- **Chat Basic**: Basic chat functionality
- **Chat Enhanced**: Advanced chat features

### 3. Diagnostic System Tests
- **Basic Diagnostic Session**: Simple diagnostic flow
- **Enhanced Diagnostic Session**: Advanced diagnostic capabilities
- **Diagnostic Answer Processing**: Answer handling logic
- **Session History**: Session management and retrieval

### 4. Confidence Scoring Tests (Phase 1 Month 1)
- **Confidence Utils**: Core confidence calculation utilities
- **Diagnostic with Confidence**: Confidence-aware diagnostics
- **Doctor Recommendations with Confidence**: Confidence-based recommendations
- **Confidence Fallback**: Low confidence handling
- **Confidence Edge Cases**: Edge case validation

### 5. Adaptive Diagnostic Tests (Phase 1 Month 2)
- **Adaptive Diagnostic Imports**: Module import validation
- **Adaptive Diagnostic Database**: Database schema testing
- **V2 Endpoints**: New adaptive API endpoints
- **Adaptive Diagnostic Session**: Full adaptive flow
- **Question Generator**: LLM-powered question generation

### 6. Test Booking Tests
- **Available Tests**: Medical test catalog
- **Test Recommendations**: Test suggestion logic
- **Book Tests**: Test appointment booking
- **Patient Tests**: Patient test history
- **Test Categories**: Test categorization
- **Cancel Test**: Test cancellation

### 7. Calendar Integration Tests
- **Calendar Setup Page**: Google Calendar setup
- **Google Calendar Resilience**: Error handling
- **Doctor Availability**: Calendar-based availability

### 8. Phone Recognition Tests (Phase 2)
- **New Patient Phone Recognition**: First-time patient detection
- **Existing Patient Phone Recognition**: Returning patient identification
- **Phone Number Normalization**: Phone format standardization
- **Smart Welcome Messages**: Personalized greetings
- **Family Member Support**: Family member appointment booking

### 9. Session Management Tests
- **Session Creation**: Session initialization
- **Session Statistics**: Session analytics
- **Session History**: Historical session data

### 10. Validation Tests
- **Invalid Phone Validation**: Phone number format checking
- **Appointment Validation**: Appointment data validation
- **Double Booking Prevention**: ⭐ **NEW** - Prevents conflicting appointments
- **Reschedule Conflict Prevention**: ⭐ **NEW** - Prevents reschedule conflicts
- **Database Cleanup**: ⭐ **NEW** - Cleanup functionality testing

### 11. Advanced LLM Prompts Tests
- **Advanced Prompt Builder**: Enhanced prompt construction
- **Enhanced Consequence Messaging**: Risk communication
- **Medical Knowledge Integration**: Medical data integration
- **Psychological Sophistication**: Advanced persuasion techniques
- **Safety and Ethics Integration**: Safety compliance

### 12. Integration Tests
- **End-to-End Booking Flow**: Complete user journey
- **Smart Welcome Integration**: Welcome flow integration

### 13. Triage System Tests (Phase 1 Month 3)
- **Triage Service Imports**: Service module validation
- **Emergency Red Flag Detection**: Critical symptom detection
- **Urgency Assessment Basic**: Basic urgency calculation
- **Risk Factor Calculation**: Risk scoring algorithms
- **Age-based Risk Assessment**: Age-specific risk factors
- **Chronic Condition Risk**: Chronic condition handling
- **V2 Triage Endpoints**: New triage API endpoints
- **Smart Doctor Routing**: Triage-based routing
- **Emergency Escalation**: Emergency protocol testing
- **Adaptive Diagnostic with Triage**: Integrated diagnostic flow
- **Confidence-Triage Integration**: Combined confidence and triage
- **Triage Integration Flow**: End-to-end triage workflow
- **Complete Phase 1 Month 3 Integration**: Full system integration

## 🎯 Key Features Tested

### ✅ Core Functionality
- Complete appointment booking lifecycle
- Doctor recommendation engine
- Medical test booking system
- Chat-based interaction system

### ✅ Advanced Features
- Confidence scoring for all predictions
- Adaptive diagnostic questioning
- Phone number recognition and patient identification
- Google Calendar integration
- Cross-session patient tracking

### ✅ Safety & Validation
- **Double-booking prevention** 🔒
- **Reschedule conflict detection** 🔒
- Input validation and sanitization
- Emergency red flag detection
- Medical triage and urgency assessment

### ✅ AI/LLM Features
- Multi-LLM orchestration
- Confidence-aware decision making
- Adaptive question generation
- Context-aware conversations
- Psychological persuasion techniques

### ✅ Integration & Infrastructure
- Database connectivity and operations
- API endpoint validation
- Error handling and resilience
- Session management
- Calendar synchronization

## 📊 Test Results

The master test suite provides:
- **Total test count** across all sections
- **Pass/Fail/Skip statistics** for each section
- **Success rate percentage** for overall system health
- **Detailed logging** with timestamps
- **Section-by-section breakdown** for targeted debugging

## 🔧 Test Configuration

### Environment Requirements
- Backend server running on `http://localhost:8000`
- Database connectivity
- Google Calendar credentials (for calendar tests)
- Internet connectivity (for LLM API calls)

### Test Data
- Uses future dates to avoid conflicts
- Creates and cleans up test appointments automatically
- Uses distinct patient names for different test scenarios
- Implements proper cleanup to avoid database pollution

## 🏥 Medical Safety

The test suite ensures:
- **No double-booking** of appointments
- **Proper emergency detection** for critical symptoms
- **Appropriate urgency assessment** based on medical factors
- **Safe handling** of patient data
- **Proper validation** of all medical inputs

## 📝 Adding New Tests

To add new tests to the master suite:

1. **Create test function** following naming convention: `test_your_feature()`
2. **Add to appropriate section** in the `run_*_tests()` functions
3. **Use proper error handling** and logging via `runner.log()`
4. **Return boolean** indicating success/failure
5. **Clean up test data** to avoid side effects

Example:
```python
def test_new_feature():
    """Test description"""
    try:
        # Test logic here
        runner.log("Test passed")
        return True
    except Exception as e:
        runner.log(f"Test failed: {e}", "ERROR")
        return False
```

## 🎉 System Validation

This comprehensive test suite validates that the Hospital LLM Project is:
- **Functionally complete** across all major features
- **Medically safe** with proper validation and conflict prevention
- **Performance optimized** with efficient API calls and database operations
- **User-friendly** with proper error handling and messaging
- **Production ready** with comprehensive testing coverage

The master test suite is the **single source of truth** for system validation and should be run before any production deployment or major feature releases. 