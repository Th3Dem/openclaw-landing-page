from __future__ import annotations

import datetime
import html
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("openclaw.landing")

# Directory paths & storage
BASE_DIR: Path = Path(__file__).resolve().parent
STATIC_DIR: Path = BASE_DIR / "static"
TEMPLATES_DIR: Path = BASE_DIR / "templates"
LEADS_FILE: Path = BASE_DIR / "leads.json"

# In-memory leads storage
LEADS_STORE: List[Dict[str, Any]] = []

# Create FastAPI application
app = FastAPI(
    title="OpenClaw AI Engineering Team",
    description="Showcase landing page for the autonomous AI development team",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

# Ensure static & templates directory exist before mounting
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files and initialize templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class LeadRequest(BaseModel):
    """Pydantic model validating incoming lead intake requests."""

    name: str = Field(
        ..., min_length=2, max_length=100, description="Lead submitter full name"
    )
    contact: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Contact information (Telegram/Email/Phone)",
    )
    message: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional project scope or requirements",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 3:
            raise ValueError(
                "Contact must contain at least 3 non-whitespace characters"
            )
        return cleaned

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned if cleaned else None


def save_lead(lead_data: LeadRequest, client_ip: str = "unknown") -> Dict[str, Any]:
    """Persist a newly received lead to in-memory list and local JSON tracking file."""
    lead_id = f"lead-{uuid.uuid4().hex[:8]}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record: Dict[str, Any] = {
        "lead_id": lead_id,
        "created_at": created_at,
        "name": lead_data.name,
        "contact": lead_data.contact,
        "message": lead_data.message,
        "client_ip": client_ip,
    }
    LEADS_STORE.append(record)

    try:
        existing_leads: List[Dict[str, Any]] = []
        if LEADS_FILE.exists():
            try:
                content = LEADS_FILE.read_text(encoding="utf-8")
                if content.strip():
                    parsed = json.loads(content)
                    if isinstance(parsed, list):
                        existing_leads = parsed
            except Exception as read_err:
                logger.warning(
                    "Could not parse existing leads file %s: %s", LEADS_FILE, read_err
                )
                existing_leads = []

        existing_leads.append(record)
        LEADS_FILE.write_text(
            json.dumps(existing_leads, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as write_err:
        logger.error("Failed to write lead to %s: %s", LEADS_FILE, write_err)

    return record


# Localization datasets for English and Russian
LOCALIZATION_DATA: Dict[str, Dict[str, Any]] = {
    "en": {
        "lang_code": "en",
        "html_title": "OpenClaw AI Engineering Team | Autonomous Dev Studio",
        "meta_desc": (
            "OpenClaw AI Dev Team - 1 Lead Engineer + 5 Autonomous AI Bots delivering "
            "studio-grade software with 10x velocity and zero bad commits."
        ),
        "app_name": "OpenClaw AI Dev Team",
        "app_tagline": "1 Lead Engineer + 5 Autonomous AI Bots = Studio-Grade Output",
        "version": "1.0.0",
        "nav": {
            "title_prefix": "OpenClaw",
            "title_suffix": "AI Dev Studio",
            "overview": "Overview",
            "workflow": "Autonomous Flow",
            "roster": "Team Roster",
            "capabilities": "Capabilities",
            "trust": "AI vs Classic Matrix",
            "status": "5 AGENTS OPERATIONAL",
        },
        "hero": {
            "pill_badge": "NEXT-GEN PARADIGM",
            "pill_text": "Autonomous Multi-Agent Software Engineering",
            "title_line1": "Human Ingenuity. Autonomous Precision.",
            "title_line2": "Studio-Grade Output at 10x Velocity.",
            "description": (
                "A proven engineering architecture: <strong>1 Lead Human Architect</strong> "
                "orchestrates <strong>5 specialized autonomous AI bots</strong>. Together, "
                "we deliver production-hardened Golang backends, FastAPI microservices, "
                "and automated DevOps with zero bad commits."
            ),
            "cta_button": "Apply for AI Dev Team",
            "metrics": {
                "velocity": "10x",
                "velocity_label": "Delivery Velocity",
                "velocity_sub": "Idea to production cycle time",
                "qa_pass_rate": "100%",
                "qa_pass_label": "QA Gatekeeper Pass",
                "qa_pass_sub": "Strict ≥80% coverage mandate",
                "bad_commits": "0",
                "bad_commits_label": "Bad Commits on Main",
                "bad_commits_sub": "Protected branch release isolation",
                "uptime_readiness": "24/7",
                "uptime_label": "Continuous Readiness",
                "uptime_sub": "Zero downtime development loop",
            },
            "telemetry": [
                {"label": "SECURITY MODEL:", "val": "Least Privilege Sandboxing"},
                {"label": "AUDIT TRAIL:", "val": "Immutable WORKLOG.md"},
                {"label": "QUALITY GATES:", "val": "flake8 + golangci-lint + SAST"},
                {"label": "STATUS:", "val": "Healthy (200 OK)"},
            ],
        },
        "workflow": {
            "tag": "DETERMINISTIC PIPELINE",
            "title": "The Autonomous Delivery Flow",
            "subtitle": (
                "Every feature follows a strict, unidirectional quality pipeline. No agent operates "
                "outside its allocated privileges, guaranteeing auditability, code correctness, "
                "and repository safety."
            ),
            "steps": [
                {
                    "num": "01",
                    "icon": "💡",
                    "title": "Idea & Vision",
                    "bot_id": "User & Human Lead",
                    "desc": (
                        "High-level concept, strategic architecture guidelines, and core business "
                        "requirements are submitted."
                    ),
                    "badges": ["Product Strategy", "Domain Vision"],
                },
                {
                    "num": "02",
                    "icon": "📋",
                    "title": "Spec Architecture",
                    "bot_id": "pm_bot (Paula)",
                    "desc": (
                        "Decomposes ideas into atomic <code>TASK-XX.md</code> files, maps "
                        "dependency graphs, and initializes the WORKLOG."
                    ),
                    "badges": ["TASK-XX.md Specs", "Acceptance Criteria"],
                },
                {
                    "num": "03",
                    "icon": "⚡ / 🐍",
                    "title": "Code & Unit Tests",
                    "bot_id": "dev_bot & py_bot",
                    "desc": (
                        "Parallel implementation in Golang or Python with unit test suites, "
                        "type annotations, and local verification."
                    ),
                    "badges": ["Go 1.22+ / FastAPI", "Pytest / go test"],
                },
                {
                    "num": "04",
                    "icon": "🔍",
                    "title": "Security & Audit",
                    "bot_id": "qa_bot (QA)",
                    "desc": (
                        "Enforces strict ≥80% test coverage gate, runs linters, SAST vulnerability "
                        "scans, and issues formal <code>QA_REPORT.md</code>."
                    ),
                    "badges": ["Coverage ≥80%", "SAST Security Scan"],
                },
                {
                    "num": "05",
                    "icon": "🌿",
                    "title": "Release & PR",
                    "bot_id": "git_bot (Git)",
                    "desc": (
                        "The sole bot with Git write permissions. Creates feature branches, "
                        "crafts atomic commits, and raises production PRs."
                    ),
                    "badges": ["Protected Branches", "Zero Main Pollution"],
                },
            ],
            "security": {
                "title": "Least Privilege Security Architecture",
                "desc": (
                    "Traditional AI coding setups suffer from catastrophic hallucinated commits "
                    "and permission leaks. OpenClaw enforces hardware-isolated roles where "
                    "developers cannot touch git remotes, QA cannot alter code, and only the "
                    "dedicated release guardian merges verified pull requests."
                ),
                "rules": [
                    {
                        "label": "DEV ISOLATION",
                        "text": (
                            "Dev bots write code and unit tests only. No write access to git "
                            "remote or prod environments."
                        ),
                    },
                    {
                        "label": "INDEPENDENT AUDIT",
                        "text": (
                            "QA bot acts as an unbypassable gatekeeper before any code can be "
                            "considered complete."
                        ),
                    },
                    {
                        "label": "IMMUTABLE AUDIT TRAIL",
                        "text": (
                            "Every single action, decision, test output, and handoff is logged "
                            "append-only in WORKLOG.md."
                        ),
                    },
                ],
            },
        },
        "roster": {
            "tag": "ENGINEERING SQUAD",
            "title": "Autonomous Team Roster",
            "subtitle": (
                "A specialized multi-agent collective where each bot excels in its dedicated "
                "engineering domain."
            ),
            "human_lead": {
                "name": "Lead Architect & Product Owner",
                "badge": "Human Strategic Lead",
                "role": "Strategic Direction • Architecture Vision • Prompt Governance",
                "desc": (
                    "Provides macro engineering oversight, business requirements alignment, "
                    "prompt refinement, and final sign-off on studio deliverables."
                ),
            },
            "skills_title": "Core Competencies & Stack",
            "agents": [
                {
                    "id": "pm_bot",
                    "name": "Paula",
                    "role": "Project Manager & Orchestrator",
                    "icon": "📋",
                    "badge": "Orchestration",
                    "description": (
                        "Deconstructs raw user ideas into rigorous specifications, defines "
                        "acceptance criteria, maps dependencies, and maintains immutable "
                        "WORKLOG audit trails."
                    ),
                    "skills": [
                        "Task Decomposition (TASK-XX.md)",
                        "Dependency Analysis",
                        "Sprint Governance",
                        "WORKLOG Maintenance",
                    ],
                },
                {
                    "id": "dev_bot",
                    "name": "Dev",
                    "role": "Lead Golang Developer",
                    "icon": "⚡",
                    "badge": "High-Load Go",
                    "description": (
                        "Engineers ultra-high-throughput Go backend services, concurrent "
                        "pipelines, gRPC microservices, and memory-safe systems with strict race "
                        "condition testing."
                    ),
                    "skills": [
                        "Golang 1.22+ Concurrency",
                        "High-Throughput gRPC / REST",
                        "Memory Optimization",
                        "go test -race Verification",
                    ],
                },
                {
                    "id": "py_bot",
                    "name": "Alex",
                    "role": "Python Developer",
                    "icon": "🐍",
                    "badge": "FastAPI & DevOps",
                    "description": (
                        "Builds production-grade FastAPI microservices, Telegram bot "
                        "architectures, Docker/SSH automation workflows, and comprehensive "
                        "Pytest suites."
                    ),
                    "skills": [
                        "FastAPI & AsyncIO",
                        "Docker & SSH Orchestration",
                        "Telegram Bot Architecture",
                        "Pytest (≥80% Coverage)",
                    ],
                },
                {
                    "id": "qa_bot",
                    "name": "QA",
                    "role": "Quality Gatekeeper & Security Auditor",
                    "icon": "🔍",
                    "badge": "Quality & SAST",
                    "description": (
                        "Enforces strict zero-defect policy: runs static analysis, coverage "
                        "audits (≥80% gate), SAST security scans, CVE dependency checks, and "
                        "formal QA reports."
                    ),
                    "skills": [
                        "flake8 / golangci-lint",
                        "SAST & Vulnerability Auditing",
                        "≥80% Coverage Gatekeeping",
                        "QA_REPORT Formal Sign-Off",
                    ],
                },
                {
                    "id": "git_bot",
                    "name": "Git",
                    "role": "Release Manager & Git Guardian",
                    "icon": "🌿",
                    "badge": "Release Guardian",
                    "description": (
                        "Guards repository integrity: creates isolated feat/* branches, enforces "
                        "atomic clean commits, generates pull requests, tags semantic releases, "
                        "and prevents bad code on main."
                    ),
                    "skills": [
                        "Isolated Branching (feat/*)",
                        "Atomic Commit Integrity",
                        "Pull Request Generation",
                        "Zero Bad Commits on Main",
                    ],
                },
            ],
        },
        "capabilities_section": {
            "tag": "TECHNICAL SCOPE",
            "title": "Capabilities & Engineering Stack",
            "subtitle": (
                "Full-stack systems engineering built for scalability, concurrency, high "
                "availability, and rapid deployment."
            ),
            "items": [
                {
                    "title": "High-Load Go Backends",
                    "icon": "⚡",
                    "description": (
                        "Ultra-fast compiled Golang services designed for thousands of concurrent "
                        "requests, minimal memory footprints, and low-latency gRPC/HTTP "
                        "interfaces."
                    ),
                },
                {
                    "title": "FastAPI Async Microservices",
                    "icon": "🐍",
                    "description": (
                        "Modern, typed, self-documenting asynchronous REST APIs powered by "
                        "Pydantic v2 and FastAPI with automated OpenAPI contracts."
                    ),
                },
                {
                    "title": "Telegram Bots & Automation",
                    "icon": "🤖",
                    "description": (
                        "Interactive, stateful, and asynchronous bot solutions for customer "
                        "support, team notifications, monitoring, and automated event triggers."
                    ),
                },
                {
                    "title": "Docker & SSH Server Orchestration",
                    "icon": "🐳",
                    "description": (
                        "Lightweight, multi-stage production container builds, secure sudo command "
                        "management, and automated remote host configuration."
                    ),
                },
                {
                    "title": "Automated CI/CD Quality Pipelines",
                    "icon": "🛡️",
                    "description": (
                        "Multi-tier quality gates combining linters, type checkers, race "
                        "detectors, vulnerability scanners, and test coverage mandates."
                    ),
                },
                {
                    "title": "Least Privilege Security Governance",
                    "icon": "🔒",
                    "description": (
                        "Sandboxed bot roles where developers write code, QA audits quality, and "
                        "only the release guardian merges to protected branches."
                    ),
                },
            ],
        },
        "trust": {
            "tag": "BENCHMARK COMPARISON",
            "title": "AI Team vs Traditional Development",
            "subtitle": (
                "How the autonomous multi-agent studio outclasses classical in-house and "
                "outsourced development across critical benchmarks."
            ),
            "col_dim": "Evaluation Dimension",
            "col_team": "OpenClaw AI Dev Studio",
            "col_classic": "Classic Dev (Agency / In-House)",
            "col_adv": "Advantage",
            "rows": [
                {
                    "icon": "⚡",
                    "dimension": "Delivery Velocity",
                    "team": (
                        "Rapid turnarounds: features shipped in hours with automated "
                        "spec-to-release workflows."
                    ),
                    "classic": (
                        "Weeks of sprint planning, meetings, context-switching, and backlog delays."
                    ),
                    "advantage": "10x Faster",
                },
                {
                    "icon": "🛡️",
                    "dimension": "Test Coverage & Rigor",
                    "team": (
                        "Strict automated gatekeeping: ≥80% test coverage enforced before any PR "
                        "is generated."
                    ),
                    "classic": (
                        "Tests often skipped due to sprint deadlines; typical coverage <40% in "
                        "legacy code."
                    ),
                    "advantage": "≥80% Min",
                },
                {
                    "icon": "🔒",
                    "dimension": "Security & Least Privilege",
                    "team": (
                        "Zero-trust sandboxed agent roles. Automated SAST scans, CVE dependency "
                        "auditing on every task."
                    ),
                    "classic": (
                        "Shared admin credentials, developer direct-push to main, manual "
                        "infrequent audits."
                    ),
                    "advantage": "Zero-Trust",
                },
                {
                    "icon": "📝",
                    "dimension": "Documentation & Traceability",
                    "team": (
                        "Immutable WORKLOG.md and formal DEV_HANDOVER.md on 100% of tasks."
                    ),
                    "classic": (
                        "Outdated wikis, tribal knowledge silos, undocumented decisions lost "
                        "during turnover."
                    ),
                    "advantage": "100% Logged",
                },
                {
                    "icon": "💰",
                    "dimension": "Cost & Resource Efficiency",
                    "team": (
                        "Fractional inference & compute costs; zero idle billable hours or "
                        "communication overhead."
                    ),
                    "classic": (
                        "High agency retainers, recruiting fees, project overhead, and "
                        "expensive onboarding."
                    ),
                    "advantage": "90% Less",
                },
                {
                    "icon": "🌿",
                    "dimension": "Release Reliability",
                    "team": (
                        "0 bad commits on main. Atomic commits, isolated branches (feat/*), "
                        "and QA sign-off."
                    ),
                    "classic": (
                        "Unreviewed merges, merge conflicts, broken staging environments, "
                        "Friday deploy panics."
                    ),
                    "advantage": "0 Defects",
                },
            ],
        },
        "footer": {
            "tagline": (
                "1 Lead Engineer + 5 Autonomous AI Bots • Studio-Grade Software Engineering"
            ),
            "badges": [
                "FastAPI v0.110+",
                "Go 1.22+ Ready",
                "Docker Sandboxed",
                "Strict QA Enforced",
            ],
        },
        "modal": {
            "badge": "FAST LEAD INTAKE",
            "title": "Apply for AI Dev Team",
            "subtitle": (
                "Leave your contacts and we'll prepare an architectural proposal and estimate."
            ),
            "name_label": "Your Name",
            "name_placeholder": "e.g. Alex Smith",
            "contact_label": "Contact Details",
            "contact_placeholder": "Telegram @username, email, or phone",
            "message_label": "Project Scope & Requirements",
            "message_placeholder": (
                "Describe your project goals, preferred tech stack, or target timeline..."
            ),
            "submit_btn": "Send Application",
            "submitting_btn": "Submitting...",
            "close_btn_aria": "Close modal window",
            "success_title": "Thank you! Application received.",
            "success_msg": (
                "Our Lead Architect & PM will review your task and reach out within 15 minutes."
            ),
            "success_close_btn": "Close",
            "error_generic": "Failed to submit application. Please check your inputs and try again.",
            "required_badge": "Required",
            "optional_badge": "Optional",
        },
    },
    "ru": {
        "lang_code": "ru",
        "html_title": "Инженерная команда OpenClaw AI | Автономная студия разработки",
        "meta_desc": (
            "OpenClaw AI Dev Team - 1 ведущий архитектор + 5 автономных ИИ-ботов: создание ПО "
            "студийного уровня с 10-кратной скоростью без единого ошибочного коммита."
        ),
        "app_name": "OpenClaw AI Dev Team",
        "app_tagline": "1 ведущий архитектор + 5 автономных ИИ-ботов = Результат студийного уровня",
        "version": "1.0.0",
        "nav": {
            "title_prefix": "OpenClaw",
            "title_suffix": "ИИ-Студия Разработки",
            "overview": "Обзор",
            "workflow": "Автономный процесс",
            "roster": "Состав команды",
            "capabilities": "Возможности",
            "trust": "Сравнение с Classic Dev",
            "status": "5 АГЕНТОВ В СТРОЮ",
        },
        "hero": {
            "pill_badge": "ПАРАДИГМА НОВОГО ПОКОЛЕНИЯ",
            "pill_text": "Автономная мультиагентная разработка ПО",
            "title_line1": "Человеческий замысел. Автономная точность.",
            "title_line2": "Результат студийного уровня с 10-кратной скоростью.",
            "description": (
                "Проверенная инженерная архитектура: <strong>1 ведущий архитектор-человек</strong> "
                "координирует <strong>5 специализированных автономных ИИ-ботов</strong>. Вместе "
                "мы создаем надежные Golang-бэкенды, микросервисы на FastAPI и автоматизированный "
                "DevOps без единого ошибочного коммита."
            ),
            "cta_button": "ПОДАТЬ ЗАЯВКУ",
            "metrics": {
                "velocity": "10x",
                "velocity_label": "Скорость поставки",
                "velocity_sub": "Цикл от идеи до продакшена",
                "qa_pass_rate": "100%",
                "qa_pass_label": "Прохождение QA-контроля",
                "qa_pass_sub": "Строгий норматив покрытия ≥80%",
                "bad_commits": "0",
                "bad_commits_label": "Ошибочных коммитов в main",
                "bad_commits_sub": "Изоляция релизов в защищенных ветках",
                "uptime_readiness": "24/7",
                "uptime_label": "Непрерывная готовность",
                "uptime_sub": "Цикл разработки 24/7 без простоев",
            },
            "telemetry": [
                {
                    "label": "МОДЕЛЬ БЕЗОПАСНОСТИ:",
                    "val": "Изоляция наименьших привилегий",
                },
                {"label": "ЖУРНАЛ АУДИТА:", "val": "Неизменяемый WORKLOG.md"},
                {"label": "КОНТРОЛЬ КАЧЕСТВА:", "val": "flake8 + golangci-lint + SAST"},
                {"label": "СТАТУС:", "val": "Работает стабильно (200 OK)"},
            ],
        },
        "workflow": {
            "tag": "ДЕТЕРМИНИРОВАННЫЙ ПАЙПЛАЙН",
            "title": "Автономный процесс поставки",
            "subtitle": (
                "Каждая фича проходит строгий однонаправленный конвейер качества. Ни один агент "
                "не выходит за рамки выданных привилегий, что гарантирует аудит, корректность кода "
                "и безопасность репозитория."
            ),
            "steps": [
                {
                    "num": "01",
                    "icon": "💡",
                    "title": "Идея и видение",
                    "bot_id": "Пользователь и Human Lead",
                    "desc": (
                        "Формируются концепция высокого уровня, стратегические архитектурные "
                        "требования и ключевые бизнес-цели."
                    ),
                    "badges": ["Продуктовая стратегия", "Видение домена"],
                },
                {
                    "num": "02",
                    "icon": "📋",
                    "title": "Архитектура спецификаций",
                    "bot_id": "pm_bot (Пола)",
                    "desc": (
                        "Декомпозирует задачи на атомарные файлы <code>TASK-XX.md</code>, "
                        "строит граф зависимостей и ведет журнал WORKLOG."
                    ),
                    "badges": ["Спецификации TASK-XX.md", "Критерии приемки"],
                },
                {
                    "num": "03",
                    "icon": "⚡ / 🐍",
                    "title": "Разработка и тесты",
                    "bot_id": "dev_bot и py_bot",
                    "desc": (
                        "Параллельная реализация на Golang или Python с набором модульных "
                        "тестов, строгой типизацией и локальной проверкой."
                    ),
                    "badges": ["Go 1.22+ / FastAPI", "Pytest / go test"],
                },
                {
                    "num": "04",
                    "icon": "🔍",
                    "title": "Безопасность и аудит",
                    "bot_id": "qa_bot (QA)",
                    "desc": (
                        "Обеспечивает порог покрытия тестами ≥80%, запускает линтеры, "
                        "SAST-сканеры и формирует официальный отчет <code>QA_REPORT.md</code>."
                    ),
                    "badges": ["Покрытие ≥80%", "SAST-сканирование"],
                },
                {
                    "num": "05",
                    "icon": "🌿",
                    "title": "Релиз и PR",
                    "bot_id": "git_bot (Гит)",
                    "desc": (
                        "Единственный бот с правами на запись в Git. Создает feature-ветки, "
                        "атомарные коммиты и оформляет PR в прод."
                    ),
                    "badges": ["Защищенные ветки", "Чистота ветки main"],
                },
            ],
            "security": {
                "title": "Архитектура безопасности на базе наименьших привилегий",
                "desc": (
                    "Традиционные схемы работы с ИИ страдают от галлюцинированных коммитов и "
                    "утечек прав. OpenClaw использует аппаратно изолированные роли: разработчики "
                    "не имеют доступа к git remote, QA не меняет код, а релиз-бот мержит только "
                    "проверенные PR."
                ),
                "rules": [
                    {
                        "label": "ИЗОЛЯЦИЯ РАЗРАБОТКИ",
                        "text": (
                            "Бот-разработчики пишут только код и тесты. Без доступа к удаленному "
                            "git и прод-окружениям."
                        ),
                    },
                    {
                        "label": "НЕЗАВИСИМЫЙ АУДИТ",
                        "text": (
                            "QA-бот выступает обязательным контрольным рубежом перед завершением "
                            "любой задачи."
                        ),
                    },
                    {
                        "label": "НЕИЗМЕНЯЕМЫЙ АУДИТ",
                        "text": (
                            "Каждое действие, решение, вывод тестов и передача задачи фиксируются "
                            "в WORKLOG.md."
                        ),
                    },
                ],
            },
        },
        "roster": {
            "tag": "ИНЖЕНЕРНАЯ КОМАНДА",
            "title": "Состав автономной команды",
            "subtitle": (
                "Специализированный мультиагентный коллектив, где каждый бот безупречно решает "
                "задачи в своем домене."
            ),
            "human_lead": {
                "name": "Ведущий архитектор и Product Owner",
                "badge": "Стратегический лидер (Человек)",
                "role": "Стратегическое руководство • Видение архитектуры • Контроль промптов",
                "desc": (
                    "Обеспечивает глобальный инженерный надзор, согласование бизнес-требований, "
                    "калибровку промптов и финальную приемку результатов работы студии."
                ),
            },
            "skills_title": "Ключевые компетенции и стек",
            "agents": [
                {
                    "id": "pm_bot",
                    "name": "Paula (Пола)",
                    "role": "Project Manager и координатор",
                    "icon": "📋",
                    "badge": "Координация",
                    "description": (
                        "Декомпозирует идеи в строгие спецификации, определяет критерии "
                        "приемки, выстраивает зависимости и ведет неизменяемый журнал WORKLOG."
                    ),
                    "skills": [
                        "Декомпозиция задач (TASK-XX.md)",
                        "Анализ зависимостей",
                        "Управление спринтами",
                        "Ведение WORKLOG",
                    ],
                },
                {
                    "id": "dev_bot",
                    "name": "Dev (Дев)",
                    "role": "Ведущий Golang-разработчик",
                    "icon": "⚡",
                    "badge": "Высоконагруженный Go",
                    "description": (
                        "Разрабатывает сверхпроизводительные бэкенды на Go, конкурентные "
                        "пайплайны, gRPC-микросервисы и системы с проверкой race condition."
                    ),
                    "skills": [
                        "Конкурентность в Golang 1.22+",
                        "Высоконагруженный gRPC / REST",
                        "Оптимизация памяти",
                        "Проверка через go test -race",
                    ],
                },
                {
                    "id": "py_bot",
                    "name": "Alex (Алекс)",
                    "role": "Python-разработчик",
                    "icon": "🐍",
                    "badge": "FastAPI и DevOps",
                    "description": (
                        "Создает production-ready микросервисы на FastAPI, архитектуры "
                        "Telegram-ботов, автоматизацию Docker/SSH и полные наборы тестов Pytest."
                    ),
                    "skills": [
                        "FastAPI и AsyncIO",
                        "Оркестрация Docker и SSH",
                        "Архитектура Telegram-ботов",
                        "Pytest (покрытие ≥80%)",
                    ],
                },
                {
                    "id": "qa_bot",
                    "name": "QA",
                    "role": "Контролер качества и аудитор безопасности",
                    "icon": "🔍",
                    "badge": "Качество и SAST",
                    "description": (
                        "Обеспечивает политику нулевого брака: статический анализ, аудит покрытия "
                        "(порог ≥80%), SAST-сканирование безопасности, проверка CVE и отчеты "
                        "QA_REPORT."
                    ),
                    "skills": [
                        "flake8 / golangci-lint",
                        "SAST и аудит уязвимостей",
                        "Контроль покрытия ≥80%",
                        "Утверждение QA_REPORT",
                    ],
                },
                {
                    "id": "git_bot",
                    "name": "Git (Гит)",
                    "role": "Релиз-инженер и хранитель Git",
                    "icon": "🌿",
                    "badge": "Хранитель релизов",
                    "description": (
                        "Охраняет целостность репозитория: создает изолированные ветки feat/*, "
                        "обеспечивает атомарные коммиты, формирует PR и не допускает багов в main."
                    ),
                    "skills": [
                        "Изолированные ветки (feat/*)",
                        "Атомарность коммитов",
                        "Формирование Pull Request",
                        "0 сломанных коммитов в main",
                    ],
                },
            ],
        },
        "capabilities_section": {
            "tag": "ТЕХНИЧЕСКИЙ СТЕК",
            "title": "Возможности и инженерный стек",
            "subtitle": (
                "Системная разработка полного цикла, спроектированная для масштабируемости, "
                "высокой доступности и быстрого развертывания."
            ),
            "items": [
                {
                    "title": "Высоконагруженные Go-бэкенды",
                    "icon": "⚡",
                    "description": (
                        "Сверхбыстрые компилируемые сервисы на Golang, рассчитанные на тысячи "
                        "одновременных запросов, минимальный footprint памяти и быстрые "
                        "интерфейсы gRPC/HTTP."
                    ),
                },
                {
                    "title": "Асинхронные микросервисы на FastAPI",
                    "icon": "🐍",
                    "description": (
                        "Современные типизированные асинхронные REST API на базе Pydantic v2 и "
                        "FastAPI с автоматической генерацией контрактов OpenAPI."
                    ),
                },
                {
                    "title": "Telegram-боты и автоматизация",
                    "icon": "🤖",
                    "description": (
                        "Интерактивные асинхронные боты с сохранением состояния для клиентской "
                        "поддержки, оповещений команды, мониторинга и триггеров."
                    ),
                },
                {
                    "title": "Оркестрация серверов Docker и SSH",
                    "icon": "🐳",
                    "description": (
                        "Легковесные многоэтапные контейнеры, безопасное управление sudo-командами "
                        "и автоматизированная настройка удаленных хостов."
                    ),
                },
                {
                    "title": "Автоматизированные CI/CD пайплайны качества",
                    "icon": "🛡️",
                    "description": (
                        "Многоуровневые рубежи качества: линтеры, проверка типов, race detector, "
                        "сканеры уязвимостей и обязательное покрытие тестами."
                    ),
                },
                {
                    "title": "Безопасность на базе наименьших привилегий",
                    "icon": "🔒",
                    "description": (
                        "Изолированные роли ботов: разработчики пишут код, QA проверяет качество, "
                        "и только релиз-бот делает мерж в защищенные ветки."
                    ),
                },
            ],
        },
        "trust": {
            "tag": "СРАВНИТЕЛЬНЫЙ АНАЛИЗ",
            "title": "ИИ-команда против традиционной разработки",
            "subtitle": (
                "Как автономная мультиагентная студия превосходит классическую разработку in-house "
                "и аутсорсинг по ключевым показателям."
            ),
            "col_dim": "Критерий оценки",
            "col_team": "OpenClaw AI Dev Studio",
            "col_classic": "Классическая разработка (Агентство / In-House)",
            "col_adv": "Преимущество",
            "rows": [
                {
                    "icon": "⚡",
                    "dimension": "Скорость поставки",
                    "team": (
                        "Быстрый цикл: поставка фич за считанные часы с автоматизацией от ТЗ до "
                        "релиза."
                    ),
                    "classic": (
                        "Недели планирования спринтов, митинги, переключение контекста и задержки "
                        "в бэклоге."
                    ),
                    "advantage": "В 10 раз быстрее",
                },
                {
                    "icon": "🛡️",
                    "dimension": "Покрытие тестами и надежность",
                    "team": (
                        "Строгий автоматический контроль: обязательное покрытие тестами ≥80% до "
                        "создания PR."
                    ),
                    "classic": (
                        "Тесты часто откладываются из-за дедлайнов; типичное покрытие <40% в "
                        "легаси-коде."
                    ),
                    "advantage": "≥80% Мин",
                },
                {
                    "icon": "🔒",
                    "dimension": "Безопасность и модель привилегий",
                    "team": (
                        "Zero-trust изоляция ролей агентов. Автоматические SAST-сканы и проверка "
                        "CVE зависимостей в каждой задаче."
                    ),
                    "classic": (
                        "Общие админ-доступы, прямой пуш разработчиков в main, редкие ручные "
                        "аудиты."
                    ),
                    "advantage": "Zero-Trust",
                },
                {
                    "icon": "📝",
                    "dimension": "Документация и прозрачность",
                    "team": (
                        "Неизменяемый WORKLOG.md и отчет DEV_HANDOVER.md для 100% выполненных "
                        "задач."
                    ),
                    "classic": (
                        "Устаревшие wiki, потеря знаний при увольнениях сотрудников, "
                        "незадокументированные решения."
                    ),
                    "advantage": "100% Логи",
                },
                {
                    "icon": "💰",
                    "dimension": "Экономическая эффективность",
                    "team": (
                        "Низкая стоимость инференса и вычислений; отсутствие простоев и расходов "
                        "на коммуникацию."
                    ),
                    "classic": (
                        "Высокие рейты агентств, затраты на рекрутинг, накладные расходы и долгий "
                        "онбординг."
                    ),
                    "advantage": "На 90% экономнее",
                },
                {
                    "icon": "🌿",
                    "dimension": "Надежность релизов",
                    "team": (
                        "0 сломанных коммитов в main. Атомарные коммиты, изолированные ветки "
                        "(feat/*) и подтверждение QA."
                    ),
                    "classic": (
                        "Непроверенные мержи, конфликты слияния, падение staging-окружений, "
                        "паника при релизах в пятницу."
                    ),
                    "advantage": "0 Дефектов",
                },
            ],
        },
        "footer": {
            "tagline": (
                "1 ведущий инженер + 5 автономных ИИ-ботов • Разработка студийного уровня"
            ),
            "badges": [
                "FastAPI v0.110+",
                "Готовность к Go 1.22+",
                "Изоляция в Docker",
                "Строгий контроль QA",
            ],
        },
        "modal": {
            "badge": "БЫСТРАЯ ЗАЯВКА",
            "title": "Подать заявку на разработку",
            "subtitle": (
                "Оставьте контакты, и мы подготовим архитектурное решение и оценку задачи."
            ),
            "name_label": "Ваше имя",
            "name_placeholder": "например, Алексей Смирнов",
            "contact_label": "Контактные данные",
            "contact_placeholder": "Telegram @username, email или телефон",
            "message_label": "Описание задачи и требования",
            "message_placeholder": (
                "Расскажите о проекте, стеке технологий или желаемых сроках..."
            ),
            "submit_btn": "Отправить заявку",
            "submitting_btn": "Отправка...",
            "close_btn_aria": "Закрыть модальное окно",
            "success_title": "Спасибо! Ваша заявка принята.",
            "success_msg": (
                "PM свяжется с вами в течение 15 минут с архитектурным решением и оценкой."
            ),
            "success_close_btn": "Закрыть",
            "error_generic": "Ошибка при отправке заявки. Пожалуйста, проверьте данные и попробуйте снова.",
            "required_badge": "Обязательно",
            "optional_badge": "Опционально",
        },
    },
}


def get_landing_context(lang: str = "en") -> Dict[str, Any]:
    """Provide structured context data for the landing page template in the requested language."""
    selected_lang = lang if lang in LOCALIZATION_DATA else "en"
    data = LOCALIZATION_DATA[selected_lang]

    context: Dict[str, Any] = {
        "lang": selected_lang,
        "lang_code": data["lang_code"],
        "html_title": data["html_title"],
        "meta_desc": data["meta_desc"],
        "app_name": data["app_name"],
        "app_tagline": data["app_tagline"],
        "version": data["version"],
        "nav": data["nav"],
        "hero": data["hero"],
        "metrics": {
            "velocity": data["hero"]["metrics"]["velocity"],
            "qa_pass_rate": data["hero"]["metrics"]["qa_pass_rate"],
            "bad_commits": data["hero"]["metrics"]["bad_commits"],
            "uptime_readiness": data["hero"]["metrics"]["uptime_readiness"],
        },
        "workflow": data["workflow"],
        "roster": data["roster"],
        "team_roster": data["roster"]["agents"],
        "capabilities": data["capabilities_section"]["items"],
        "capabilities_section": data["capabilities_section"],
        "trust": data["trust"],
        "footer": data["footer"],
        "modal": data["modal"],
    }
    return context


@app.get("/", response_class=HTMLResponse)
async def get_index_page(request: Request, lang: Optional[str] = None) -> HTMLResponse:
    """Serve the landing page in the requested language (defaults to 'en')."""
    selected_lang = (lang or request.cookies.get("openclaw_lang") or "en").lower()
    if selected_lang not in LOCALIZATION_DATA:
        selected_lang = "en"

    logger.info(
        "Serving landing page request (lang=%s) from %s",
        selected_lang,
        request.client.host if request.client else "unknown",
    )
    context = get_landing_context(lang=selected_lang)
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )
    response.set_cookie(
        key="openclaw_lang",
        value=selected_lang,
        max_age=30 * 24 * 3600,
        httponly=False,
        samesite="lax",
    )
    return response


@app.post("/api/leads", response_class=JSONResponse)
async def submit_lead_application(request: Request, lead: LeadRequest) -> JSONResponse:
    """Intake customer lead application, validate payload, and store lead record."""
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "Lead submission received from %s: name='%s', contact='%s'",
        client_ip,
        lead.name,
        lead.contact,
    )
    record = save_lead(lead, client_ip=client_ip)
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Thank you! Your application has been received successfully.",
            "lead_id": record["lead_id"],
        },
    )


@app.get("/health", response_class=JSONResponse)
async def get_health_status(request: Request) -> JSONResponse:
    """Healthcheck endpoint verifying service status and telemetry."""
    logger.info(
        "Health check requested from %s",
        request.client.host if request.client else "unknown",
    )
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": "openclaw-ai-landing-page",
            "version": "1.0.0",
            "agents_active": 5,
            "security_model": "least_privilege",
            "supported_languages": ["en", "ru"],
        },
    )


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception) -> HTMLResponse:
    """Custom 404 handler returning styled not-found page."""
    safe_path = html.escape(request.url.path)
    logger.warning("404 Not Found: %s", request.url.path)
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Page Not Found | OpenClaw AI Dev Team</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body class="error-page">
    <div class="error-container">
        <div class="error-badge">404 ERROR</div>
        <h1>Endpoint Not Found</h1>
        <p>The requested route <code>{safe_path}</code> does not exist on this server.</p>
        <a href="/" class="btn-return">Return to Landing Page</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=content, status_code=404)
