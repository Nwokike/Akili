# Akili Platform - Comprehensive Rebranding Assessment & Implementation Plan

## Executive Summary

This document provides a complete technical assessment of the Akili educational platform, currently focused on exam preparation (JAMB, SSCE, JSS), and outlines a phased plan to rebrand it as a comprehensive secondary education platform covering JS1 through SS3.

**Key Constraints:**
- Target hosting: 1GB RAM VM (Render)
- Maintain backwards compatibility with existing users
- Preserve the AI-powered learning approach

---

## Part 1: Current Architecture Assessment

### 1.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend Framework | Django | 5.2.8 |
| Database | PostgreSQL | Latest |
| Frontend CSS | Tailwind CSS | CDN-based |
| AI Integration | Google Gemini + Groq | Gemini 2.5 Flash (primary) |
| Payment Gateway | Paystack | REST API |
| Static Files | Whitenoise | 6.6.0 |
| WSGI Server | Gunicorn | 21.2.0 |
| Math Rendering | KaTeX | 0.16.9 |

### 1.2 Django Apps Structure

| App | Purpose | Key Models |
|-----|---------|------------|
| `core` | Dashboard, home, error pages, context processors | None (utility app) |
| `users` | Authentication, custom user model, referrals | CustomUser |
| `admin_syllabus` | Official exam syllabuses | JAMBSyllabus, SSCESyllabus, JSSSyllabus |
| `courses` | Course & module management, AI content generation | Course, Module, CachedLesson |
| `quizzes` | Practice quiz generation and tracking | QuizAttempt |
| `exams` | Mock exam generation and results | Exam, ExamQuestion |
| `payments` | Paystack credit purchases | Payment |
| `profiles` | User profile management, account deletion | None (uses CustomUser) |

### 1.3 Current Data Model Analysis

**Exam-Centric Structure (Problem for Rebranding):**

```
Course.EXAM_CHOICES = [('JAMB', 'JAMB'), ('SSCE', 'SSCE'), ('JSS', 'JSS')]
```

- `Course` model uses `exam_type` field tied to exam names, not class levels
- Three separate syllabus tables (JAMBSyllabus, SSCESyllabus, JSSSyllabus) with no unified structure
- All downstream logic (course creation, AI prompts, quizzes, exams) depends on these exam types
- No concept of class levels (JS1, JS2, JS3, SS1, SS2, SS3) or terms

### 1.4 AI Integration Architecture

**4-Tier Fallback System:**
1. Gemini 2.5 Flash (Free, Fast) - Primary
2. Gemini Pro (Paid, High Quality) - First fallback
3. Groq API (Free, Fast) - Second fallback
4. Circuit Breaker (Graceful error message)

**Current Implementation Issues:**
- Synchronous 5000-token AI calls that block request threads
- Full JSON responses held in Python memory before database write
- No streaming or pagination for large content
- Subject-aware LaTeX instructions (good practice)
- Automatic credit refunds on AI failure (good practice)

### 1.5 Credit System

| Action | Credit Cost |
|--------|-------------|
| Course Creation | 5 credits |
| Mock Exam (20 questions) | 5 credits |
| AI Tutor Question | 1 credit |
| Practice Quiz | FREE |

**Daily Allocation:**
- 10 free credits daily (resets at midnight WAT)
- +2 daily limit per successful referral (max 30)
- Purchased credits never expire

---

## Part 2: Rebranding Requirements Analysis

### 2.1 Target Class Structure

The Nigerian secondary education system:

| Level | Classes | Duration |
|-------|---------|----------|
| Junior Secondary School (JSS) | JS1, JS2, JS3 | 3 years |
| Senior Secondary School (SSS) | SS1, SS2, SS3 | 3 years |

### 2.2 Core Subjects by Level

**Junior Secondary (JS1-JS3):**
- English Language
- Mathematics
- Basic Science
- Basic Technology
- Social Studies
- Civic Education
- Agricultural Science
- Business Studies
- Computer Studies/ICT
- French (optional)
- Fine Art
- Home Economics
- Physical & Health Education
- Religious Studies (CRS/IRS)
- Nigerian Languages (Yoruba/Igbo/Hausa)

