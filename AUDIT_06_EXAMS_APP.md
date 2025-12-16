# COMPREHENSIVE AUDIT: exams App (TO BE REMOVED)

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Status: **MARKED FOR DELETION**

---

## 1. Overview

**Purpose**: Full mock exams (20 questions) for courses. Costs 5 credits per attempt.

**User Request**: "Let's remove and delete everything about the old exam app"

**Files to Delete**:
- `exams/` (entire directory)
- `templates/exams/` (entire directory)

---

## 2. Current Files Inventory

### 2.1 App Files
| File | Lines | Purpose |
|------|-------|---------|
| `exams/__init__.py` | - | Package init |
| `exams/admin.py` | - | Admin registration |
| `exams/apps.py` | - | App config |
| `exams/models.py` | 50 | Exam + ExamQuestion models |
| `exams/views.py` | 217 | start_exam, take_exam, results |
| `exams/urls.py` | 10 | URL patterns |
| `exams/tests.py` | - | Tests |
| `exams/migrations/` | 5 files | Database migrations |

### 2.2 Template Files
| File | Purpose |
|------|---------|
| `templates/exams/exam_center.html` | Exam center page (in core templates) |
| `exams/templates/exams/take_exam.html` | Take exam form |
| `exams/templates/exams/results.html` | Exam results display |

---

## 3. Dependencies Analysis

### 3.1 Code References to exams App

| File | Reference | Line(s) | Action Required |
|------|-----------|---------|-----------------|
| `akili_project/settings.py` | `'exams'` in INSTALLED_APPS | 106 | Remove |
| `akili_project/urls.py` | `path('exams/', include('exams.urls'))` | 29 | Remove |
| `akili_project/urls.py` | `path('exam-center/', ...)` | 22 | Remove |
| `core/views.py` | `from exams.models import Exam` | 17 | Remove import |
| `core/views.py` | `exam_center_view` function | 38-55 | Remove function |
| `core/views.py` | `exams_count` in dashboard_view | 25 | Remove variable |
| `core/middleware.py` | `/exams/start` in RATE_LIMITED_PATHS | 38 | Remove path |
| `courses/views.py` | References to legacy syllabus | 10, 393-400 | Review (may be for course creation) |

### 3.2 Template References

| Template | Reference | Action |
|----------|-----------|--------|
| `templates/core/dashboard.html` | `{{ exams_count }}` | Remove stat card |
| `templates/partials/sidebar.html` | Exam center link? | Check and remove |
| `templates/partials/bottom_nav.html` | Exam center link? | Check and remove |

### 3.3 Database Tables

Tables created by exams app:
- `exams_exam` (or similar)
- `exams_examquestion`

**IMPORTANT**: These tables will have user data!

---

## 4. Data Migration Considerations

### 4.1 Current Exam Data

Before deletion, consider:
1. **User Exam History**: Do users lose their exam history?
2. **Analytics**: Any reporting dependent on exam data?
3. **Backup**: Should export exam data before deletion?

### 4.2 RECOMMENDATION

**Option A - Hard Delete (Recommended for fresh start)**:
1. Back up database
2. Run migration to drop exam tables
3. Delete exams app directory
4. Remove all code references
5. Deploy

**Option B - Soft Deprecation**:
1. Remove from INSTALLED_APPS
2. Keep database tables (orphaned)
3. Remove code references
4. Delete app directory later

**User seems to prefer Option A** based on "remove and delete everything about the old exam app".

---

## 5. Step-by-Step Removal Plan

### Phase 1: Code Cleanup (No database changes)

1. **Remove from INSTALLED_APPS**:
   ```python
   # akili_project/settings.py line 106
   # Remove: 'exams',
   ```

2. **Remove URL patterns**:
   ```python
   # akili_project/urls.py
   # Remove: path('exam-center/', core_views.exam_center_view, name='exam_center'),
   # Remove: path('exams/', include('exams.urls')),
   ```

