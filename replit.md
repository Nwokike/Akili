# Akili - AI-Powered Nigerian Exam Prep Platform

## Project Overview
Akili is Nigeria's first personal AI-powered study platform designed to make one-on-one tutoring accessible through dynamic, responsive learning. The platform generates all content on demand via AI to avoid copyright and cost issues.

## Current State
- **Platform**: Django 5.2.8 web application
- **Database**: PostgreSQL (Replit managed)
- **Environment**: Configured for Replit deployment
- **Status**: Imported from GitHub, setup in progress

## Project Architecture

### Django Apps Structure

**Team Lead (Complete):**
- `akili_core`: Base template, PWA, AI utilities, context processors
- `akili_users`: CustomUser model, authentication, referral system
- `akili_admin_syllabus`: JAMB/SSCE/JSS syllabus storage

**Developer 1 (To Implement):**
- `akili_courses`: Dashboard, course personalization, lessons, 2-pass validation
- `akili_profiles`: Profile page, referral display, account deletion

**Developer 2 (To Implement):**
- `akili_quizzes`: Dynamic quiz generation with credit logic
- `akili_exams`: Mock exam center with syllabus-grounded generation
- `akili_payments`: Paystack integration for credit purchases

### Database Models

**CustomUser** (akili_users):
- username, email (both unique)
- tutor_credits, daily_credit_limit, last_daily_reset
- referred_by (username of referrer)

**Syllabus Models** (akili_admin_syllabus):
- JAMBSyllabus, SSCESyllabus, JSSSyllabus
- Fields: subject, syllabus_content (Markdown with LaTeX), version

**Course Models** (akili_courses):
- Course: user, exam_type, subject
- Module: course, title, order, syllabus_topic
- CachedLesson: topic, content, syllabus_version, is_validated, report_count

## AI Smart Fallback System

4-tier architecture to manage AI costs and uptime:

1. **Tier 1**: Gemini 2.5 Flash (Free) - Primary
2. **Tier 2**: Groq API (Free) - Fallback
3. **Tier 3**: Gemini Paid - Secondary fallback
4. **Tier 4**: Circuit Breaker - "AI tutors at full capacity" message

**Location**: `akili_core/utils/ai_fallback.py`

All AI prompts automatically include LaTeX formatting instructions for math/science content.

## Freemium Credit System

### Credit Costs
- Ask Follow-up Question: 1 credit
- Generate Mock Exam: 5 credits
- Take Quiz (First Time): Free
- Retake Quiz: 1 credit

### Credit Logic
- **Free Tier**: 10 credits on signup
- **Daily Reset**: Automatic on first daily access (no cron jobs)
- **Referrals**: +2 daily limit per referral (max 30)
- **Purchased Credits**: Don't reset, persist across days

**Implementation**: `CustomUser.reset_daily_credits()` and `deduct_credits()`

## Referral System

**URL Pattern**: `akili.ng/join/{username}`

**Flow**:
1. User shares referral URL with their username
2. New user signs up via /join/username
3. Referrer's daily_credit_limit increases by 2 (max 30)

**Implementation**:
- View: `akili_users/views.py:referral_signup_view()`
- Model method: `CustomUser.increase_daily_limit()`

## PWA Configuration

**Files**:
- `static/pwa/manifest.json`: App metadata
- `static/pwa/serviceworker.js`: Offline caching
- `static/js/main.js`: Install prompt handler

**Features**:
- Mobile-first bottom navigation
- Desktop sidebar navigation
- Install button (auto-shows on eligible devices)
- Offline-ready static assets

## Replit Configuration

### Development Server
- Port: 5000
- Host: 0.0.0.0
- Command: `python manage.py runserver 0.0.0.0:5000`

### Database
- Replit-managed PostgreSQL
- Environment variables automatically configured
- Migrations: `python manage.py migrate`

### Required API Keys (Optional)
- `GEMINI_API_KEY`: For AI content generation
- `GROQ_API_KEY`: For AI fallback tier

## User Preferences

### Code Style
- Standard Django conventions
- Clear separation of concerns (apps by feature)
- Docstrings for all major functions
- LaTeX rendering via KaTeX (already in base.html)

### Workflow
- PostgreSQL for dev consistency (no SQLite)
- Migrations managed via Django ORM
- No manual SQL except for debugging

## Recent Changes
- 2025-11-10: Imported from GitHub to Replit
- 2025-11-10: Configured for Replit environment (port 5000, database settings)
- 2025-11-10: Added CSRF trusted origins for Replit domains

## Next Steps for Developers

### Developer 1 (Courses & Profiles):
1. Implement course dashboard with "Add Course" functionality
2. Build AI course personalizer (15 modules from syllabus)
3. Create lesson viewer with 2-pass validation
4. Add "Ask Your Tutor" feature (1 credit)
5. Build profile page with referral URL copy function

### Developer 2 (Quizzes, Exams, Payments):
1. Implement dynamic quiz generation with LaTeX rendering
2. Add quiz retake logic (1 credit cost)
3. Build mock exam center (5 credits, syllabus-grounded)
4. Integrate Paystack for credit purchases
5. Create transaction logging system

## Important Notes

- **KaTeX** is already loaded in base.html - just use `$formula$` or `$$formula$$` syntax
- **AI utility** is ready to use: `from akili_core.utils.ai_fallback import call_ai_with_fallback`
- **Credit checks** are automatic via context processor
- **Templates** must extend `base.html` for consistent UI
- **LaTeX** in syllabus content will auto-render on frontend
