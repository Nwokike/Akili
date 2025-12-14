# Akili Platform - Administrator Guide

## Overview

Akili is a comprehensive Nigerian secondary education platform covering JS1 through SS3 (Junior Secondary 1 to Senior Secondary 3). The platform uses AI-powered lesson generation to deliver personalized learning content aligned with the Nigerian curriculum.

## Architecture

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.2 |
| Database | PostgreSQL |
| Frontend CSS | Tailwind CSS |
| AI Integration | Google Gemini + Groq (4-tier fallback) |
| Payment Gateway | Paystack |
| Static Files | Whitenoise |
| WSGI Server | Gunicorn |

### Django Apps

| App | Purpose |
|-----|---------|
| `core` | Dashboard, home, context processors |
| `users` | Authentication, CustomUser model, referrals |
| `curriculum` | SchoolLevel, Subject, Term, Week, Topic models |
| `courses` | Course & module management, AI content generation |
| `quizzes` | Practice quiz generation |
| `exams` | Mock exam generation |
| `payments` | Paystack credit purchases |
| `profiles` | User profile management |
| `assessments` | Continuous assessment, teacher/parent features |
| `admin_syllabus` | Legacy exam syllabuses (JAMB, SSCE, JSS) |

## Curriculum Structure

### School Levels

| Level | Type | Description |
|-------|------|-------------|
| JS1 | Junior | Junior Secondary School Year 1 |
| JS2 | Junior | Junior Secondary School Year 2 |
| JS3 | Junior | Junior Secondary School Year 3 |
| SS1 | Senior | Senior Secondary School Year 1 |
| SS2 | Senior | Senior Secondary School Year 2 |
| SS3 | Senior | Senior Secondary School Year 3 |

### Terms

- First Term (September - December): 14 weeks
- Second Term (January - April): 14 weeks
- Third Term (May - July): 12 weeks

### Week Types

- INSTRUCTIONAL: Regular teaching content
- REVISION: Pre-exam revision
- EXAM: Examination period

## Admin Panel Features

### Curriculum Management

Access at `/admin/curriculum/`

**SubjectCurriculum**: Define curriculum for each subject/level/term combination
- School Level: JS1-SS3
- Subject: Mathematics, English, Physics, etc.
- Term: First/Second/Third Term
- Version: Curriculum version (e.g., "2024")

**Topic**: Create topics for each week
- Curriculum: Link to SubjectCurriculum
- Week: Week number within term
- Title: Topic title
- Learning Objectives: JSON array
- Difficulty Level: BASIC, INTERMEDIATE, ADVANCED

### Assessments Management

Access at `/admin/assessments/`

**Assessment**: Create tests and exams
- Assessment Types: WEEKLY, MONTHLY, MIDTERM, TERMINAL
- Status: DRAFT, PUBLISHED, CLOSED
- Link to SubjectCurriculum and Week

**AssessmentQuestion**: Add questions inline
- Question Types: MCQ, SHORT, ESSAY, TRUE_FALSE
- Options (for MCQ): JSON format {"A": "option1", "B": "option2"}
- Correct Answer and Explanation

**Grade**: View and manage student grades
- Computed automatically via compute_grade() method
- Grade Scale: A (70+), B (60-69), C (50-59), D (45-49), E (40-44), F (<40)

**ProgressReport**: Term-end progress reports
- Includes position, average score, teacher/principal remarks

### Teacher Management

**TeacherProfile**: Manage teacher accounts
- Employee ID
- Subjects taught (M2M)
- School levels (M2M)
- Verification status

**TeacherClass**: Assign teachers to classes
- Teacher, School Level, Subject, Academic Session, Term
- Current Week tracking
- Student roster (M2M)

**Assignment**: Teacher-created assignments
- Linked to TeacherClass
- Due date, total marks, status

### Parent Portal

**ParentProfile**: Link parents to children
- Children (M2M to CustomUser)
- Notification preferences

**Notification**: System notifications
- Types: GRADE, ASSESSMENT, REPORT, PAYMENT, GENERAL
- Read/unread status