**Senior Secondary (SS1-SS3):**
- English Language
- Mathematics
- Physics
- Chemistry
- Biology
- Economics
- Government
- Literature in English
- History
- Geography
- Agricultural Science
- Commerce
- Accounting/Financial Accounting
- Computer Science
- Further Mathematics
- Technical Drawing
- Civic Education
- Yoruba/Igbo/Hausa

### 2.3 Areas Requiring Changes

| Component | Current State | Required Change |
|-----------|---------------|-----------------|
| Course.exam_type | JAMB/SSCE/JSS choices | Class levels (JS1-SS3) |
| Syllabus Models | 3 separate tables | Unified curriculum structure |
| Course Form | Exam type dropdown | Class level + term + subject |
| AI Prompts | Exam-focused language | Class-level curriculum language |
| Landing Page | "Exam preparation" messaging | "Complete education" messaging |
| Branding | "JAMB, WAEC, NECO" references | "JS1 to SS3" references |

---

## Part 3: Technical Assessment & Improvements

### 3.1 Memory Optimization for 1GB RAM VM

**Current Concerns:**
```python
# settings.py - Current cache config
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'akili-cache',
    }
}
```

**Recommended Gunicorn Configuration:**
```bash
# For 1GB RAM VM
gunicorn --bind=0.0.0.0:5000 \
         --workers=2 \
         --threads=2 \
         --worker-class=gthread \
         --max-requests=1000 \
         --max-requests-jitter=50 \
         --timeout=120 \
         --keepalive=5 \
         akili_project.wsgi:application
```

**Database Connection Pooling:**
```python
# settings.py - Recommended
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=60,  # Reduce from 600
        conn_health_checks=True,
    )
}
```

**AI Response Optimization:**
- Reduce max_tokens from 5000 to 3000 where possible
- Implement streaming for lesson content
- Write AI responses directly to database in chunks
- Add request timeout guards (currently 50-60s)

### 3.2 Code Quality Issues

**Found Issues:**

1. **Duplicate dark mode classes in sidebar.html:**
```html
<!-- Line 3 - Duplicate classes -->
<aside class="sidebar ... dark:bg-gray-800 dark:bg-gray-800 ... dark:border-gray-700 dark:border-gray-700">
```

2. **Inconsistent dashboard view locations:**
   - `users/views.py` has `dashboard_view` (line 84-89)
   - `core/views.py` has `dashboard_view` (line 13-35) - this is the active one

3. **Missing type hints throughout codebase**

4. **No request rate limiting** (noted as "ready but disabled" in docs)

5. **LSP diagnostics show 69 issues across 23 files** - primarily missing imports for type checking

### 3.3 Security Assessment

**Positive Findings:**
- CSRF protection enabled on all forms
- Password hashing via Django's bcrypt
- HTTPS enforcement in production
- Secure cookie settings (HttpOnly, SameSite, Secure)
- HTML sanitization with bleach for AI content
- SQL injection protection via Django ORM

**Areas for Improvement:**
- Add rate limiting (currently disabled)
- Implement request size limits for AI endpoints
- Add audit logging for payments and referrals
- Consider Content Security Policy headers

### 3.4 Missing Features for Complete Platform

| Feature | Priority | Description |
|---------|----------|-------------|
| Term/Semester Structure | High | Academic calendar alignment |
| Continuous Assessment | High | Track student progress over time |
| Teacher Dashboard | Medium | For schools/tutoring centers |
| Parent Visibility | Medium | Progress reports for parents |
| Content Moderation | Medium | Review AI-generated content |
| Timetable/Schedule | Low | Study planning tools |
| Offline Content Download | Low | Pre-cache lessons for offline |
| Analytics Dashboard | Low | Learning insights |

---

## Part 4: Proposed New Data Model

### 4.1 Nigerian Academic Calendar Structure

**Term Structure (3 Terms per Academic Year):**

| Term | Typical Duration | Instructional Weeks | Exam Weeks |
|------|------------------|---------------------|------------|
| First Term | September - December | 12 weeks | 2 weeks |
| Second Term | January - April | 12 weeks | 2 weeks |
| Third Term | May - July | 10 weeks | 2 weeks |

