# Akili - AI-Powered Educational Platform

Akili is a comprehensive AI-powered educational platform designed to help Nigerian secondary school students master their studies from JS1 to SS3. The platform leverages Google Gemini AI and Groq API to generate personalized learning content, interactive quizzes, and mock tests aligned with the Nigerian curriculum.

## Features

* **Class-Based Learning**: Organized curriculum covering JS1, JS2, JS3, SS1, SS2, and SS3 class levels
* **Term Structure**: Content organized by First, Second, and Third Term following Nigerian academic calendar
* **Personalized Course Generation**: AI automatically creates comprehensive courses tailored to student's class level and subject
* **Interactive Lessons**: Comprehensive lesson content with mathematical formulas rendered using KaTeX
* **Practice Quizzes**: FREE unlimited quizzes with instant feedback and explanations
* **Mock Tests**: Full-length practice tests (20 questions) to assess understanding
* **Progress Tracking**: Students can track quiz scores, completion rates, and learning journey
* **Credit System**: All users receive 10 free credits daily, which reset every 24 hours
* **Referral System**: Earn +2 daily credit limit for each successful user referral
* **Dark Mode**: Eye-friendly interface with automatic dark mode support
* **PWA Support**: Install as a Progressive Web App on mobile devices

---

## Technology Stack

* **Backend**: Django 5.2.8
* **Database**: PostgreSQL
* **AI Integration**: Google Gemini AI (2.5 Flash, Pro) & Groq API
* **Frontend**: Tailwind CSS
* **Math Rendering**: KaTeX (for LaTeX)
* **Deployment**: Render (production)
* **Payments**: Paystack

---

## Credit System

### Free Credits

* **10 free credits daily** for all users
* Credits reset automatically every 24 hours

### Credit Costs

* **Course Creation**: 5 credits
* **Practice Quiz**: FREE
* **Mock Test**: 5 credits
* **AI Tutor Question**: 1 credit

### Purchase Packages

* **Starter**: ₦500 (50 credits)
* **Standard**: ₦1,000 (120 credits)
* **Premium**: ₦2,000 (300 credits)

---

## AI Integration

### Multi-Tier Fallback System

The platform uses a robust 4-tier AI fallback system:

1. **Tier 1**: Gemini 2.5 Flash (Primary - Fast, Free)
2. **Tier 2**: Gemini Pro (First fallback - High Quality, Paid)
3. **Tier 3**: Groq API (Second fallback - Fast, Free)
4. **Tier 4**: Circuit Breaker (Graceful Error)

### Memory Optimization

* Tier-specific token caps (2000-3000 tokens per tier)
* Streaming responses for large content
* Connection pooling for database efficiency

---

## Getting Started

### Prerequisites

* Python 3.11+
* PostgreSQL
* Git

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd akili-platform
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file (see Environment Variables section)

4. **Run migrations**

   ```bash
   python manage.py migrate
   ```

5. **Seed curriculum data**

   ```bash
   python manage.py seed_curriculum
   ```

6. **Create a superuser**

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**

   ```bash
   python manage.py runserver 0.0.0.0:5000
   ```

---

## Environment Variables

### Required for Development

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
DATABASE_URL=postgresql://user:pass@host/dbname
```

### Required for Production

```env
SECRET_KEY=your-production-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:pass@host/dbname
ALLOWED_HOSTS=your.domain.com
CSRF_TRUSTED_ORIGINS=https://your.domain.com
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
PAYSTACK_SECRET_KEY=your-paystack-secret-key
```

---

## Project Structure

```
akili-platform/
├── akili_project/        # Main Django project settings
├── core/                 # Core app (dashboard, home, AI utilities)
│   └── utils/            # AI fallback and module generator
├── curriculum/           # New curriculum structure
│   ├── models.py         # SchoolLevel, Subject, Term, Topic models
│   ├── fixtures/         # Seed data for curriculum
│   └── management/       # Data migration commands
├── users/                # Custom user authentication
├── courses/              # Course and module management
├── quizzes/              # Quiz generation and attempts
├── exams/                # Mock test functionality
├── payments/             # Credit purchase system (Paystack)
├── profiles/             # User profile management
├── admin_syllabus/       # Legacy syllabus storage
├── static/               # Static assets
├── templates/            # HTML templates
└── requirements.txt
```

---

## Database Models

### Curriculum App (New)
* `SchoolLevel`: JS1-SS3 class levels
* `Subject`: All subjects with school level associations
* `Term`: First, Second, Third Term structure
* `Week`: 14 weeks per term (12 instructional + 2 exam)
* `SubjectCurriculum`: Curriculum per subject/level/term
* `Topic`: Individual topics per curriculum week
* `StudentProgramme`: Student enrollment by academic session
* `SubjectEnrolment`: Subject-specific enrollment tracking

### Legacy Support
* `LegacyExamMapping`: Maps old exam types (JAMB/SSCE/JSS) to new structure

---

## Management Commands

```bash
# Seed curriculum data (run after migrations)
python manage.py seed_curriculum

# Migrate legacy courses (if upgrading from old version)
python manage.py migrate_legacy_courses

# Map legacy syllabuses to new curriculum
python manage.py map_syllabuses
```

---

## Testing

Run all tests:

```bash
python manage.py test
```

Current test coverage: 119 tests across all apps

---

## Deployment

The project includes a `render.yaml` for Render deployment:

1. Push code to GitHub
2. Connect repository to Render
3. Add production environment variables
4. Render runs `build.sh` automatically
5. Gunicorn starts the production server

Optimized for 1GB RAM VM with:
* 2 workers, 2 threads
* Connection pooling (conn_max_age=60)
* Request rate limiting

---

## Contributors

* **Ogechi Obinwa** (github.com/Ogetec-python)
* **Stephen Ayankoso** (github.com/Steve-ayan)
