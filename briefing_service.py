"""AI Briefing Assistant Service for OpenClaw AI Dev Studio.

Conducts an adaptive, multi-step interactive briefing session with potential clients
to extract technical requirements, visual preferences, architecture scope,
and stakeholder contact information.
"""

import html
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("openclaw.briefing")

BRIEFS_FILE = Path(__file__).resolve().parent / "briefs.json"

# Question steps definition for RU and EN
BRIEFING_STEPS_RU = [
    {
        "step_id": "goals",
        "question": "Приветствую! Я AI-архитектор команды OpenClaw. Какой продукт или сайт вы планируете создать и какова его главная цель (например, привлечение лидов, запуск SaaS, продажа услуг)?",
        "suggestions": [
            "Конверсионный Landing Page",
            "SaaS-платформа / Сервис",
            "Корпоративный сайт компании",
            "Интернет-магазин / E-commerce",
        ],
    },
    {
        "step_id": "audience_usp",
        "question": "Отлично! Кто ваша целевая аудитория и в чем главное уникальное торговое предложение (УТП) или ключевая выгода для клиента?",
        "suggestions": [
            "B2B клиенты и enterprise-сегмент",
            "Стартапы и технологический бизнес",
            "Розничные покупатели / B2C",
            "Разработчики и IT-специалисты",
        ],
    },
    {
        "step_id": "visual_style",
        "question": "Какую стилистику и визуальную эстетику вы предпочитаете? Есть ли сайты-референсы или предпочтения по цветам?",
        "suggestions": [
            "Темный минимализм (как Helias)",
            "Студийный кибер-стиль с неоном",
            "Светлый лаконичный корпоративный",
            "Apple-стиль: чистый и просторный",
        ],
    },
    {
        "step_id": "sections_features",
        "question": "Какие ключевые разделы и функциональные модули понадобятся (например, Hero-блок, калькулятор, тарифы, кейсы, интеграция Telegram/CRM)?",
        "suggestions": [
            "Hero + Кейсы + Тарифы + Заявка",
            "Калькулятор + Онлайн-оплата + CRM",
            "Интерактивный AI-виджет + Блог",
            "Личный кабинет + Дашборд аналитики",
        ],
    },
    {
        "step_id": "contact_info",
        "question": "Зафиксировал! Укажите ваше имя и контакт для связи (Telegram, Email или телефон), чтобы мы сохранили бриф и выслали оценку сроков и стоимости.",
        "suggestions": [
            "@username (Telegram)",
            "email@example.com",
            "+7 (999) 000-00-00",
        ],
    },
]

BRIEFING_STEPS_EN = [
    {
        "step_id": "goals",
        "question": "Hello! I am OpenClaw's AI Web Architect. What kind of website or digital product are you looking to build, and what is its primary objective?",
        "suggestions": [
            "High-Converting Landing Page",
            "SaaS Platform / Web App",
            "Corporate Brand Website",
            "E-commerce Online Store",
        ],
    },
    {
        "step_id": "audience_usp",
        "question": "Great! Who is your target audience, and what is your main unique value proposition (UVP) or core competitive edge?",
        "suggestions": [
            "B2B Enterprise & Companies",
            "Startups & Tech Founders",
            "Direct Consumers / B2C",
            "Developers & Engineers",
        ],
    },
    {
        "step_id": "visual_style",
        "question": "What visual style and design aesthetic do you prefer? Do you have reference websites or specific color mood in mind?",
        "suggestions": [
            "Dark Minimalist (Helias aesthetic)",
            "Cyber Studio with Glowing Accents",
            "Clean Apple-like Modern Light",
            "Futuristic Glassmorphism",
        ],
    },
    {
        "step_id": "sections_features",
        "question": "What essential sections and features do you need (e.g., Hero CTA, Pricing tiers, Case studies, CRM/Telegram integrations)?",
        "suggestions": [
            "Hero + Features + Pricing + Lead Modal",
            "Interactive Calculator + CRM Sync",
            "AI Widget + Portfolio + Reviews",
            "Customer Portal + Payment Gateway",
        ],
    },
    {
        "step_id": "contact_info",
        "question": "Understood! Please provide your name and preferred contact details (Telegram, Email, or Phone) so we can send you the finalized brief and estimate.",
        "suggestions": [
            "@username (Telegram)",
            "email@example.com",
            "+1 (555) 019-2834",
        ],
    },
]


def sanitize_input(text: str) -> str:
    """Sanitize user inputs to prevent XSS and formatting artifacts."""
    cleaned = text.strip()
    return html.escape(cleaned)


def get_steps_for_lang(lang: str) -> List[Dict[str, Any]]:
    """Return localized steps list based on language."""
    return BRIEFING_STEPS_RU if lang.lower().startswith("ru") else BRIEFING_STEPS_EN


