# Akili - AI-Powered Educational Platform

Akili is a comprehensive AI-powered educational platform designed to help Nigerian students prepare for JAMB, SSCE, and JSS examinations. The platform leverages Google Gemini AI and Groq API to generate personalized learning content, interactive quizzes, and mock exams.

## 🌟 Features

  * **Personalized Course Generation**: AI automatically creates 15-module courses tailored to a student's exam type and subject.
  * **Interactive Lessons**: Comprehensive lesson content with mathematical formulas rendered using KaTeX.
  * **Practice Quizzes**: FREE unlimited quizzes with instant feedback and explanations to reinforce learning.
  * **Mock Exams**: Full-length practice exams (20 questions) to simulate real exam conditions.
  * **Progress Tracking**: Students can track their quiz scores, completion rates, and learning journey.
  * **Credit System**: All users receive 10 free credits daily, which reset every 24 hours.
  * **Referral System**: Earn a +2 daily credit limit for each successful user referral.
  * **Dark Mode**: Eye-friendly interface with automatic dark mode support based on system preference.
  * **PWA Support**: Can be installed as a Progressive Web App (PWA) on mobile devices for an app-like experience.

-----

## 💻 Technology Stack

  * **Backend**: Django 5.2.8
  * **Database**: PostgreSQL
  * **AI Integration**: Google Gemini AI (2.5 Flash, Pro) & Groq API
  * **Frontend**: Tailwind CSS
  * **Math Rendering**: KaTeX (for LaTeX)
  * **Deployment**: Render (production) 
  * **Payments**: Paystack

-----

## 💳 Credit System

### Free Credits

  * **10 free credits daily** for all users.
  * Credits reset automatically every 24 hours (unused credits do not carry over).

### Credit Costs

  * **Course Creation**: 5 credits
  * **Practice Quiz**: FREE
  * **Mock Exam**: 5 credits
  * **AI Tutor Question**: 1 credit

### Purchase Packages

  * **20 credits**: ₦500
  * **50 credits**: ₦1,000
  * **100 credits**: ₦1,800

-----

## 🤖 AI Integration

### Multi-Tier Fallback System

The platform uses a robust 4-tier AI fallback system to ensure high availability and reliability:

1.  **Tier 1**: Gemini 2.5 Flash (Primary - Fast, Free)
2.  **Tier 2**: Gemini Pro (First fallback - High Quality, Paid)
3.  **Tier 3**: Groq API (Second fallback - Fast, Free)
4.  **Tier 4**: Circuit Breaker (Graceful Error)

### LaTeX Rendering

  * All AI responses are prompted to use **double-escaped backslashes** for LaTeX (e.g., `\\frac{a}{b}`) to ensure correct JSON formatting.
  * KaTeX renders the math formulas on the frontend using `$$...$$` (display) and `$...$` (inline) delimiters.

-----

## 🚀 Getting Started

### Prerequisites

  * Python 3.11+
  * PostgreSQL (recommended for production)
  * Git

### Installation

1.  **Clone the repository**

    ```bash
    git clone <repository-url>
    cd akili-platform
    ```

2.  **Create a virtual environment**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables**
    Create a `.env` file in the project root (see `Environment Variables` section below).

5.  **Run migrations**

    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser**

    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server**

    ```bash
    python manage.py runserver 0.0.0.0:5000
    ```

    Access the application at `http://localhost:5000`.

-----

## ⚙️ Environment Variables

### Required for Development

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
DATABASE_URL=  # Leave empty to use SQLite by default
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

-----

## 📂 Project Structure

```
akili-platform/
├── akili_project/        # Main Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                 # Core app (dashboard, home, exam center)
│   ├── utils/            # AI utilities and helpers
│   │   ├── ai_fallback.py
│   │   └── ai_module_generator.py
│   ├── templates/
│   └── views.py
├── users/                # Custom user authentication
│   ├── models.py         # CustomUser model with credit system
│   └── views.py
├── courses/              # Course and module management
│   ├── models.py         # Course, Module, CachedLesson models
│   └── views.py
├── quizzes/              # Quiz generation and attempts
│   ├── models.py         # QuizAttempt model
│   ├── utils.py          # Quiz generation logic
│   └── views.py
├── exams/                # Mock exam functionality
│   ├── models.py         # Exam, ExamQuestion models
│   └── views.py
├── payments/             # Credit purchase system (Paystack)
│   ├── models.py         # Payment model
│   └── views.py
├── profiles/             # User profile management
├── admin_syllabus/       # Syllabus management (JAMB, SSCE, JSS)
├── static/               # Static assets (CSS, JS, images)
├── templates/            # Base templates and partials
│   ├── base.html
│   └── partials/
└── requirements.txt
```

-----

## 🗃️ Database Models

  * **Users App**
      * `CustomUser`: Extends Django User. Manages `tutor_credits`, `daily_credit_limit`, and `referred_by`.
  * **Courses App**
      * `Course`: A user's personalized course (links user, exam\_type, subject).
      * `Module`: The 15 modules generated for each course.
      * `CachedLesson`: Stores the AI-generated lesson content.
  * **Quizzes App**
      * `QuizAttempt`: Stores user quiz results, including `questions_data` (JSON), `score`, and `passed` status.
  * **Exams App**
      * `Exam`: Stores mock exam attempts linked to a user and course.
      * `ExamQuestion`: Stores individual questions for an exam.
  * **Payments App**
      * `Payment`: Records Paystack transactions and verification status.

-----

## 🌐 Deployment

The project includes a `render.yaml` file for easy deployment to Render.

1.  Push your code to a GitHub repository.
2.  Connect your repository to a new "Web Service" on Render.
3.  Render will automatically detect `render.yaml` and configure the build and start commands.
4.  Add your production environment variables (from the section above) in the Render dashboard.
5.  Render will automatically run the `build.sh` script, which collects static files and runs database migrations.
6.  Gunicorn starts the production server.

-----

## 🧪 Testing

Run tests:

```bash
python manage.py test
```

Check code quality and production readiness:

```bash
python manage.py check
python manage.py check --deploy
```

-----

## 🤝 Contributors

  * **Ogechi Obinwa** ([github.com/Ogetec-python/](https://www.google.com/search?q=https://github.com/Ogetec-python/))
  * **Stephen Ayankoso** ([github.com/Steve-ayan](https://www.google.com/search?q=https://github.com/Steve-ayan))
