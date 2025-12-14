# Akili Platform - Comprehensive Production Audit Report

**Audit Date:** December 14, 2025  
**Target Environment:** 1GB RAM Google Cloud VM  
**Purpose:** Production readiness assessment before public launch

---

## AUDIT SUMMARY

| App | Status | Critical Issues | Warnings | Improvements |
|-----|--------|-----------------|----------|--------------|
| CORE | Audited | 3 | 5 | 8 |
| USERS | Audited | 2 | 4 | 4 |
| ADMIN_SYLLABUS | Audited | 0 | 1 | 2 |
| COURSES | Audited | 1 | 4 | 4 |
| PROFILES | Pending | - | - | - |
| QUIZZES | Pending | - | - | - |
| EXAMS | Pending | - | - | - |
| PAYMENTS | Pending | - | - | - |
| CURRICULUM | Pending | - | - | - |
| ASSESSMENTS | Pending | - | - | - |
| PROJECT-WIDE | Pending | - | - | - |

---

## 1. CORE APP AUDIT

### 1.1 Files Reviewed
- `core/models.py` - Empty (no models)
- `core/views.py` - 9 views
- `core/middleware.py` - RateLimitMiddleware, ErrorLoggingMiddleware
- `core/admin.py` - Empty (no registrations)
- `core/apps.py` - Standard config
- `core/tests.py` - 15 test cases
- `core/context_processors.py` - credits_processor
- `core/services/curriculum.py` - CurriculumService class (264 lines)
- `core/utils/ai_module_generator.py` - AI module generation (236 lines)
- `core/utils/ai_fallback.py` - 4-tier AI fallback system (259 lines)
- `core/templatetags/custom_filters.py` - get_item filter

### 1.2 CRITICAL ISSUES

#### CRITICAL-1: Memory Leak Risk in AI Fallback
**File:** `core/utils/ai_fallback.py`
**Issue:** Using `gc.collect()` manually after each AI call is a sign of poor memory management. On a 1GB VM, this could cause issues.
**Impact:** Server crashes under load
**Recommendation:** 
- Implement streaming responses for large AI outputs
- Add memory monitoring/alerts
- Consider async processing for AI calls

#### CRITICAL-2: Rate Limiting Uses Database Cache
**File:** `core/middleware.py` + `settings.py`
**Issue:** Rate limiting stores data in `DatabaseCache` which means every rate limit check = database query. On high traffic, this adds significant DB load.
**Impact:** Database bottleneck under load
**Recommendation:**
- Use Redis or in-memory cache for rate limiting (if Redis not available, use LocMemCache for rate limiting only)
- Current: 10 requests/min for authenticated, 30/min for anonymous - may be too restrictive

#### CRITICAL-3: No Health Check Endpoint
**File:** `akili_project/urls.py`
**Issue:** No `/health` or `/ping` endpoint for load balancer/monitoring
**Impact:** Cannot implement proper health monitoring or zero-downtime deployments
**Recommendation:** Add simple health check endpoint

### 1.3 WARNINGS

#### WARNING-1: Context Processor Calls reset_daily_credits() on EVERY Request
**File:** `core/context_processors.py` (line 6)
**Issue:** `request.user.reset_daily_credits()` is called on every authenticated request
**Impact:** Unnecessary database writes, performance degradation
**Recommendation:** Only call this once per day (check last_credit_reset timestamp first)

#### WARNING-2: Dashboard View Has N+1 Query Potential
**File:** `core/views.py` (line 34)
**Issue:** `user_courses[:3]` without prefetch for modules
**Impact:** Multiple DB queries for dashboard
**Recommendation:** Add `.prefetch_related('modules')` to course queryset

#### WARNING-3: Exam Center View Has Comment "THIS IS THE FIXED LINE"
**File:** `core/views.py` (line 45)
**Issue:** Debug comment left in production code
**Impact:** Code cleanliness
**Recommendation:** Remove debug comments

#### WARNING-4: AI Token Limits May Be Too Restrictive
**File:** `core/utils/ai_fallback.py`
**Issue:** Token limits are very conservative (2000-2500 tokens)
**Impact:** Truncated lessons for complex topics
**Recommendation:** Test with actual content to ensure quality not compromised

