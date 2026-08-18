# OpenClaw AI Dev Team Landing Page (TASK-01)

A high-converting, studio-grade landing page served by FastAPI, showcasing the OpenClaw AI Engineering Team (1 Lead Engineer + 5 Autonomous AI Bots), their synergy, workflows, roles, capabilities, trust metrics, and an interactive lead capture system with asynchronous email dispatch.

---

## Architecture & Technical Stack

- **Backend:** FastAPI (Python 3.12+), Uvicorn, Jinja2 Templates, Pydantic, StaticFiles, BackgroundTasks
- **Email Service:** Asynchronous SMTP dispatch (`email_service.py`) supporting Mail.ru (SSL 465), Yandex, Gmail, and custom SMTP with dark cyber HTML templates
- **Frontend:** Semantic HTML5, Studio-Grade Cyber-Engineering Dark Theme CSS (pure CSS, responsive glassmorphism, glowing accents, zero framework bloat), accessible modal dialog
- **Lead Capture:** Asynchronous `POST /api/leads` endpoint with Pydantic validation (`LeadRequest`), dual persistence (`leads.json` + SMTP email dispatch)
- **Localization:** Bilingual (RU / EN) with instant navbar switch, cookie (`openclaw_lang`), and query parameter (`?lang=ru|en`) persistence
- **Quality & Standards:** Pytest, pytest-cov (29 tests, 99% coverage), black, flake8, mypy
- **Containerization:** Production Dockerfile (python:3.12-slim, non-root user, healthcheck)

---

## Core Sections & Features

1. **Hero Section:** Human + AI engineering synergy (1 dev + 5 autonomous bots = studio-grade output, 10x velocity, 100% QA pass rate, 0 bad commits on main).
2. **Hero CTA & Lead Modal:** Glowing emerald gradient button (`ПОДАТЬ ЗАЯВКУ` / `Apply for AI Dev Team`) triggering a cyber glassmorphism contact intake modal with real-time validation and asynchronous submission.
3. **Email Notification Engine:** Immediate dispatch of incoming leads to `qxzib@yandex.ru` with complete client details, formatted message, and timestamp.
4. **Workflow (Automated Flow):** Visual, deterministic delivery pipeline (`User/Idea -> pm_bot -> ui_ux_bot -> dev_bot / py_bot -> qa_bot -> git_bot`) with the Least Privilege security model.
5. **Team Roster:** Full profiles & skills for `pm_bot` (Paula), `ui_ux_bot` (Elena), `dev_bot` (Dev), `py_bot` (Alex), `qa_bot` (QA), `git_bot` (Git), and Lead Human Architect.
6. **Capabilities:** High-load Go backends, FastAPI microservices, Telegram bots, Docker/SSH automation, automated CI/CD pipelines.
7. **Analytics & Trust:** Comprehensive comparison matrix comparing AI-driven dev team vs classic outsourced/in-house development.

---

## Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Email Notifications (.env)
Copy the example environment file and add your Yandex App Password (Пароль приложения Яндекс):
```bash
cp .env.example .env
# Edit .env and set:
# SMTP_PASSWORD=your_yandex_app_password
```

### 3. Run the Application
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

### 4. Run Tests and Linters
```bash
# Run pytest with coverage report
pytest -v --cov=. --cov-report=term-missing

# Code formatting check
black --check .

# Linting check
flake8 .

# Type checking
mypy app.py email_service.py tests/
```

---

## Docker Deployment

### Build Container
```bash
docker build -t openclaw-landing-page:latest .
```

### Run Container
```bash
docker run -d -p 8000:8000 --env-file .env --name openclaw-landing openclaw-landing-page:latest
```
Check health:
```bash
curl http://localhost:8000/health
```
