# COMPREHENSIVE AUDIT: curriculum App

## Audit Date: December 16, 2025
## Auditor: Production Readiness Review
## Target Environment: 1GB RAM Google Cloud VM

---

## 1. Overview & Ownership

**Purpose**: Manages the Nigerian secondary school curriculum structure - school levels (JS1-SS3), subjects, terms, weeks, topics, and student enrolments.

**Files Reviewed**:
- `curriculum/models.py` (187 lines)
- `curriculum/views.py` (1 line - empty)
- `curriculum/urls.py` (not present)
- `curriculum/admin.py`
- `curriculum/fixtures/initial_data.json`
- `curriculum/fixtures/subjects.json`
- `curriculum/management/commands/seed_curriculum.py`
- `curriculum/management/commands/migrate_legacy_courses.py`
- `curriculum/management/commands/map_syllabuses.py`
- `curriculum/tests/test_curriculum_service.py`

---

## 2. Data Models Analysis (curriculum/models.py)

### 2.1 Model Hierarchy

```
AcademicSession
    └── StudentProgramme
            └── SubjectEnrolment

SchoolLevel (JS1-SS3)
    └── Subject (linked via M2M)
            └── SubjectCurriculum (per level/subject/term)
                    └── Topic (per week)

Term (First/Second/Third)
    └── Week (1-14 per term)
            └── Topic

LegacyExamMapping (LEGACY - for migration)
```

### 2.2 Model Details

#### AcademicSession

```python
class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g., 2024/2025
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
```

**ISSUES**:
- No validation that only one session is_active at a time
- No date overlap validation

**RECOMMENDATION**:
```python
def save(self, *args, **kwargs):
    if self.is_active:
        AcademicSession.objects.filter(is_active=True).update(is_active=False)
    super().save(*args, **kwargs)
```

#### SchoolLevel

```python
class SchoolLevel(models.Model):
    name = models.CharField(max_length=10, unique=True)  # JS1, JS2, etc.
    level_order = models.IntegerField(unique=True)  # 1-6
    level_type = models.CharField(max_length=10, choices=LEVEL_TYPE_CHOICES)
```

✅ Good structure. Appropriate for 6 levels.

#### Subject

```python
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    school_levels = models.ManyToManyField(SchoolLevel, related_name='subjects')
    is_science_subject = models.BooleanField(default=False)
```

✅ Good - M2M allows subjects available at multiple levels.

**NOTE**: `is_science_subject` is used for LaTeX/formula handling in AI prompts.

#### Term

```python
class Term(models.Model):
    name = models.CharField(max_length=20, unique=True)
    order = models.IntegerField(unique=True)
    total_weeks = models.IntegerField(default=14)
    instructional_weeks = models.IntegerField(default=12)
    exam_weeks = models.IntegerField(default=2)
```

✅ Good structure for Nigerian academic calendar.

#### Week

```python
class Week(models.Model):
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.IntegerField()
    week_type = models.CharField(max_length=15, choices=WEEK_TYPE_CHOICES)
```

**WEEK_TYPE_CHOICES**:
- INSTRUCTIONAL
- REVISION
- EXAM

✅ Good - allows flexibility in week types.

#### SubjectCurriculum

```python
class SubjectCurriculum(models.Model):
    school_level = models.ForeignKey(SchoolLevel, ...)
    subject = models.ForeignKey(Subject, ...)
    term = models.ForeignKey(Term, ...)
    version = models.CharField(max_length=50, default="2025")
    overview = models.TextField(blank=True)
    learning_objectives = models.JSONField(default=list, blank=True)
```

**Unique Together**: `['school_level', 'subject', 'term', 'version']`

✅ Good - allows versioned curricula.

#### Topic

```python
class Topic(models.Model):
    curriculum = models.ForeignKey(SubjectCurriculum, ...)
    week = models.ForeignKey(Week, ...)
    title = models.CharField(max_length=300)
    order = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    learning_objectives = models.JSONField(default=list, blank=True)
    key_concepts = models.JSONField(default=list, blank=True)
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES)
    estimated_duration_minutes = models.IntegerField(default=45)
```

✅ Comprehensive topic structure.

**ISSUE**: `learning_objectives` and `key_concepts` are JSONFields - could be large:
- Memory concern for 1GB VM
- **RECOMMENDATION**: Ensure fixtures don't have excessively large JSON

#### StudentProgramme

```python
class StudentProgramme(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    academic_session = models.ForeignKey(AcademicSession, ...)
    school_level = models.ForeignKey(SchoolLevel, ...)
```

**Unique Together**: `['user', 'academic_session', 'school_level']`

**ISSUE**: A student can only be enrolled in ONE level per session - is this intentional?
- What if student changes class mid-year?
- **RECOMMENDATION**: Consider adding `is_active` flag instead of unique constraint

#### SubjectEnrolment

```python
class SubjectEnrolment(models.Model):
    programme = models.ForeignKey(StudentProgramme, ...)
    subject = models.ForeignKey(Subject, ...)
    curriculum = models.ForeignKey(SubjectCurriculum, ...)
    current_term = models.ForeignKey(Term, ...)
    current_week = models.ForeignKey(Week, ...)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
```

✅ Good progress tracking structure.

#### LegacyExamMapping (LEGACY)

```python
class LegacyExamMapping(models.Model):
    exam_type = models.CharField(...)  # JAMB, SSCE, JSS
    subject_name = models.CharField(...)
    school_level = models.ForeignKey(SchoolLevel, ...)
    subject = models.ForeignKey(Subject, ...)
    curriculum = models.ForeignKey(SubjectCurriculum, ...)
```

**STATUS**: Used for migrating old exam-type courses to new curriculum system.

