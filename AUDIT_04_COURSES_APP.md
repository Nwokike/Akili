# COMPREHENSIVE AUDIT: courses App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM

---

## 1. Overview & Ownership

**Purpose**: Core learning functionality - course creation, module management, AI-generated lessons, and the "Ask Tutor" feature.

**Files Reviewed**:
- `courses/models.py` (119 lines)
- `courses/views.py` (403 lines)
- `courses/urls.py` (23 lines)
- `courses/forms.py` (160 lines)
- `courses/admin.py`
- `courses/tests.py`
- `courses/templates/courses/course_creation.html`
- `courses/templates/courses/dashboard.html`
- `courses/templates/courses/lesson_detail.html`
- `courses/templates/courses/module_listing.html`

---

## 2. Data Models Analysis (courses/models.py)

### 2.1 Course Model

```python
class Course(models.Model):
    EXAM_CHOICES = [
        ('JAMB', 'JAMB'),
        ('SSCE', 'SSCE'),
        ('JSS', 'JSS'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    exam_type = models.CharField(max_length=10, choices=EXAM_CHOICES, blank=True, null=True)  # LEGACY
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    school_level = models.ForeignKey('curriculum.SchoolLevel', ...)
    term = models.ForeignKey('curriculum.Term', ...)
    curriculum = models.ForeignKey('curriculum.SubjectCurriculum', ...)
```

### 2.2 LEGACY FIELD ANALYSIS

| Field | Status | Notes |
|-------|--------|-------|
| exam_type | **LEGACY** | Used for old JAMB/SSCE/JSS courses |
| school_level | NEW | For new curriculum-based courses |
| term | NEW | For new curriculum-based courses |
| curriculum | NEW | Links to structured curriculum |

**CRITICAL FINDING**: The model has BOTH legacy (exam_type) and new (school_level/term/curriculum) fields.

**RECOMMENDATION**: After removing exams app:
1. Run migration script to ensure all courses have school_level/term/curriculum
2. Remove exam_type field in future migration
3. Update Course.__str__ and display_name to not reference exam_type

### 2.3 Module Model

```python
class Module(models.Model):
    course = models.ForeignKey(Course, ...)
    title = models.CharField(max_length=300)
    order = models.IntegerField()
    syllabus_topic = models.CharField(max_length=500)
    lesson_content = models.ForeignKey('CachedLesson', null=True, blank=True, ...)
    topic = models.ForeignKey('curriculum.Topic', null=True, blank=True, ...)
```

✅ Good structure - links to both CachedLesson and curriculum Topic.

### 2.4 CachedLesson Model

```python
class CachedLesson(models.Model):
    topic = models.CharField(max_length=500)
    content = models.TextField()  # Contains HTML
    syllabus_version = models.CharField(max_length=50)
    report_count = models.IntegerField(default=0)  # For error reporting
    is_validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, ...)
```

**MEMORY CONCERN**: `content` is TextField containing full HTML lesson. For 1GB VM:
- Monitor average lesson size
- Consider adding max_length constraint
- Consider lazy loading in templates

**FEATURE: Report Count**
- Lessons with `report_count > 3` are auto-regenerated
- Good self-healing mechanism

---

## 3. Views Analysis (courses/views.py)

### 3.1 Views Inventory

| View | Class/Function | Auth | Purpose | Credits |
|------|----------------|------|---------|---------|
| CourseDashboardView | Class | Yes | List user courses | FREE |
| CourseCreationView | Class | Yes | Create new course | 5 credits |
| ModuleListingView | Class | Yes | List course modules | FREE |
| LessonDetailView | Class | Yes | View/generate lesson | FREE (cached) |
| AskTutorView | Class | Yes | AI Q&A | 1 credit |
| ReportErrorView | Class | Yes | Report lesson errors | FREE |
| DeleteCourseView | Class | Yes | Delete course | FREE |
| GetAvailableSubjectsView | Class | Yes | API for form | FREE |

### 3.2 CRITICAL ISSUES FOUND

#### Issue 1: CourseCreationView Credit Deduction (lines 63-88)

```python
with transaction.atomic():
    if not request.user.deduct_credits(5):
        messages.error(request, 'Insufficient credits...')
        return render(...)  # PROBLEM: Returns inside transaction!
```

**PROBLEM**: If deduct_credits fails, the return happens inside transaction.atomic(), but since no exception is raised, the transaction completes normally. However, the user.deduct_credits() already saved the user object.

