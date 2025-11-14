# Akili - AI-Powered Nigerian Exam Prep Platform

## Project Overview
Nigeria's first personal AI-powered study platform for JAMB, WAEC, NECO, and JSS exams with a freemium business model.

## Recent Changes (Nov 14, 2025)

### Critical Fixes Applied
- **Fixed CSRF Cookie Issues**: Configured for production with proper cookie settings
- **Fixed Admin Interface**: Resolved FieldError for non-editable username field in CustomUser admin
- **Fixed Import Errors**: Restored CachedLesson import in courses/views.py
- **Fixed URL Namespaces**: Added all missing app URLs (profiles, quizzes, exams, payments)
- **Added Missing Views**: Implemented ModuleListingView, LessonDetailView, AskTutorView, ReportErrorView, DeleteCourseView
- **Implemented Two-Pass AI Validation**: Lessons are generated and validated before display
- **Completed Module Generation**: AI-powered course module creation with syllabus integration
- **Removed Replit-Specific Code**: Simplified settings for production deployment
- **Updated Logo Design**: Centered logo in header, increased size across all pages (h-20 in header, w-32 h-32 in auth pages)

### Environment Configuration
- Django development server running on 0.0.0.0:5000
- PostgreSQL database (Replit Helium): heliumdb
- CSRF and session cookies configured for iframe
- Static files served correctly
- PWA service worker active

## Project Structure

### Team Lead (Complete ✓)
- **core**: Base templates, PWA, AI utilities with 4-tier fallback system
- **users**: Email authentication, freemium credit system, referrals
- **admin_syllabus**: JAMB/SSCE/JSS syllabus storage

### Developer 1 (Complete ✓)
- **courses**: Dashboard, course creation, module listing, lesson generation with two-pass validation
- **profiles**: Profile page, referral system, account deletion
- **quizzes**: Dynamic quiz generation (partially complete - credit logic implemented)

### Developer 2 (Remaining Work)
- **exams**: Mock exam center (5-credit logic needed)
- **payments**: Paystack integration for credit purchases

## Tech Stack
- **Backend**: Django 5.2.8, PostgreSQL, Gunicorn
- **Frontend**: Tailwind CSS (CDN), Vanilla JavaScript, KaTeX for LaTeX
- **AI**: Google Gemini 2.5 Flash, Groq API (4-tier fallback)
- **Deployment**: Replit (dev), Render (production)

## Key Features Implemented

### Freemium Credit System
- **Daily Credits**: 10 free credits, reset at midnight (Africa/Lagos timezone)
- **Credit Costs**:
  - Create course: 5 credits
  - Ask tutor question: 1 credit
  - Retake quiz: 1 credit (first attempt free)
  - Generate mock exam: 5 credits (Developer 2 task)
- **Referral Bonuses**: +2 credits per referral (max 30 daily limit)
- **Credit Methods**:
  - `user.deduct_credits(amount)`: Returns True if successful
  - `user.reset_daily_credits()`: Auto-called in context processor
  - `user.add_credits(amount)`: For purchased credits
  - `user.increase_daily_limit(amount)`: For referrals

### AI Smart Fallback System
**4-Tier Architecture:**
1. **Tier 1**: Gemini 2.5 Flash (Free) - Primary
2. **Tier 2**: Groq API (Free) - Backup
3. **Tier 3**: Gemini Paid - Premium fallback
4. **Tier 4**: Circuit Breaker - Graceful error message

**Two-Pass Validation:**
- Pass 1: AI generates lesson content
- Pass 2: Second AI validates for accuracy
- If validation fails: Content marked as "under review"
- If reported >3 times: Content regenerated

### Course Creation Flow
1. User selects exam type (JAMB/SSCE/JSS) and subject
2. System deducts 5 credits
3. AI generates exactly 15 modules from syllabus data
4. Modules created and linked to course
5. Lessons generated on-demand when user views module

## Database Schema