#### WARNING-5: Profile View Says "Developer 1 Will Implement"
**File:** `core/views.py` (line 62)
**Issue:** Comment suggests incomplete feature
**Impact:** Potential incomplete functionality
**Recommendation:** Verify profile is fully implemented in profiles app

### 1.4 IMPROVEMENTS NEEDED

#### IMPROVE-1: Add Request Timing Middleware
**Recommendation:** Log slow requests (>1s) for performance monitoring

#### IMPROVE-2: Add Structured Logging
**Current:** Basic logging
**Recommendation:** Add JSON structured logging with request IDs for production debugging

#### IMPROVE-3: Cache Curriculum Service Queries
**File:** `core/services/curriculum.py`
**Issue:** Many queries could be cached (school levels, subjects, terms rarely change)
**Recommendation:** Add caching with appropriate TTL (1 hour for static data)

#### IMPROVE-4: AI Content Validation Is Recursive Risk
**File:** `core/utils/ai_fallback.py` (line 253)
**Issue:** `validate_ai_content()` calls `call_ai_with_fallback()` - potential infinite loop if validation content is malformed
**Recommendation:** Add max validation attempts or disable validation in production

#### IMPROVE-5: Add Retry Logic for AI API Calls
**File:** `core/utils/ai_fallback.py`
**Issue:** Single attempt per tier before failover
**Recommendation:** Add 1-2 retries with exponential backoff for transient failures

#### IMPROVE-6: Missing Feature - Offline Content Download
**User Request:** Pre-cache lessons for offline
**Current State:** PWA exists but no offline lesson caching
**Recommendation:** Implement lesson content caching in service worker

#### IMPROVE-7: Missing Feature - Study Timetable/Schedule
**User Request:** Study planning tools
**Current State:** Not implemented
**Recommendation:** Add simple study schedule feature

#### IMPROVE-8: Missing Feature - Analytics Dashboard
**User Request:** Learning insights
**Current State:** Basic stats on dashboard only
**Recommendation:** Add dedicated analytics page with progress charts

### 1.5 TEMPLATES AUDIT