**Weekly Breakdown (per Term):**
- Weeks 1-12: Instructional content
- Weeks 13-14: Revision and Examinations
- Total: ~14 weeks per term

### 4.2 Curriculum Schema (ERD)

```
AcademicSession
├── id (PK)
├── name (e.g., "2024/2025")
├── start_date
├── end_date
├── is_active (boolean)
└── created_at

SchoolLevel
├── id (PK)
├── name (JS1, JS2, JS3, SS1, SS2, SS3)
├── level_order (1-6)
├── level_type (JUNIOR, SENIOR)
└── description

Subject
├── id (PK)
├── name
├── code (e.g., "ENG", "MTH", "PHY")
├── school_levels (M2M → SchoolLevel)
├── is_science_subject (for LaTeX handling)
└── description

Term
├── id (PK)
├── name (First Term, Second Term, Third Term)
├── order (1, 2, 3)
├── total_weeks (default: 14)
├── instructional_weeks (default: 12)
├── exam_weeks (default: 2)
└── description

Week
├── id (PK)
├── term (FK → Term)
├── week_number (1-14)
├── week_type (INSTRUCTIONAL, REVISION, EXAM)
├── title (e.g., "Week 1: Introduction")
└── description

SubjectCurriculum
├── id (PK)
├── school_level (FK → SchoolLevel)
├── subject (FK → Subject)
├── term (FK → Term)
├── version (e.g., "2025")
├── overview (text description)
├── learning_objectives (JSON array)
└── last_updated

Topic
├── id (PK)
├── curriculum (FK → SubjectCurriculum)
├── week (FK → Week)
├── title
├── order (within week)
├── description
├── learning_objectives (JSON)
├── key_concepts (JSON array)
├── difficulty_level (BASIC, INTERMEDIATE, ADVANCED)
└── estimated_duration_minutes

# Student Enrolment (replaces Course)
StudentProgramme
├── id (PK)
├── user (FK → CustomUser)
├── academic_session (FK → AcademicSession)
├── school_level (FK → SchoolLevel)
├── created_at
└── is_active

# Subject Enrolment within a Programme
SubjectEnrolment
├── id (PK)
├── programme (FK → StudentProgramme)
├── subject (FK → Subject)
├── current_term (FK → Term)
├── current_week (FK → Week)
├── progress_percentage
├── created_at
└── last_accessed

# Module (AI-generated content per Topic)
Module
├── id (PK)
├── subject_enrolment (FK → SubjectEnrolment)
├── topic (FK → Topic)
├── title
├── order
├── syllabus_topic
├── lesson_content (FK → CachedLesson, nullable)
└── created_at

# Legacy Mapping (for backwards compatibility)
LegacyExamMapping
├── id (PK)
├── exam_type (JAMB, SSCE, JSS)
├── subject_name
├── school_level (FK → SchoolLevel)
├── subject (FK → Subject)
├── curriculum (FK → SubjectCurriculum)
└── notes
```

### 4.3 Weekly Content Organization

**How Topics Map to Weeks:**

| Week | Type | Content Focus |
|------|------|---------------|
| 1 | Instructional | Introduction & Foundation concepts |
| 2-4 | Instructional | Core concepts (progressive difficulty) |
| 5-6 | Instructional | Intermediate topics + practice |
| 7 | Instructional | Mid-term revision & assessment |
| 8-10 | Instructional | Advanced topics |
| 11-12 | Instructional | Complex applications & integration |
| 13 | Revision | Comprehensive revision |
| 14 | Exam | Terminal examination |

**Example: Mathematics JS1 First Term**
```
Week 1: Number Systems - Counting and Place Value
Week 2: Number Systems - Whole Numbers Operations
Week 3: Number Systems - Fractions (Introduction)
Week 4: Number Systems - Fractions (Operations)
Week 5: Algebraic Thinking - Introduction to Variables
Week 6: Algebraic Thinking - Simple Equations
Week 7: MID-TERM ASSESSMENT
Week 8: Geometry - Basic Shapes
Week 9: Geometry - Angles and Lines
Week 10: Measurement - Length and Perimeter
Week 11: Measurement - Area
Week 12: Data Handling - Collection and Organization
Week 13: REVISION
Week 14: EXAMINATION
```

