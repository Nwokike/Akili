# Akili - AI-Powered Study Platform

## Project Overview
Akili is a Django-based AI-powered study platform designed for Nigerian students preparing for JAMB, WAEC/NECO, and JSS exams. The platform uses a freemium model with AI-generated lessons and quizzes.

**Tech Stack:**
- Backend: Django 5.2.8, Python 3.11
- Database: SQLite (development), PostgreSQL (production via Render)
- AI: Gemini Flash, Groq (4-tier fallback system)
- Payments: Paystack integration
- Frontend: Tailwind CSS (CDN for dev, needs PostCSS for production)

## Current Status (November 16, 2025)
✅ **Completed:**
- Full Django project setup with 8 apps (core, users, admin_syllabus, courses, profiles, quizzes, exams, payments)
- Database models and migrations created
- CSRF authentication fixed for Replit's iframe environment
- Subject selection restricted to available syllabuses only
- UI improvements (removed duplicate nav items, added Quizzes to bottom nav)
- All missing templates created (lesson_detail, exam templates, payment templates, quiz_history)
- Superuser created: nwokikeonyeka@gmail.com
- 4-tier AI fallback system: Gemini Flash → Groq → Gemini Paid → Circuit Breaker

🚧 **In Progress:**
- LSP errors need fixing (7 in users/views.py, template syntax issues)
- Need to test major features (signup, login, course creation, quizzes, exams)
- Need to add syllabus content via Django admin
- Production deployment configuration

## Project Architecture

### Apps Structure
```
akili_project/
├── core/                 # Shared utilities, AI fallback system
├── users/                # Custom user model, authentication
├── admin_syllabus/       # Syllabus management (admin only)
├── courses/              # Course creation and management
├── profiles/             # User profiles and settings
├── quizzes/              # Quiz generation and history
├── exams/                # Practice exam generation
└── payments/             # Paystack payment integration
```

### Key Features
1. **Freemium Model**: 10 free credits daily, paid packages available
2. **AI Content Generation**: 
   - Lessons: AI-generated, validated content
   - Quizzes: 5 credits, AI-generated questions
   - Exams: 10 credits, 20-question practice exams
3. **Subject Restriction**: Students can only select subjects with available syllabuses
4. **Referral System**: Users earn bonus credits for referrals
5. **Dark Mode**: Full dark mode support

## User Preferences
- Use modern, clean UI with Tailwind CSS
- Follow Django best practices
- Prioritize security and data integrity
- Mobile-first responsive design
- Keep code maintainable and well-documented

## ⚠️ REPLIT-SPECIFIC SETTINGS (REMOVE FOR PRODUCTION)

The following settings are configured specifically for Replit's development environment and **MUST BE CHANGED** before deploying to production:

### 1. CSRF Settings (`akili_project/settings.py`)

**Current (Replit-specific):**
```python
# CSRF Settings
CSRF_TRUSTED_ORIGINS_ENV = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [origin for origin in CSRF_TRUSTED_ORIGINS_ENV.split(',') if origin]

# Add Replit domains for development (use exact domain from REPLIT_DOMAINS)
REPLIT_DOMAINS = os.getenv('REPLIT_DOMAINS', '')
if REPLIT_DOMAINS:
    for domain in REPLIT_DOMAINS.split(','):
        domain = domain.strip()
        if domain:
            CSRF_TRUSTED_ORIGINS.append(f'https://{domain}')

# Cookie settings - configured for Replit's iframe environment
CSRF_COOKIE_SECURE = True  # Always True since Replit uses HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'  # Required for iframe/cross-site in Replit
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access if needed
SESSION_COOKIE_HTTPONLY = True

# X-Frame-Options - allow Replit to iframe the app
X_FRAME_OPTIONS = 'ALLOWALL' if DEBUG else 'DENY'
```

**Change to (Production):**
```python
# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',  # Add your production domain
    'https://www.yourdomain.com',
]

# Cookie settings - secure for production
CSRF_COOKIE_SECURE = True  # Require HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'  # Standard security for non-iframe
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_HTTPONLY = True

# X-Frame-Options - prevent clickjacking
X_FRAME_OPTIONS = 'DENY'
```

### 2. Tailwind CSS (Currently using CDN)

**Current (Development):**
```html
<!-- In templates/base.html -->
<script src="https://cdn.tailwindcss.com"></script>
```

**Change to (Production):**
1. Install Tailwind CSS via npm: `npm install -D tailwindcss`
2. Create `tailwind.config.js` and configure PostCSS
3. Build CSS file: `npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify`
4. Replace CDN with: `<link href="{% static 'css/output.css' %}" rel="stylesheet">`

### 3. ALLOWED_HOSTS

**Current:**
```python
ALLOWED_HOSTS = ['*']  # Accept all hosts
```

**Change to:**
```python
ALLOWED_HOSTS = [
    'yourdomain.com',
    'www.yourdomain.com',
    'your-app.onrender.com',  # Render domain
]
```

### 4. Debug Mode

**Current:**
```python
DEBUG = os.getenv('DEBUG', 'True') == 'True'
```

**Change to:**
```python
DEBUG = False  # Always False in production
```

### 5. Secret Key
Ensure `SECRET_KEY` is set via environment variable in production, never hardcoded.

## Database Configuration

### Development (Replit) - SQLite
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Production (Render) - PostgreSQL
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

## Environment Variables Required

### Development (Replit Secrets)
- `GEMINI_API_KEY` ✅ (configured)
- `GROQ_API_KEY` ✅ (configured)
- `SECRET_KEY` (Django secret)
- `DATABASE_URL` (auto-set by Replit for PostgreSQL, empty for SQLite)

### Production (Render Environment Variables)
- `SECRET_KEY` (generate new one for production)
- `DATABASE_URL` (auto-set by Render PostgreSQL)
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `PAYSTACK_SECRET_KEY`
- `DEBUG=False`
- `CSRF_TRUSTED_ORIGINS` (your production domain)

## Deployment Checklist

### Before Deploying to Render:
- [ ] Remove all Replit-specific CSRF settings
- [ ] Set `DEBUG = False`
- [ ] Update `ALLOWED_HOSTS` with production domains
- [ ] Change `CSRF_COOKIE_SAMESITE` to `'Lax'`
- [ ] Change `X_FRAME_OPTIONS` to `'DENY'`
- [ ] Install Tailwind CSS via PostCSS (remove CDN)
- [ ] Set all environment variables in Render
- [ ] Run migrations on production database
- [ ] Create superuser on production
- [ ] Configure static files with WhiteNoise
- [ ] Test payment integration with Paystack
- [ ] Add SSL certificate (Render provides free SSL)

## Recent Changes
- **Nov 16, 2025**: Fixed CSRF issues for Replit iframe, created all missing templates, made nwokikeonyeka@gmail.com a superuser

## Next Steps
1. Add syllabus content via `/admin/` (JAMB, WAEC/NECO, JSS subjects)
2. Fix remaining LSP errors
3. Test complete user flow: signup → create course → view lessons → take quiz → take exam
4. Test payment flow with Paystack test keys
5. Deploy to Render for production testing
6. Remove all Replit-specific settings before production launch

## Notes
- Users can only select subjects that have syllabuses in the database
- Each user gets 10 free credits daily
- Lesson content is cached and validated by AI
- Lessons reported 3+ times are automatically regenerated
- Quiz costs 5 credits, Exam costs 10 credits
