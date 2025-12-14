# Akili - AI-Powered Nigerian Secondary Education Platform

Akili is a comprehensive AI-powered educational platform designed to help Nigerian secondary school students master their studies from Junior Secondary 1 (JS1) to Senior Secondary 3 (SS3). The platform leverages advanced AI models to generate personalized learning content, interactive assessments, and progress tracking aligned with the Nigerian curriculum.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [Credit System](#credit-system)
- [AI Integration](#ai-integration)
- [Assessment System](#assessment-system)
- [Teacher Features](#teacher-features)
- [Parent Portal](#parent-portal)
- [Management Commands](#management-commands)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Endpoints](#api-endpoints)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Learning Features
- **Class-Based Learning**: Organized curriculum covering JS1, JS2, JS3, SS1, SS2, and SS3 class levels
- **Term Structure**: Content organized by First, Second, and Third Term following the Nigerian academic calendar
- **AI-Powered Course Generation**: Automatically creates comprehensive, personalized courses tailored to student's class level and subject
- **Interactive Lessons**: Rich lesson content with mathematical formulas rendered using KaTeX
- **Practice Quizzes**: FREE unlimited quizzes with instant feedback and detailed explanations
- **Mock Tests**: Full-length practice tests (20 questions) to assess understanding

### Assessment System (NEW)
- **Continuous Assessment**: Weekly and monthly tests with automatic grading
- **Grade Computation**: Automatic grade calculation (A-F) based on Nigerian grading standards
- **Progress Reports**: Term-end progress reports with position ranking and remarks

### Teacher Features (NEW)
- **Teacher Dashboard**: Comprehensive view of assigned classes and students
- **Student Management**: Enroll and manage students in classes
- **Assignment Creation**: Create and distribute assignments with due dates
- **Class Analytics**: View performance statistics and identify struggling students

### Parent Portal (NEW)
- **Child Progress Tracking**: Monitor children's grades and academic progress
- **Payment Management**: View payment history and credit balances
- **Notifications**: Receive alerts for grades, assessments, and reports

### Content Management (NEW)
- **Curriculum Version Control**: Track changes to curriculum content
- **Content Moderation Queue**: Review AI-generated content before publication
- **Curriculum Update Requests**: Request and approve curriculum modifications

### User Experience
- **Progress Tracking**: Track quiz scores, completion rates, and learning journey
- **Credit System**: 10 free credits daily with referral bonuses
- **Dark Mode**: Eye-friendly interface with automatic dark mode support
- **PWA Support**: Install as a Progressive Web App on mobile devices
- **Referral System**: Earn +2 daily credit limit for each successful referral

---

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend Framework | Django | 5.2.8 |
| Database | PostgreSQL | Latest |
| Frontend CSS | Tailwind CSS | 3.x |
| AI Integration | Google Gemini + Groq | Multi-tier |
| Math Rendering | KaTeX | 0.16.9 |
| Payment Gateway | Paystack | REST API |
| Static Files | Whitenoise | 6.6.0 |
| WSGI Server | Gunicorn | 21.2.0 |
| Deployment | Render | Cloud |

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (for Tailwind CSS)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd akili-platform
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

5. **Set up the database**
   ```bash
   python manage.py migrate
   ```

6. **Seed curriculum data**
   ```bash
   python manage.py seed_curriculum
   ```

7. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver 0.0.0.0:5000
   ```

9. **Access the application**
   - Main site: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

---

## Environment Variables

### Development
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost/akili_dev
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
```

### Production
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@host/akili_prod
ALLOWED_HOSTS=your.domain.com
CSRF_TRUSTED_ORIGINS=https://your.domain.com
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key
```

---

## Project Structure

```
akili-platform/
├── akili_project/           # Django project settings
│   ├── settings.py          # Configuration
│   ├── urls.py               # URL routing
│   └── wsgi.py               # WSGI entry point
├── core/                     # Core utilities
│   ├── utils/                # AI fallback, module generator
│   ├── middleware.py         # Rate limiting, error handling
│   └── services/             # Business logic services
├── curriculum/               # Curriculum management
│   ├── models.py             # SchoolLevel, Subject, Term, Topic
│   ├── fixtures/             # Seed data (31 subjects)
│   └── management/commands/  # Data migration scripts
├── courses/                  # Course management
│   ├── models.py             # Course, Module, CachedLesson
│   ├── views.py              # Course creation, viewing
│   └── forms.py              # Course creation forms
├── assessments/              # Assessment system (NEW)
│   ├── models.py             # Assessment, Grade, TeacherProfile, etc.
│   ├── views.py              # Dashboard views
│   └── templates/            # Assessment templates
├── quizzes/                  # Practice quizzes
├── exams/                    # Mock tests
├── users/                    # Authentication
│   └── models.py             # CustomUser model
├── payments/                 # Paystack integration
├── profiles/                 # User profile management
├── admin_syllabus/           # Legacy exam syllabuses
├── static/                   # CSS, JS, images
├── templates/                # HTML templates
├── requirements.txt          # Python dependencies
├── render.yaml               # Render deployment config
└── manage.py                 # Django CLI
```

---

## Database Models

### Curriculum App
| Model | Description |
|-------|-------------|
| `AcademicSession` | Academic year (e.g., 2024/2025) |
| `SchoolLevel` | JS1-SS3 class levels |
| `Subject` | 31 subjects with level associations |
| `Term` | First, Second, Third Term |
| `Week` | 14 weeks per term |
| `SubjectCurriculum` | Curriculum per subject/level/term |
| `Topic` | Individual topics per week |
| `StudentProgramme` | Student enrollment |
| `SubjectEnrolment` | Subject-specific tracking |
| `LegacyExamMapping` | JAMB/SSCE/JSS compatibility |

### Assessments App (NEW)
| Model | Description |
|-------|-------------|
| `Assessment` | Weekly/monthly tests and exams |
| `AssessmentQuestion` | MCQ, short answer, essay questions |
| `AssessmentSubmission` | Student submissions with scores |
| `Grade` | Term grades (A-F with GPA) |
| `ProgressReport` | Term-end reports |
| `TeacherProfile` | Teacher accounts |
| `TeacherClass` | Class assignments |
| `Assignment` | Teacher-created assignments |
| `ParentProfile` | Parent accounts with children |
| `Notification` | System notifications |
| `ContentVersion` | Curriculum version control |
| `ContentModerationQueue` | AI content review |
| `CurriculumUpdateRequest` | Curriculum change requests |

---

## Credit System

### Daily Allocation
- **10 free credits** for all users (resets at midnight WAT)
- **+2 daily limit** per successful referral (max 30)

### Credit Costs
| Action | Credits |
|--------|---------|
| Course Creation | 5 |
| Mock Test (20 questions) | 5 |
| AI Tutor Question | 1 |
| Practice Quiz | FREE |

### Purchase Packages
| Package | Price | Credits |
|---------|-------|---------|
| Starter | ₦500 | 50 |
| Standard | ₦1,000 | 120 |
| Premium | ₦2,000 | 300 |

---

## AI Integration

### 4-Tier Fallback System

```
Tier 1: Gemini 2.5 Flash (Primary - Fast, Free)
    ↓ (on failure)
Tier 2: Gemini Pro (High Quality, Paid)
    ↓ (on failure)
Tier 3: Groq API (Fast, Free)
    ↓ (on failure)
Tier 4: Circuit Breaker (Graceful Error + Credit Refund)
```

### Token Limits (Memory Optimized)
| Tier | Max Tokens |
|------|------------|
| Gemini Flash | 2,500 |
| Gemini Pro | 3,000 |
| Groq | 2,000 |

---

## Assessment System

### Assessment Types
- **WEEKLY**: Weekly topic tests
- **MONTHLY**: Monthly comprehensive tests
- **MIDTERM**: Mid-term examinations
- **TERMINAL**: End-of-term examinations

### Grading Scale
| Score | Grade | GPA | Remarks |
|-------|-------|-----|---------|
| 70-100 | A | 4.0 | Excellent |
| 60-69 | B | 3.0 | Very Good |
| 50-59 | C | 2.0 | Good |
| 45-49 | D | 1.0 | Fair |
| 40-44 | E | 0.5 | Pass |
| 0-39 | F | 0.0 | Fail |

---

## Management Commands

```bash
# Seed curriculum data (required after fresh install)
python manage.py seed_curriculum

# Migrate legacy courses (for upgrades from old version)
python manage.py migrate_legacy_courses

# Map legacy syllabuses to new curriculum
python manage.py map_syllabuses

# Collect static files (production)
python manage.py collectstatic --noinput
```

---

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test assessments -v 2
python manage.py test curriculum -v 2
python manage.py test courses -v 2

# Run with coverage
coverage run manage.py test
coverage report
```

**Current Test Coverage**: 138+ tests across all apps

---

## Deployment

### Render Deployment

The project includes `render.yaml` for one-click Render deployment:

1. Push code to GitHub
2. Connect repository to Render
3. Add environment variables in Render dashboard
4. Render automatically runs `build.sh`
5. Gunicorn starts with optimized settings

### Production Configuration (1GB RAM)

```bash
gunicorn --bind=0.0.0.0:5000 \
         --workers=2 \
         --threads=2 \
         --worker-class=gthread \
         --max-requests=1000 \
         --max-requests-jitter=50 \
         --timeout=120 \
         akili_project.wsgi:application
```

---

## API Endpoints

### Course API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/courses/api/subjects/` | GET | Get subjects by class level |
| `/courses/create/` | POST | Create new course |
| `/courses/<id>/` | GET | View course details |

### Assessment API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/assessments/` | GET | List available assessments |
| `/assessments/<id>/` | GET/POST | Take assessment |
| `/assessments/grades/` | GET | View student grades |

---

## Security

### Implemented Measures
- CSRF protection on all forms
- Password hashing via Django bcrypt
- HTTPS enforcement in production
- Secure cookie settings (HttpOnly, SameSite, Secure)
- HTML sanitization with bleach for AI content
- SQL injection protection via Django ORM
- Request rate limiting with database cache
- @login_required on all protected views

### Security Headers (Production)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Strict-Transport-Security: max-age=31536000

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use Django coding style guidelines
- Write tests for new features
- Update documentation as needed

---

## License

This project is proprietary software. All rights reserved.

---

## Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team

---

## Contributors

- **Ogechi Obinwa** - Lead Developer ([@Ogetec-python](https://github.com/Ogetec-python))
- **Stephen Ayankoso** - Developer ([@Steve-ayan](https://github.com/Steve-ayan))

---

*Built with love for Nigerian students*
