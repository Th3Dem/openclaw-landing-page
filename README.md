# OpenClaw AI Dev Team Landing Page (TASK-01)

A high-converting, studio-grade landing page served by FastAPI, showcasing the OpenClaw AI Engineering Team (1 Lead Engineer + 5 Autonomous AI Bots), their synergy, workflows, roles, capabilities, trust metrics, and an interactive lead capture system.

---

## Architecture & Technical Stack

- **Backend:** FastAPI (Python 3.12+), Uvicorn, Jinja2 Templates, Pydantic, StaticFiles
- **Frontend:** Semantic HTML5, Studio-Grade Cyber-Engineering Dark Theme CSS (pure CSS, responsive glassmorphism, glowing accents, zero framework bloat), accessible modal dialog
- **Lead Capture:** Asynchronous \POST /api/leads\ endpoint with Pydantic validation (\LeadRequest\) and dual persistence (in-memory + atomic \leads.json\)
- **Localization:** Bilingual (RU / EN) with instant navbar switch, cookie (\openclaw_lang\), and query parameter (\?lang=ru|en\) persistence
- **Quality & Standards:** Pytest, pytest-cov (100% test coverage across 20 test cases), black, flake8, mypy
- **Containerization:** Production Dockerfile (python:3.12-slim, non-root user, healthcheck)

---

## Core Sections & Features

1. **Hero Section:** Human + AI engineering synergy (1 dev + 5 autonomous bots = studio-grade output, 10x velocity, 100% QA pass rate, 0 bad commits on main).
2. **Hero CTA & Lead Modal:** Glowing emerald gradient button (\ПОДАТЬ ЗАЯВКУ\ / \Apply for AI Dev Team\) triggering a cyber glassmorphism contact intake modal with real-time validation and asynchronous submission.
3. **Workflow (Automated Flow):** Visual, deterministic delivery pipeline (\User/Idea -> pm_bot -> dev_bot / py_bot -> qa_bot -> git_bot\) with the Least Privilege security model.
4. **Team Roster:** Full profiles & skills for \pm_bot\ (Paula), \dev_bot\ (Dev), \py_bot\ (Alex), \qa_bot\ (QA), \git_bot\ (Git), and Lead Human Architect.
5. **Capabilities:** High-load Go backends, FastAPI microservices, Telegram bots, Docker/SSH automation, automated CI/CD pipelines.
6. **Analytics & Trust:** Comprehensive comparison matrix comparing AI-driven dev team vs classic outsourced/in-house development.

---

## Running Locally

### 1. Install Dependencies
\\ash
pip install -r requirements.txt
\
### 2. Run the Application
\\ash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
\Open [http://localhost:8000](http://localhost:8000) in your browser.

### 3. Run Tests and Linters
\\ash
# Run pytest with coverage report
pytest -v --cov=app --cov-report=term-missing

# Code formatting check
black --check .

# Linting check
flake8 .

# Type checking
mypy app.py tests/
\
---

## Docker Deployment

### Build Container
\\ash
docker build -t openclaw-landing-page:latest .
\
### Run Container
\\ash
docker run -d -p 8000:8000 --name openclaw-landing openclaw-landing-page:latest
\Check health:
\\ash
curl http://localhost:8000/health
\EOF