#### Templates Reviewed:
- `templates/base.html` - Good structure, KaTeX loaded, PWA support
- `templates/core/home.html` - Clean landing page
- `templates/core/dashboard.html` - Good stats display
- `templates/partials/header.html` - Profile dropdown works
- `templates/partials/sidebar.html` - Navigation complete
- `templates/partials/bottom_nav.html` - Mobile nav works
- `templates/partials/credit_modal.html` - Payment options clear
- `templates/partials/footer.html` - Social links are placeholder (#)
- `templates/errors/404.html` - Good design
- `templates/errors/500.html` - Good design
- `templates/legal/privacy.html` - Complete content

#### Template Issues:
1. **Footer social links are "#"** - Need real links or remove
2. **bottom_nav.html has duplicate dark: classes** (line 2, 18, 28, 36)
3. **credit_modal.html dark mode classes incomplete** (line 17-18)

### 1.6 STATIC FILES AUDIT

#### Files Reviewed:
- `static/js/main.js` - Complete (304 lines)
- `static/js/dark-mode.js` - Working (7 lines)
- `static/css/styles.css` - Tailwind compiled
- `static/src/main.css` - Tailwind source with custom utilities

#### Static File Issues:
1. **main.js uses older execCommand for clipboard** - Has fallback, acceptable
2. **PWA service worker needs audit** (not yet reviewed)

### 1.7 TESTS AUDIT

**File:** `core/tests.py`
- 15 test cases covering views
- Good coverage for basic functionality
- Missing: Rate limit tests, AI fallback tests, error handling tests

### 1.8 CODE TO REMOVE/CLEAN

1. Debug comment in `core/views.py` line 45-46
2. Developer comment in `core/views.py` line 62
3. Placeholder social links in footer

---

## 2. USERS APP AUDIT

### 2.1 Files Reviewed
- `users/models.py` - CustomUser model, CustomUserManager (136 lines)
- `users/views.py` - Signup, login, logout, referral, delete account (111 lines)
- `users/forms.py` - SignupForm, LoginForm (24 lines)
- `users/admin.py` - CustomUserAdmin configuration (45 lines)
- `users/urls.py` - Auth URLs including password reset (16 lines)
- `users/utils.py` - **DEAD CODE** (duplicate of urls.py)
- `users/tests.py` - 22 test cases (244 lines)
- `templates/users/login.html` - Login template (93 lines)
- `templates/users/signup.html` - Signup template (197 lines)

### 2.2 CRITICAL ISSUES

#### CRITICAL-4: Password Reset Templates Missing
**File:** `users/urls.py` + `templates/registration/`
**Issue:** Password reset URLs reference `templates/registration/password_reset_form.html` etc., but this directory doesn't exist
**Impact:** Password reset feature is BROKEN - users cannot reset forgotten passwords
**Recommendation:** Create password reset templates:
- `templates/registration/password_reset_form.html`
- `templates/registration/password_reset_done.html`
- `templates/registration/password_reset_confirm.html`
- `templates/registration/password_reset_complete.html`

#### CRITICAL-5: Dead Code File - users/utils.py
**File:** `users/utils.py`
**Issue:** This file is a duplicate of `urls.py` - it contains URL patterns, not utilities. Also references non-existent `views.dashboard_view`
**Impact:** Confusion, maintenance burden, potential import conflicts
**Recommendation:** DELETE this file immediately

### 2.3 WARNINGS

#### WARNING-6: Referral Signup Shows Raw Username (with UUID)
**File:** `templates/users/signup.html` (line 23)
**Issue:** Shows `{{ referred_by }}` which is the username with UUID suffix (e.g., "john.doea1b2c3d4")
**Impact:** Poor UX - users see ugly auto-generated usernames
**Recommendation:** Pass referrer's first_name or full_name instead of username

#### WARNING-7: Double Database Write on Signup with Referral
**File:** `users/views.py` (lines 22-33)
**Issue:** When referral is present, `form.save()` creates user, then `user.save()` is called again. Two database writes.
**Impact:** Minor performance issue
**Recommendation:** Use `form.save(commit=False)`, set `referred_by`, then single `save()`

#### WARNING-8: Account Deletion Has No Confirmation Modal
**File:** `users/views.py` (line 88-111)
**Issue:** Account deletion happens immediately on POST with no client-side confirmation check
**Impact:** Risk of accidental account deletion
**Recommendation:** Add confirmation step (type email or "DELETE" to confirm)

#### WARNING-9: No Email Verification on Signup
**File:** `users/views.py` (line 36)
**Issue:** Users are logged in immediately after signup without email verification
**Impact:** Potential for fake accounts, no way to confirm user owns email
**Recommendation:** Add email verification flow (can be done post-MVP)

### 2.4 IMPROVEMENTS NEEDED

#### IMPROVE-9: Add Rate Limiting on Login
**File:** `users/views.py` `login_view`
**Issue:** No protection against brute force attacks on login
**Recommendation:** Add login attempt limiting (5 failed attempts = 15min lockout)

#### IMPROVE-10: Add Password Strength Indicator
**File:** `templates/users/signup.html`
**Current:** Only text hint "Must be at least 8 characters"
**Recommendation:** Add JavaScript password strength meter

#### IMPROVE-11: Add "Show Password" Toggle
**File:** `templates/users/signup.html` and `login.html`
**Recommendation:** Add eye icon to toggle password visibility

#### IMPROVE-12: Session Management Page
**Current:** No way for users to see/manage active sessions
**Recommendation:** Add session management in profile (post-MVP)

### 2.5 SECURITY ANALYSIS

**GOOD:**
- Email-based authentication (not username)
- CSRF protection via `@ensure_csrf_cookie`
- Password hashing handled by Django
- Terms agreement required
- Atomic transaction for account deletion

**CONCERNS:**
- No email verification
- No login rate limiting
- No password breach checking (HaveIBeenPwned API)
- Referral URL uses predictable usernames

### 2.6 TEMPLATES AUDIT

#### `templates/users/login.html`
- Clean, responsive design
- Proper error handling
- Dark mode support
- ✓ No issues found

#### `templates/users/signup.html`
- Good form structure
- Terms of service checkbox
- Free credits badge (marketing)
- Password hints present
- Minor: Terms notice appears twice (checkbox + bottom text)

### 2.7 TESTS AUDIT

**File:** `users/tests.py`
- 22 test cases in 3 classes
- Good coverage of user model methods
- Good coverage of auth views
- Good referral tests

**Missing Tests:**
- Password reset flow
- Account deletion
- Email validation edge cases
- Duplicate email handling

### 2.8 CODE TO REMOVE/CLEAN

1. **DELETE** `users/utils.py` - Dead code, duplicate of urls.py
2. Remove duplicate terms notice in signup.html (lines 176-182)

## 3. ADMIN_SYLLABUS APP AUDIT

### 3.1 Files Reviewed
- `admin_syllabus/models.py` - 3 syllabus models (56 lines)
- `admin_syllabus/views.py` - Empty (3 lines - just boilerplate)
- `admin_syllabus/admin.py` - Admin configuration for all 3 models (24 lines)
- `admin_syllabus/tests.py` - 15 test cases (167 lines)

### 3.2 CRITICAL ISSUES

*None found*

### 3.3 WARNINGS

#### WARNING-10: Duplicate Model Structure
**File:** `admin_syllabus/models.py`
**Issue:** JAMBSyllabus, SSCESyllabus, and JSSSyllabus are nearly identical models
**Impact:** Code duplication, maintenance burden
**Recommendation:** Consider a single `Syllabus` model with `exam_type` field:
```python
class Syllabus(models.Model):
    EXAM_TYPES = [('JAMB', 'JAMB'), ('SSCE', 'SSCE'), ('JSS', 'JSS')]
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPES)
    subject = models.CharField(max_length=200)
    # ... rest of fields
    class Meta:
        unique_together = ['exam_type', 'subject']
```

### 3.4 IMPROVEMENTS NEEDED

#### IMPROVE-13: Empty views.py File
**File:** `admin_syllabus/views.py`
**Issue:** File contains only boilerplate comment
**Recommendation:** Either delete the file or add views for syllabus display to students

#### IMPROVE-14: Add Syllabus Display for Students
**Current:** Syllabuses only viewable in admin
**Recommendation:** Add views/templates for students to view syllabuses for exam prep

### 3.5 SECURITY ANALYSIS

**GOOD:**
- Admin-only access by default
- No public endpoints

### 3.6 TESTS AUDIT

**File:** `admin_syllabus/tests.py`
- 15 test cases in 4 classes
- Good coverage for CRUD operations
- Tests uniqueness constraints
- Tests LaTeX content support

### 3.7 CODE TO REMOVE/CLEAN

1. Consider consolidating 3 models into 1 with exam_type field
2. Remove empty `views.py` if not planning to add student-facing views

## 4. COURSES APP AUDIT

### 4.1 Files Reviewed
- `courses/models.py` - Course, Module, CachedLesson models (119 lines)
- `courses/views.py` - 8 views including course creation, lessons, AI tutor (397 lines)
- `courses/forms.py` - CourseCreationForm, LegacyCourseCreationForm (160 lines)
- `courses/urls.py` - 8 URL patterns (22 lines)
- `courses/admin.py` - Admin configuration for 3 models (24 lines)
- `courses/tests.py` - 11 test cases (350 lines)
- `courses/templates/courses/` - 4 templates

### 4.2 CRITICAL ISSUES

#### CRITICAL-6: AskTutorView Credits Deducted AFTER AI Call
**File:** `courses/views.py` (lines 331-335)
**Issue:** Credits are deducted AFTER the AI call succeeds. If user closes browser or network fails between AI response and credit deduction, AI is used but credits are not deducted.
**Impact:** Potential free AI usage, credit system bypass
**Recommendation:** Deduct credits BEFORE AI call, refund on failure:
```python
if not request.user.deduct_credits(1):
    messages.error(request, 'Insufficient credits.')
    return redirect(...)
try:
    result = call_ai_with_fallback(...)
    if not result['success']:
        request.user.add_credits(1)  # Refund
        ...
```

### 4.3 WARNINGS

#### WARNING-11: N+1 Query in ModuleListingView
**File:** `courses/views.py` (lines 94-136)
**Issue:** For each module, 3 separate QuizAttempt queries are made inside the loop
**Impact:** Performance degradation with many modules
**Recommendation:** Prefetch quiz attempts in single query, then filter in Python:
```python
all_attempts = QuizAttempt.objects.filter(
    user=request.user,
    module__course=course
).select_related('module')
```

#### WARNING-12: Import Inside View Methods (Circular Import Workaround)
**File:** `courses/views.py` (lines 106, 117, 158, 182, 312)
**Issue:** `from quizzes.models import QuizAttempt` imported inside methods multiple times
**Impact:** Minor performance overhead, code smell
**Recommendation:** Refactor to avoid circular imports (use get_model or late binding)

#### WARNING-13: print() Used for Logging
**File:** `courses/views.py` (line 83)
**Issue:** `print()` statement used for error logging: `print(f"Course creation failed...")`
**Impact:** Logs lost in production, no structured logging
**Recommendation:** Use `import logging; logger = logging.getLogger(__name__)`

#### WARNING-14: GetAvailableSubjectsView Not Login Protected
**File:** `courses/views.py` (line 373)
**Issue:** API endpoint `/api/subjects/` has no `LoginRequiredMixin`
**Impact:** Minor info disclosure (subject list), unnecessary DB queries from bots
**Recommendation:** Add `LoginRequiredMixin` or rate limiting

### 4.4 IMPROVEMENTS NEEDED

#### IMPROVE-15: Cache Curriculum Service Queries in Form
**File:** `courses/forms.py` (lines 33, 38)
**Issue:** `CurriculumService.get_school_levels()` and `get_terms()` called on every form load
**Recommendation:** Cache these values (they rarely change)

#### IMPROVE-16: Add Lesson Content Caching
**File:** `courses/views.py` `_generate_lesson`
**Issue:** If same topic requested, new lesson generated each time (unless module.lesson_content exists)
**Recommendation:** Check if CachedLesson with same topic exists before generating

#### IMPROVE-17: Add Progress Tracking
**Current:** No way to track which lessons user has viewed
**Recommendation:** Add `LessonView` model or track in user progress

#### IMPROVE-18: LegacyCourseCreationForm May Be Dead Code
**File:** `courses/forms.py` (lines 95-159)
**Issue:** `LegacyCourseCreationForm` exists but unclear if still used
**Recommendation:** Verify usage, remove if not needed

### 4.5 SECURITY ANALYSIS

**GOOD:**
- All main views require login (`LoginRequiredMixin`)
- Course/module access restricted to owner (`course__user=request.user`)
- Password required for course deletion
- Transaction atomic for course creation
- HTML sanitization with bleach for AI content
- XSS protection with allowed tags/attributes

**CONCERNS:**
- API endpoint unprotected (minor)
- Credit deduction timing issue (CRITICAL-6)

### 4.6 TEMPLATES AUDIT

#### `lesson_detail.html`
- Good structure, responsive design
- KaTeX support for math
- Dark mode support
- Proper CSRF protection
- ✓ Well implemented

#### `course_creation.html`
- Clean form design
- Loading states handled
- Spinner on submit
- ✓ No major issues

### 4.7 TESTS AUDIT

**File:** `courses/tests.py`
- 11 test cases in 3 classes
- Good coverage of course creation flow
- Tests credit deduction
- Tests duplicate prevention
- Tests curriculum linkage

**Missing Tests:**
- AskTutorView credit flow
- Lesson generation
- Module locking logic
- Error reporting

### 4.8 CODE TO REMOVE/CLEAN

1. `print()` statement in line 83 - replace with logger
2. Multiple duplicate imports inside methods - consolidate
3. Verify if `LegacyCourseCreationForm` is still needed

## 5. PROFILES APP AUDIT
*Pending*

## 6. QUIZZES APP AUDIT
*Pending*

## 7. EXAMS APP AUDIT
*Pending*

## 8. PAYMENTS APP AUDIT
*Pending*

## 9. CURRICULUM APP AUDIT
*Pending*

## 10. ASSESSMENTS APP AUDIT
*Pending*

## 11. PROJECT-WIDE AUDIT
*Pending*

---

## FEATURE REQUESTS TRACKING

| Feature | Priority | Current State | Recommendation |
|---------|----------|---------------|----------------|
| Timetable/Schedule | HIGH | Not implemented | Add study planning feature |
| Offline Content Download | HIGH | PWA exists, no lesson cache | Implement in service worker |
| Analytics Dashboard | MEDIUM | Basic stats only | Add dedicated analytics page |

---

## PRODUCTION CHECKLIST (To Be Updated)

- [ ] All critical issues resolved
- [ ] All warnings addressed or documented
- [ ] Security audit complete
- [ ] Performance testing done
- [ ] Database indexes verified
- [ ] Static files optimized
- [ ] Error monitoring configured
- [ ] Backup strategy confirmed
- [ ] SSL/HTTPS configured
- [ ] Environment variables secured
