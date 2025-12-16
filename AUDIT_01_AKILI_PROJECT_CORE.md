# COMPREHENSIVE AUDIT: akili_project (Settings) + core App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM

---

# PART A: AKILI_PROJECT (Django Settings & Configuration)

## 1. Overview & Ownership

**Purpose**: Core Django project configuration containing settings, URL routing, and WSGI/ASGI entry points.

**Files Reviewed**:
- `akili_project/settings.py` (317 lines)
- `akili_project/urls.py` (45 lines)
- `akili_project/wsgi.py`
- `akili_project/asgi.py`

---

## 2. Settings.py Analysis

### 2.1 CRITICAL ISSUES (Must Fix Before Production)

| Issue | Location | Severity | Description | Recommendation |
|-------|----------|----------|-------------|----------------|
| **Missing logs directory** | Line 294 | HIGH | `os.makedirs(log_dir, exist_ok=True)` creates logs at startup but if LOG_DIR env is not set in production, it defaults to project directory which may not be writable | Set LOG_DIR environment variable explicitly in production or use /var/log/akili |
| **File logging handler path** | Line 269 | HIGH | `LOG_FILE_PATH` defaults to `BASE_DIR / 'logs' / 'akili.log'` - in production on ephemeral filesystem, logs may be lost | Use cloud logging service or persistent volume |
| **ALLOWED_HOSTS empty in production** | Line 49-50 | CRITICAL | If `ALLOWED_HOSTS_ENV` not set in production, ALLOWED_HOSTS becomes empty list causing all requests to fail | Ensure ALLOWED_HOSTS is ALWAYS set in production env vars |

### 2.2 SECURITY CONFIGURATION (Good Practices Found)

| Setting | Status | Notes |
|---------|--------|-------|
| SECRET_KEY handling | ✅ GOOD | Raises ValueError if not set in production (line 39) |
| DEBUG check | ✅ GOOD | Defaults to False, reads from env (line 29) |
| CSRF_TRUSTED_ORIGINS | ⚠️ CHECK | Must be set in production via env var |
| Cookie security | ✅ GOOD | CSRF and Session cookies secure in production (lines 70-85) |
| HSTS headers | ✅ GOOD | Enabled in production (lines 79-85) |
| X-Frame-Options | ✅ GOOD | DENY in production (line 76) |

### 2.3 DATABASE CONFIGURATION

| Setting | Current Value | 1GB RAM Recommendation |
|---------|---------------|------------------------|
| conn_max_age | 60 | OK for 1GB - prevents connection churn |
| conn_health_checks | True | ✅ Good - prevents stale connections |
| Pool size | Not configured | Consider adding `max_pool_size=2` for 1GB RAM |

**Development Fallback Issue**: SQLite used when DATABASE_URL not set - ensure DATABASE_URL is ALWAYS set in production.

### 2.4 CACHE CONFIGURATION

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    },
    'ratelimit': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        ...
    }
}
```

**CRITICAL ISSUE**: Database cache requires `python manage.py createcachetable` to be run in production. This is NOT in build.sh!

**RECOMMENDATION**: 
1. Add `python manage.py createcachetable` to build.sh
2. For 1GB RAM VM, consider Redis if available, or keep DB cache but monitor performance

### 2.5 AKILI BUSINESS SETTINGS

| Setting | Value | Notes |
|---------|-------|-------|
| AKILI_DAILY_FREE_CREDITS | 10 | Configurable via env? NO - hardcoded |
| AKILI_MAX_REFERRAL_CREDITS | 30 | Hardcoded |
| AKILI_CREDITS_PER_REFERRAL | 2 | Hardcoded |

**RECOMMENDATION**: Make these configurable via environment variables for A/B testing without redeployment.

### 2.6 INSTALLED_APPS ORDER

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'users',
    'admin_syllabus',  # LEGACY - Consider removal
    'courses',
    'profiles',
    'quizzes',
    'exams',           # TO BE REMOVED per user request
    'payments',
    'curriculum',
    'assessments',
]
```

**ACTION REQUIRED**: Remove `exams` app from INSTALLED_APPS after audit confirms all dependencies are resolved.

---

## 3. URLs.py Analysis

### 3.1 Current URL Structure

