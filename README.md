# Akili - AI-Powered Educational Platform

Akili is a comprehensive educational platform designed to help Nigerian students prepare for JAMB, SSCE, and JSS examinations using AI-powered personalized learning paths, interactive quizzes, and mock exams.

## 🌟 Features

### For Students
- **Personalized Course Generation**: AI automatically creates 15-module courses tailored to your exam type and subject
- **Interactive Lessons**: Comprehensive lesson content with LaTeX-rendered mathematical formulas
- **Practice Quizzes**: FREE unlimited quizzes with instant feedback and explanations
- **Mock Exams**: Full-length practice exams with 20 questions (5 credits)
- **Progress Tracking**: Track your quiz scores, completion rates, and learning journey
- **Referral System**: Earn bonus credits by inviting friends
- **Dark Mode**: Eye-friendly interface with automatic dark mode support
- **PWA Support**: Install as a mobile app for offline access

### AI-Powered Features
- **Smart Content Generation**: Multi-tier AI fallback system (Gemini 2.5 Flash → Gemini Pro → Groq)
- **Validated Lessons**: Two-pass AI validation ensures content accuracy
- **Context-Aware Questions**: Questions generated from official syllabi
- **Adaptive Learning**: Progressive module unlocking based on quiz performance

### Technology Stack
- **Backend**: Django 5.2.8
- **Database**: PostgreSQL (production) / SQLite (development)
- **AI Integration**: Google Gemini AI & Groq API
- **Frontend**: Tailwind CSS with dark mode support
- **Math Rendering**: KaTeX for LaTeX equations
- **Deployment**: Render (production) / Replit (development)

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL (for production)
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd akili-platform
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
DATABASE_URL=  # Leave empty for SQLite in development
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create a superuser**
```bash
python manage.py createsuperuser
```

7. **Run the development server**
```bash
python manage.py runserver 0.0.0.0:5000
```

8. **Access the application**
- Development: http://localhost:5000
- Admin panel: http://localhost:5000/admin

## 📚 Project Structure

```
akili-platform/
├── akili_project/          # Main project settings
├── core/                   # Core app (dashboard, home)
│   ├── utils/             # AI utilities and helpers
│   └── templates/         # Core templates
├── users/                  # Custom user authentication
├── courses/                # Course and module management
├── quizzes/                # Quiz generation and attempts
├── exams/                  # Mock exam functionality
├── payments/               # Credit purchase system
├── profiles/               # User profile management
├── admin_syllabus/         # Syllabus management
├── static/                 # Static assets (CSS, JS, images)
├── templates/              # Base templates and partials
└── requirements.txt        # Python dependencies
```

## 💳 Credit System

### Free Credits
- **10 free credits daily** for all users
- Credits reset automatically every 24 hours
- Unused credits don't carry over

### Credit Costs
- **Course Creation**: 5 credits (generates 15 modules)
- **Practice Quiz**: FREE (unlimited)
- **Mock Exam**: 5 credits (20 questions)
- **AI Tutor Question**: 1 credit

### Earning Credits
- **Referrals**: +2 daily credit limit per successful referral
- **Purchase Packages**:
  - 20 credits: ₦500
  - 50 credits: ₦1,000 (Most Popular)
  - 100 credits: ₦1,800 (Best Value - Save ₦200)

## 🎯 How It Works

### 1. Create a Course
1. Select your exam type (JAMB, SSCE, or JSS)
2. Choose your subject from the official syllabus
3. AI generates 15 personalized study modules (costs 5 credits)

### 2. Study Lessons
- Each module contains comprehensive lesson content
- Math formulas rendered with LaTeX
- Report errors to improve content quality

### 3. Take Quizzes
- Practice quizzes are completely FREE
- Get instant feedback with explanations
- Pass with 60% to unlock the next module

### 4. Practice with Mock Exams
- Full-length 20-question exams (5 credits)
- Simulates real exam conditions
- Detailed performance analysis

## 🔧 Configuration

### AI Model Tiers
The platform uses a 4-tier fallback system for reliability:
1. **Tier 1**: Gemini 2.5 Flash (Free, Fast)
2. **Tier 2**: Gemini Pro (Paid, High Quality)
3. **Tier 3**: Groq API (Free Fallback)
4. **Tier 4**: Circuit Breaker (Graceful Error)

### Settings
Key settings in `akili_project/settings.py`:
- `AKILI_DAILY_FREE_CREDITS`: Daily free credit allocation (default: 10)
- `AKILI_MAX_REFERRAL_CREDITS`: Maximum daily credits from referrals (default: 50)

## 🌐 Deployment

### Render Deployment

The project includes `render.yaml` for one-click deployment:

1. **Connect to Render**
   - Push your code to GitHub
   - Connect your repository to Render

2. **Configure Environment Variables**
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `GROQ_API_KEY`: Your Groq API key
   - Other variables are auto-configured

3. **Deploy**
   - Render automatically runs `build.sh`
   - Database migrations run automatically
   - Gunicorn starts the production server

### Production Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`
- [ ] Set up PostgreSQL database
- [ ] Configure static file serving with WhiteNoise
- [ ] Add SSL certificate
- [ ] Set up payment gateway (Paystack)

## 🧪 Testing

Run tests:
```bash
python manage.py test
```

Check code quality:
```bash
python manage.py check
python manage.py check --deploy  # Production readiness check
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is proprietary software. All rights reserved.

## 📧 Support

For support or inquiries:
- Email: support@akili.ng
- Website: https://akili.ng

## 🙏 Acknowledgments

- Google Gemini AI for content generation
- Groq for fallback AI processing
- KaTeX for mathematical formula rendering
- Tailwind CSS for the beautiful UI
- Nigerian education community for syllabus support

---

**Built with ❤️ for Nigerian students**