def build_brief_markdown(answers: Dict[str, str], lang: str) -> str:
    """Construct a structured markdown summary of the gathered brief."""
    is_ru = lang.lower().startswith("ru")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if is_ru:
        return f"""# 📋 ТЕХНИЧЕСКИЙ БРИФ ПРОЕКТА (OPENCLAW AI DEV STUDIO)
**Дата формирования:** {now_str}

---
### 1. 🎯 Цель проекта и тип продукта:
{answers.get('goals', 'Не указано')}

### 2. 👥 Целевая аудитория и УТП:
{answers.get('audience_usp', 'Не указано')}

### 3. 🎨 Визуальная эстетика и референсы:
{answers.get('visual_style', 'Не указано')}

### 4. 🧩 Архитектурные разделы и функционал:
{answers.get('sections_features', 'Не указано')}

### 5. 👤 Контактные данные заказчика:
{answers.get('contact_info', 'Не указано')}
---
*Сформировано автоматически интерактивным AI-интервьюером OpenClaw.*
"""
    else:
        return f"""# 📋 PROJECT SPECIFICATION BRIEF (OPENCLAW AI DEV STUDIO)
**Generated at:** {now_str}

---
### 1. 🎯 Project Goals & Product Type:
{answers.get('goals', 'Not specified')}

### 2. 👥 Target Audience & UVP:
{answers.get('audience_usp', 'Not specified')}

### 3. 🎨 Visual Aesthetics & References:
{answers.get('visual_style', 'Not specified')}

### 4. 🧩 Core Sections & Functionality:
{answers.get('sections_features', 'Not specified')}

### 5. 👤 Client Contact Details:
{answers.get('contact_info', 'Not specified')}
---
*Generated automatically by OpenClaw AI Briefing Assistant.*
"""


def save_brief_record(record: Dict[str, Any]) -> None:
    """Save completed brief to persistent storage JSON file."""
    try:
        data: List[Dict[str, Any]] = []
        if BRIEFS_FILE.exists():
            try:
                content = BRIEFS_FILE.read_text(encoding="utf-8").strip()
                if content:
                    data = json.loads(content)
            except Exception as read_err:
                logger.warning("Could not read existing briefs.json: %s", read_err)
                data = []

        data.append(record)
        BRIEFS_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Saved brief record %s to %s", record.get("brief_id"), BRIEFS_FILE)
    except Exception as exc:
        logger.error("Failed to save brief record to disk: %s", exc)


def process_briefing_message(
    session_id: str,
    message: Optional[str],
    history: List[Dict[str, str]],
    lang: str = "ru",
    client_ip: str = "127.0.0.1",
) -> Dict[str, Any]:
    """Process incoming chat message, advance state machine, and return next question or completion."""
    steps = get_steps_for_lang(lang)
    total_steps = len(steps)
    is_ru = lang.lower().startswith("ru")

    # Reconstruct answers from history
    user_messages = [
        msg["content"].strip()
        for msg in history
        if msg.get("role") == "user" and msg.get("content")
    ]

    if message and message.strip():
        user_messages.append(message.strip())

    step_index = len(user_messages)

    # Initial session start (0 user messages)
    if step_index == 0:
        first_step = steps[0]
        return {
            "session_id": session_id,
            "step_index": 0,
            "total_steps": total_steps,
            "message": first_step["question"],
            "suggestions": first_step["suggestions"],
            "is_completed": False,
            "brief_summary": None,
        }

    # Map answered steps
    answers: Dict[str, str] = {}
    for i, answer_text in enumerate(user_messages[:total_steps]):
        step_def = steps[i]
        answers[step_def["step_id"]] = answer_text

    # Ongoing questioning steps (steps 1 to total_steps - 1)
    if step_index < total_steps:
        current_step = steps[step_index]
        return {
            "session_id": session_id,
            "step_index": step_index,
            "total_steps": total_steps,
            "message": current_step["question"],
            "suggestions": current_step["suggestions"],
            "is_completed": False,
            "brief_summary": None,
        }

    # Brief Completed! (all 5 questions answered)
    brief_id = f"brief-{uuid.uuid4().hex[:8]}"
    brief_md = build_brief_markdown(answers, lang)
    created_at = datetime.now(timezone.utc).isoformat()

    record = {
        "brief_id": brief_id,
        "session_id": session_id,
        "client_ip": client_ip,
        "language": lang,
        "created_at": created_at,
        "answers": answers,
        "brief_markdown": brief_md,
    }

    # Save to disk
    save_brief_record(record)

    # Trigger email dispatch asynchronously via email_service
    try:
        from email_service import send_lead_notification_email

        email_lead_data = {
            "lead_id": brief_id,
            "name": answers.get("contact_info", "AI Brief Client"),
            "contact": answers.get("contact_info", "Provided in brief"),
            "message": f"⚡ ЗАВЕРШЕННЫЙ AI-БРИФ ПРОЕКТА:\n\n{brief_md}",
            "client_ip": client_ip,
            "created_at": created_at,
        }
        send_lead_notification_email(email_lead_data)
    except Exception as email_err:
        logger.warning("Could not dispatch brief email notification: %s", email_err)

    congrats_msg = (
        f"🎉 Спасибо! Ваш интерактивный бриф успешно сформирован и передан инженерам OpenClaw (ID: {brief_id}). "
        "Мы свяжемся с вами по указанным контактам в течение рабочего дня с готовым планом разработки и оценкой!"
        if is_ru
        else f"🎉 Thank you! Your interactive project brief is complete and delivered to OpenClaw engineers (ID: {brief_id}). "
        "We will reach out to you shortly with a tailored architecture proposal and timeline estimate!"
    )

    return {
        "session_id": session_id,
        "step_index": total_steps,
        "total_steps": total_steps,
        "message": congrats_msg,
        "suggestions": [],
        "is_completed": True,
        "brief_id": brief_id,
        "brief_summary": brief_md,
    }