3. **Clean core/views.py**:
   - Remove: `from exams.models import Exam`
   - Remove: `exam_center_view` function
   - Remove: `exams_count` from dashboard_view

4. **Clean core/middleware.py**:
   - Remove `/exams/start` from RATE_LIMITED_PATHS

5. **Update templates**:
   - Remove exam stats from dashboard
   - Remove exam center links from navigation

### Phase 2: Template Cleanup

1. Delete `templates/exams/exam_center.html`
2. Delete `exams/templates/exams/` directory

### Phase 3: App Directory Deletion

1. Delete entire `exams/` directory

### Phase 4: Database Migration

Create migration to drop tables:
```python
# Create: curriculum/migrations/XXXX_remove_exam_tables.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('curriculum', 'previous_migration'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS exams_examquestion;",
            reverse_sql="-- Cannot recreate"
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS exams_exam;",
            reverse_sql="-- Cannot recreate"
        ),
    ]
```

---

## 6. Exam Functionality to Migrate

### What exams app provides that quizzes doesn't:

| Feature | Exams | Quizzes | Gap? |
|---------|-------|---------|------|
| Questions per attempt | 20 | 5 | Maybe add "long quiz" option |
| Cost | 5 credits | Free | Different model |
| Full course coverage | Yes | Per module | Different scope |
| Time tracking | Started/completed | Same | No gap |

### RECOMMENDATION: 
Keep quizzes as-is. The exam functionality was for JAMB/SSCE prep which is being deprecated.

---

## 7. Verification Checklist

After removal, verify:

| Check | Command/Action | Expected Result |
|-------|----------------|-----------------|
| App not in settings | Grep for 'exams' | Not found |
| URLs don't reference exams | `python manage.py show_urls` | No /exams/ routes |
| No import errors | `python manage.py check` | No errors |
| Migrations complete | `python manage.py migrate` | Success |
| Dashboard loads | Visit /dashboard/ | No errors, no exam stats |
| Exam center 404 | Visit /exam-center/ | 404 page |

---

## 8. Rollback Plan

If issues occur:
1. Restore from git (code)
2. Restore from database backup (data)
3. Re-add 'exams' to INSTALLED_APPS
4. Re-add URL patterns

---

## 9. Related Legacy Items to Review

With exams removal, also review:

1. **admin_syllabus app**: Contains JAMB/SSCE/JSS syllabuses
   - Used by: course module generation (legacy path)
   - Consider: Keep for now, deprecate later

2. **Course.exam_type field**: Legacy field in courses model
   - Used by: display_name, level_type properties
   - Consider: Remove in future migration after data cleanup

3. **LegacyExamMapping model**: In curriculum app
   - Used for: Migrating old courses
   - Consider: Remove after migration complete

---

## 10. Timeline Recommendation

| Day | Action |
|-----|--------|
| Day 1 | Code cleanup (Phase 1-3) |
| Day 1 | Test in development |
| Day 2 | Database migration (Phase 4) |
| Day 2 | Full testing |
| Day 3 | Deploy to production |
| Day 3 | Verify all functionality |

---

## 11. Files Summary

### TO DELETE:
```
exams/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tests.py
├── urls.py
├── views.py
├── migrations/
│   ├── __init__.py
│   ├── 0001_initial.py
│   ├── 0002_initial.py
│   ├── 0003_migrate_exam_to_course.py
│   ├── 0004_add_indexes.py
│   └── 0005_remove_exam_exams_user_course_idx_and_more.py
└── templates/
    └── exams/
        ├── results.html
        └── take_exam.html

templates/exams/
└── exam_center.html
```

### TO MODIFY:
```
akili_project/settings.py
akili_project/urls.py
core/views.py
core/middleware.py
templates/core/dashboard.html
templates/partials/sidebar.html (check)
templates/partials/bottom_nav.html (check)
```

---

**AUDIT COMPLETE FOR: exams App**
**Status: READY FOR REMOVAL**
**Next App: assessments**
