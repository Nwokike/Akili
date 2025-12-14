# Akili Platform - Complete Production Implementation Tracker

**Started:** December 14, 2025  
**Target:** Production-ready for 1GB RAM Google Cloud VM  
**Reference:** AUDIT_REPORT_CORE_APP.md  
**Total Issues:** 8 Critical + 26 Warnings + 34 Improvements = 68 Total

---

## IMPLEMENTATION STATUS SUMMARY

| Phase | Category | Total | Completed | Remaining |
|-------|----------|-------|-----------|-----------|
| 1 | Critical Issues | 8 | 7 | 1 |
| 2 | Warnings | 26 | 14 | 12 |
| 3 | Improvements | 34 | 0 | 34 |
| 4 | New Features | 3 | 0 | 3 |

---

# PHASE 1: CRITICAL ISSUES (8 Total)

## CRITICAL-1: Memory Leak Risk in AI Fallback
**File:** `core/utils/ai_fallback.py`  
**Issue:** Using `gc.collect()` manually after each AI call  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Review gc.collect() usage and determine if necessary
- [ ] Add memory monitoring/alerts
- [ ] Consider implementing streaming responses for large AI outputs
- [ ] Test memory usage under load

## CRITICAL-2: Rate Limiting Uses Database Cache
**File:** `core/middleware.py` + `akili_project/settings.py`  
**Issue:** Rate limiting stores data in DatabaseCache (DB query per check)  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Add LocMemCache configuration for rate limiting
- [x] Update RateLimitMiddleware to use caches['ratelimit']

## CRITICAL-3: No Health Check Endpoint
**File:** `akili_project/urls.py`  
**Issue:** No `/health` endpoint for load balancer/monitoring  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Add health_check view returning JSON {'status': 'healthy'}
- [x] Add URL path at /health/

## CRITICAL-4: Password Reset Templates Missing
**File:** `templates/registration/`  
**Issue:** Password reset URLs reference non-existent templates  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Create password_reset_form.html
- [x] Create password_reset_done.html
- [x] Create password_reset_confirm.html
- [x] Create password_reset_complete.html

## CRITICAL-5: Dead Code File - users/utils.py
**File:** `users/utils.py`  
**Issue:** Duplicate of urls.py, references non-existent views  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] DELETE users/utils.py

## CRITICAL-6: AskTutorView Credits Deducted AFTER AI Call
**File:** `courses/views.py` (AskTutorView)  
**Issue:** Credits deducted after AI call succeeds - bypass possible  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Deduct credits BEFORE AI call
- [x] Refund credits if AI call fails using add_credits()

## CRITICAL-7: Paystack Webhook Signature Verification
**File:** `payments/views.py`  
**Issue:** @csrf_exempt without webhook signature verification  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Add verify_paystack_signature() function using HMAC SHA512
- [x] Add paystack_webhook() endpoint with signature verification
- [x] Add webhook URL to payments/urls.py

## CRITICAL-8: No Health Check Endpoint (Duplicate of CRITICAL-3)
**Status:** [x] COMPLETED (Same as CRITICAL-3)

---

# PHASE 2: WARNINGS (26 Total)

## CORE APP WARNINGS (5)

### WARNING-1: Context Processor Calls reset_daily_credits() on EVERY Request
**File:** `core/context_processors.py`  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Check last_daily_reset timestamp before calling reset_daily_credits()

### WARNING-2: Dashboard View Has N+1 Query Potential
**File:** `core/views.py` (line 34)  
**Issue:** `user_courses[:3]` without prefetch for modules  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Add `.prefetch_related('modules')` to course queryset in dashboard_view

### WARNING-3: Exam Center View Has Debug Comment
**File:** `core/views.py` (line 45)  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Remove "THIS IS THE FIXED LINE" comment

### WARNING-4: AI Token Limits May Be Too Restrictive
**File:** `core/utils/ai_fallback.py`  
**Issue:** Token limits are conservative (2000-2500)  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Test with actual content to ensure quality
- [ ] Document reasoning for token limits
- [ ] Consider making token limits configurable

### WARNING-5: Profile View Developer Comment
**File:** `core/views.py` (line 62)  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Remove "Developer 1 will implement" comment

## USERS APP WARNINGS (4)

### WARNING-6: Referral Signup Shows Raw Username (with UUID)
**File:** `templates/users/signup.html` (line 23)  
**Issue:** Shows username with UUID suffix instead of name  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Pass referrer's first_name or full_name from view
- [x] Update template to show friendly name

### WARNING-7: Double Database Write on Signup with Referral
**File:** `users/views.py` (lines 22-33)  
**Issue:** form.save() then user.save() - two DB writes  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Use form.save(commit=False)
- [x] Set referred_by
- [x] Single save() call