### Key Models
- **CustomUser**: Email login, credit tracking, referrals
- **Course**: User's personalized courses (unique per exam+subject)
- **Module**: 15 modules per course with syllabus topics
- **CachedLesson**: AI-generated lessons with validation tracking
- **QuizAttempt**: Quiz history with scoring
- **JAMBSyllabus, SSCESyllabus, JSSSyllabus**: Official exam syllabuses

## Development Setup

### Environment Variables (Already Configured)
```
PGDATABASE=heliumdb
PGUSER=postgres
PGPASSWORD=password
PGHOST=helium
PGPORT=5432
REPLIT_DOMAINS=<auto-set>
```

### Required API Keys (User Must Provide)
- `GEMINI_API_KEY`: For AI lesson generation
- `GROQ_API_KEY`: For AI fallback tier

### Running Locally
Server is already running on port 5000. To restart:
```bash
python manage.py runserver 0.0.0.0:5000
```

### Creating Superuser
```bash
python manage.py createsuperuser
```
Enter email, first name, last name, and password. Username auto-generates.

## Important Notes

### For Developer 2
1. **Exams App**: Mock exam generation needs:
   - 5-credit deduction before generation
   - Syllabus-grounded prompts (prepend full syllabus)
   - LaTeX formula rendering
   - JAMB-style question format

2. **Payments App**: Paystack integration needs:
   - Buy 20 credits (₦500), 50 credits (₦1,000)
   - Use `user.add_credits(amount)` for purchased credits
   - Purchased credits don't reset daily

### Current Limitations
- **Tailwind CSS**: Using CDN (production should use PostCSS)
- **No Vector DB**: Using simple syllabus lookup (future: RAG with embeddings)
- **No Social Login**: Email-only (future: Google OAuth via django-allauth)
- **No CAPTCHA**: Vulnerable to spam (future: django-recaptcha)

## URLs Configuration

### Main Routes
- `/` - Homepage
- `/login/`, `/signup/` - Authentication
- `/dashboard/` - Course dashboard (courses app)
- `/courses/` - Course management
- `/courses/<id>/modules/` - Module listing
- `/courses/module/<id>/lesson/` - Lesson detail with two-pass validation
- `/quizzes/` - Quiz management
- `/exams/` - Mock exam center (Developer 2)
- `/payments/` - Payment processing (Developer 2)
- `/profile/` - User profile and referrals
- `/admin/` - Django admin

## Testing Checklist

### What Works ✓
- [x] User registration and login
- [x] Course creation with AI module generation
- [x] Credit deduction and daily reset
- [x] Module listing
- [x] Lesson generation with two-pass validation
- [x] Ask tutor questions (1 credit)
- [x] Report errors in lessons
- [x] Course deletion
- [x] Admin interface
- [x] PWA service worker
- [x] Responsive design with bottom nav

### Needs Testing
- [ ] Referral system (increase daily limit)
- [ ] Quiz generation and scoring
- [ ] Quiz retake credit deduction
- [ ] Account deletion
- [ ] AI fallback tiers under load
- [ ] LaTeX formula rendering in lessons

### Known Issues
- None currently blocking

## Deployment Configuration

### Production Settings (Render)
- See `render.yaml` for complete configuration
- Uses Gunicorn WSGI server
- PostgreSQL database (Render-managed)
- Static files collected to `staticfiles/`
- Debug=False in production

### Build Command
```bash
./build.sh
```
Installs dependencies, collects static files, runs migrations.

## Best Practices Followed
- Email-only authentication with auto-generated usernames
- Credit system with proper transaction handling
- Two-pass AI validation for content quality
- Syllabus-grounded AI generation
- Mobile-first responsive design
- PWA for offline capability
- Proper CSRF protection
- Environment-based configuration

## Future Enhancements (v2.0)
1. Social login (Google)
2. Enhanced security (CAPTCHA)
3. True RAG with vector database
4. Tailwind PostCSS compilation
5. Advanced analytics dashboard
6. Spaced repetition learning
7. Community study groups

## Contact & Support
For technical questions, check the code comments or review the spec document in `attached_assets/`.