**RECOMMENDATION**: Check credits BEFORE starting transaction:
```python
if not request.user.tutor_credits >= 5:
    messages.error(request, 'Insufficient credits...')
    return render(...)

with transaction.atomic():
    request.user.deduct_credits(5)
    # ... create course
```

#### Issue 2: ModuleListingView Performance (lines 97-152)

```python
modules = list(course.modules.all().order_by('order'))
module_ids = [m.id for m in modules]
all_attempts = QuizAttempt.objects.filter(user=request.user, module_id__in=module_ids)
```

**GOOD**: Uses single query for all quiz attempts (N+1 avoided).

**ISSUE**: If a course has many modules (15+), this creates large in-memory lists.

**RECOMMENDATION** for 1GB VM: Consider pagination for courses with many modules.

#### Issue 3: LessonDetailView AI Generation (lines 155-304)

**GOOD PRACTICES**:
- Uses bleach for HTML sanitization
- Uses markdown for rendering
- Validates AI content

**MEMORY CONCERNS**:
```python
raw_html = markdown.markdown(content_markdown, extensions=['extra', 'codehilite', 'tables', 'fenced_code'])
```
- Markdown processing of large content uses memory
- HTML sanitization creates string copies

**ISSUE**: `validate_ai_content()` call doubles AI API usage:
```python
validation_result = validate_ai_content(content_markdown)
```

**RECOMMENDATION**: Make validation optional or run asynchronously:
```python
# Skip validation for now - can be done via background task
is_validated = True  # Or add to task queue
```

#### Issue 4: Legacy Syllabus References (lines 10, 393-400)

```python
from admin_syllabus.models import JAMBSyllabus, SSCESyllabus, JSSSyllabus
```

**GetAvailableSubjectsView** returns subjects from legacy syllabuses when exam_type is provided:
```python
if exam_type == 'JAMB':
    subjects = list(JAMBSyllabus.objects.all().values_list('subject', flat=True))
```

**AFTER EXAM REMOVAL**: This legacy path should be removed.

### 3.3 AskTutorView Analysis (lines 307-345)

```python
if not request.user.deduct_credits(1):
    messages.error(...)
    return redirect(...)

result = call_ai_with_fallback(prompt, max_tokens=1000, subject=course.subject)

if result['success']:
    messages.success(request, f"AI Tutor: {result['content']}")
else:
    request.user.add_credits(1)  # Refund on failure
```

**GOOD**: Credits refunded on AI failure.

**ISSUE**: AI response displayed in messages.success() - what if response is very long?
- Django messages stored in session
- Large messages could bloat session data

**RECOMMENDATION**: Store AI response in session with truncation, or display inline in template.

---

## 4. URLs Analysis (courses/urls.py)

```python
app_name = 'courses'

urlpatterns = [
    path('', views.CourseDashboardView.as_view(), name='course_list'),
    path('new/', views.CourseCreationView.as_view(), name='create_course'),
    path('api/subjects/', views.GetAvailableSubjectsView.as_view(), name='get_subjects'),
    path('<int:course_id>/modules/', views.ModuleListingView.as_view(), name='module_listing'),
    path('module/<int:module_id>/lesson/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('module/<int:module_id>/ask/', views.AskTutorView.as_view(), name='ask_tutor'),
    path('module/<int:module_id>/report/', views.ReportErrorView.as_view(), name='report_error'),
    path('<int:course_id>/delete/', views.DeleteCourseView.as_view(), name='delete_course'),
]
```

✅ Good - has app_name namespace.

**SECURITY**: `delete_course` requires password confirmation - ✅ Good.

---

## 5. Forms Analysis (courses/forms.py)

### 5.1 CourseCreationForm (New Curriculum)

```python
class CourseCreationForm(forms.Form):
    school_level = forms.ChoiceField(...)
    term = forms.ChoiceField(...)
    subject = forms.ChoiceField(...)
```

**GOOD PRACTICES**:
- Validates subject availability for level
- Checks curriculum exists for combination
- Uses CurriculumService for data access

### 5.2 LegacyCourseCreationForm

```python
class LegacyCourseCreationForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['exam_type', 'subject']
```

**STATUS**: This is the legacy form for JAMB/SSCE/JSS courses.

**AFTER EXAM REMOVAL**: Remove this form entirely.

---

