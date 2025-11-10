# Akili - AI-Powered Nigerian Exam Prep Platform

Nigeria's first personal AI-powered study platform for JAMB, WAEC, NECO, and JSS exams.

## 🚀 Local Development Quick Start

1.  **Install PostgreSQL on Windows**
    * Download the installer from the [official website](https://www.postgresql.org/download/windows/).
    * Run the installer. During setup, remember the password you set for the `postgres` user.

2.  **Install Dependencies**
    * Install all required Python packages:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Set Up Environment**
    * Copy the `.env.example` file to a new file named `.env`.
    * Edit your new `.env` file to add your `PGPASSWORD` (from step 1) and your API keys.

4.  **Run Migrations**
    * Create the database tables:
        ```bash
        python manage.py migrate
        ```

5.  **Create Superuser** (Optional)
    ```bash
    python manage.py createsuperuser
    ```

6.  **Start Development Server**
    ```bash
    python manage.py runserver
    ```

Visit: `http://127.0.0.1:8000/`

---

## ⚙️ Environment Variables (`.env` file)

Your local `.env` file must be configured for the project to run.

*Note: This project is configured to use **PostgreSQL for all environments**. You must have it installed and running locally.*

* `SECRET_KEY`: (Use the one from `.env.example`)
* `DEBUG`: `True`
* `ALLOWED_HOSTS`: `127.0.0.1,localhost`
* `PGDATABASE`: `akili_db` (or your local DB name)
* `PGUSER`: `akili_user` (or your local DB user)
* `PGPASSWORD`: (Your local DB password)
* `PGHOST`: `localhost`
* `PGPORT`: `5432`
* `GEMINI_API_KEY`: (Your key)
* `GROQ_API_KEY`: (Your key)

---

## Project Structure

### Team Lead (In Progress)
* **core** - Base templates, PWA, AI utilities
* **users** - Authentication, freemium credits, referrals
* **admin_syllabus** - JAMB/SSCE/JSS syllabus storage

### Developer 1 (To Implement)
* **courses** - Dashboard, course management, lessons
* **quizzes** - Dynamic quiz generation
* **profiles** - Profile page, referrals, account deletion

### Developer 2 (To Implement)
* **exams** - Mock exam center
* **payments** - Paystack integration

---

## Key Features

* **AI Smart Fallback**: 4-tier system (Gemini Flash → Groq → Gemini Paid → Circuit Breaker)
* **Freemium Credits**: 10 daily credits, +2 per referral (max 30)
* **PWA Ready**: Offline-capable Progressive Web App
* **Mobile-First**: Responsive design with bottom navigation
* **LaTeX Support**: KaTeX rendering for math/science formulas

---

## Tech Stack

* **Backend**: Django 5.2.8, PostgreSQL
* **Frontend**: Tailwind CSS, Vanilla JavaScript
* **AI**: Google Gemini, Groq API
* **Payment**: Paystack (to be implemented)

---

## Developer Notes

* Username is auto-generated from email (part before @)
* All user displays show `full_name`, not `username`
* Templates extend `base.html` for consistent UI
* KaTeX is pre-loaded for LaTeX formula rendering
* Use `call_ai_with_fallback()` from `core.utils.ai_fallback`

---

## Deployment

This project is configured for deployment on platforms like Render. A `render.yaml` file is included in the root directory for easy "Blueprint" setup. For any production environment, ensure `DEBUG` is set to `False` and `ALLOWED_HOSTS` is set to your production domain.

---

## License

Copyright © 2025 Akili. All rights reserved.
