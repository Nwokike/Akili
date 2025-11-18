# Akili - AI-Powered Educational Platform

## Overview

Akili is an AI-powered educational platform designed to help Nigerian students prepare for JAMB, SSCE (WAEC/NECO), and JSS examinations. The platform uses Google Gemini AI and Groq API to dynamically generate personalized course content, interactive lessons, practice quizzes, and mock exams based on official syllabuses. The application operates on a freemium credit-based model where users receive 10 free daily credits that reset every 24 hours, with the ability to purchase additional credits or increase their daily limit through referrals.

**Key Features:**
- AI-generated personalized 15-module courses tailored to exam type and subject
- Interactive lessons with LaTeX-rendered mathematical formulas (using KaTeX)
- Unlimited free practice quizzes with instant feedback
- Full-length mock exams (20 questions, 5 credits)
- Progress tracking and analytics
- Referral system (+2 daily credit limit per referral, max 30)
- Dark mode support with system preference detection
- Progressive Web App (PWA) capabilities for mobile installation


## System Architecture

### Backend Architecture

**Framework:** Django 5.2.8 with PostgreSQL database

**Authentication System:**
- Custom user model (`CustomUser`) extending Django's `AbstractUser`
- Email-based authentication (username auto-generated from email)
- Password reset functionality via Django's built-in views
- Custom user manager (`CustomUserManager`) handling user and superuser creation

**Credit System Design:**
- Daily credit allocation (10 free credits, resets at midnight WAT)
- Referral-based daily limit increases (max 30 credits/day)
- Purchased credits never expire
- Credit costs: Course creation (5), Mock exam (5), AI tutor (1), Quizzes (FREE)
- Non-transferable, non-refundable credits

**Django Apps Structure:**
1. **core** - Main views (home, dashboard, exam center), custom middleware, context processors
2. **users** - Authentication, user management, referral system
3. **courses** - Course and module management, AI content generation
4. **quizzes** - Practice quiz generation and tracking
5. **exams** - Mock exam generation and results
6. **payments** - Paystack integration for credit purchases
7. **profiles** - User profile management and account deletion
8. **admin_syllabus** - Official syllabus storage (JAMB, SSCE, JSS)

**Data Models:**
- Courses linked to users with unique constraint on (user, exam_type, subject)
- Modules ordered within courses, containing lesson content
- QuizAttempts track user progress with JSON-stored questions and answers
- Exams are course-wide (not module-specific) with 20 questions
- Syllabuses stored as markdown with LaTeX support

**AI Content Generation:**
- 4-tier fallback system: Gemini 2.5 Flash (free) → Gemini Paid → Groq API → Circuit breaker
- Structured JSON responses with robust error handling
- **Subject-aware prompting**: LaTeX instructions only for STEM subjects to avoid model confusion
- Content generated on-demand (no pre-cached content except syllabus)
- **Guaranteed credit refunds**: All AI failures trigger automatic refunds and cleanup
- Single-backslash LaTeX output (JSON escaping handled automatically)

### Frontend Architecture

**UI Framework:** Tailwind CSS (CDN-based) with custom utility classes

**Design System:**
- Custom color palette with primary (blue), accent (yellow), and semantic colors
- Dark mode implementation using CSS class-based toggle with localStorage persistence
- Responsive design with mobile-first approach
- Card-based component system with hover effects
- Gradient text effects for branding

**JavaScript Features:**
- Dark mode toggle with system preference detection
- Toast notification system for user feedback
- Credit modal for purchases
- Referral link copying with clipboard API
- Loading spinner overlay for async operations
- Form validation and AJAX subject loading
- **Exam timer**: Client-side persistence with localStorage, automatic cleanup on submit
- **Sticky exam timer**: IntersectionObserver-based floating timer during scroll
- **Duplicate submission prevention**: Guard flags prevent multiple form POSTs

**Progressive Web App:**
- Manifest file for installation
- Service worker for offline caching
- Mobile-optimized bottom navigation
- Safe area support for notched devices

### Database Schema

**PostgreSQL with Django ORM:**
- Custom user table with credit fields (tutor_credits, daily_credit_limit, last_daily_reset)
- Referral tracking (referred_by username field)
- Courses with unique constraint preventing duplicate user enrollments
- Modules with ordering and foreign key to courses
- Quiz attempts with JSON fields for questions and user answers
- Exam questions stored as JSON with correct answers
- Payment records with Paystack reference tracking
- Syllabus tables for each exam type (JAMB, SSCE, JSS)

**Performance Optimizations:**
- Database indexes on all high-volume query fields:
  - Users: email, tutor_credits, last_daily_reset
  - Courses: user+created_at, module ordering
  - Quizzes: user+module+completion, user+passed status
  - Exams: user+course+completion, exam questions
- select_related() and prefetch_related() for reducing N+1 queries
- Unique constraints preventing duplicate data

### Security Implementation

**Production-Ready Security:**
- CSRF protection on all forms with proper token validation
- Password hashing using Django's bcrypt implementation
- HTTPS enforcement in production (via Whitenoise)
- Environment-aware SECRET_KEY with secure fallback warnings
- Proper ALLOWED_HOSTS for Replit, development, and production
- Secure SESSION/CSRF cookies (HttpOnly, SameSite, Secure in production)
- HSTS, SSL redirect, and XSS protection headers
- Environment variable-based configuration (SECRET_KEY, API keys)
- User input sanitization for AI prompts
- **Note**: Rate limiting ready but disabled (requires Redis for multi-instance production)

## External Dependencies

### AI Services

**Google Gemini AI:**
- Primary AI provider for content generation
- Models: Gemini 2.5 Flash (free tier), Gemini Pro (paid tier)
- Used for: Course module generation, lesson content, quiz questions, mock exams, AI tutor

**Groq API:**
- Backup AI provider in fallback chain
- Free tier alternative when Gemini is unavailable

### Payment Processing

**Paystack:**
- Nigerian payment gateway for credit purchases
- Handles: Payment initialization, transaction verification, webhook callbacks
- Integration via REST API with requests library
- Secret key stored in environment variables

### Third-Party Services

**KaTeX:**
- Client-side mathematical formula rendering
- Renders LaTeX expressions in lesson content
- Used for STEM subjects (Mathematics, Physics, Chemistry, etc.)

### Python Dependencies

**Core Framework:**
- Django 5.2.8 - Web framework
- psycopg2-binary 2.9.11 - PostgreSQL adapter
- gunicorn 21.2.0 - WSGI HTTP server for production

**Utilities:**
- python-dotenv 1.2.1 - Environment variable management
- requests 2.31.0 - HTTP library for API calls
- markdown 3.7 - Markdown rendering
- whitenoise 6.6.0 - Static file serving
- dj-database-url 2.1.0 - Database URL parsing

### Deployment Environment

**Platform:** Autoscale deployment (Replit/Render compatible)
- **Build command**: `pip install -r requirements.txt`
- **Run command**: `gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=4 akili_project.wsgi:application`
- Static files served via Whitenoise
- PostgreSQL database hosting
- Environment variable configuration
- Automatic HTTPS with custom domain support

**Development:**
- Replit support with domain detection
- DEBUG mode controlled via environment variable
- ALLOWED_HOSTS dynamically configured from REPLIT_DOMAINS or ALLOWED_HOSTS env var
- Django development server on port 5000

**Logging:**
- Comprehensive logging to console and file (logs/akili.log)
- Error tracking middleware with user context
- Environment-aware configuration (console-only in DEBUG)
