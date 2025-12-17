# Akili Platform - Replit Project Documentation

## Overview
Akili is an AI-powered educational platform for Nigerian secondary school students (JS1 to SS3). It uses Django 5.2.8, PostgreSQL, Tailwind CSS, and AI APIs (Gemini/Groq) to provide personalized course generation, quizzes, and assessments.

## Current State
- Django server running on port 5000
- PostgreSQL database connected via DATABASE_URL
- Tailwind CSS compiled and ready
- All major apps functional: courses, quizzes, curriculum, users, payments, profiles

## Recent Changes (December 17, 2025)

### Phase 1 Cleanup - Legacy Code Removal
- **Removed admin_syllabus references**: Deleted all imports and usages of JAMBSyllabus, SSCESyllabus, JSSSyllabus from:
  - `core/utils/ai_module_generator.py` - Removed generate_legacy_modules() function
  - `core/tests.py` - Removed ExamCenterViewTestCase and exams imports
  - `courses/views.py` - Cleaned GetAvailableSubjectsView of legacy exam_type code
  - `courses/forms.py` - Removed LegacyCourseCreationForm class
  
- **Deleted legacy management commands**:
  - `curriculum/management/commands/map_syllabuses.py`

- **Fixed URL routing errors**:
  - `templates/partials/bottom_nav.html` line 36: Changed `profiles:profile` to `profiles:my_profile`
  - Previous fix: `payments:buy_credits` → `payments:initialize_payment`

- **Updated documentation**:
  - `README.md` - Removed references to deleted exams/ and admin_syllabus/ directories

## Project Architecture

### Apps
- **core**: Utilities, middleware, AI fallback system, curriculum services
- **curriculum**: SchoolLevel, Subject, Term, Topic models (replaces legacy admin_syllabus)
- **courses**: Course, Module, CachedLesson models
- **quizzes**: Quiz functionality for students
- **assessments**: Assessment system for teachers
- **users**: CustomUser model with authentication
- **payments**: Paystack integration for credits
- **profiles**: User profile management

### Key URL Patterns
- `/dashboard/` - Main dashboard (requires login)
- `/courses/` - Course management
- `/quizzes/` - Quiz functionality
- `/profiles/` - User profile (URL name: `profiles:my_profile`)
- `/payments/` - Payment handling (URL name: `payments:initialize_payment`)

## User Preferences
- Nigerian secondary school focus (JS1-SS3)
- Credit-based system for AI features
- Mobile-first design with bottom navigation
- Dark mode support

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection
- `GEMINI_API_KEY` - Google Gemini API
- `GROQ_API_KEY` - Groq API (fallback)
- `PAYSTACK_SECRET_KEY` - Payment processing
- `ALLOWED_HOSTS` - Set to "*" for development
- `CSRF_TRUSTED_ORIGINS` - Auto-detected from REPLIT_DEV_DOMAIN

## Known Issues to Address
1. LSP diagnostics in core/tests.py and courses/tests.py (minor)
2. Legacy `exam_type` field still exists in Course model (kept for backwards compatibility)
3. Some templates still reference `course.exam_type` (display only, non-breaking)
