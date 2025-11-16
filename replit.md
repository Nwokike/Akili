# Akili - AI-Powered Educational Platform

**Last Updated:** November 16, 2025

## Project Overview

Akili is a comprehensive AI-powered educational platform designed to help Nigerian students prepare for JAMB, SSCE, and JSS examinations. The platform leverages Google Gemini AI and Groq API to generate personalized learning content, interactive quizzes, and mock exams.

## Tech Stack

- **Backend:** Django 5.2.8 (Python)
- **Database:** SQLite (development) / PostgreSQL (production)
- **AI Integration:** Google Gemini AI 2.5 Flash, Gemini Pro, Groq API (multi-tier fallback)
- **Frontend:** Tailwind CSS with dark mode support
- **Math Rendering:** KaTeX for LaTeX equations
- **Deployment:** Replit (development) / Render (production)
- **Payment Processing:** Paystack

## Key Features

### For Students
- **FREE Unlimited Quizzes:** Practice without credit cost
- **AI-Generated Courses:** 15-module courses tailored to exam type and subject (5 credits)
- **Mock Exams:** Full-length practice exams with 20 questions (5 credits)
- **Progress Tracking:** Quiz scores, completion rates, and learning journey
- **Referral System:** Earn +2 daily credits per successful referral
- **Dark Mode:** Auto-detect system preference
- **PWA Support:** Install as mobile app

### Credit System
- **10 free credits daily** for all users
- Credits reset automatically every 24 hours
- **Course Creation:** 5 credits
- **Practice Quiz:** FREE
- **Mock Exam:** 5 credits

## Project Structure

```
akili-platform/
├── akili_project/          # Main Django project settings
│   ├── settings.py        # Django configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI application
├── core/                   # Core app (dashboard, home, exam center)
│   ├── utils/             # AI utilities and helpers
│   │   ├── ai_fallback.py # Multi-tier AI fallback system
│   │   └── ai_module_generator.py
│   ├── templates/         # Core templates
│   └── views.py           # Core views
├── users/                  # Custom user authentication
│   ├── models.py          # CustomUser model with credit system
│   └── views.py           # Auth views
├── courses/                # Course and module management
│   ├── models.py          # Course, Module, CachedLesson models
│   ├── views.py           # Course creation, lesson viewing
│   └── templates/         # Course templates
├── quizzes/                # Quiz generation and attempts
│   ├── models.py          # QuizAttempt model
│   ├── utils.py           # Quiz generation logic
│   └── views.py           # Quiz views
├── exams/                  # Mock exam functionality
│   ├── models.py          # Exam, ExamQuestion models
│   └── views.py           # Exam generation and taking
├── payments/               # Credit purchase system (Paystack)
│   ├── models.py          # Payment model
│   └── views.py           # Payment initialization and verification
├── profiles/               # User profile management
├── admin_syllabus/         # Syllabus management (JAMB, SSCE, JSS)
├── static/                 # Static assets
│   ├── css/custom.css     # Custom styles
│   ├── js/main.js         # Main JavaScript
│   └── images/            # Images and logo
├── templates/              # Base templates and partials
│   ├── base.html          # Base template with KaTeX
│   ├── partials/          # Reusable components
│   │   ├── header.html    # Top header with dark mode
│   │   ├── sidebar.html   # Desktop sidebar navigation
│   │   ├── bottom_nav.html # Mobile bottom navigation
│   │   ├── credit_modal.html # Credit purchase modal
│   │   └── footer.html
│   └── core/              # Core page templates
└── requirements.txt        # Python dependencies
```

## Database Models

### Users App
- **CustomUser:** Extends Django User with tutor_credits, daily_credit_limit, referred_by

### Courses App
- **Course:** User's personalized course (exam_type, subject)
- **Module:** 15 modules per course with syllabus topics
- **CachedLesson:** AI-generated lessons with two-pass validation

### Quizzes App
- **QuizAttempt:** User quiz attempts with questions_data (JSON), score, passed status

### Exams App
- **Exam:** Mock exam attempts linked to modules
- **ExamQuestion:** Individual exam questions with options and correct answers

### Payments App
- **Payment:** Paystack payment records with verification status

## AI Integration

### Multi-Tier Fallback System
The platform uses a robust 4-tier AI fallback system for reliability:

1. **Tier 1:** Gemini 2.5 Flash (Free, Fast) - Primary
2. **Tier 2:** Gemini Pro (Paid, High Quality) - First fallback
3. **Tier 3:** Groq API (Free Fallback) - Second fallback
4. **Tier 4:** Circuit Breaker (Graceful Error) - Final fallback

### LaTeX Rendering
- All AI responses use **double-escaped backslashes** for LaTeX (e.g., `\\\\frac{a}{b}`)
- KaTeX renders math formulas on the frontend
- Delimiters: `$$...$$` (display), `$...$` (inline)

## Environment Variables

### Required for Development
```bash
DEBUG=True
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
```

### Required for Production
```bash
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://...
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key
```

## Running Locally (Replit)

The project is configured to run on Replit with the following workflow:

1. **Install Dependencies:** `pip install -r requirements.txt`
2. **Run Migrations:** `python manage.py migrate`
3. **Create Superuser:** `python manage.py createsuperuser`
4. **Run Server:** `python manage.py runserver 0.0.0.0:5000`

## Recent Changes (November 2025)

### Fixes Implemented
- ✅ Added KaTeX rendering to lesson detail and exam pages
- ✅ Updated sidebar navigation to match mobile nav (added Quizzes, removed Profile)
- ✅ Fixed exam center text (changed from 10 credits to 5 credits)
- ✅ Removed PWA install button from homepage
- ✅ Fixed payment modal buttons with proper form submission
- ✅ Added loading spinner to all AI actions
- ✅ Cleaned up requirements.txt (removed duplicates)

### Pending Improvements
- Refactor exam system to link exams to Courses instead of Modules
- Add 20-minute timer to exam taking page with auto-submit
- Fix course progress display to show "3/5" format instead of percentage
- Add "Start Mock Exam" button to main dashboard

## User Preferences

None specified yet.

## Development Notes

- Always use double-escaped backslashes for LaTeX in AI prompts
- Test KaTeX rendering after any content generation changes
- Keep the multi-tier AI fallback system intact for reliability
- Credits are managed at the user level, not transactions
- Exams are temporary - old completed exams are deleted when creating new ones

## Support

For development questions or issues:
- Check Django logs for backend errors
- Check browser console for frontend errors
- Verify AI API keys are correctly set in environment variables
