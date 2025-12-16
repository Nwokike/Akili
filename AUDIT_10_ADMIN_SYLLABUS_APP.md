# COMPREHENSIVE AUDIT: admin_syllabus App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM
## Status: **LEGACY - CONSIDER FOR DEPRECATION**

---

## 1. Overview & Ownership

**Purpose**: Stores legacy JAMB, SSCE, and JSS syllabus data. Used for legacy course creation before curriculum-based system.

**Files Reviewed**:
- `admin_syllabus/models.py` (48 lines)
- `admin_syllabus/admin.py`
- `admin_syllabus/apps.py`
- `admin_syllabus/fixtures/` (syllabuses_jamb.json, syllabuses_ssce.json, syllabuses_jss.json)

---

## 2. Data Models Analysis (admin_syllabus/models.py)

### 2.1 JAMBSyllabus Model

```python
class JAMBSyllabus(models.Model):
    subject = models.CharField(max_length=200, unique=True)
    topics = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'JAMB Syllabus'
        verbose_name_plural = 'JAMB Syllabuses'
```

### 2.2 SSCESyllabus Model

```python
class SSCESyllabus(models.Model):
    subject = models.CharField(max_length=200, unique=True)
    topics = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2.3 JSSSyllabus Model

```python
class JSSSyllabus(models.Model):
    subject = models.CharField(max_length=200, unique=True)
    topics = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2.4 MODEL ANALYSIS

All three models are identical structure with different verbose names.

**DESIGN CRITIQUE**: Could have been a single model with exam_type field:
```python
class LegacySyllabus(models.Model):
    EXAM_TYPES = [('JAMB', 'JAMB'), ('SSCE', 'SSCE'), ('JSS', 'JSS')]
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPES)
    subject = models.CharField(max_length=200)
    topics = models.JSONField(default=list)
    
    class Meta:
        unique_together = ['exam_type', 'subject']
```

But since this is legacy code marked for deprecation, no need to refactor.

---

## 3. Current Usage Analysis

### 3.1 Where admin_syllabus is Referenced

| File | Usage | Line(s) |
|------|-------|---------|
| `courses/views.py` | GetAvailableSubjectsView | 10, 393-400 |
| `courses/forms.py` | LegacyCourseCreationForm | 3, 126-136 |
| `core/utils/ai_module_generator.py` | generate_legacy_modules | 128-235 |
| `core/services/curriculum.py` | LegacyExamMapping | 106-119 |

### 3.2 Usage Flow

1. **Legacy Course Creation**:
   - User selects exam_type (JAMB/SSCE/JSS)
   - GetAvailableSubjectsView returns subjects from legacy syllabus
   - Course created with exam_type (no school_level/term)
   - generate_legacy_modules creates modules from syllabus topics

2. **New Curriculum Creation**:
   - User selects school_level (JS1-SS3)
   - User selects term and subject
   - Course created with school_level/term/curriculum
   - Modules created from curriculum topics

---

## 4. Deprecation Analysis

### 4.1 Is admin_syllabus Still Needed?

**With exams app removal**: The primary use case (JAMB/SSCE mock exams) is removed.

**For existing legacy courses**: May still be needed if any users have courses with exam_type set.

### 4.2 Migration Strategy

**Option A - Keep but Freeze**:
1. Remove from LegacyCourseCreationForm (no new legacy courses)
2. Keep models for existing data
3. Mark as deprecated in code
4. Remove in future version

**Option B - Full Migration**:
1. Run migrate_legacy_courses to convert existing courses
2. Remove all legacy code paths
3. Delete admin_syllabus app

**RECOMMENDATION**: Option A for now - safer for existing users.

---

## 5. Dependencies to Clean Up (Future)

### When Ready to Fully Remove:

1. **courses/views.py**:
   - Remove legacy path in GetAvailableSubjectsView
   - Remove JAMBSyllabus, SSCESyllabus, JSSSyllabus imports

2. **courses/forms.py**:
   - Remove LegacyCourseCreationForm class
   - Remove legacy syllabus imports

3. **core/utils/ai_module_generator.py**:
   - Remove generate_legacy_modules function
   - Remove legacy syllabus imports

4. **core/services/curriculum.py**:
   - Remove get_legacy_mapping method
   - Remove migrate_legacy_course method

5. **akili_project/settings.py**:
   - Remove 'admin_syllabus' from INSTALLED_APPS

---

## 6. Fixtures Analysis

### 6.1 File Sizes

| File | Subjects | Estimated Size |
|------|----------|----------------|
| syllabuses_jamb.json | ~30 | ~50KB |
| syllabuses_ssce.json | ~30 | ~50KB |
| syllabuses_jss.json | ~20 | ~40KB |

**Memory Impact**: Minimal - fixtures only loaded once.

### 6.2 Sample Structure

```json
{
  "model": "admin_syllabus.jambsyllabus",
  "pk": 1,
  "fields": {
    "subject": "Mathematics",
    "topics": [
      "Number and Numeration",
      "Algebra",
      "Geometry and Mensuration",
      ...
    ]
  }
}
```

---

## 7. Production Readiness Checklist

| Item | Status | Notes |
|------|--------|-------|
| Data integrity | ✅ | Syllabuses loaded from fixtures |
| Model stability | ✅ | No changes needed |
| Usage documentation | ⚠️ | Mark as deprecated |
| Migration path | ⚠️ | Document legacy course migration |
| Memory footprint | ✅ | Minimal |
| Security | ✅ | No security concerns |

---

## 8. Items for Removal/Deprecation

### IMMEDIATE ACTIONS:

1. **Mark as deprecated** in code comments
2. **Remove from course creation UI** (only show curriculum-based option)
3. **Keep models** for existing data

### FUTURE ACTIONS (After migration complete):

1. Run migrate_legacy_courses for all users
2. Remove Course.exam_type field
3. Remove admin_syllabus app entirely
4. Remove all legacy code paths

---

## 9. Recommended Approach

### For Production Launch:

1. **Keep admin_syllabus app** - for existing data
2. **Hide legacy course creation** - only show curriculum-based UI
3. **Document as deprecated** - in code and README
4. **Plan Phase 2 cleanup** - full removal after data migration

### Code Changes for Launch:

1. In course creation template, don't show exam_type option
2. In GetAvailableSubjectsView, deprecation warning in logs
3. In forms.py, add deprecation comment

---

## 10. Alternative: Convert to Archive

Instead of deleting, could convert to read-only archive:

```python
class ArchivedSyllabus(models.Model):
    """
    DEPRECATED: Legacy syllabus data from JAMB/SSCE/JSS system.
    Kept for historical reference only. Do not use in new features.
    """
    exam_type = models.CharField(max_length=10)
    subject = models.CharField(max_length=200)
    topics = models.JSONField(default=list)
    archived_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'archived_syllabuses'
```

---

**AUDIT COMPLETE FOR: admin_syllabus App**
**Status: LEGACY - Keep for now, remove in Phase 2**
**Next: Templates & Static Files Audit**
