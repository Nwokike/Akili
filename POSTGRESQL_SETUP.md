# PostgreSQL Local Setup Guide for Akili

This guide will help you set up PostgreSQL locally for the Akili project on Windows.

## Option 1: PostgreSQL with pgAdmin (Recommended for Windows)

### 1. Download and Install PostgreSQL

1. Visit [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
2. Download the Windows installer (latest stable version)
3. Run the installer and follow these steps:
   - Choose installation directory (default is fine)
   - Select components: PostgreSQL Server, pgAdmin 4, Command Line Tools
   - Choose data directory (default is fine)
   - **Set a password for the `postgres` superuser** (REMEMBER THIS!)
   - Port: Use default `5432`
   - Locale: Default locale
   - Complete the installation

### 2. Create Akili Database

#### Using pgAdmin (GUI Method):
1. Open pgAdmin 4
2. Connect to PostgreSQL server (enter your password)
3. Right-click on "Databases" → "Create" → "Database"
4. Database name: `akili_db`
5. Owner: `postgres`
6. Click "Save"

#### Using psql Command Line:
```bash
# Open Command Prompt or PowerShell
psql -U postgres

# Inside psql, run:
CREATE DATABASE akili_db;
\q
```

### 3. Configure Environment Variables

Create a `.env` file in your project root:

```env
# Database Configuration
PGDATABASE=akili_db
PGUSER=postgres
PGPASSWORD=your_password_here
PGHOST=localhost
PGPORT=5432
DATABASE_URL=postgresql://postgres:your_password_here@localhost:5432/akili_db

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# AI API Keys (get these from respective platforms)
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
```

### 4. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows CMD:
venv\Scripts\activate.bat
# Windows PowerShell:
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit: `http://localhost:8000/`

---

## Option 2: PostgreSQL App (Alternative for Windows)

### 1. Download PostgreSQL App
- Visit [PostgresApp](https://postgresapp.com/) or use Docker Desktop with PostgreSQL image

### 2. Using Docker (Advanced)

```bash
# Pull PostgreSQL image
docker pull postgres:15

# Run PostgreSQL container
docker run --name akili-postgres -e POSTGRES_PASSWORD=your_password -e POSTGRES_DB=akili_db -p 5432:5432 -d postgres:15
```

Then follow steps 3-7 from Option 1.

---

## Troubleshooting

### Issue: "psycopg2" installation fails
**Solution**: Install the binary version:
```bash
pip install psycopg2-binary
```

### Issue: "password authentication failed for user postgres"
**Solution**: 
1. Verify your password in `.env` matches the PostgreSQL password
2. Try resetting PostgreSQL password:
```sql
ALTER USER postgres WITH PASSWORD 'new_password';
```

### Issue: "FATAL: database 'akili_db' does not exist"
**Solution**: Create the database using pgAdmin or psql as shown in step 2

### Issue: "could not connect to server: Connection refused"
**Solution**:
1. Ensure PostgreSQL service is running:
   - Windows: Services → PostgreSQL → Start
2. Check if port 5432 is available:
```bash
netstat -an | findstr 5432
```

---

## Verify PostgreSQL Connection

Test your connection using Python:

```python
import psycopg2

try:
    conn = psycopg2.connect(
        dbname="akili_db",
        user="postgres",
        password="your_password",
        host="localhost",
        port="5432"
    )
    print("✅ PostgreSQL connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

---

## Next Steps

1. Access Django Admin: `http://localhost:8000/admin/`
2. Add syllabus content for JAMB, SSCE, and JSS subjects
3. Get API keys from:
   - Gemini: https://ai.google.dev/
   - Groq: https://console.groq.com/
4. Start building your courses!

---

## Team Collaboration Notes

Each developer should:
1. Clone the repository
2. Follow this guide to set up PostgreSQL locally
3. Create their own `.env` file (never commit this!)
4. Run migrations to sync database schema
5. Create their own superuser for testing

---

## Production Setup (Render Free Tier)

See `render.yaml` for automatic deployment configuration. Render will:
- Automatically provision a PostgreSQL database
- Set environment variables from Render dashboard
- Deploy the application on commit to main branch

---

**Questions?** Contact the team lead for assistance.