### WARNING-8: Account Deletion Has No Confirmation Modal
**File:** `users/views.py`  
**Issue:** No client-side confirmation for account deletion  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add JavaScript confirmation modal
- [ ] Require typing "DELETE" or email to confirm

### WARNING-9: No Email Verification on Signup
**File:** `users/views.py`  
**Issue:** Users logged in immediately without email verification  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Implement email verification flow (optional toggle)
- [ ] Add email verification templates
- [ ] Add verification token model or use Django's

## ADMIN_SYLLABUS APP WARNINGS (1)

### WARNING-10: Duplicate Model Structure
**File:** `admin_syllabus/models.py`  
**Issue:** JAMBSyllabus, SSCESyllabus, JSSSyllabus are nearly identical  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Consider consolidating into single Syllabus model with exam_type field
- [ ] Create data migration if consolidating

## COURSES APP WARNINGS (4)

### WARNING-11: N+1 Query in ModuleListingView
**File:** `courses/views.py` (lines 94-136)  
**Issue:** 3 separate QuizAttempt queries per module  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Prefetch all quiz attempts in single query
- [x] Filter in Python instead of per-module queries

### WARNING-12: Import Inside View Methods
**File:** `courses/views.py` (lines 106, 117, 158, 182, 312)  
**Issue:** QuizAttempt imported inside methods multiple times  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Move import to top of file or use apps.get_model()
- [x] Refactor to avoid circular imports properly

### WARNING-13: print() Used for Logging
**File:** `courses/views.py` (line 83)  
**Issue:** print() statement for error logging  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Replace with logger = logging.getLogger(__name__)
- [x] Use logger.error() for error logging

### WARNING-14: GetAvailableSubjectsView Not Login Protected
**File:** `courses/views.py` (line 373)  
**Issue:** API endpoint has no LoginRequiredMixin  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Add LoginRequiredMixin to GetAvailableSubjectsView

## PROFILES APP WARNINGS (2)

### WARNING-15: Referral Stats Hardcoded to Zero
**File:** `templates/profiles/profile.html` (lines 96-100)  
**Issue:** Successful Referrals and Bonus Credits show 0  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Calculate referral_count in ProfileView
- [x] Calculate bonus credits earned
- [x] Pass to template context

### WARNING-16: Password Reset Says "Contact Support"
**File:** `templates/profiles/profile.html` (lines 130-132)  
**Issue:** Should link to password reset page  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Change "Contact support" to link to password_reset URL

## QUIZZES APP WARNINGS (2)

### WARNING-17: print() Statements for Logging
**File:** `quizzes/views.py` (line 56), `quizzes/utils.py` (lines 58, 63, 103-108)  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Replace all print() with proper logging in quizzes/views.py
- [x] Replace all print() with proper logging in quizzes/utils.py

### WARNING-18: Unused Import in views.py
**File:** `quizzes/views.py` (line 7)  
**Issue:** Sum is imported but not used  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Remove unused Avg import (Sum is used for quiz stats)

## EXAMS APP WARNINGS (2)

### WARNING-19: print() Statements for Logging
**File:** `exams/views.py` (lines 127, 173)  
**Status:** [x] COMPLETED  
**Tasks:**
- [x] Replace all print() with proper logging in exams/views.py

### WARNING-20: Exam Creates Record Before AI Success
**File:** `exams/views.py` (lines 117-121)  
**Issue:** Exam record created before AI call succeeds  
**Status:** [ ] PENDING (Currently handled with cleanup)  
**Tasks:**
- [ ] Review current cleanup logic
- [ ] Verify credits are properly refunded on failure
- [ ] Consider restructuring flow

## PAYMENTS APP WARNINGS (3)

### WARNING-21: No Webhook Signature Verification
**File:** `payments/views.py`  
**Status:** [x] COMPLETED (Fixed in CRITICAL-7)  

### WARNING-22: Payment Amount Stored as Float
**File:** `payments/models.py`  
**Issue:** DecimalField but uses float arithmetic  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Review all payment calculations
- [ ] Ensure all calculations use integer kobo

### WARNING-23: No Payment History Page
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Create payment history view
- [ ] Create payment history template
- [ ] Add URL pattern

## ASSESSMENTS APP WARNINGS (1)

### WARNING-24: N+1 Query in parent_dashboard
**File:** `assessments/views.py` (lines 230-239)  
**Issue:** Separate queries for each child's grades and reports  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Use prefetch_related for children's grades
- [ ] Use prefetch_related for children's reports

## PROJECT-WIDE WARNINGS (2)

### WARNING-25: Database Cache for Rate Limiting
**File:** `akili_project/settings.py`  
**Status:** [x] COMPLETED (Fixed in CRITICAL-2)  