### Content Management

**ContentVersion**: Version control for curriculum content
- Content Type: CURRICULUM, TOPIC, LESSON
- Snapshot of content at each version

**ContentModerationQueue**: Review AI-generated content
- Content Types: LESSON, QUIZ, EXAM
- Status: PENDING, APPROVED, REJECTED, NEEDS_EDIT
- Flagged issues (JSON)

**CurriculumUpdateRequest**: Propose curriculum changes
- Change type and description
- Proposed changes (JSON)
- Review workflow

## Credit System

### Credit Costs

| Action | Credits |
|--------|---------|
| Course Creation | 5 |
| Mock Exam (20 questions) | 5 |
| AI Tutor Question | 1 |
| Practice Quiz | FREE |

### Daily Allocation

- 10 free credits daily (resets at midnight WAT)
- +2 daily limit per successful referral (max 30)
- Purchased credits never expire

## AI Configuration

### 4-Tier Fallback System

1. Gemini 2.5 Flash (Free, Fast) - Primary
2. Gemini Pro (Paid, High Quality) - First fallback
3. Groq API (Free, Fast) - Second fallback
4. Circuit Breaker (Graceful error message)

### Token Limits

| Tier | Max Tokens |
|------|------------|
| gemini_flash | 2500 |
| gemini_paid | 3000 |
| groq | 2000 |

### Rate Limiting

- Request rate limiting enabled via database cache
- Configurable per-endpoint limits
- Returns HTTP 429 on threshold breach

## Production Deployment

### Environment Variables

Required secrets:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Django secret key
- `GEMINI_API_KEY`: Google Gemini API key
- `GROQ_API_KEY`: Groq API key
- `PAYSTACK_SECRET_KEY`: Paystack secret key
- `PAYSTACK_PUBLIC_KEY`: Paystack public key

### Gunicorn Configuration (1GB RAM VM)

```bash
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

### Database Configuration

```python
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=60,
        conn_health_checks=True,
    )
}
```

## Management Commands

### Curriculum Seeding

```bash
python manage.py seed_curriculum
```

Creates initial curriculum data for all school levels, subjects, and terms.

### Legacy Course Migration

```bash
python manage.py migrate_legacy_courses
```

Migrates existing exam-based courses to the new curriculum structure.

### Syllabus Mapping

```bash
python manage.py map_syllabuses
```

Maps legacy JAMB/SSCE/JSS syllabuses to the new curriculum model.

## Testing

Run all tests:
```bash
python manage.py test
```

Run specific app tests:
```bash
python manage.py test assessments -v 2
python manage.py test curriculum -v 2
python manage.py test courses -v 2
```

Current test counts:
- assessments: 19 tests
- curriculum: 15 tests
- courses: 8 tests
- Total: 119+ tests

## Monitoring

### Success Metrics

| Metric | Target |
|--------|--------|
| Memory Usage | <800MB average |
| Response Time | <2s for non-AI pages |
| AI Success Rate | >95% |
| Course Creation Success | >98% |

### Log Locations

- Application logs: stdout (Gunicorn)
- AI fallback tracking: Built into ai_fallback.py
- Payment logs: payments app logging

## Security Checklist

- [x] CSRF protection enabled
- [x] Password hashing via Django bcrypt
- [x] HTTPS enforcement in production
- [x] Secure cookie settings (HttpOnly, SameSite, Secure)
- [x] HTML sanitization with bleach for AI content
- [x] SQL injection protection via Django ORM
- [x] Rate limiting enabled
- [x] @login_required on all protected views

## Troubleshooting

### Common Issues

1. **AI Generation Fails**: Check API keys, fallback tier status
2. **Payment Verification Fails**: Verify Paystack keys, webhook configuration
3. **Database Connection Issues**: Check DATABASE_URL, connection pool settings
4. **Memory Issues**: Reduce gunicorn workers, increase max-requests

### Support

For technical support, check:
1. Application logs for error traces
2. Django admin for data integrity
3. Database queries for performance issues