### 4.4 AI Prompt Engineering Updates

**Current Prompt (Exam-focused):**
```python
prompt = f"""Based on the official {course.exam_type} syllabus for {course.subject}..."""
```

**New Prompt (Term/Week-focused):**
```python
prompt = f"""You are creating lesson content for Nigerian secondary school students.

Context:
- Class Level: {school_level.name} ({school_level.level_type})
- Subject: {subject.name}
- Term: {term.name} (Weeks {term.instructional_weeks} of instruction)
- Week: {week.week_number} ({week.week_type})
- Topic: {topic.title}
- Difficulty: {topic.difficulty_level}
- Previous Topics: {previous_topics_summary}

Nigerian Curriculum Alignment:
{topic.learning_objectives}

Generate a comprehensive lesson appropriate for Week {week.week_number} of {term.name}.
Build on concepts from previous weeks. The difficulty should match {topic.difficulty_level} level.
..."""
```

### 4.5 Course Creation Flow (Updated)

**Current Flow:**
1. User selects Exam Type (JAMB/SSCE/JSS)
2. User selects Subject
3. System generates 15 modules

**New Flow:**
1. User selects Class Level (JS1-SS3)
2. User selects Academic Session (2024/2025)
3. User selects Term (First/Second/Third)
4. User selects Subject
5. System loads predefined weekly topics from SubjectCurriculum
6. System generates modules for each week's topics

---

## Part 5: Phased Implementation Plan

### Phase 1: Foundation (Week 1-2) - COMPLETED
**Focus: Data Model & Infrastructure**

| Task | Description | Files Affected | Status |
|------|-------------|----------------|--------|
| 1.1 | Create new `curriculum` Django app | New app | DONE |
| 1.2 | Design and create new models (SchoolLevel, Subject, Term, Curriculum, Topic) | curriculum/models.py | DONE |
| 1.3 | Create legacy mapping table | curriculum/models.py | DONE |
| 1.4 | Write data migration scripts | migrations/ | DONE |
| 1.5 | Seed Nigerian curriculum data for all 6 class levels | fixtures/ | DONE |
| 1.6 | Update settings for 1GB RAM optimization | akili_project/settings.py | DONE |
| 1.7 | Update render.yaml with optimized gunicorn settings | render.yaml | DONE |

**Deliverables:**
- New curriculum app with models (AcademicSession, SchoolLevel, Subject, Term, Week, SubjectCurriculum, Topic, StudentProgramme, SubjectEnrolment, LegacyExamMapping)
- Database migrations (0001_initial.py)
- Curriculum seed data (initial_data.json, subjects.json with 31 subjects)
- Management command (seed_curriculum.py)
- Optimized production configuration (conn_max_age=60, gunicorn workers=2, threads=2)

---

### Phase 2: Service Layer Refactor (Week 3-4) - COMPLETED
**Focus: Backend Logic Adaptation**

| Task | Description | Files Affected | Status |
|------|-------------|----------------|--------|
| 2.1 | Create CurriculumService abstraction layer | core/services/curriculum.py | DONE |
| 2.2 | Update CourseCreationForm for class-level selection | courses/forms.py | DONE |
| 2.3 | Refactor Course model to use new curriculum FK | courses/models.py | DONE |
| 2.4 | Update course creation view to use CurriculumService | courses/views.py | DONE |
| 2.5 | Refactor AI module generator prompts | core/utils/ai_module_generator.py | DONE |
| 2.6 | Update quiz generation for class-based content | quizzes/utils.py | DONE |
| 2.7 | Update exam generation for class-based content | exams/views.py | DONE |
| 2.8 | Add API endpoint for fetching subjects by class level | courses/urls.py, courses/views.py | DONE |

**Deliverables:**
- CurriculumService class with 20+ methods for curriculum data access
- Updated CourseCreationForm with school_level, term, subject fields
- Refactored Course model with curriculum FKs while maintaining backwards compatibility
- Updated AI prompts for class-level context
- API endpoint for dynamic subject loading

---