| Path | View/Include | Notes |
|------|--------------|-------|
| `/health/` | health_check | ✅ Good for load balancer |
| `/` | core_views.home_view | Public landing |
| `/admin/` | admin.site.urls | Django admin |
| `/dashboard/` | core_views.dashboard_view | Main user dashboard |
| `/exam-center/` | core_views.exam_center_view | **TO BE REMOVED** with exams app |
| `/` | users.urls | Auth routes (no namespace) |
| `/courses/` | courses.urls | Course management |
| `/profiles/` | profiles.urls | User profiles |
| `/quizzes/` | quizzes.urls | Practice quizzes |
| `/exams/` | exams.urls | **TO BE REMOVED** |
| `/payments/` | payments.urls | Paystack integration |
| `/assessments/` | assessments.urls | Teacher/Parent/Student |
| `/privacy/`, `/terms/`, `/about/` | Legal pages | ✅ Good |

### 3.2 ISSUES FOUND

1. **Missing URL namespace for users**: `path('', include('users.urls'))` - should have `namespace='users'`
2. **Exam center route**: `/exam-center/` references exams app - needs removal
3. **No curriculum URLs**: Curriculum app has no public URLs - intentional?

### 3.3 ERROR HANDLERS

```python
handler404 = 'core.views.error_404_view'
handler500 = 'core.views.error_500_view'
handler403 = 'core.views.error_403_view'
```

✅ Good - Custom error pages configured.

---

# PART B: CORE APP

## 1. Overview & Ownership

**Purpose**: Core utilities, middleware, AI integration, context processors, and template tags.

**Files Reviewed**:
- `core/views.py` (91 lines)
- `core/middleware.py` (126 lines)
- `core/context_processors.py`
- `core/utils/ai_fallback.py` (269 lines)
- `core/utils/ai_module_generator.py` (236 lines)
- `core/services/curriculum.py` (264 lines)
- `core/templatetags/custom_filters.py`

---

## 2. Views Analysis (core/views.py)

### 2.1 Views Inventory

| View | Auth Required | Purpose | Issues |
|------|---------------|---------|--------|
| home_view | No | Landing page | ✅ OK - redirects authenticated users |
| dashboard_view | Yes | Main dashboard | Uses prefetch_related - ✅ Good |
| exam_center_view | Yes | Exam center | **TO BE REMOVED** - references exams app |
| profile_view | Yes | Profile redirect | Duplicate? profiles app has ProfileView |
| privacy_view | No | Privacy policy | ✅ OK |
| terms_view | No | Terms of service | ✅ OK |
| about_view | No | About page | ✅ OK |
| error_404_view | No | 404 handler | ✅ OK |
| error_500_view | No | 500 handler | ✅ OK |
| error_403_view | No | 403 handler | ✅ OK |

### 2.2 CRITICAL ISSUES

1. **exam_center_view** (lines 38-55): Must be removed when exams app is deleted
   - References `from exams.models import Exam`
   - References `from courses.models import Course`
   - Template: `exams/exam_center.html` - must be deleted

2. **Duplicate profile_view** (lines 58-61): Exists in both core/views.py and profiles app
   - Recommendation: Remove from core/views.py, use profiles app only

### 2.3 Dashboard View Performance Analysis

```python
@login_required
def dashboard_view(request):
    user_courses = Course.objects.filter(user=request.user).prefetch_related('modules')
    courses_count = user_courses.count()
    quizzes_count = QuizAttempt.objects.filter(user=request.user, completed_at__isnull=False).count()
    exams_count = Exam.objects.filter(user=request.user, completed_at__isnull=False).count()
```

**ISSUES**:
1. `exams_count` references Exam model - must be removed
2. Three separate queries for counts - could be combined
3. `user_courses[:3]` after `.count()` - causes two queries

**OPTIMIZED VERSION**:
```python
user_courses = list(Course.objects.filter(user=request.user).prefetch_related('modules')[:3])
courses_count = len(user_courses) if len(user_courses) < 3 else Course.objects.filter(user=request.user).count()
```

---

## 3. Middleware Analysis (core/middleware.py)

### 3.1 RateLimitMiddleware

**Configuration**:
- Authenticated users: 10 requests/minute per endpoint
- Anonymous users: 30 requests/minute per IP

