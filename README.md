# Akili - AI-Powered Nigerian Exam Prep Platform

Nigeria's first personal AI-powered study platform for JAMB, WAEC, NECO, and JSS exams.

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser** (Optional)
   ```bash
   python manage.py createsuperuser
   ```

4. **Start Development Server**
   ```bash
   python manage.py runserver 0.0.0.0:5000
   ```

Visit: `http://localhost:5000/`

## Environment Variables

Required for production:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Set to `False` in production
- `GEMINI_API_KEY` - For AI content generation
- `GROQ_API_KEY` - For AI fallback

Optional (PostgreSQL):
- `PGDATABASE` - Database name
- `PGUSER` - Database user
- `PGPASSWORD` - Database password
- `PGHOST` - Database host
- `PGPORT` - Database port (default: 5432)

*Note: Uses SQLite by default if PostgreSQL is not configured*

## Project Structure

### Team Lead (Complete ✅)
- **core** - Base templates, PWA, AI utilities
- **users** - Authentication, freemium credits, referrals
- **admin_syllabus** - JAMB/SSCE/JSS syllabus storage

### Developer 1 (To Implement)
- **courses** - Dashboard, course management, lessons
- **profiles** - Profile page, referrals, account deletion

### Developer 2 (To Implement)
- **quizzes** - Dynamic quiz generation
- **exams** - Mock exam center
- **payments** - Paystack integration

## Key Features

- **AI Smart Fallback**: 4-tier system (Gemini Flash → Groq → Gemini Paid → Circuit Breaker)
- **Freemium Credits**: 10 daily credits, +2 per referral (max 30)
- **PWA Ready**: Offline-capable Progressive Web App
- **Mobile-First**: Responsive design with bottom navigation
- **LaTeX Support**: KaTeX rendering for math/science formulas

## Tech Stack

- **Backend**: Django 5.2.8, PostgreSQL/SQLite
- **Frontend**: Tailwind CSS, Vanilla JavaScript
- **AI**: Google Gemini, Groq API
- **Payment**: Paystack (to be implemented)

## Developer Notes

- Username is auto-generated from email (part before @)
- All user displays show full_name, not username
- Templates extend `base.html` for consistent UI
- KaTeX is pre-loaded for LaTeX formula rendering
- Use `call_ai_with_fallback()` from `core.utils.ai_fallback`

## Deployment

Configured for Replit deployment. See `render.yaml` for production settings.

## License

Copyright © 2025 Akili. All rights reserved.