### Phase 3: Frontend & Branding (Week 5-6) - COMPLETED
**Focus: User Interface Updates**

| Task | Description | Files Affected | Status |
|------|-------------|----------------|--------|
| 3.1 | Update landing page messaging (exam → class focus) | templates/core/home.html | DONE |
| 3.2 | Update course creation template with class selector | courses/templates/courses/course_creation.html | DONE |
| 3.3 | Update dashboard to show class levels | templates/core/dashboard.html | DONE |
| 3.4 | Update sidebar navigation | templates/partials/sidebar.html | DONE |
| 3.5 | Update all "exam" references to "class" in templates | All templates | DONE |
| 3.6 | Create new class-level icons/badges | templates/core/dashboard.html | DONE |
| 3.7 | Update PWA manifest with new branding | static/pwa/manifest.json | DONE |
| 3.8 | Fix duplicate CSS classes in sidebar | templates/partials/sidebar.html | DONE |

**Deliverables:**
- Rebranded landing page with JS1-SS3 class levels
- Updated course creation flow with school_level/term/subject dropdowns
- Dashboard showing class-level badges with color coding
- Fixed duplicate CSS classes in sidebar

---

### Phase 4: Optimization & Testing (Week 7-8)
**Focus: Performance & Quality**

| Task | Description | Files Affected |
|------|-------------|----------------|
| 4.1 | Implement AI response streaming | core/utils/ai_fallback.py |
| 4.2 | Add request rate limiting | core/middleware.py |
| 4.3 | Optimize database queries (select_related, prefetch_related) | All views |
| 4.4 | Add database indexes for new curriculum models | migrations/ |
| 4.5 | Write unit tests for CurriculumService | tests/ |
| 4.6 | Write integration tests for course creation flow | tests/ |
| 4.7 | Load testing on 1GB VM | External |
| 4.8 | Fix all 69 LSP diagnostic issues | Multiple files |

**Deliverables:**
- Optimized AI integration
- Rate limiting middleware
- Test suite
- Performance benchmarks

---

### Phase 5: Data Migration & Launch (Week 9-10)
**Focus: Production Deployment**

| Task | Description | Files Affected |
|------|-------------|----------------|
| 5.1 | Create script to migrate existing user courses | management commands |
| 5.2 | Map existing syllabuses to new curriculum structure | data migration |
| 5.3 | Update Paystack integration for new branding | payments/views.py |
| 5.4 | Update email templates (if any) | templates/ |
| 5.5 | Production database migration | Render console |
| 5.6 | Monitor memory usage post-deployment | Render dashboard |
| 5.7 | User communication about rebranding | External |

**Deliverables:**
- Data migration scripts
- Production deployment
- Monitoring setup

---

## Part 6: Future Enhancements (Post-Launch)

### 6.1 Priority 1: Continuous Assessment
- Weekly/Monthly tests tracking
- Progress reports per term
- Grade computation

### 6.2 Priority 2: Teacher Features
- Teacher accounts with student management
- Assignment creation
- Class performance analytics

### 6.3 Priority 3: Parent Portal
- View child's progress
- Receive notifications
- Payment management

### 6.4 Priority 4: Content Management
- Admin interface for curriculum updates
- Content moderation queue
- Version control for syllabuses

---

## Part 7: Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Memory issues on 1GB VM | Medium | High | Aggressive caching, worker limits, monitoring |
| AI API rate limits | Medium | Medium | 4-tier fallback already in place |
| Data migration errors | Low | High | Backup before migration, rollback plan |
| User confusion during transition | Medium | Medium | Clear communication, gradual rollout |
| Performance degradation with new schema | Low | Medium | Proper indexing, query optimization |

---

## Part 8: Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Memory Usage | <800MB average | Render metrics |
| Response Time | <2s for non-AI pages | Application monitoring |
| AI Success Rate | >95% | Fallback tier tracking |
| User Retention | Maintain current levels | Analytics |
| Course Creation Success | >98% | Error logging |

---

## Appendix A: Files Requiring Changes