**Rate Limited Paths**:
```python
RATE_LIMITED_PATHS = [
    '/courses/create',
    '/exams/start',      # TO BE REMOVED
    '/courses/ask-tutor',
]
```

**ISSUES**:
1. `/exams/start` path needs removal when exams app deleted
2. Rate limit uses `locmem` cache - OK for single worker, but won't work with multiple gunicorn workers!

**CRITICAL FOR 1GB VM**: With 2 gunicorn workers, rate limits will NOT be shared. Each worker has its own locmem cache.

**RECOMMENDATION**: Change ratelimit cache to database cache or Redis for multi-worker support:
```python
'ratelimit': {
    'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    'LOCATION': 'ratelimit_cache_table',
}
```

### 3.2 ErrorLoggingMiddleware

✅ Good implementation - logs user context with exceptions.

---

## 4. AI Integration Analysis (core/utils/ai_fallback.py)

### 4.1 4-Tier Fallback System

| Tier | Service | Max Tokens | Timeout | Notes |
|------|---------|------------|---------|-------|
| 1 | Gemini 2.5 Flash | 2500 | 45s | Primary - free tier |
| 2 | Gemini Pro | 3000 | 55s | Paid tier fallback |
| 3 | Groq API | 2000 | 35s | Free fallback |
| 4 | Circuit Breaker | N/A | N/A | Graceful error |

### 4.2 CRITICAL ISSUES FOR 1GB RAM

1. **Memory Management** (lines 28-29):
   ```python
   MAX_RESPONSE_SIZE_BYTES = 512 * 1024  # 512KB max response size
   ```
   ✅ Good - prevents large responses from causing OOM

2. **Garbage Collection** (lines 144-146):
   ```python
   del result
   gc.collect()
   ```
   ✅ Good - explicit memory cleanup

3. **Token Limits** (lines 22-27):
   Appropriately conservative for 1GB RAM.

### 4.3 API KEY HANDLING

```python
gemini_key = settings.GEMINI_API_KEY
groq_key = settings.GROQ_API_KEY
```

**ISSUE**: No validation if API keys are empty strings vs None
**RECOMMENDATION**: Add check:
```python
if gemini_key and len(gemini_key) > 10:  # Validate key length
```

### 4.4 validate_ai_content Function (lines 250-268)

**ISSUE**: This function calls AI to validate AI content - double API cost!
**RECOMMENDATION**: Consider removing or making optional. Currently used in lesson generation (courses/views.py line 288).

---

## 5. AI Module Generator Analysis (core/utils/ai_module_generator.py)

### 5.1 Functions

| Function | Purpose | Issues |
|----------|---------|--------|
| generate_course_modules | Main router | ✅ OK |
| generate_curriculum_modules | Creates modules from curriculum topics | ✅ OK |
| generate_ai_modules_for_curriculum | Fallback AI generation | ✅ OK |
| generate_legacy_modules | Legacy exam-type modules | **USES LEGACY SYLLABUSES** |

### 5.2 LEGACY DEPENDENCIES

**generate_legacy_modules** (lines 128-235):
- References `JAMBSyllabus`, `SSCESyllabus`, `JSSSyllabus` from admin_syllabus
- Uses `course.exam_type` field
- This is for backward compatibility with old exam system

**DECISION NEEDED**: 
- If admin_syllabus is to be kept for data, function can stay
- If completely removing exam legacy, this function should be deprecated

---

## 6. Curriculum Service Analysis (core/services/curriculum.py)

### 6.1 Service Methods

| Method | Purpose | Performance Notes |
|--------|---------|-------------------|
| get_school_levels | Fetch all levels | ✅ Uses order_by |
| get_subjects_for_level | Fetch subjects for level | ✅ Uses order_by |
| get_curriculum | Fetch specific curriculum | ✅ Single query |
| get_topics_for_curriculum | Fetch topics | ✅ Uses select_related |
| get_legacy_mapping | Legacy exam mapping | **LEGACY** |
| migrate_legacy_course | Migrate old course | **LEGACY** |

### 6.2 LEGACY METHODS (Lines 106-119, 218-228)

These methods support legacy exam_type migration:
- `get_legacy_mapping`
- `migrate_legacy_course`

**RECOMMENDATION**: Keep for now but document as deprecated. Do not use in new code.

---

## 7. Templates Connected to Core

