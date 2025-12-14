# Schedule Risk Monitoring - Backend API

A comprehensive FastAPI-based backend system for project schedule risk analysis, forecasting, and mitigation simulation with user authentication, ML-powered risk prediction, and LLM-powered risk explanations.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Overview](#project-overview)
3. [Architecture & Project Structure](#architecture--project-structure)
4. [Setup Instructions](#setup-instructions)
5. [Environment Configuration](#environment-configuration)
6. [Database Setup](#database-setup)
7. [Authentication System](#authentication-system)
8. [API Endpoints](#api-endpoints)
9. [Core Logic & Workflow](#core-logic--workflow)
10. [ML Model Integration](#ml-model-integration)
11. [LLM Integration](#llm-integration)
12. [Performance Optimizations](#performance-optimizations)
13. [Troubleshooting](#troubleshooting)
14. [Production Deployment](#production-deployment)

---

## Quick Start

### Start the Server (One Command)

After setting up your `.env` file, start the server with:

```bash
python run.py
```

That's it! The server will start on `http://localhost:8000`

**Alternative commands:**
- **Windows**: `start.bat` or `python run.py`
- **Linux/Mac**: `./start.sh` or `python3 run.py`
- **With Make**: `make start` or `make dev`

### First Time Setup

1. **Install dependencies** (required first step):
   ```bash
   pip install -r requirements.txt
   ```
   
   Or if using virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create `.env` file** (see [Environment Configuration](#environment-configuration))
3. **Setup PostgreSQL** (see [Database Setup](#database-setup))
4. **Start server**: `python run.py`

### Server URLs

Once running:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Production Deployment

For production (AWS, Azure, etc.), set environment variables:

```bash
# Production mode (no auto-reload)
RELOAD=false HOST=0.0.0.0 PORT=8000 python run.py

# Or use Make
make prod
```

The server automatically:
- ✅ Loads `.env` file
- ✅ Initializes database tables
- ✅ Validates configuration
- ✅ Works on any platform (Windows, Linux, Mac, AWS, Azure, Docker)

---

## Project Overview

This backend API provides:

- **Project Management**: Upload and manage project schedules from CSV files
- **Risk Analysis**: Identify and score schedule risks using digital twin technology
- **ML-Powered Predictions**: Machine learning model for enhanced risk prediction (optional)
- **Forecasting**: Monte Carlo simulation for P50/P80/P90/P95 completion forecasts
- **Mitigation Simulation**: Test "what-if" scenarios for risk reduction with ranked options
- **Anomaly Detection**: Automatic detection of zombie tasks and resource black holes
- **LLM Explanations**: AI-powered explanations of risk factors
- **User Authentication**: Token-based JWT authentication with user isolation
- **Audit Logging**: Complete event history for all project operations
- **Portfolio Management**: Multi-project analysis and resource allocation

### Tech Stack

- **Framework**: FastAPI (Python 3.13+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **ML**: scikit-learn for risk prediction models
- **LLM**: Support for Ollama (local), Groq, and Hugging Face
- **Data Processing**: Pandas, NumPy, NetworkX for CSV processing and calculations
- **Caching**: In-memory caching for digital twins and forecasts

---

## Architecture & Project Structure

The backend follows a **modular, SOLID-compliant architecture** with clear separation of concerns.

```
schedule-risk-backend/
├── main.py                 # FastAPI application entry point
├── run.py                  # Simple server startup script (use this!)
├── start.bat               # Windows startup script
├── start.sh                # Linux/Mac startup script
├── Makefile                # Make commands (optional)
├── .env                    # Environment variables (create this)
├── requirements.txt        # Python dependencies
│
├── domain/                 # Domain Layer (Business Logic)
│   ├── entities.py        # Domain entities (User, Project, Activity, etc.)
│   └── interfaces.py      # Repository and service interfaces
│
├── infrastructure/         # Infrastructure Layer (External Dependencies)
│   ├── database/
│   │   ├── connection.py  # Database connection management
│   │   └── models.py      # SQLAlchemy ORM models
│   ├── repositories/      # Repository implementations
│   │   ├── user_repository.py
│   │   ├── project_repository.py
│   │   ├── activity_repository.py
│   │   └── audit_log_repository.py
│   └── adapters/          # Adapters for legacy code
│
├── application/            # Application Layer (Use Cases)
│   └── services/
│       └── project_service.py  # High-level business operations
│
├── framework/              # Framework Layer (DI Container)
│   ├── container.py       # Dependency injection container
│   └── bootstrap.py       # Application bootstrap
│
├── api/                    # Presentation Layer (HTTP Endpoints)
│   ├── auth.py            # Authentication endpoints (register, login)
│   ├── projects.py        # Project upload and listing
│   ├── risks.py           # Risk analysis endpoints
│   ├── forecast.py        # Forecasting endpoints
│   ├── simulate.py        # Mitigation simulation
│   ├── explain.py         # LLM-powered risk explanations
│   ├── ml_training.py     # ML model training endpoints
│   └── portfolio.py       # Portfolio management endpoints
│
└── core/                   # Legacy/Shared Code
    ├── database.py        # Database connection (deprecated - use infrastructure)
    ├── db_models.py       # SQLAlchemy models (deprecated - use infrastructure)
    ├── db_service.py      # Database CRUD operations
    ├── db_adapter.py      # Compatibility layer
    │
    ├── auth_dependencies.py  # Authentication dependency injection
    ├── auth.py            # JWT token creation/validation
    ├── user_service.py    # User management
    ├── project_auth.py    # Project ownership verification
    │
    ├── csv_connector.py   # CSV parsing and validation
    ├── risk_pipeline.py   # Risk analysis pipeline
    ├── risk_model.py      # Risk scoring algorithms
    ├── digital_twin.py    # Digital twin generation
    ├── features.py        # Feature extraction
    ├── anomalies.py       # Anomaly detection
    ├── mc_forecaster.py   # Monte Carlo forecasting
    ├── mitigation.py      # Mitigation simulation logic
    ├── llm_adapter.py     # LLM provider integration
    ├── ml_risk_model.py   # ML model integration
    │
    ├── config.py          # Application configuration
    ├── middleware.py      # Request logging middleware
    └── audit_log.py       # Audit logging utilities
```

### Architecture Principles

#### SOLID Principles

1. **Single Responsibility Principle (SRP)**: Each class/module has one reason to change
2. **Open/Closed Principle (OCP)**: Open for extension, closed for modification
3. **Liskov Substitution Principle (LSP)**: Repository implementations are interchangeable
4. **Interface Segregation Principle (ISP)**: Small, focused interfaces
5. **Dependency Inversion Principle (DIP)**: High-level modules depend on abstractions

#### Layer Structure

```
API Layer (Presentation)
    ↓ (depends on)
Application Layer (Use Cases)
    ↓ (depends on)
Domain Layer (Business Logic & Interfaces)
    ↑ (implemented by)
Infrastructure Layer (Repositories & Database)
```

**Key Rule**: Dependencies flow inward. Outer layers depend on inner layers, never the reverse.

### Key Components

#### 1. **Domain Layer** (`domain/`)
- **Entities**: Pure business objects with no infrastructure dependencies
- **Interfaces**: Contracts that define what repositories and services must do
- Follows Domain-Driven Design principles

#### 2. **Infrastructure Layer** (`infrastructure/`)
- **Database**: SQLAlchemy models and connection management
- **Repositories**: Implement domain interfaces using SQLAlchemy
- **Adapters**: Bridge between legacy code and new architecture

#### 3. **Application Layer** (`application/`)
- **Services**: Coordinate between repositories and domain logic
- **Use Cases**: High-level operations that span multiple repositories

#### 4. **Framework Layer** (`framework/`)
- **Dependency Injection**: Container for managing dependencies
- **Bootstrap**: Initializes and wires dependencies

#### 5. **Authentication System** (`core/auth_dependencies.py`, `api/auth.py`)
- JWT token-based authentication
- Password hashing with bcrypt
- User registration and login
- Project ownership verification
- Protected endpoint decorators

#### 6. **Risk Analysis Pipeline** (`core/risk_pipeline.py`)
- CSV upload → Validation → Digital Twin → Risk Scoring → Forecasting
- Feature extraction from activities
- Anomaly detection (zombie tasks, resource black holes)
- Risk score calculation (rule-based or ML-enhanced)

#### 7. **Forecasting** (`core/mc_forecaster.py`)
- Monte Carlo simulation (2,000-10,000 simulations)
- P50, P80, P90, P95 percentile calculations
- Criticality Index (CI) calculation
- Confidence intervals

#### 8. **ML Integration** (`core/ml_risk_model.py`)
- Random Forest regressor for risk prediction
- Ensemble mode (ML + rule-based)
- Automatic fallback to rule-based
- Model training and versioning

#### 9. **LLM Integration** (`core/llm_adapter.py`)
- Multi-provider support (Ollama, Groq, Hugging Face)
- Automatic fallback chain
- Risk explanation generation

### Architecture Benefits

- ✅ **SOLID Principles**: Follows all five SOLID principles
- ✅ **Testability**: Easy to mock interfaces for unit testing
- ✅ **Flexibility**: Swap implementations without changing business logic
- ✅ **Maintainability**: Clear separation makes code easier to understand
- ✅ **Scalability**: Add new features without modifying existing code
- ✅ **Backward Compatibility**: Legacy code maintained alongside new architecture

---

## Setup Instructions

### Prerequisites

- Python 3.13+ 
- PostgreSQL 12+ (with pgAdmin)
- pip (Python package manager)

### Step 1: Install Dependencies

**Important**: Install dependencies first before running the server!

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

**If you get "ModuleNotFoundError"**, it means dependencies are not installed. Run:
```bash
pip install -r requirements.txt
```

The `run.py` script will automatically check for dependencies and show helpful error messages if anything is missing.

### Step 2: Configure Environment

Create a `.env` file in `schedule-risk-backend/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/schedule_risk_db

# JWT Secret Key (generate a secure random string, minimum 32 characters)
JWT_SECRET_KEY=your-very-long-secret-key-minimum-32-characters-change-in-production

# ML Model Configuration (Optional)
USE_ML_MODEL=false
ML_MODEL_PATH=models/ml_risk_model.pkl
ML_ENSEMBLE_WEIGHT=0.7
ML_FALLBACK_TO_RULE_BASED=true
ML_MIN_TRAINING_SAMPLES=50

# LLM Provider Configuration (Optional)
# Option 1: Hugging Face
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct:together

# Option 2: Groq (Fast, Free Tier Available)
# GROQ_API_KEY=your_groq_api_key_here
# GROQ_MODEL=llama-3.1-8b-instant

# Option 3: Ollama (Local, No API Key Needed)
# OLLAMA_MODEL=llama2

# Performance Configuration
ENABLE_REQUEST_LOGGING=true
CORS_ORIGINS=http://localhost:3000
```

**Important**: Replace `YOUR_PASSWORD` with your actual PostgreSQL password.

### Step 3: Setup PostgreSQL Database

1. **Open pgAdmin** (PostgreSQL administration tool)

2. **Create Database**:
   - Right-click "Databases" → "Create" → "Database..."
   - Name: `schedule_risk_db`
   - Owner: `postgres`
   - Click "Save"

3. **Find Your PostgreSQL Password**:
   - Check pgAdmin connection settings
   - Or reset: Right-click `postgres` user → Properties → Definition → Set new password
   - Common passwords: `postgres`, `root`, `admin`, `password`

4. **Update `.env` file** with your password:
   ```
   DATABASE_URL=postgresql://postgres:your_actual_password@localhost:5432/schedule_risk_db
   ```

### Step 4: Initialize Database

The database tables are created automatically when you start the server. Alternatively, you can run:

```bash
python init_db.py
```

### Step 5: Start the Server

**Simple way (recommended):**
```bash
python run.py
```

**Alternative ways:**
```bash
# Windows
start.bat

# Linux/Mac
./start.sh

# With Make
make start

# Manual (if needed)
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## Environment Configuration

### Required Variables

- **`DATABASE_URL`**: PostgreSQL connection string
  - Format: `postgresql://username:password@host:port/database_name`
  - Example: `postgresql://postgres:mypassword@localhost:5432/schedule_risk_db`

- **`JWT_SECRET_KEY`**: Secret key for JWT token signing
  - Minimum 32 characters
  - Use a secure random string in production
  - Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Optional Variables

#### ML Configuration
- **`USE_ML_MODEL`**: Enable ML model (default: `false`)
- **`ML_MODEL_PATH`**: Path to ML model file (default: `models/ml_risk_model.pkl`)
- **`ML_ENSEMBLE_WEIGHT`**: Weight for ML in ensemble (0.0-1.0, default: `0.7`)
- **`ML_FALLBACK_TO_RULE_BASED`**: Auto-fallback if ML fails (default: `true`)
- **`ML_MIN_TRAINING_SAMPLES`**: Minimum activities needed for training (default: `50`)

#### LLM Configuration
- **`HUGGINGFACE_API_KEY`**: Hugging Face API key for LLM
- **`HUGGINGFACE_MODEL`**: Model name (default: `Qwen/Qwen2.5-7B-Instruct:together`)
- **`GROQ_API_KEY`**: Groq API key (fast, free tier available)
- **`GROQ_MODEL`**: Groq model name
- **`OLLAMA_MODEL`**: Ollama model name (if using local Ollama)

#### Performance Configuration
- **`ENABLE_REQUEST_LOGGING`**: Enable/disable request logging (default: `true`)
- **`CORS_ORIGINS`**: Comma-separated list of allowed CORS origins

---

## Database Setup

### Database Schema

#### Tables

1. **`users`**
   - `id` (Primary Key)
   - `email` (Unique)
   - `hashed_password`
   - `full_name`
   - `created_at`
   - `is_active`

2. **`projects`**
   - `project_id` (Primary Key, UUID)
   - `user_id` (Foreign Key → users.id)
   - `created_at`
   - `updated_at`

3. **`activities`**
   - `id` (Primary Key)
   - `project_id` (Foreign Key → projects.project_id)
   - All CSV columns (Activity ID, Name, Duration, Start, Finish, etc.)
   - Dynamic columns based on CSV structure

4. **`audit_logs`**
   - `id` (Primary Key)
   - `project_id` (Foreign Key → projects.project_id)
   - `user_id` (Foreign Key → users.id)
   - `timestamp`
   - `event` (event type)
   - `details` (JSON metadata)

### Connection String Format

```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

Example:
```
postgresql://postgres:mypassword@localhost:5432/schedule_risk_db
```

### Automatic Table Creation

Tables are created automatically on server startup via `init_db()` in `main.py`. No manual SQL required.

---

## Authentication System

### Architecture

The authentication system uses **JWT (JSON Web Tokens)** with a centralized dependency injection pattern:

- **`core/auth_dependencies.py`**: Central authentication dependency
- **`core/auth.py`**: JWT token creation and validation
- **`core/user_service.py`**: User management (create, verify, get)
- **`core/project_auth.py`**: Project ownership verification

### Authentication Flow

```
1. User registers/logs in → JWT token generated
2. Client stores token (localStorage in frontend)
3. Client sends token in Authorization header: "Bearer <token>"
4. get_current_user dependency validates token
5. User object injected into endpoint
6. Project operations verify ownership
```

### Public Endpoints (No Authentication)

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (form data)
- `POST /api/auth/login-json` - Login (JSON)
- `GET /api/llm/status` - LLM status
- `GET /health` - Health check
- `GET /docs` - API documentation

### Protected Endpoints (Authentication Required)

All other endpoints require a valid JWT token in the `Authorization: Bearer <token>` header.

### Using Authentication in Code

```python
from core.auth_dependencies import get_current_user
from api.auth import UserResponse

@router.get("/my-endpoint")
def my_endpoint(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # current_user is authenticated
    return {"user_id": current_user.id, "email": current_user.email}
```

### Project Ownership Verification

```python
from core.project_auth import verify_project_ownership

@router.get("/projects/{project_id}/my-endpoint")
def my_endpoint(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_project_ownership(db, project_id, current_user)
    # Now safe to access project
    ...
```

### Token Details

- **Expiration**: 7 days
- **Algorithm**: HS256
- **Format**: `{"sub": "user_email", "exp": timestamp}`

---

## API Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"  // optional
}
```

#### Login
```http
POST /api/auth/login-json
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Projects

#### Upload Project CSV
```http
POST /api/projects/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <CSV file>
```

#### List Projects
```http
GET /api/projects?limit=50
Authorization: Bearer <token>
```

#### Get Project Audit Log
```http
GET /api/projects/{project_id}/audit
Authorization: Bearer <token>
```

### Risk Analysis

#### Get Top Risks
```http
GET /api/projects/{project_id}/risks/top?limit=10
Authorization: Bearer <token>
```

Response includes:
- Risk scores with explanations
- Risk factors (delay, critical_path, resource)
- Key metrics (delay days, float, critical path status)
- Problem statement format explanations

#### Get Anomalies
```http
GET /api/projects/{project_id}/anomalies
Authorization: Bearer <token>
```

Returns:
- Zombie tasks (tasks that should have started but didn't)
- Resource black holes (overloaded resources with time-phased overlaps)

### Forecasting

#### Get Forecast
```http
GET /api/projects/{project_id}/forecast
Authorization: Bearer <token>
```

Response includes:
- P50, P80, P90, P95 percentiles
- Criticality Index (CI) count
- Forecast timeline data

### Risk Explanation

#### Get Risk Explanation
```http
GET /api/projects/{project_id}/explain/{activity_id}?use_llm=true
Authorization: Bearer <token>
```

Response includes:
- LLM-powered or rule-based explanation
- Key factors and recommendations
- Method used (llm_ollama, llm_groq, llm_huggingface, rule_based)

### Mitigation Simulation

#### Simulate Mitigation
```http
POST /api/projects/{project_id}/simulate
Authorization: Bearer <token>
Content-Type: application/json

{
  "activity_id": "A001",
  "duration_reduction": 5,  // Reduce duration by 5 days
  "risk_mitigation": 0.2    // Reduce risk by 20%
}
```

#### Get Ranked Mitigation Options
```http
GET /api/projects/{project_id}/mitigations/{activity_id}
Authorization: Bearer <token>
```

Returns top 5-10 ranked mitigation options with:
- Utility score (ranked by best impact)
- P50/P80 improvement
- Cost impact
- FTE days required

### ML Model Management

#### Get ML Status
```http
GET /api/ml/status
Authorization: Bearer <token>
```

#### Train ML Model
```http
POST /api/ml/train
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_ids": null,  // null = use all projects
  "use_background": false
}
```

#### Get ML Metrics
```http
GET /api/ml/metrics
Authorization: Bearer <token>
```

---

## Core Logic & Workflow

### Project Upload Flow

```
1. CSV Upload (api/projects.py)
   ↓
2. CSV Validation (core/csv_connector.py)
   - Check required columns
   - Validate data types
   - Parse dates
   ↓
3. Store in Database (core/db_service.py)
   - Create Project record
   - Store all Activities
   - Create Audit Log entry
   ↓
4. Generate Digital Twin (core/digital_twin.py)
   - Extract features from activities
   - Build activity relationships
   - Cache in memory
   ↓
5. Risk Analysis (core/risk_pipeline.py)
   - Calculate risk scores (rule-based or ML-enhanced)
   - Identify anomalies
   - Generate risk factors
```

### Risk Scoring Algorithm

The risk model (`core/risk_model.py`) calculates risk scores based on:

1. **Schedule Delay Score** (25%): Deviation from baseline schedule
2. **Progress Slip Score** (20%): Actual vs planned progress
3. **Critical Path Score** (20%): Position on critical path + float
4. **Risk Register Score** (15%): Probability × Impact + expected delay
5. **Dependency Score** (10%): Number of dependencies + critical depth
6. **Resource Overload Score** (10%): Resource utilization and overlaps

**Risk Score Formula**:
```python
risk_score = (
    0.25 * schedule_delay_score +
    0.20 * progress_slip_score +
    0.20 * critical_path_score +
    0.15 * risk_register_score +
    0.10 * dependency_score +
    0.10 * resource_overload_score
)
```

- ✅ Weights sum to 1.0
- ✅ Each component normalized to 0-100
- ✅ Final score clamped to 0-100

### Forecasting Algorithm

Monte Carlo Simulation (`core/mc_forecaster.py`):

1. **Generate Scenarios**: 2,000-10,000 random scenarios (default: 2,000 for API)
2. **Apply Risk Factors**: Adjust durations based on risk scores
3. **Calculate Critical Path**: Find longest path through project using NetworkX
4. **Aggregate Results**: Calculate P50 (median), P80, P90, P95 percentiles
5. **Calculate Criticality Index**: % of simulations where activity is on critical path
6. **Generate Timeline**: Forecast completion dates

### Digital Twin Generation

The digital twin (`core/digital_twin.py`) creates a computational model of the project:

- **Activity Graph**: Network of activities and dependencies (NetworkX)
- **Feature Extraction**: Numerical features for ML/analysis
- **Relationship Mapping**: Predecessor/successor relationships
- **Caching**: Stored in memory for fast access

### Anomaly Detection

**Zombie Tasks** (`core/anomalies.py`):
- Tasks with `planned_start < today`
- `actual_start` is None and `percent_complete == 0`
- Calculates days overdue

**Resource Black Holes**:
- Time-phased analysis identifies resource overlaps
- Calculates utilization at each time interval
- Tracks critical period overlaps

### Mitigation Simulation

When simulating mitigations (`core/mitigation.py`):

1. **Load Project**: Get activities from database
2. **Apply Changes**: Modify duration/risk for target activity
3. **Recalculate**: Re-run risk analysis and forecasting
4. **Rank Options**: Calculate utility score = improvement - cost_penalty - fte_penalty
5. **Compare**: Show before/after metrics
6. **Return Impact**: Quantify improvement in schedule and risk score

---

## ML Model Integration

### Overview

The ML risk model enhances the existing rule-based risk model by learning from historical project data. It's designed to be **backward compatible** - existing functionality continues to work while ML provides improved predictions.

### Quick Start

#### 1. Check ML Status

```http
GET /api/ml/status
Authorization: Bearer <token>
```

Response:
```json
{
  "ml_enabled": false,
  "model_available": false,
  "model_path": "models/ml_risk_model.pkl",
  "training_data": {
    "project_count": 5,
    "activity_count": 250,
    "feature_count": 16,
    "sample_count": 250,
    "sufficient_data": true
  },
  "can_train": true,
  "min_samples_required": 50
}
```

#### 2. Train ML Model

**Minimum Requirements**: At least 50 activities across all projects

```http
POST /api/ml/train
Authorization: Bearer <token>
Content-Type: application/json

{
  "project_ids": null,  // null = use all projects
  "use_background": false
}
```

#### 3. Enable ML Model

Add to `.env` file:
```env
USE_ML_MODEL=true
ML_ENSEMBLE_WEIGHT=0.7  # 70% ML, 30% rule-based
ML_FALLBACK_TO_RULE_BASED=true
```

#### 4. Use ML Predictions

Once enabled, risk predictions will automatically use ML model (with fallback to rule-based if needed).

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_ML_MODEL` | `false` | Enable ML model (requires trained model) |
| `ML_MODEL_PATH` | `models/ml_risk_model.pkl` | Path to saved ML model |
| `ML_ENSEMBLE_WEIGHT` | `0.7` | Weight for ML in ensemble (0.0-1.0) |
| `ML_FALLBACK_TO_RULE_BASED` | `true` | Auto-fallback if ML fails |
| `ML_MIN_TRAINING_SAMPLES` | `50` | Minimum activities needed for training |

### Ensemble Modes

- **Pure ML** (`ML_ENSEMBLE_WEIGHT=1.0`): Use only ML predictions
- **Pure Rule-Based** (`ML_ENSEMBLE_WEIGHT=0.0`): Use only rule-based (default)
- **Ensemble** (`0.0 < ML_ENSEMBLE_WEIGHT < 1.0`): Weighted combination

### How It Works

#### Training Process

1. **Data Collection**: Collects features and risk scores from all historical projects
2. **Label Generation**: Uses rule-based model predictions as labels (initially)
3. **Model Training**: Trains Random Forest regressor on collected data
4. **Evaluation**: Calculates R², MAE, MSE metrics
5. **Persistence**: Saves model and metadata to disk

#### Prediction Process

1. **Feature Extraction**: Computes features for each activity (same as rule-based)
2. **ML Prediction**: If ML enabled and available, predicts risk score
3. **Ensemble**: Combines ML and rule-based predictions (if configured)
4. **Fallback**: Falls back to rule-based if ML unavailable or fails

### Best Practices

1. **Training Data**: Minimum 50 activities, recommended 100+ for better accuracy
2. **Model Updates**: Retrain monthly or after significant new data
3. **Monitoring**: Regularly review R² and MAE scores
4. **Feature Importance**: Review which features matter most

---

## LLM Integration

### Supported Providers

The system tries LLM providers in this order:

1. **Ollama** (Local, Free, Recommended)
   - Runs locally on your computer
   - No API key needed
   - No internet required after setup
   - Setup: Install Ollama → `ollama pull llama2`

2. **Groq** (Fast API, Free Tier)
   - Very fast inference
   - Free tier available
   - Setup: Get API key at https://console.groq.com

3. **Hugging Face** (Fallback)
   - Free tier with limits
   - Setup: Get API key at https://huggingface.co/settings/tokens

### LLM Setup

#### Option 1: Ollama (Recommended)

1. **Install Ollama**: https://ollama.ai
2. **Pull a Model**:
   ```bash
   ollama pull llama2
   # or
   ollama pull mistral
   ```
3. **Configure** (optional, in `.env`):
   ```
   OLLAMA_MODEL=llama2
   ```
4. **Verify**: Check http://localhost:11434

#### Option 2: Groq

1. **Get API Key**: https://console.groq.com
2. **Add to `.env`**:
   ```
   GROQ_API_KEY=your_api_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   ```

#### Option 3: Hugging Face

1. **Get API Key**: https://huggingface.co/settings/tokens
2. **Add to `.env`**:
   ```
   HUGGINGFACE_API_KEY=your_api_key_here
   HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct:together
   ```

### LLM Usage

The LLM is used for risk explanations via `/api/projects/{project_id}/explain/{activity_id}?use_llm=true`.

The system automatically:
- Tries Ollama first (if running)
- Falls back to Groq (if API key set)
- Falls back to Hugging Face (if API key set)
- Falls back to rule-based explanation (if all LLM providers fail)

---

## Performance Optimizations

### Backend Optimizations

#### 1. Risk Pipeline Optimization ✅
- Build digital twin once and reuse for all activities
- Pass twin directly to `compute_features()` to avoid repeated cache lookups
- **Impact**: 20-30% improvement in risk calculation speed

#### 2. Response Compression ✅
- GZip middleware compresses responses larger than 1000 bytes
- **Impact**: 60-80% reduction in network transfer time

#### 3. Digital Twin Caching ✅
- Twin cached in memory for fast access
- Cache invalidation on project update

#### 4. Mitigation Ranking Optimization ✅
- Reduced simulations from 2,000 to 500 for ranking (3-4x faster)
- **Impact**: 10-15s → 2-7s for mitigation ranking

### Performance Metrics

| Operation | Expected Time | Status |
|-----------|---------------|--------|
| CSV Upload | 2-3s | ✅ Good |
| Risk Analysis (150 activities) | 0.6-0.9s | ✅ Good |
| Forecast (2K sims) | 1-3s | ✅ Good |
| Anomaly Detection | 0.5-1s | ✅ Good |
| Single Mitigation | 2-5s | ⚠️ Acceptable |
| Mitigation Ranking | 2-7s | ✅ Optimized |

### Scalability

- ✅ **Small Projects** (<100 activities): Excellent performance
- ✅ **Medium Projects** (100-500 activities): Good performance
- ⚠️ **Large Projects** (500-1000 activities): Acceptable, optimization recommended
- ⚠️ **Very Large Projects** (>1000 activities): May need optimization

### Recommendations

1. **Database Indexing**: Ensure indexes on frequently queried columns
2. **Response Caching**: Cache forecast/risks for 5 minutes (future)
3. **Parallel Processing**: Use multiprocessing for multiple mitigation simulations (future)
4. **Connection Pooling**: Ensure SQLAlchemy connection pooling is configured

---

## Troubleshooting

### Database Connection Issues

**Error: "password authentication failed"**
- Check `.env` file has correct PostgreSQL password
- Common passwords: `postgres`, `root`, `admin`, `password`
- Reset password in pgAdmin: Right-click `postgres` user → Properties → Definition

**Error: "connection refused"**
- Ensure PostgreSQL service is running
- Check port 5432 is not blocked
- Verify database `schedule_risk_db` exists (create in pgAdmin)

**Error: "database does not exist"**
- Create database in pgAdmin: Right-click "Databases" → Create → Database
- Name: `schedule_risk_db`

### Authentication Issues

**Error: "Could not validate credentials"**
- Check token is in `Authorization: Bearer <token>` header
- Verify token hasn't expired (7 days)
- Ensure `JWT_SECRET_KEY` is set in `.env`
- Check user account is active

**Token not working after server restart**
- Ensure `JWT_SECRET_KEY` is in `.env` file (not just environment variable)
- Don't use default secret key in production

### LLM Issues

**LLM not working**
- Check which provider you're using
- **Ollama**: Verify it's running at http://localhost:11434
- **Groq/Hugging Face**: Verify API key is set in `.env`
- Check `llm_error` and `llm_debug` fields in API response

**All LLM providers failing**
- System falls back to rule-based explanations automatically
- Check API response for `llm_debug` field with setup instructions

### ML Model Issues

**ML model not available**
- Check if model file exists: `models/ml_risk_model.pkl`
- Train model: `POST /api/ml/train`
- Check status: `GET /api/ml/status`

**Low accuracy**
- Collect more training data (aim for 100+ activities)
- Review feature importance to identify issues
- Consider retraining with more recent data

### CSV Upload Issues

**Error: "Invalid CSV format"**
- Ensure CSV has required columns: Activity ID, Name, Duration, Start, Finish
- Check date formats (YYYY-MM-DD or similar)
- Verify CSV is valid (open in Excel to check)

### General Issues

**Server won't start**
- Check Python version (3.13+)
- Verify virtual environment is activated
- Check all dependencies installed: `pip install -r requirements.txt`
- Check `.env` file exists and has `DATABASE_URL`

**CORS errors**
- Add frontend origin to `CORS_ORIGINS` in `.env`
- Or set `CORS_ORIGINS` environment variable

**Import errors**
- Ensure you're in the `schedule-risk-backend` directory
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

---

## Production Deployment

### Security Checklist

- [ ] Change `JWT_SECRET_KEY` to secure random string
- [ ] Use strong PostgreSQL password
- [ ] Enable HTTPS
- [ ] Set `REQUIRE_HTTPS=true` in `.env`
- [ ] Configure `CORS_ORIGINS` to specific domains
- [ ] Use environment variables, not `.env` file in production
- [ ] Enable rate limiting if needed
- [ ] Set up database backups
- [ ] Monitor authentication failures

### Environment Variables for Production

```env
DATABASE_URL=postgresql://user:password@db-host:5432/schedule_risk_db
JWT_SECRET_KEY=<generate-secure-random-32-char-string>
REQUIRE_HTTPS=true
CORS_ORIGINS=https://yourdomain.com
ENABLE_RATE_LIMITING=true
RELOAD=false
HOST=0.0.0.0
PORT=8000
```

### Deployment Options

#### Simple Deployment (Any Platform)

```bash
# Production mode
RELOAD=false HOST=0.0.0.0 PORT=8000 python run.py
```

#### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

Run:
```bash
docker build -t schedule-risk-api .
docker run -p 8000:8000 --env-file .env schedule-risk-api
```

#### AWS/Azure/GCP Deployment

1. **Set environment variables** in your cloud platform (don't use `.env` file in production)
2. **Use production mode**:
   ```bash
   RELOAD=false HOST=0.0.0.0 PORT=8000 python run.py
   ```
3. **Or use gunicorn** (for better performance):
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

---

## Support

For issues or questions, check the troubleshooting section or create an issue in the repository.