### High Priority (Core Changes)
1. `courses/models.py` - Add school_level, term FKs
2. `courses/forms.py` - New class-level form
3. `courses/views.py` - Update course creation logic
4. `core/utils/ai_module_generator.py` - Update AI prompts
5. `admin_syllabus/models.py` - Migrate to new structure
6. `akili_project/settings.py` - Memory optimizations

### Medium Priority (UI Changes)
7. `templates/core/home.html` - Rebrand messaging
8. `templates/core/dashboard.html` - Class level display
9. `templates/courses/course_creation.html` - New form fields
10. `templates/partials/sidebar.html` - Navigation updates

### Low Priority (Cleanup)
11. All template files - Terminology updates
12. `static/pwa/manifest.json` - Branding
13. `README.md` - Documentation updates
14. `TECHNICAL_DOCUMENTATION.md` - Architecture updates

---

## Appendix B: Curriculum Seed Data Structure

```json
{
  "academic_sessions": [
    {
      "name": "2024/2025",
      "start_date": "2024-09-09",
      "end_date": "2025-07-18",
      "is_active": true
    }
  ],
  
  "school_levels": [
    {"name": "JS1", "level_order": 1, "level_type": "JUNIOR", "description": "Junior Secondary School Year 1"},
    {"name": "JS2", "level_order": 2, "level_type": "JUNIOR", "description": "Junior Secondary School Year 2"},
    {"name": "JS3", "level_order": 3, "level_type": "JUNIOR", "description": "Junior Secondary School Year 3"},
    {"name": "SS1", "level_order": 4, "level_type": "SENIOR", "description": "Senior Secondary School Year 1"},
    {"name": "SS2", "level_order": 5, "level_type": "SENIOR", "description": "Senior Secondary School Year 2"},
    {"name": "SS3", "level_order": 6, "level_type": "SENIOR", "description": "Senior Secondary School Year 3"}
  ],
  
  "terms": [
    {
      "name": "First Term",
      "order": 1,
      "total_weeks": 14,
      "instructional_weeks": 12,
      "exam_weeks": 2,
      "typical_start": "September",
      "typical_end": "December"
    },
    {
      "name": "Second Term",
      "order": 2,
      "total_weeks": 14,
      "instructional_weeks": 12,
      "exam_weeks": 2,
      "typical_start": "January",
      "typical_end": "April"
    },
    {
      "name": "Third Term",
      "order": 3,
      "total_weeks": 12,
      "instructional_weeks": 10,
      "exam_weeks": 2,
      "typical_start": "May",
      "typical_end": "July"
    }
  ],
  
  "weeks_template": [
    {"week_number": 1, "week_type": "INSTRUCTIONAL", "title": "Week 1"},
    {"week_number": 2, "week_type": "INSTRUCTIONAL", "title": "Week 2"},
    {"week_number": 3, "week_type": "INSTRUCTIONAL", "title": "Week 3"},
    {"week_number": 4, "week_type": "INSTRUCTIONAL", "title": "Week 4"},
    {"week_number": 5, "week_type": "INSTRUCTIONAL", "title": "Week 5"},
    {"week_number": 6, "week_type": "INSTRUCTIONAL", "title": "Week 6"},
    {"week_number": 7, "week_type": "INSTRUCTIONAL", "title": "Week 7 (Mid-Term)"},
    {"week_number": 8, "week_type": "INSTRUCTIONAL", "title": "Week 8"},
    {"week_number": 9, "week_type": "INSTRUCTIONAL", "title": "Week 9"},
    {"week_number": 10, "week_type": "INSTRUCTIONAL", "title": "Week 10"},
    {"week_number": 11, "week_type": "INSTRUCTIONAL", "title": "Week 11"},
    {"week_number": 12, "week_type": "INSTRUCTIONAL", "title": "Week 12"},
    {"week_number": 13, "week_type": "REVISION", "title": "Week 13 (Revision)"},
    {"week_number": 14, "week_type": "EXAM", "title": "Week 14 (Examination)"}
  ],
  
  "subjects": {
    "junior_secondary": [
      {"name": "English Language", "code": "ENG", "is_science": false},
      {"name": "Mathematics", "code": "MTH", "is_science": true},
      {"name": "Basic Science", "code": "BSC", "is_science": true},
      {"name": "Basic Technology", "code": "BTC", "is_science": true},
      {"name": "Social Studies", "code": "SST", "is_science": false},
      {"name": "Civic Education", "code": "CVE", "is_science": false},
      {"name": "Agricultural Science", "code": "AGR", "is_science": true},
      {"name": "Business Studies", "code": "BSS", "is_science": false},
      {"name": "Computer Studies", "code": "ICT", "is_science": true},
      {"name": "French", "code": "FRN", "is_science": false},
      {"name": "Fine Art", "code": "FAR", "is_science": false},
      {"name": "Home Economics", "code": "HEC", "is_science": false},
      {"name": "Physical & Health Education", "code": "PHE", "is_science": false},
      {"name": "Christian Religious Studies", "code": "CRS", "is_science": false},
      {"name": "Islamic Religious Studies", "code": "IRS", "is_science": false},
      {"name": "Yoruba", "code": "YOR", "is_science": false},
      {"name": "Igbo", "code": "IGB", "is_science": false},
      {"name": "Hausa", "code": "HAU", "is_science": false}
    ],
    "senior_secondary": [
      {"name": "English Language", "code": "ENG", "is_science": false},
      {"name": "Mathematics", "code": "MTH", "is_science": true},
      {"name": "Physics", "code": "PHY", "is_science": true},
      {"name": "Chemistry", "code": "CHM", "is_science": true},
      {"name": "Biology", "code": "BIO", "is_science": true},
      {"name": "Economics", "code": "ECO", "is_science": false},
      {"name": "Government", "code": "GOV", "is_science": false},
      {"name": "Literature in English", "code": "LIT", "is_science": false},
      {"name": "History", "code": "HIS", "is_science": false},
      {"name": "Geography", "code": "GEO", "is_science": false},
      {"name": "Agricultural Science", "code": "AGR", "is_science": true},
      {"name": "Commerce", "code": "COM", "is_science": false},
      {"name": "Financial Accounting", "code": "ACC", "is_science": false},
      {"name": "Computer Science", "code": "CSC", "is_science": true},
      {"name": "Further Mathematics", "code": "FMT", "is_science": true},
      {"name": "Technical Drawing", "code": "TDR", "is_science": true},
      {"name": "Civic Education", "code": "CVE", "is_science": false}
    ]
  }
}
```