| Template | Purpose | Issues |
|----------|---------|--------|
| `templates/core/home.html` | Landing page | ✅ OK - well designed |
| `templates/core/dashboard.html` | User dashboard | References exams stats - needs update |
| `templates/errors/403.html` | 403 page | ✅ OK |
| `templates/errors/404.html` | 404 page | ✅ OK |
| `templates/errors/500.html` | 500 page | ✅ OK |
| `templates/exams/exam_center.html` | Exam center | **TO BE REMOVED** |

---

## 8. Production Readiness Checklist

| Item | Status | Action Required |
|------|--------|-----------------|
| DEBUG=False handling | ✅ | None |
| SECRET_KEY validation | ✅ | None |
| ALLOWED_HOSTS | ⚠️ | Ensure env var is set |
| CSRF_TRUSTED_ORIGINS | ⚠️ | Ensure env var is set |
| Database connection pooling | ⚠️ | Consider adding pool limits |
| Cache table creation | ❌ | Add to build.sh |
| Rate limit multi-worker | ❌ | Change to DB cache |
| AI timeouts | ✅ | Appropriate for 1GB |
| Memory cleanup | ✅ | gc.collect() implemented |
| Error logging | ✅ | Configured |
| Health check | ✅ | /health/ endpoint exists |

---

## 9. Items for Removal/Deprecation

### MUST REMOVE (when exams app deleted):
1. `core/views.py`: `exam_center_view` function (lines 38-55)
2. `core/views.py`: `from exams.models import Exam` import (line 17)
3. `core/views.py`: `exams_count` variable in dashboard_view (line 25)
4. `core/middleware.py`: `/exams/start` from RATE_LIMITED_PATHS (line 38)
5. `akili_project/urls.py`: `/exam-center/` URL pattern (line 22)
6. `akili_project/urls.py`: exams URL include (line 29)
7. `akili_project/settings.py`: 'exams' from INSTALLED_APPS (line 106)

### SHOULD REMOVE:
1. `core/views.py`: `profile_view` - duplicate of profiles app (lines 58-61)

### CONSIDER DEPRECATING:
1. `core/utils/ai_fallback.py`: `validate_ai_content` function - doubles AI costs
2. `core/utils/ai_module_generator.py`: `generate_legacy_modules` - legacy support
3. `core/services/curriculum.py`: `get_legacy_mapping`, `migrate_legacy_course`

---

## 10. Recommended Improvements

### 10.1 High Priority (Before Production)

1. **Add cache table creation to build.sh**:
   ```bash
   python manage.py createcachetable
   ```

2. **Fix rate limit cache backend** for multi-worker:
   ```python
   'ratelimit': {
       'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
       'LOCATION': 'ratelimit_cache',
   }
   ```

3. **Set required environment variables checklist**:
   - DATABASE_URL
   - SECRET_KEY
   - ALLOWED_HOSTS
   - CSRF_TRUSTED_ORIGINS
   - GEMINI_API_KEY
   - GROQ_API_KEY (optional fallback)
   - PAYSTACK_SECRET_KEY
   - LOG_DIR (optional)

### 10.2 Medium Priority (Recommended)

1. Make credit settings configurable via env vars
2. Remove duplicate profile_view from core
3. Add API key validation length checks
4. Consider removing validate_ai_content or making it optional

### 10.3 Low Priority (Nice to Have)

1. Add request ID to error logging for tracing
2. Add metrics endpoint for monitoring
3. Consider structured logging (JSON format) for production

---

## 11. Environment Variables Required

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| SECRET_KEY | YES | None | Raises error if not set in production |
| DEBUG | YES | False | Must be False in production |
| DATABASE_URL | YES | SQLite | Must be set for PostgreSQL |
| ALLOWED_HOSTS | YES | Empty | Comma-separated list |
| CSRF_TRUSTED_ORIGINS | YES | Empty | Full URLs with https:// |
| GEMINI_API_KEY | YES | Empty | Primary AI provider |
| GROQ_API_KEY | NO | Empty | Fallback AI provider |
| PAYSTACK_SECRET_KEY | YES | Empty | Payment processing |
| LOG_DIR | NO | ./logs | Production log directory |
| LOG_FILE_PATH | NO | ./logs/akili.log | Log file path |

---

**AUDIT COMPLETE FOR: akili_project + core**
**Next App: users**
