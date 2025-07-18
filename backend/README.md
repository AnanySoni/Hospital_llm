# 🏥 Hospital Appointment System - Backend

## 🏗️ **Organized Project Structure**

```
backend/
├── 📁 core/                    # Core application components
│   ├── __init__.py
│   ├── database.py            # Database configuration
│   └── models.py              # SQLAlchemy models
│
├── 📁 services/               # Business logic layer
│   ├── __init__.py
│   └── appointment_service.py # Appointment operations
│
├── 📁 middleware/             # FastAPI middleware
│   ├── __init__.py
│   └── error_handler.py       # Error handling & exceptions
│
├── 📁 schemas/                # Request/Response models
│   ├── __init__.py
│   └── request_models.py      # Pydantic validation models
│
├── 📁 utils/                  # Utility functions
│   ├── __init__.py
│   └── llm_utils.py          # LLM integration utilities
│
├── 📁 integrations/           # External service integrations
│   ├── __init__.py
│   └── google_calendar.py     # Google Calendar integration
│
├── 📁 scripts/                # Database & utility scripts
│   ├── __init__.py
│   ├── init_db.py            # Database initialization
│   └── optimize_database.py  # Database optimization
│
├── 📄 main.py                 # Main FastAPI application
├── 📄 requirements.txt        # Python dependencies
├── 📄 OPTIMIZATION_SUMMARY.md # Optimization details
└── 📄 README.md              # This file
```

## 🚀 **Quick Start**

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Initialize Database**
```bash
python scripts/init_db.py
```

### 3. **Apply Optimizations**
```bash
python scripts/optimize_database.py
```

### 4. **Run the Application**
```bash
python main.py
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 **API Endpoints**

### Core Endpoints
- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /recommend-doctors` - Get AI-powered doctor recommendations
- `POST /book-appointment` - Book new appointment
- `PUT /reschedule-appointment` - Reschedule existing appointment
- `DELETE /cancel-appointment/{id}` - Cancel appointment
- `GET /doctors` - Get all doctors
- `GET /appointments/patient/{name}` - Get patient appointments

### Authentication Endpoints
- `GET /auth/google` - Google OAuth login
- `GET /auth/callback` - OAuth callback
- `POST /auth/connect-calendar` - Connect doctor's calendar

## 🏗️ **Architecture Benefits**

### ✅ **Organized Structure**
- **Separation of Concerns**: Each module has a specific responsibility
- **Easy Navigation**: Logical directory structure
- **Scalable**: Easy to add new features and services

### ✅ **Service Layer Pattern**
- **Business Logic**: Centralized in service classes
- **Validation**: Comprehensive input validation
- **Error Handling**: Consistent error responses

### ✅ **Middleware Integration**
- **Error Handling**: Automatic error formatting
- **Logging**: Comprehensive request/response logging
- **CORS**: Proper cross-origin support

### ✅ **Database Optimizations**
- **Indexes**: Optimized query performance
- **Constraints**: Data integrity enforcement
- **Audit Trail**: Created/updated timestamps

## 🔧 **Development Guidelines**

### **Adding New Features**

1. **New Service**: Add to `services/` directory
2. **New Models**: Add to `schemas/request_models.py`
3. **New Endpoints**: Add to `main.py` with proper service calls
4. **New Integrations**: Add to `integrations/` directory

### **Database Changes**

1. **Models**: Update `core/models.py`
2. **Migrations**: Use Alembic for schema changes
3. **Optimizations**: Add to `scripts/optimize_database.py`

### **Error Handling**

All errors are automatically handled by the middleware:
- **Validation Errors**: 422 with detailed field errors
- **Business Logic Errors**: 400 with descriptive messages
- **Not Found Errors**: 404 with resource information
- **Server Errors**: 500 with sanitized error messages

## 📊 **Performance Features**

### **Database Optimizations**
- ✅ **Indexes** on frequently queried columns
- ✅ **Connection Pooling** for better concurrency
- ✅ **Query Optimization** with proper relationships

### **API Optimizations**
- ✅ **Async/Await** for non-blocking operations
- ✅ **Pydantic Validation** for fast request parsing
- ✅ **Structured Logging** for monitoring

### **Code Quality**
- ✅ **Type Hints** throughout the codebase
- ✅ **Docstrings** for all functions and classes
- ✅ **Error Handling** with proper exception hierarchy

## 🔒 **Security Features**

- **Input Validation**: Comprehensive Pydantic models
- **SQL Injection Prevention**: SQLAlchemy ORM
- **Error Information Leakage**: Sanitized error responses
- **CORS Configuration**: Configurable origins

## 🧪 **Testing**

### **Run Tests** (when implemented)
```bash
pytest tests/
```

### **API Testing**
- Use the interactive docs at `/docs`
- Test with Postman or similar tools
- All endpoints include proper response models

## 📈 **Monitoring & Logging**

### **Logs Include**
- Request/Response details
- Error stack traces
- Performance metrics
- Business logic events

### **Health Checks**
- Database connectivity
- External service status
- Application health metrics

## 🚀 **Production Deployment**

### **Environment Variables**
Create a `.env` file with:
```env
DATABASE_URL=postgresql://user:password@localhost/hospital_appointments
GROQ_API_KEY=your_groq_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### **Production Settings**
- Set `reload=False` in `main.py`
- Configure specific CORS origins
- Use proper logging configuration
- Set up database connection pooling

---

**🎉 The backend is now professionally organized with enterprise-level architecture!** 