### WARNING-26: Logs Directory in BASE_DIR
**File:** `akili_project/settings.py` (line 292)  
**Issue:** Logs written to project directory  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Make log path configurable via environment variable
- [ ] Consider /var/log/ for production

---

# PHASE 3: IMPROVEMENTS (34 Total)

## CORE APP IMPROVEMENTS (8)

### IMPROVE-1: Add Request Timing Middleware
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Create TimingMiddleware to log slow requests (>1s)
- [ ] Add to MIDDLEWARE in settings.py

### IMPROVE-2: Add Structured Logging
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add JSON formatter for production logs
- [ ] Add request IDs to log entries
- [ ] Update LOGGING configuration

### IMPROVE-3: Cache Curriculum Service Queries
**File:** `core/services/curriculum.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add caching for get_school_levels()
- [ ] Add caching for get_terms()
- [ ] Add caching for get_subjects_for_level()
- [ ] Use 1 hour TTL for static data

### IMPROVE-4: AI Content Validation Recursive Risk
**File:** `core/utils/ai_fallback.py` (line 253)  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add max validation attempts counter
- [ ] Add fallback if validation fails repeatedly

### IMPROVE-5: Add Retry Logic for AI API Calls
**File:** `core/utils/ai_fallback.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add 1-2 retries with exponential backoff
- [ ] Only retry on transient failures (timeout, 5xx)

### IMPROVE-6: Offline Content Download (Feature)
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Update serviceworker.js to cache lesson content
- [ ] Add offline indicator UI
- [ ] Test offline functionality

### IMPROVE-7: Study Timetable/Schedule (Feature)
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Create StudySchedule model
- [ ] Create schedule views
- [ ] Create schedule templates
- [ ] Add to navigation

### IMPROVE-8: Analytics Dashboard (Feature)
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Create analytics view
- [ ] Create analytics template with charts
- [ ] Add progress visualization
- [ ] Add learning insights

## USERS APP IMPROVEMENTS (4)

### IMPROVE-9: Add Rate Limiting on Login
**File:** `users/views.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add login attempt tracking
- [ ] Implement 5 failed attempts = 15min lockout
- [ ] Add lockout message to login template

### IMPROVE-10: Add Password Strength Indicator
**File:** `templates/users/signup.html`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add JavaScript password strength meter
- [ ] Show strength feedback (weak/medium/strong)

### IMPROVE-11: Add "Show Password" Toggle
**File:** `templates/users/signup.html` and `login.html`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add eye icon to toggle password visibility
- [ ] Add JavaScript toggle functionality

### IMPROVE-12: Session Management Page
**Status:** [ ] PENDING (Post-MVP)  
**Tasks:**
- [ ] Create session management view
- [ ] Show active sessions
- [ ] Allow revoking other sessions

## ADMIN_SYLLABUS APP IMPROVEMENTS (2)

### IMPROVE-13: Empty views.py File
**File:** `admin_syllabus/views.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Either delete file or add student-facing syllabus views

### IMPROVE-14: Add Syllabus Display for Students
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Create syllabus listing view
- [ ] Create syllabus detail template
- [ ] Add URL patterns

## COURSES APP IMPROVEMENTS (4)

### IMPROVE-15: Cache Curriculum Service Queries in Form
**File:** `courses/forms.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Cache get_school_levels() in form initialization
- [ ] Cache get_terms() in form initialization

### IMPROVE-16: Add Lesson Content Caching
**File:** `courses/views.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Check for existing CachedLesson with same topic before generating
- [ ] Reuse cached content when available

### IMPROVE-17: Add Progress Tracking
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Create LessonView model or add to user progress
- [ ] Track which lessons user has viewed
- [ ] Show progress indicators

