# Akili Project

## Overview
Akili is a Django-based AI Tutor web application designed to help students master JAMB, WAEC, NECO, and JSS exams with AI-powered personalized learning. It offers a freemium model with daily free credits.

## Technology Stack
- **Framework**: Django 5.2.8
- **Language**: Python 3.12
- **Database**: PostgreSQL (via Replit's built-in database)
- **Static Files**: WhiteNoise for serving static assets
- **Production Server**: Gunicorn

## Project Structure
```
akili_project/          # Django project settings
  settings.py           # Main settings file
  urls.py               # Root URL configuration
  wsgi.py               # WSGI entry point

core/                   # Core utilities and middleware
courses/                # Course management app
exams/                  # Exam management app
payments/               # Payment processing app (Paystack)
profiles/               # User profile management
quizzes/                # Quiz system app
users/                  # Custom user model and authentication
admin_syllabus/         # Admin syllabus management

static/                 # Static files (CSS, JS, images)
templates/              # HTML templates
```

## Environment Variables
### Required in Production
- `SECRET_KEY`: Django secret key (required in production)
- `DATABASE_URL`: PostgreSQL connection string (auto-configured by Replit)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF

### Optional
- `DEBUG`: Set to "True" for development mode (defaults to False)
- `GEMINI_API_KEY`: Google Gemini API key for AI features
- `GROQ_API_KEY`: Groq API key for AI features
- `PAYSTACK_SECRET_KEY`: Paystack secret key for payment processing

## Running Locally
The app runs on port 5000 with the Django development server:
```bash
python manage.py runserver 0.0.0.0:5000
```

## Database
- Uses PostgreSQL via the DATABASE_URL environment variable
- Run migrations: `python manage.py migrate`

## Static Files
- Development: Served by Django/WhiteNoise
- Production: Collected with `python manage.py collectstatic`

## Key Features
- AI-powered personalized learning
- Daily free credits system (10 credits/day)
- Referral system for bonus credits
- Quiz and exam practice
- Course management

## Deployment
Uses Gunicorn for production:
```bash
gunicorn --bind 0.0.0.0:5000 akili_project.wsgi:application
```
