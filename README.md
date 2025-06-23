# Education Center Management System

A comprehensive backend API for managing educational institutions with role-based access for administrators, teachers, students, and parents.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT
- **Documentation**: Swagger/OpenAPI

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Run the Application**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Project Structure

```
education_center_backend/
├── app/                    # Main application
│   ├── models.py          # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   └── utils/             # Utilities
├── uploads/               # File storage
├── tests/                 # Test files
└── scripts/               # Utility scripts
```

## API Endpoints

- `/auth/*` - Authentication
- `/admin/*` - Admin management
- `/teacher/*` - Teacher operations
- `/student/*` - Student operations
- `/parent/*` - Parent operations
- `/files/*` - File management

## License

MIT License