---

## Appendix C: Sample Topic Structure (Mathematics JS1 First Term)

```json
{
  "curriculum": {
    "school_level": "JS1",
    "subject": "Mathematics",
    "term": "First Term",
    "version": "2025"
  },
  "topics": [
    {
      "week": 1,
      "title": "Number Systems - Counting and Place Value",
      "difficulty": "BASIC",
      "learning_objectives": [
        "Count numbers up to millions",
        "Understand place value system",
        "Read and write numbers in words and figures"
      ],
      "key_concepts": ["place value", "units", "tens", "hundreds", "thousands", "millions"]
    },
    {
      "week": 2,
      "title": "Whole Numbers - Basic Operations",
      "difficulty": "BASIC",
      "learning_objectives": [
        "Perform addition and subtraction with whole numbers",
        "Solve word problems involving addition and subtraction"
      ],
      "key_concepts": ["addition", "subtraction", "carrying", "borrowing"]
    },
    {
      "week": 3,
      "title": "Whole Numbers - Multiplication and Division",
      "difficulty": "BASIC",
      "learning_objectives": [
        "Multiply multi-digit numbers",
        "Divide numbers with remainders",
        "Apply BODMAS rule"
      ],
      "key_concepts": ["multiplication", "division", "BODMAS", "remainder"]
    },
    {
      "week": 4,
      "title": "Fractions - Introduction",
      "difficulty": "INTERMEDIATE",
      "learning_objectives": [
        "Identify parts of a fraction",
        "Convert between proper and improper fractions",
        "Find equivalent fractions"
      ],
      "key_concepts": ["numerator", "denominator", "proper fraction", "improper fraction", "equivalent"]
    }
  ]
}
```

---

*Document prepared by: AI Technical Assessment*
*Date: December 2025*
*Version: 1.1 (Updated with Term/Week Structure)*