## 6. Templates Analysis

### 6.1 courses/dashboard.html

**Purpose**: List user's courses with stats.

**ISSUES TO CHECK**:
- Does it handle empty state gracefully? (Check template)
- Performance with many courses?

### 6.2 courses/course_creation.html

**Purpose**: Form for creating new course.

**FEATURES**:
- Dynamic subject loading via JavaScript
- Credit cost display (5 credits)

### 6.3 courses/module_listing.html

**Purpose**: Display course modules with lock/unlock status.

**FEATURES**:
- Module locking based on quiz pass status
- Progress indicators
- Quiz attempt display

### 6.4 courses/lesson_detail.html

**Purpose**: Display AI-generated lesson content.

**CRITICAL FEATURES**:
- KaTeX math rendering
- HTML content display (sanitized)
- "Ask Tutor" form
- Quiz start button
- Report error button

**SECURITY**: Ensure content is properly escaped even though bleach is used.

---

## 7. Production Readiness Checklist

| Item | Status | Action Required |
|------|--------|-----------------|
| Course creation transaction | ⚠️ | Fix credit check order |
| Lesson caching | ✅ | CachedLesson model works |
| AI fallback | ✅ | Uses 4-tier fallback |
| Credit system | ⚠️ | Race condition (see users audit) |
| HTML sanitization | ✅ | Bleach used correctly |
| KaTeX rendering | ✅ | Client-side rendering |
| Error reporting | ✅ | report_count auto-regeneration |
| Module locking | ✅ | Based on quiz pass status |
| Password for deletion | ✅ | Required |
| Legacy fields | ⚠️ | Plan removal of exam_type |

---

## 8. Items for Removal/Deprecation

### MUST REMOVE (with exams app):
1. `courses/forms.py`: `LegacyCourseCreationForm` class
2. `courses/views.py`: Legacy syllabus imports (line 10)
3. `courses/views.py`: exam_type paths in GetAvailableSubjectsView

### SHOULD REMOVE (future migration):
1. `courses/models.py`: `exam_type` field from Course
2. `courses/models.py`: `EXAM_CHOICES` constant
3. Update Course.display_name and __str__ to not reference exam_type

---

## 9. Recommended Improvements

### 9.1 High Priority (Before Production)

1. **Fix credit deduction order**:
   ```python
   # Check before transaction
   if request.user.tutor_credits < 5:
       messages.error(...)
       return render(...)
   
   with transaction.atomic():
       if not request.user.deduct_credits(5):
           raise ValueError("Credit deduction failed")
       # ... rest of creation
   ```

2. **Remove or defer validate_ai_content**:
   - Currently doubles AI API calls
   - Consider background validation or removal

3. **Add rate limiting to AskTutorView**:
   - Currently not in RATE_LIMITED_PATHS
   - Add `/courses/module/*/ask/` pattern

### 9.2 Medium Priority

1. Add lesson content size monitoring
2. Consider lazy loading for lesson content
3. Add module pagination for large courses
4. Truncate AI tutor responses in messages

### 9.3 Low Priority (Nice to Have)

1. Add lesson bookmarking
2. Add lesson highlighting/notes
3. Add offline lesson caching (PWA)
4. Add lesson audio narration option

---

## 10. Feature Analysis: Offline Content Download

User mentioned wanting offline content. Current status:

### What Exists:
- PWA manifest configured
- Service worker caches static assets
- Lessons stored in database (CachedLesson)

### What's Missing:
- No explicit "Download for Offline" button
- Service worker doesn't cache lesson content
- No offline indicator in UI

### RECOMMENDATION (Future Feature):
1. Add "Download Course" button in module listing
2. Cache lesson HTML in IndexedDB via JavaScript
3. Update service worker to intercept lesson requests
4. Add offline indicator and sync mechanism

---

## 11. Performance Optimization Opportunities

### For 1GB RAM VM:

1. **Lesson Content Compression**:
   - Consider gzip compression for stored lesson HTML
   - WhiteNoise already handles static compression

2. **Query Optimization**:
   ```python
   # Current (good)
   user_courses = Course.objects.filter(user=request.user).select_related(
       'school_level', 'term', 'curriculum'
   )
   ```

3. **Caching Strategy**:
   - Add cache decorators for API endpoints
   - Cache curriculum data (rarely changes)

---

**AUDIT COMPLETE FOR: courses App**
**Next App: quizzes**
