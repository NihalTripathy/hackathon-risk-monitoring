# Complete Setup Guide - Schedule Risk Monitoring System

This guide explains everything you need to set up and run the Schedule Risk Monitoring project from scratch, including database setup, environment variables, virtual environments, and both backend and frontend configuration.

---

## Table of Contents

1. [Understanding Virtual Environments (venv)](#understanding-virtual-environments-venv)
2. [Prerequisites](#prerequisites)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Running the Application](#running-the-application)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## Understanding Virtual Environments (venv)

### What is a Virtual Environment?

A **virtual environment (venv)** is an isolated Python environment that allows you to install packages specific to a project without affecting your system-wide Python installation or other projects.

### Why is venv Important?

1. **Dependency Isolation**: Each project can have different versions of the same package
2. **Avoid Conflicts**: Prevents package version conflicts between projects
3. **Clean System**: Keeps your system Python installation clean
4. **Reproducibility**: Ensures everyone working on the project uses the same package versions
5. **Easy Cleanup**: Delete the `venv` folder to remove all project dependencies

### Do You Need the venv Folder from the Repository?

**NO!** You should **NOT** use the `venv` folder from the repository (if it exists). Here's why:

- ✅ **Create Your Own**: Each developer creates their own `venv` folder locally
- ✅ **Platform-Specific**: venv folders contain platform-specific binaries (Windows vs Linux vs Mac)
- ✅ **Git Ignored**: The `venv` folder is in `.gitignore` and shouldn't be committed
- ✅ **Personal Setup**: Each developer's venv is configured for their specific system

### How venv Works

```
Your Project/
├── venv/                    ← Created locally (NOT from repo)
│   ├── Scripts/            ← Windows activation script
│   ├── bin/                ← Linux/Mac activation script
│   └── Lib/                ← Installed packages (isolated)
├── requirements.txt        ← Package list (shared in repo)
└── your_code.py
```

When you activate venv:
- Python uses packages from `venv/Lib/` instead of system-wide packages
- `pip install` installs packages into `venv/`, not system-wide
- You can have multiple venv folders for different projects

---

## Prerequisites

Before starting, ensure you have the following installed:

### Required Software

1. **Python 3.13+**
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version` or `python3 --version`

2. **PostgreSQL 12+**
   - Download from: https://www.postgresql.org/download/
   - Includes pgAdmin (database administration tool)
   - Verify: PostgreSQL service should be running

3. **Node.js 18+ and npm**
   - Download from: https://nodejs.org/
   - Verify: `node --version` and `npm --version`

4. **Git** (optional, if cloning from repository)
   - Download from: https://git-scm.com/downloads

### System Requirements

- **Windows 10+**, **macOS 10.15+**, or **Linux** (Ubuntu 20.04+)
- At least **2GB RAM** free
- **Internet connection** for downloading packages

---

## Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd schedule-risk-backend
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
```

**Linux/Mac:**
```bash
python3 -m venv venv
```

This creates a new `venv` folder in the `schedule-risk-backend` directory. This folder is **NOT** in the repository - you create it locally.

### Step 3: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

**How to know it's activated:**
- Your command prompt will show `(venv)` at the beginning
- Example: `(venv) C:\Hackathon2025\hackathon-risk-monitoring\schedule-risk-backend>`

### Step 4: Install Python Dependencies

With venv activated, install all required packages:

```bash
pip install -r requirements.txt
```

This installs packages like FastAPI, SQLAlchemy, pandas, scikit-learn, etc. into your `venv` folder, not system-wide.

**Expected output:** You should see packages being downloaded and installed. This may take 2-5 minutes.

### Step 5: Setup PostgreSQL Database

#### 5.1. Open pgAdmin

- Launch **pgAdmin** (installed with PostgreSQL)
- Connect to your PostgreSQL server (usually `localhost`)

#### 5.2. Create Database

1. Right-click **"Databases"** → **"Create"** → **"Database..."**
2. **Database name**: `schedule_risk_db`
3. **Owner**: `postgres` (default)
4. Click **"Save"**

#### 5.3. Find Your PostgreSQL Password

You need your PostgreSQL `postgres` user password. Common default passwords:
- `postgres`
- `root`
- `admin`
- `password`
- (or the password you set during PostgreSQL installation)

**To reset password (if needed):**
1. In pgAdmin, right-click **"postgres"** user → **"Properties"**
2. Go to **"Definition"** tab
3. Set a new password
4. Click **"Save"**

### Step 6: Create Environment Variables File

Create a `.env` file in the `schedule-risk-backend` directory:

**Windows (PowerShell):**
```powershell
New-Item -Path .env -ItemType File
```

**Linux/Mac:**
```bash
touch .env
```

**Or manually create** a file named `.env` in the `schedule-risk-backend` folder.

### Step 7: Configure Environment Variables

Open the `.env` file and add the following configuration:

```env
# ============================================
# REQUIRED: Database Configuration
# ============================================
# Replace YOUR_PASSWORD with your actual PostgreSQL password
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/schedule_risk_db

# ============================================
# REQUIRED: JWT Secret Key
# ============================================
# Generate a secure random key (minimum 32 characters)
# Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-very-long-secret-key-minimum-32-characters-change-in-production

# ============================================
# OPTIONAL: ML Model Configuration
# ============================================
USE_ML_MODEL=false
ML_MODEL_PATH=models/ml_risk_model.pkl
ML_ENSEMBLE_WEIGHT=0.7
ML_FALLBACK_TO_RULE_BASED=true
ML_MIN_TRAINING_SAMPLES=50

# ============================================
# OPTIONAL: LLM Provider Configuration
# ============================================
# Option 1: Hugging Face (requires API key)
# HUGGINGFACE_API_KEY=your_huggingface_api_key_here
# HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct:together

# Option 2: Groq (fast, free tier available)
# GROQ_API_KEY=your_groq_api_key_here
# GROQ_MODEL=llama-3.1-8b-instant

# Option 3: Ollama (local, no API key needed)
# OLLAMA_MODEL=llama2

# ============================================
# OPTIONAL: Performance Configuration
# ============================================
ENABLE_REQUEST_LOGGING=true
CORS_ORIGINS=http://localhost:3000
```

**Important Notes:**

1. **DATABASE_URL**: Replace `YOUR_PASSWORD` with your actual PostgreSQL password
   - Format: `postgresql://username:password@host:port/database_name`
   - Example: `postgresql://postgres:mypassword123@localhost:5432/schedule_risk_db`

2. **JWT_SECRET_KEY**: Generate a secure random key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Copy the output and paste it as your `JWT_SECRET_KEY` value.

3. **Optional Variables**: LLM and ML configurations are optional. The system works without them, but some features (like AI-powered risk explanations) won't be available.

### Step 8: Initialize Database Tables

The database tables are created automatically when you start the server. However, you can also initialize them manually:

```bash
python init_db.py
```

**Expected output:**
```
Initializing database...
✓ Database tables created successfully!
```

If you see an error, check:
- PostgreSQL service is running
- Database `schedule_risk_db` exists
- `DATABASE_URL` in `.env` is correct

### Step 9: Verify Backend Setup

Test that everything is configured correctly:

```bash
python run.py
```

**Expected output:**
```
Starting Schedule Risk Monitoring API Server...
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**If you see errors:**
- **"ModuleNotFoundError"**: Activate venv and run `pip install -r requirements.txt`
- **"password authentication failed"**: Check `DATABASE_URL` in `.env`
- **"connection refused"**: Ensure PostgreSQL service is running
- **"database does not exist"**: Create database in pgAdmin (Step 5.2)

**Stop the server** with `Ctrl+C` for now. We'll start it again after frontend setup.

---

## Frontend Setup

### Step 1: Navigate to Frontend Directory

Open a **new terminal window** (keep backend terminal open) and navigate to:

```bash
cd schedule-risk-frontend
```

### Step 2: Install Node.js Dependencies

```bash
npm install
```

This installs all required packages (Next.js, React, Tailwind CSS, etc.) into `node_modules/` folder.

**Expected output:** Packages being downloaded. This may take 2-5 minutes.

### Step 3: Create Environment Variables File

Create a `.env.local` file in the `schedule-risk-frontend` directory:

**Windows (PowerShell):**
```powershell
New-Item -Path .env.local -ItemType File
```

**Linux/Mac:**
```bash
touch .env.local
```

### Step 4: Configure Frontend Environment Variables

Open `.env.local` and add:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

This tells the frontend where to find the backend API.

**Note:** If your backend runs on a different port, update this URL accordingly.

### Step 5: Verify Frontend Setup

Test that everything is configured:

```bash
npm run dev
```

**Expected output:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
- event compiled client and server successfully
```

**If you see errors:**
- **"Module not found"**: Run `npm install` again
- **Port 3000 in use**: Next.js will automatically use the next available port (3001, 3002, etc.)

**Stop the server** with `Ctrl+C` for now. We'll start both servers together next.

---

## Running the Application

### Starting Both Servers

You need **two terminal windows** - one for backend, one for frontend.

#### Terminal 1: Backend Server

```bash
# Navigate to backend
cd schedule-risk-backend

# Activate virtual environment (IMPORTANT!)
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Start backend server
python run.py
```

**Keep this terminal open.** Backend should be running on `http://localhost:8000`

#### Terminal 2: Frontend Server

```bash
# Navigate to frontend
cd schedule-risk-frontend

# Start frontend server
npm run dev
```

**Keep this terminal open.** Frontend should be running on `http://localhost:3000`

### Accessing the Application

1. **Frontend UI**: Open browser to `http://localhost:3000`
2. **Backend API Docs**: Open browser to `http://localhost:8000/docs`
3. **Health Check**: Open browser to `http://localhost:8000/health`

### First-Time User Registration

1. Go to `http://localhost:3000`
2. Click **"Sign Up"** or navigate to `/signup`
3. Enter:
   - Email address
   - Password
   - Full name (optional)
4. Click **"Register"**
5. You'll be automatically logged in

### Quick Start Workflow

1. **Register/Login** at `http://localhost:3000`
2. **Upload a CSV file** with project schedule data
3. **View Dashboard** with forecasts and risks
4. **Analyze Risks** and get explanations
5. **Simulate Mitigations** to test "what-if" scenarios

---

## Verification & Testing

### Backend Health Check

Visit: `http://localhost:8000/health`

**Expected response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Backend API Documentation

Visit: `http://localhost:8000/docs`

This shows all available API endpoints with interactive testing.

### Frontend Connection Test

1. Open `http://localhost:3000`
2. Try to register a new user
3. If successful, backend connection is working

### Database Verification

In pgAdmin:
1. Connect to `schedule_risk_db`
2. Expand **"Schemas"** → **"public"** → **"Tables"**
3. You should see tables:
   - `users`
   - `projects`
   - `activities`
   - `audit_logs`

---

## Troubleshooting

### Backend Issues

#### "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Make sure venv is activated (you should see (venv) in prompt)
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### "password authentication failed for user postgres"

**Solution:**
1. Check `.env` file has correct password in `DATABASE_URL`
2. Try common passwords: `postgres`, `root`, `admin`, `password`
3. Reset password in pgAdmin: Right-click `postgres` user → Properties → Definition

#### "connection refused" or "could not connect to server"

**Solution:**
1. Ensure PostgreSQL service is running
   - **Windows**: Check Services (services.msc) → PostgreSQL
   - **Linux**: `sudo systemctl status postgresql`
   - **Mac**: Check PostgreSQL in System Preferences
2. Verify PostgreSQL is listening on port 5432

#### "database 'schedule_risk_db' does not exist"

**Solution:**
1. Open pgAdmin
2. Create database: Right-click "Databases" → Create → Database
3. Name: `schedule_risk_db`
4. Owner: `postgres`

#### "JWT_SECRET_KEY is not set"

**Solution:**
1. Check `.env` file exists in `schedule-risk-backend/`
2. Verify `JWT_SECRET_KEY` is set (minimum 32 characters)
3. Generate new key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Frontend Issues

#### "Network Error" or "Failed to fetch"

**Solution:**
1. Verify backend is running on `http://localhost:8000`
2. Check `.env.local` has: `NEXT_PUBLIC_API_BASE=http://localhost:8000/api`
3. Restart frontend server after changing `.env.local`

#### "401 Unauthorized"

**Solution:**
1. User needs to login/register first
2. Check token is stored in browser localStorage
3. Token expires after 7 days - login again

#### "Port 3000 already in use"

**Solution:**
- Next.js will automatically use the next available port (3001, 3002, etc.)
- Or kill the process using port 3000:
  - **Windows**: `netstat -ano | findstr :3000` then `taskkill /PID <pid> /F`
  - **Linux/Mac**: `lsof -ti:3000 | xargs kill`

### Virtual Environment Issues

#### "venv is not recognized as an internal or external command"

**Solution:**
- Use full path: `python -m venv venv`
- Or use `python3 -m venv venv` on Linux/Mac

#### "Activate script cannot be loaded because running scripts is disabled"

**Solution (Windows PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Virtual environment not activating

**Solution:**
- Make sure you're in the `schedule-risk-backend` directory
- Check `venv` folder exists
- Use correct activation command for your OS

### Database Issues

#### Tables not created

**Solution:**
1. Run manually: `python init_db.py`
2. Check database connection in `.env`
3. Verify PostgreSQL user has CREATE TABLE permissions

#### "relation does not exist" errors

**Solution:**
- Tables might not be initialized
- Run: `python init_db.py`
- Or restart backend server (tables are auto-created on startup)

---

## Summary Checklist

Use this checklist to ensure complete setup:

### Backend Setup ✅
- [ ] Python 3.13+ installed
- [ ] Virtual environment created (`venv` folder)
- [ ] Virtual environment activated (see `(venv)` in prompt)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] PostgreSQL installed and running
- [ ] Database `schedule_risk_db` created in pgAdmin
- [ ] `.env` file created with:
  - [ ] `DATABASE_URL` with correct password
  - [ ] `JWT_SECRET_KEY` (32+ characters)
- [ ] Database tables initialized (`python init_db.py`)
- [ ] Backend server starts without errors (`python run.py`)

### Frontend Setup ✅
- [ ] Node.js 18+ installed
- [ ] Dependencies installed (`npm install`)
- [ ] `.env.local` file created with `NEXT_PUBLIC_API_BASE`
- [ ] Frontend server starts without errors (`npm run dev`)

### Verification ✅
- [ ] Backend health check works (`http://localhost:8000/health`)
- [ ] Backend API docs accessible (`http://localhost:8000/docs`)
- [ ] Frontend loads (`http://localhost:3000`)
- [ ] Can register new user
- [ ] Can login
- [ ] Can upload CSV file

---

## Important Notes

### Virtual Environment Best Practices

1. **Always activate venv** before running backend:
   ```bash
   # Windows
   .\venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Deactivate when done** (optional):
   ```bash
   deactivate
   ```

3. **Don't commit venv** to Git (already in `.gitignore`)

4. **Recreate if corrupted**:
   ```bash
   # Delete old venv
   rm -rf venv  # Linux/Mac
   rmdir /s venv  # Windows
   
   # Create new one
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

### Environment Variables Security

- **Never commit `.env` files** to Git (already in `.gitignore`)
- **Use strong passwords** for database and JWT secret
- **Generate secure JWT keys** using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Change default values** in production

### Development Workflow

1. **Start backend first** (Terminal 1)
2. **Then start frontend** (Terminal 2)
3. **Keep both terminals open** while developing
4. **Backend auto-reloads** on code changes (if using `python run.py`)
5. **Frontend auto-reloads** on code changes (Next.js hot reload)

---

## Next Steps

After setup is complete:

1. **Upload a CSV file** with project schedule data
2. **Explore the dashboard** to see forecasts and risks
3. **Read the documentation**:
   - `COMPLETE_ARCHITECTURE_AND_EXPERT_ANALYSIS.md`
   - `COMPLETE_FEATURES_GUIDE.md`
   - `UI_AND_API_COMPLETE_EXPLANATION.md`
4. **Test features**:
   - Risk analysis
   - Forecasting
   - Mitigation simulation
   - Anomaly detection

---

## Support

If you encounter issues not covered in this guide:

1. Check the troubleshooting section above
2. Review backend logs in Terminal 1
3. Review frontend logs in Terminal 2
4. Check browser console for frontend errors
5. Verify all prerequisites are installed correctly
6. Ensure both servers are running simultaneously

For detailed API documentation, visit: `http://localhost:8000/docs`