**RECOMMENDATION**: Keep for data migration purposes, but:
- Mark as deprecated in code
- Consider removing after all legacy data migrated

---

## 3. Database Indexes Analysis

### Current Indexes (from migrations)

The migrations show indexes were added and some removed. Current state:

| Model | Field(s) | Index Status |
|-------|----------|--------------|
| AcademicSession | is_active | ❓ Check |
| SchoolLevel | level_order | Implicit (unique) |
| Subject | code | Implicit (unique) |
| Week | (term, week_number) | Implicit (unique_together) |
| SubjectCurriculum | (school_level, subject, term, version) | Implicit (unique_together) |
| Topic | (curriculum, week, order) | ❓ Check |
| StudentProgramme | user | ❓ Check - high query frequency |
| SubjectEnrolment | (programme, subject) | Implicit (unique_together) |

**RECOMMENDATION**: Add explicit indexes for:
```python
class StudentProgramme(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

class Topic(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['curriculum', 'week']),
        ]
```

---

## 4. Views Analysis (curriculum/views.py)

```python
from django.shortcuts import render
```

**STATUS**: Empty file - no views defined.

**ANALYSIS**: Curriculum data is accessed via:
1. `core/services/curriculum.py` - CurriculumService
2. `courses/views.py` - Course creation forms
3. Django admin interface

**CONCLUSION**: This is intentional - curriculum is a data layer, not user-facing.

---

## 5. Management Commands Analysis

### 5.1 seed_curriculum.py

**Purpose**: Seeds initial curriculum data from fixtures.

**Status**: Must be run after fresh install (documented in README).

**CRITICAL**: Ensure this is in build.sh for deployment:
```bash
python manage.py seed_curriculum
```

### 5.2 migrate_legacy_courses.py

**Purpose**: Migrates old exam-type courses to new curriculum structure.

**Status**: One-time migration script.

**RECOMMENDATION**: Run before deprecating exams app.

### 5.3 map_syllabuses.py

**Purpose**: Maps old syllabus content to new curriculum.

**Status**: One-time migration script.

---

## 6. Fixtures Analysis

### 6.1 initial_data.json

**Contents**: 
- School levels (JS1-SS3)
- Terms (First, Second, Third)
- Weeks (14 per term)
- Academic sessions

**Size**: Moderate - should load quickly.

### 6.2 subjects.json

**Contents**: 31 subjects as documented in README.

**Expected subjects** (from README):
- Core: English, Mathematics, Civic Education
- Sciences: Physics, Chemistry, Biology
- Arts: Literature, History, Government
- Commerce: Economics, Commerce, Accounting
- etc.

**RECOMMENDATION**: Verify all 31 subjects are present and correctly linked to school levels.

---

## 7. Production Readiness Checklist

| Item | Status | Action Required |
|------|--------|-----------------|
| Fixtures load without error | ❓ | Test: `python manage.py seed_curriculum` |
| Foreign key integrity | ✅ | Properly configured |
| Cascade delete safety | ✅ | Uses SET_NULL where appropriate |
| JSONField size limits | ⚠️ | Monitor in production |
| Query optimization | ⚠️ | Add missing indexes |
| Academic session uniqueness | ❌ | Add is_active constraint |
| Legacy migration ready | ⚠️ | Run migrate_legacy_courses before go-live |

---

## 8. Items for Removal/Deprecation

### CONSIDER DEPRECATING (after migration complete):
1. `LegacyExamMapping` model - only needed for migration
2. `migrate_legacy_courses.py` - one-time use
3. `map_syllabuses.py` - one-time use

### KEEP:
All other models are core to the new curriculum system.

---

## 9. Recommended Improvements

### 9.1 High Priority (Before Production)

1. **Add seed_curriculum to build.sh**:
   ```bash
   python manage.py seed_curriculum
   ```

2. **Ensure only one active session**:
   ```python
   class AcademicSession(models.Model):
       def save(self, *args, **kwargs):
           if self.is_active:
               AcademicSession.objects.exclude(pk=self.pk).update(is_active=False)
           super().save(*args, **kwargs)
   ```

3. **Run legacy migration** before removing exams app:
   ```bash
   python manage.py migrate_legacy_courses
   ```

### 9.2 Medium Priority

1. Add database indexes for frequent queries
2. Document curriculum data structure for content team
3. Add admin actions for bulk curriculum updates

### 9.3 Low Priority (Nice to Have)

1. Add curriculum version comparison feature
2. Add curriculum export/import functionality
3. Add curriculum validation command (check all subjects have topics)

---

## 10. Data Integrity Verification Needed

Before production, verify:

1. **All 6 school levels exist**: JS1, JS2, JS3, SS1, SS2, SS3
2. **All 3 terms exist**: First Term, Second Term, Third Term
3. **14 weeks per term**: 12 instructional + 2 exam
4. **All 31 subjects exist** with correct level assignments
5. **SubjectCurriculum exists** for each subject/level/term combination
6. **Topics exist** for each curriculum

**Verification Command** (create if not exists):
```bash
python manage.py verify_curriculum_integrity
```

---

## 11. Feature Analysis: Timetable/Schedule Support

The user mentioned wanting timetable/schedule features. Current curriculum structure supports this:

### What's Already Available:
- Week structure (1-14)
- Week types (Instructional, Revision, Exam)
- Topics per week
- Estimated duration per topic

### What's Missing:
- No day-of-week assignment
- No time slot assignment
- No recurring schedule model

### RECOMMENDATION (Future Feature):
```python
class ScheduleSlot(models.Model):
    enrolment = models.ForeignKey(SubjectEnrolment, ...)
    day_of_week = models.IntegerField(choices=DAYS)  # 0=Monday, etc.
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=True)
```

---

**AUDIT COMPLETE FOR: curriculum App**
**Next App: courses**
