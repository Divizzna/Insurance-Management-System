# 🛡️ InsureFlow AI — Enterprise Insurance Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat-square&logo=mysql&logoColor=white)](https://www.mysql.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![Frontend](https://img.shields.io/badge/Frontend-HTML5%20%2F%20CSS3%20%2F%20Vanilla%20JS-E34F26?style=flat-square&logo=html5&logoColor=white)](./frontend)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

An enterprise-grade **Insurance Management System** that combines policy lifecycle administration, claims management, and payment reconciliation with an automated **Multi-Agent AI Adjudication Engine** and interactive **ChatGPT Copilot**.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
  - [Multi-Agent Claim Review Workflow](#multi-agent-claim-review-workflow)
- [Technology Stack](#-technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
  - [1. Clone / Navigate to Workspace](#1-navigate-to-project-folder)
  - [2. Create and Activate Virtual Environment](#2-create-and-activate-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Set Up the MySQL Database](#4-set-up-the-mysql-database)
  - [5. Configure Environment Variables](#5-configure-environment-variables)
- [Running the Application](#-running-the-application)
- [Interactive Web Dashboard](#-interactive-web-dashboard)
- [API Documentation & Endpoints](#-api-documentation--endpoints)
- [AI Engine Modes & Configuration](#-ai-engine-modes--configuration)
- [Database Schema](#-database-schema)
- [Verification & Health Checks](#-verification--health-checks)

---

## 🌟 Overview

**InsureFlow AI** bridges the gap between conventional insurance administrative databases and modern artificial intelligence. In addition to handling everyday CRUD operations for customers, insurance policies, products, and premium payments, the platform introduces an **automated claims adjudication pipeline** powered by specialized rule agents alongside OpenAI's GPT models.

If OpenAI API credentials are not provided, the system gracefully falls back to an internal **Heuristic Risk Adjudication Engine**, ensuring zero operational interruption.

---

## ✨ Key Features

### 1. 👥 Customer Management
- Register and maintain policyholder profiles (name, email, phone, date of birth).
- Automated email uniqueness and data format validation with Pydantic.

### 2. 📜 Policy Lifecycle Management
- Link customers to pre-configured insurance products (Auto, Life, Health, Homeowners).
- Configure policy terms, coverage caps, premium schedules, and statuses (`active`, `pending`, `expired`, `cancelled`).
- Foreign key integrity verification ensuring valid customer and product associations.

### 3. 💳 Premium Payments & Billing Ledger
- Track policy payments, transaction reference IDs, and payment methods.
- Monitor payment statuses (`paid`, `pending`, `failed`) and link transactions directly to active policies.

### 4. 📝 Claim Administration
- Log incident reports, loss dates, claimed amounts, and detailed claimant descriptions.
- Dynamic claim statuses (`submitted`, `under_review`, `approved`, `rejected`, `investigate`).

### 5. 🤖 Multi-Agent AI Claim Adjudication
- **Policy Validation Agent**: Verifies that the policy is currently active and that the incident date falls strictly within the coverage term.
- **Claim Amount Agent**: Compares requested claim compensation against the policy's maximum coverage limit.
- **Data Completeness Agent**: Audits claimant statements, description length, and validates positive numerical amounts.
- **ChatGPT Adjudication Agent**: Performs natural language processing on the incident narrative, identifies fraud keywords and suspicious circumstances, outputs a calibrated **Risk Score (0–100)**, confidence index, and human-readable recommendations (`approve`, `investigate`, `reject`).

### 6. 📊 Compliance & Immutable AI Audit Trail
- Every AI assessment is automatically recorded in `ai_runs` and `agent_results` with structured JSON evidence.
- Review historical decisions, risk scores, red flags, and timestamps directly in the UI.

### 7. 💬 ChatGPT Insurance Copilot
- Interactive AI chat assistant tailored for claims adjusters and customers.
- Explains coverage clauses, policy validation criteria, and claim status inquiries.
- Includes dynamic runtime settings allowing adjusters to configure their OpenAI API key, model selection, or custom proxy base URL directly from the interface.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend Single-Page App                  │
│       HTML5 + CSS3 (Glassmorphism / Dark Theme) + Vanilla JS│
└───────────────▲─────────────────────────────▲───────────────┘
                │                             │
          REST APIs                     Static Assets
                │                             │
┌───────────────▼─────────────────────────────▼───────────────┐
│                     FastAPI Application                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Customers   │  │   Policies   │  │     Payments      │  │
│  ├──────────────┤  ├──────────────┤  ├───────────────────┤  │
│  │    Claims    │  │  AI Reviews  │  │  AI Copilot/Chat  │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└───────────────▲─────────────────────────────▲───────────────┘
                │                             │
        SQLAlchemy Core                OpenAI SDK /
        + PyMySQL Pool               Heuristic Engine
                │                             │
┌───────────────▼──────────────┐       ┌──────▼───────────────┐
│        MySQL Database        │       │  OpenAI / Heuristics │
│  - customers                 │       │  - GPT-4o-mini       │
│  - insurance_products        │       │  - Custom Base URL   │
│  - policies                  │       │  - Offline Fallback  │
│  - payments                  │       └──────────────────────┘
│  - claims                    │
│  - ai_runs                   │
│  - agent_results             │
└──────────────────────────────┘
```

### Multi-Agent Claim Review Workflow

```mermaid
flowchart TD
    A[New Claim Filed] --> B[POST /api/v1/claims/{id}/review]
    B --> C[Fetch Claim & Associated Policy]
    
    subgraph Multi-Agent Pipeline
        D[Agent 1: Policy Validator] -->|Active status & Date range check| H[Consolidate Findings]
        E[Agent 2: Amount Checker] -->|Claim amount <= Coverage limit| H
        F[Agent 3: Completeness Auditor] -->|Narrative presence & validity| H
        G[Agent 4: ChatGPT / AI Adjudicator] -->|Risk Score 0-100, NLP & Red Flags| H
    end
    
    C --> D
    C --> E
    C --> F
    C --> G
    
    H --> I{Any Flag or High Risk?}
    I -- Yes --> J[Outcome: human_review_required]
    I -- No --> K[Outcome: checks_completed / approve]
    
    J --> L[(Persist to ai_runs & agent_results)]
    K --> L
    L --> M[Return JSON Report to UI & Audit Trail]
```

---

## 💻 Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+) |
| **ASGI Web Server** | [Uvicorn](https://www.uvicorn.org/) |
| **ORM & Database Driver** | [SQLAlchemy](https://www.sqlalchemy.org/) Core, [PyMySQL](https://github.com/PyMySQL/PyMySQL) |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| **AI / Large Language Model** | [OpenAI Python SDK](https://github.com/openai/openai-python) (GPT-4o, GPT-4o-mini) + Fallback Heuristic Rule Engine |
| **Database** | [MySQL 8.0+](https://www.mysql.com/) |
| **Frontend** | Vanilla HTML5, Modern CSS3 (CSS Custom Properties, Glassmorphism), ES6+ JavaScript |
| **API Documentation** | OpenAPI 3.0, Swagger UI, ReDoc |

---

## 📁 Project Directory Structure

```plaintext
insurance-management-system/
├── backend/
│   ├── routers/
│   │   ├── ai_chat.py             # ChatGPT copilot, status & dynamic AI config
│   │   ├── claim.py               # Claims CRUD endpoints
│   │   ├── claim_review.py        # Trigger AI review & historical audit trails
│   │   ├── customer.py            # Customer registration & management
│   │   ├── payment.py             # Payment recording & ledger lookup
│   │   └── policy.py              # Policy CRUD & product associations
│   ├── schemas/
│   │   ├── claim.py               # Pydantic models for claims
│   │   ├── customer.py            # Pydantic models for customers
│   │   ├── payment.py             # Pydantic models for payments
│   │   └── policy.py              # Pydantic models for policies
│   ├── services/
│   │   └── claim_review_service.py # 4-agent review orchestration & heuristic engine
│   ├── config.py                  # Pydantic-based configuration & .env loader
│   ├── db.py                      # SQLAlchemy connection engine & SessionLocal
│   ├── main.py                    # FastAPI entrypoint, middleware, static mounts
│   └── requirements.txt           # Python dependencies
├── database/
│   └── schema.sql                 # Complete MySQL schema & initial product seed data
├── frontend/
│   ├── css/
│   │   └── style.css              # Custom styling, dark mode & layout rules
│   ├── js/
│   │   └── app.js                 # Frontend SPA state, API handlers, modal logic
│   └── index.html                 # Main dashboard interface
├── .env.example                   # Template for environment variables
├── .gitignore                     # Git exclusion rules
└── README.md                      # Comprehensive project documentation
```

---

## ⚙️ Prerequisites

Before getting started, make sure you have the following installed:

1. **Python 3.10+** — Check with `python --version`
2. **MySQL Server 8.0+** — Running locally or accessible via network
3. **Git** — For version control
4. *(Optional)* **OpenAI API Key** — For live ChatGPT evaluations (the app functions completely with heuristic fallbacks if omitted)

---

## 🚀 Installation & Setup

### 1. Navigate to Project Folder

Open your terminal or command prompt:

```bash
cd insurance-management-system
```

### 2. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r backend/requirements.txt
```

### 4. Set Up the MySQL Database

1. Start your local MySQL service.
2. Run the provided schema script in your MySQL client (MySQL Workbench, phpMyAdmin, or the CLI):

```bash
mysql -u root -p < database/schema.sql
```

> **Note:** The `database/schema.sql` script creates the database `insurance_db` (if it does not exist) and populates the `insurance_products` table with default products:
> - Comprehensive Auto Insurance
> - Term Life Insurance
> - Health Plus Premium
> - Homeowners Protection

### 5. Configure Environment Variables

Create a `.env` file in the project root directory by copying `.env.example`:

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**On Linux / macOS:**
```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```ini
APP_NAME="InsureFlow AI"
APP_ENV="development"
API_V1_PREFIX="/api/v1"

# Database Configuration
MYSQL_HOST="localhost"
MYSQL_PORT=3306
MYSQL_DATABASE="insurance_db"
MYSQL_USER="root"
MYSQL_PASSWORD="your_mysql_password"

# AI Adjudication & Copilot (Optional)
OPENAI_BASE_URL=""
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"
```

---

## 🏃 Running the Application

Start the FastAPI application using the integrated runner or directly via Uvicorn:

### Option A: Direct Python Execution
```bash
python backend/main.py
```

### Option B: Uvicorn CLI (with Hot Reload)
```bash
uvicorn backend.main:app --reload --port 8001
```

Once started, the server will output:
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

---

## 🖥️ Interactive Web Dashboard

Once the server is running, navigate in your browser to:

👉 **Web Dashboard:** [http://localhost:8001/app](http://localhost:8001/app) *(or simply [http://localhost:8001/](http://localhost:8001/))*

### Dashboard Tabs:
1. **Overview**: Real-time KPI summary (total claims, active policies, approved/investigate counts, system health).
2. **Customers**: View existing policyholders and register new ones with instant form validation.
3. **Policies**: Create new policies tied to customers and products; change status and review coverage.
4. **Payments**: Record premiums, browse transaction history, and filter by payment status.
5. **Claims & AI Review**: Submit claims and click **"Run AI Review"** to execute the multi-agent pipeline in real time.
6. **AI Audit Trail**: Inspect detailed agent-by-agent breakdowns, risk scores, and stored JSON audit records.
7. **ChatGPT Copilot**: Chat in real-time with the insurance assistant.
8. **AI Settings Modal**: Update your OpenAI API Key, Model, and Base URL on the fly without restarting the server.

---

## 📚 API Documentation & Endpoints

FastAPI provides interactive, self-documenting API interfaces:

- **Interactive Swagger UI:** [http://localhost:8001/docs](http://localhost:8001/docs)
- **ReDoc Documentation:** [http://localhost:8001/redoc](http://localhost:8001/redoc)

### Summary of REST Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/health` | Basic service health status |
| | `GET` | `/health/database` | Validates active MySQL connection |
| | `GET` | `/api/v1/info` | Returns system config & AI readiness |
| **Customers** | `GET` | `/api/v1/customers` | List all registered customers |
| | `POST` | `/api/v1/customers` | Register a new customer |
| | `GET` | `/api/v1/customers/{id}` | Get specific customer details |
| **Policies** | `GET` | `/api/v1/policies` | List all insurance policies |
| | `POST` | `/api/v1/policies` | Create a new policy |
| | `GET` | `/api/v1/policies/{id}` | Retrieve policy details |
| | `PUT` | `/api/v1/policies/{id}` | Update existing policy |
| | `DELETE` | `/api/v1/policies/{id}` | Delete policy (if no references exist) |
| **Payments** | `GET` | `/api/v1/payments` | List payment ledger |
| | `POST` | `/api/v1/payments` | Record a new premium payment |
| | `GET` | `/api/v1/payments/{id}` | Get payment transaction details |
| **Claims** | `GET` | `/api/v1/claims` | List all submitted claims |
| | `POST` | `/api/v1/claims` | Submit a new insurance claim |
| | `GET` | `/api/v1/claims/{id}` | Retrieve specific claim record |
| | `PUT` | `/api/v1/claims/{id}` | Update claim details / status |
| | `DELETE` | `/api/v1/claims/{id}` | Delete claim |
| **AI Review** | `POST` | `/api/v1/claims/{id}/review` | **Execute multi-agent adjudication pipeline** |
| | `GET` | `/api/v1/claims/{id}/reviews` | Get all past AI runs for a specific claim |
| | `GET` | `/api/v1/claims/reviews/audit` | Global audit log of all AI review runs |
| | `GET` | `/api/v1/claims/reviews/runs/{run_id}` | Detailed agent findings for a single run |
| **AI Copilot** | `GET` | `/api/v1/ai/status` | Current AI config & active agents status |
| | `POST` | `/api/v1/ai/chat` | Conversational assistant query |
| | `POST` | `/api/v1/ai/config` | Dynamically update AI key, URL, or model |

---

## 🧠 AI Engine Modes & Configuration

InsureFlow AI supports two execution modes for AI claims adjudication and conversational chat:

### Mode 1: Live OpenAI Mode (ChatGPT)
- **Activation:** Supply a valid `OPENAI_API_KEY` in `.env` or via the UI settings modal.
- **Model:** Defaults to `gpt-4o-mini`, compatible with `gpt-4o`, `gpt-3.5-turbo`, or custom OpenAI-compatible endpoints via `OPENAI_BASE_URL`.
- **Functionality:** 
  - Dynamic JSON output schema extraction.
  - Deep semantic reasoning on claim descriptions.
  - Detection of inconsistencies, fraud signals, and nuanced risk scoring.

### Mode 2: Heuristic Fallback Engine (Offline Mode)
- **Activation:** Automatically activated when `OPENAI_API_KEY` is blank or if the OpenAI API is unreachable.
- **Functionality:**
  - Evaluates rule checks (policy period bounds, amount vs limit ratio, narrative keyword screening).
  - Flags sensitive patterns (`lost`, `unattended`, `cash`, `unknown person`, etc.).
  - Calculates a calibrated risk score (0–100) and outputs human-review suggestions.

---

## 🗄️ Database Schema

The system uses 7 relational tables defined in [`database/schema.sql`](./database/schema.sql):

1. **`customers`** — Stores customer personal information and contact details.
2. **`insurance_products`** — Catalog of available insurance plans and base premiums.
3. **`policies`** — Issued policies with coverage amount, premium, period, and status.
4. **`payments`** — Transaction records linked to policies with payment method and reference codes.
5. **`claims`** — Incident records, claimed amounts, descriptions, and resolution statuses.
6. **`ai_runs`** — Records each execution of the multi-agent review workflow on a claim.
7. **`agent_results`** — Detailed JSON outputs, checks, and verdicts generated by each individual agent during a run.

---

## 🔍 Verification & Health Checks

Verify your backend and database connectivity with these quick commands:

### 1. Check API Health
```bash
curl -X GET http://localhost:8001/health
```
**Response:**
```json
{"status": "healthy", "service": "insurance-management-api"}
```

### 2. Check Database Connectivity
```bash
curl -X GET http://localhost:8001/health/database
```
**Response:**
```json
{"status": "healthy", "database": "insurance_db", "connection": "successful"}
```

### 3. Check AI Engine Readiness
```bash
curl -X GET http://localhost:8001/api/v1/ai/status
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