### IMPROVE-18: Remove LegacyCourseCreationForm if Dead Code
**File:** `courses/forms.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Search codebase for LegacyCourseCreationForm usage
- [ ] Remove if not used

## PROFILES APP IMPROVEMENTS (3)

### IMPROVE-19: Add Profile Editing
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add profile edit form
- [ ] Allow editing first_name, last_name
- [ ] Add save functionality

### IMPROVE-20: Add Avatar Upload
**Status:** [ ] PENDING (Post-MVP)  
**Tasks:**
- [ ] Add avatar field to CustomUser or Profile model
- [ ] Add upload functionality
- [ ] Display uploaded avatar

### IMPROVE-21: Empty models.py File
**File:** `profiles/models.py`  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Remove empty file or add profile-specific models

## QUIZZES APP IMPROVEMENTS (2)

### IMPROVE-22: Quiz Generation is Free
**Note:** This is intentional design decision, NOT an issue  
**Status:** N/A  

### IMPROVE-23: Add Quiz Time Limit
**Status:** [ ] PENDING (Post-MVP)  
**Tasks:**
- [ ] Add time_limit field to quiz
- [ ] Add countdown timer UI
- [ ] Auto-submit on timeout

## EXAMS APP IMPROVEMENTS (2)

### IMPROVE-24: Add Exam Time Limit Display
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add countdown timer UI during exam
- [ ] Show time remaining

### IMPROVE-25: Review Exam Questions Feature
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add review mode after exam submission
- [ ] Show questions with explanations

## PAYMENTS APP IMPROVEMENTS (3)

### IMPROVE-26: Add Payment Receipt
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Generate PDF receipt
- [ ] Add download functionality
- [ ] Email receipt option

### IMPROVE-27: Add Email Confirmation
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Send payment confirmation email
- [ ] Include credits added, transaction reference

### IMPROVE-28: Add Admin Payment Dashboard
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Create payment analytics view for admin
- [ ] Show revenue metrics

## CURRICULUM APP IMPROVEMENTS (1)

### IMPROVE-29: Populate More Curriculum Data
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Complete curriculum data for all subjects
- [ ] Complete curriculum data for all levels

## ASSESSMENTS APP IMPROVEMENTS (2)

### IMPROVE-30: Complete Teacher/Parent Templates
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Verify all assessment templates are functional
- [ ] Complete any missing templates

### IMPROVE-31: Add Assessment Notifications
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Integrate Notification model
- [ ] Auto-notify for grades, assignments

## PROJECT-WIDE IMPROVEMENTS (3)

### IMPROVE-32: Add Sentry or Error Monitoring
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Add sentry-sdk package
- [ ] Configure Sentry DSN
- [ ] Test error reporting

### IMPROVE-33: Add Database Indexes
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Review frequently queried fields
- [ ] Add indexes to Course, Module, QuizAttempt
- [ ] Create migration

### IMPROVE-34: Configure ALLOWED_HOSTS Properly
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Document required ALLOWED_HOSTS for production
- [ ] Add validation/warning if not set

---

# PHASE 4: TEMPLATE/CODE CLEANUP

## Footer Social Links
**File:** `templates/partials/footer.html`  
**Issue:** Social links are placeholder "#"  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Get actual social media URLs or remove links

## bottom_nav.html Duplicate Classes
**File:** `templates/partials/bottom_nav.html`  
**Issue:** Duplicate dark: classes on lines 2, 18, 28, 36  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Clean up duplicate CSS classes

## credit_modal.html Dark Mode
**File:** `templates/partials/credit_modal.html`  
**Issue:** Dark mode classes incomplete (lines 17-18)  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Complete dark mode styling

## Duplicate Terms Notice
**File:** `templates/users/signup.html`  
**Issue:** Terms notice appears twice (lines 176-182)  
**Status:** [ ] PENDING  
**Tasks:**
- [ ] Remove duplicate terms notice

---

# IMPLEMENTATION LOG

## December 14, 2025

### Phase 1 Critical Fixes - COMPLETED (7/8)

**Completed:**
1. CRITICAL-2: Added LocMemCache for rate limiting
2. CRITICAL-3: Added /health/ endpoint
3. CRITICAL-4: Created 4 password reset templates
4. CRITICAL-5: Deleted users/utils.py dead code
5. CRITICAL-6: Fixed credit deduction timing in AskTutorView
6. CRITICAL-7: Added Paystack webhook with signature verification
7. WARNING-1: Fixed context processor performance
8. WARNING-3: Removed debug comment from core/views.py
9. WARNING-5: Removed developer comment from core/views.py

**Files Modified:**
- `users/utils.py` - DELETED
- `core/views.py` - Removed debug comments
- `core/context_processors.py` - Performance optimization
- `core/middleware.py` - Use LocMemCache for rate limiting
- `courses/views.py` - Credit deduction timing fix
- `payments/views.py` - Webhook with signature verification
- `payments/urls.py` - Added webhook URL
- `akili_project/urls.py` - Added health check endpoint
- `akili_project/settings.py` - Added ratelimit cache config
- `templates/registration/password_reset_form.html` - NEW
- `templates/registration/password_reset_done.html` - NEW
- `templates/registration/password_reset_confirm.html` - NEW
- `templates/registration/password_reset_complete.html` - NEW

**Architect Review:** PASSED - All critical fixes approved

**Remaining Critical:**
- CRITICAL-1: Memory leak risk in AI fallback (needs investigation)

---

## NEXT IMPLEMENTATION SESSION

Continue with Phase 2 Warnings:
1. WARNING-2: Fix N+1 query in dashboard view
2. WARNING-6 through WARNING-26
3. Replace all print() statements with proper logging
4. Fix N+1 queries in ModuleListingView and parent_dashboard
