"""Autonomous Context-Aware AI Briefing Consultant for OpenClaw AI Dev Studio.

Operates as a Senior Product Manager & Web Architect conducting organic,
adaptive briefing interviews. Maintains full conversational context, performs
active clarification loops, tracks specification completeness (0-100%),
and synthesizes comprehensive architectural briefs.
"""

import html
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("openclaw.briefing")

BRIEFS_FILE = Path(__file__).resolve().parent / "briefs.json"

# Core Dimension Keys required for production-ready brief
DIMENSIONS = ["goals", "structure", "style", "features", "contact"]

SYSTEM_PROMPT_RU = """Ты — Senior Product Manager и Главный Web-Архитектор студии OpenClaw AI Dev Studio.
Твоя цель: провести экспертный, живой и глубокий диалог с потенциальным клиентом, чтобы собрать кристально четкие требования для создания высококонверсионного сайта или веб-продукта.

ПРИНЦИПЫ ДИАЛОГА:
1. Не будь роботом-опросником. Общайся как опытный digital-консультант, предлагай идеи и подсвечивай лучшие практики.
2. Активно уточняй размытые или абстрактные ответы (например, "хочу сайт как гугл для хлеба" или "сделайте красиво"). Предложи 2-3 конкретных сценария или архитектурных решения.
3. Отслеживай 5 ключевых критериев:
   - Бизнес-цели и целевая аудитория
   - Структура страницы (блоки, логический путь клиента, размещение CTA)
   - Визуальная эстетика, цветовая гамма и сайты-референсы
   - Функционал и интеграции (формы, калькуляторы, платежи, CRM, Telegram)
   - Контактные данные заказчика для отправки сметы и брифа
4. Задавай не более 1-2 сфокусированных вопросов за раз, чтобы клиенту было комфортно отвечать.
5. Предлагай релевантные быстрые варианты ответа (чипсы).
"""

SYSTEM_PROMPT_EN = """You are the Senior Product Manager and Lead Web Architect at OpenClaw AI Dev Studio.
Your goal: conduct an insightful, adaptive, organic conversation with prospective clients to gather a production-grade specification for their website or digital product.

CONVERSATION PRINCIPLES:
1. Never sound like a rigid questionnaire. Act as an expert product strategist, suggesting high-converting architectural ideas.
2. Actively drill down into vague or overly broad inputs (e.g. "I want a site like Google for bread"). Provide 2-3 tangible structure options.
3. Systematically extract 5 core dimensions:
   - Business Goals & Target Audience
   - Page Structure & Section Hierarchy (Hero, Proof, Features, CTA flow)
   - Visual Aesthetics, Color Tone & Reference Websites
   - Key Features & Integrations (Forms, CRM, Telegram bot, Checkout)
   - Stakeholder Contact Info for brief delivery
4. Ask only 1-2 focused questions per turn.
5. Provide relevant quick-reply suggestions.
"""


def sanitize_text(text: str) -> str:
    """Sanitize user inputs to prevent XSS and formatting artifacts."""
    cleaned = text.strip()
    return html.escape(cleaned)


def is_vague_or_gibberish(text: str) -> bool:
    """Detect if user response is meaningless, too short, or lacks context."""
    cleaned = text.strip().lower()
    if len(cleaned) < 3:
        return True
    # Check for keyboard smash (e.g. asdasd, qwerty, 1111)
    if re.match(r"^[a-zа-я0-9]+$", cleaned) or cleaned in {
        "asdasd",
        "qwerty",
        "test",
        "hz",
        "хз",
        "123",
        "idk",
    }:
        return True
    return False


def analyze_extracted_dimensions(
    history: List[Dict[str, str]], current_message: Optional[str] = None
) -> Dict[str, str]:
    """Extract and categorize covered project dimensions from full conversation history."""
    extracted: Dict[str, str] = {}
    all_user_texts = [
        msg["content"].strip()
        for msg in history
        if msg.get("role") == "user" and msg.get("content")
    ]
    if current_message and current_message.strip():
        all_user_texts.append(current_message.strip())

    combined_text = " ".join(all_user_texts).lower()

    # Step-by-step heuristic extraction
    for idx, text in enumerate(all_user_texts):
        t_low = text.lower()
        if idx == 0 or any(
            k in t_low
            for k in [
                "landing",
                "лендинг",
                "сайт",
                "платформ",
                "магазин",
                "saas",
                "app",
                "b2b",
                "цель",
                "проект",
            ]
        ):
            if "goals" not in extracted:
                extracted["goals"] = text
        if any(
            k in t_low
            for k in [
                "блок",
                "раздел",
                "структур",
                "hero",
                "секц",
                "тариф",
                "цен",
                "отзыв",
                "меню",
                "каталог",
                "section",
                "pricing",
            ]
        ):
            extracted["structure"] = text
        if any(
            k in t_low
            for k in [
                "дизайн",
                "стил",
                "цвет",
                "темн",
                "минимал",
                "неон",
                "референс",
                "helias",
                "apple",
                "style",
                "dark",
                "light",
            ]
        ):
            extracted["style"] = text
        if any(
            k in t_low
            for k in [
                "интеграц",
                "crm",
                "telegram",
                "оплат",
                "калькулятор",
                "форма",
                "чат",
                "бот",
                "feature",
                "payment",
            ]
        ):
            extracted["features"] = text
        if any(
            k in t_low
            for k in [
                "@",
                "telegram",
                "телеграм",
                "mail",
                "почт",
                "+7",
                "+1",
                "89",
                "phone",
                "тел",
                ".com",
                ".ru",
            ]
        ):
            extracted["contact"] = text

    # Fallback to positional mapping if user answered sequentially
    for i, dim in enumerate(DIMENSIONS):
        if dim not in extracted and i < len(all_user_texts):
            extracted[dim] = all_user_texts[i]

    return extracted


def calculate_completeness(extracted: Dict[str, str]) -> Tuple[int, List[str]]:
    """Calculate brief completeness percentage (0 to 100) and identify missing dimensions."""
    covered = [
        k
        for k in DIMENSIONS
        if k in extracted and not is_vague_or_gibberish(extracted[k])
    ]
    score = int((len(covered) / len(DIMENSIONS)) * 100)
    missing = [k for k in DIMENSIONS if k not in covered]
    return score, missing


def generate_autonomous_response(
    session_id: str,
    message: Optional[str],
    history: List[Dict[str, str]],
    lang: str = "ru",
    client_ip: str = "127.0.0.1",
) -> Dict[str, Any]:
    """Generate context-aware next question, suggestions, and completeness score."""
    is_ru = lang.lower().startswith("ru")
    all_user_msgs = [m["content"] for m in history if m.get("role") == "user"]
    if message and message.strip():
        all_user_msgs.append(message.strip())

    extracted = analyze_extracted_dimensions(history, message)
    completeness, missing = calculate_completeness(extracted)

    # Initial turn (0 user messages)
    if not all_user_msgs:
        init_msg = (
            "Приветствую! Я Senior Product Manager и AI-архитектор команды OpenClaw. "
            "Я помогу детально проработать концепт, структуру и визуальный стиль вашего будущего сайта. "
            "Расскажите, какой продукт или услугу вы планируете упаковать и какова главная цель запуска?"
            if is_ru
            else "Hello! I'm OpenClaw's Senior Product Manager & AI Web Architect. "
            "I'm here to help you engineer a crystal-clear concept, page structure, and design aesthetic. "
            "What product or service are you building, and what is the primary business objective of this site?"
        )
        suggestions = (
            [
                "B2B Landing Page с высокой конверсией",
                "SaaS / Web App платформа",
                "Корпоративный сайт для компании",
                "Интернет-магазин / E-commerce витрина",
            ]
            if is_ru
            else [
                "High-Converting B2B Landing Page",
                "SaaS / Web Application Platform",
                "Corporate Brand Website",
                "Modern E-Commerce Storefront",
            ]
        )
        return {
            "session_id": session_id,
            "message": init_msg,
            "suggestions": suggestions,
            "completeness": 10,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    last_user_msg = all_user_msgs[-1]

    # Handle Vague or Gibberish Input
    if is_vague_or_gibberish(last_user_msg):
        clarification_msg = (
            f"Кажется, ответ «{last_user_msg}» немного абстрактен. Чтобы сайт точно приносил заявки, "
            "давайте конкретизируем: кто ваши основные клиенты и какое главное преимущество мы покажем на первом экране?"
            if is_ru
            else f"The input '{last_user_msg}' seems a bit brief. To ensure high conversion, "
            "let's narrow it down: who is your core customer and what primary value proposition should we highlight on the hero screen?"
        )
        suggestions = (
            [
                "Премиальный B2B enterprise сегмент",
                "Стартапы и технологические фаундеры",
                "Розничные покупатели / B2C",
                "Срочные услуги для частных лиц",
            ]
            if is_ru
            else [
                "B2B Enterprise & Mid-Market",
                "Tech Startups & Founders",
                "Direct-to-Consumer / B2C",
                "High-Ticket Services",
            ]
        )
        return {
            "session_id": session_id,
            "message": clarification_msg,
            "suggestions": suggestions,
            "completeness": completeness,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Autonomous Steering based on missing dimensions
    if "structure" in missing:
        msg = (
            "Отлично, направление понято! Теперь определим структуру страницы. "
            "Какие смысловые блоки критически важно включить? Например: Hero с ярким CTA, калькулятор тарифов, интерактивное портфолио, отзывы и ответы на вопросы?"
            if is_ru
            else "Got it, strong direction! Next, let's architect the page structure. "
            "What key content sections are essential? E.g., Hero CTA, Interactive Pricing Calculator, Case Studies grid, Trust Matrix, and FAQ?"
        )
        suggestions = (
            [
                "Hero + Кейсы + Тарифы + Заявка",
                "Калькулятор цен + Сравнение с конкурентами",
                "Интерактивная демонстрация + Отзывы + FAQ",
                "Одноэкранный квиз-лендинг с лид-магнитом",
            ]
            if is_ru
            else [
                "Hero + Portfolio Cases + Pricing + Form",
                "Interactive Calculator + Competitor Matrix",
                "Live Demo Widget + Testimonials + FAQ",
                "High-Velocity Quiz Landing Page",
            ]
        )
        return {
            "session_id": session_id,
            "message": msg,
            "suggestions": suggestions,
            "completeness": max(completeness, 40),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    if "style" in missing:
        msg = (
            "Структура зафиксирована! Какая визуальная эстетика и атмосфера лучше всего передадут характер вашего бренда? "
            "Предпочитаете темный минимализм с неоновыми акцентами (как Helias), строгий светлый корпоративный стиль или воздушный glassmorphism?"
            if is_ru
            else "Section blueprint recorded! What visual style and atmosphere fits your brand best? "
            "Do you prefer obsidian dark minimalism with ambient neon glows (Helias style), clean corporate light, or high-tech glassmorphism?"
        )
        suggestions = (
            [
                "Темный минимализм с изумрудным/бирюзовым неоном",
                "Чистый светлый стиль (в духе Apple)",
                "Футуристичный Glassmorphism с анимациями",
                "Строгий премиальный корпоративный стиль",
            ]
            if is_ru
            else [
                "Obsidian Dark Minimalist with Emerald Glow",
                "Clean Light & Spacious (Apple aesthetic)",
                "Cyberpunk Glassmorphism with Smooth FX",
                "High-Trust Corporate & Editorial",
            ]
        )
        return {
            "session_id": session_id,
            "message": msg,
            "suggestions": suggestions,
            "completeness": max(completeness, 65),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    if "features" in missing:
        msg = (
            "Эстетика выглядит потрясающе! Какие интерактивные модули и технические интеграции потребуются? "
            "(Например: автоматические уведомления в Telegram, онлайн-оплата, синхронизация с CRM или мультиязычность?)"
            if is_ru
            else "Aesthetics locked in! What interactive features and third-party integrations do you need? "
            "(E.g., instant Telegram lead alerts, Stripe/YooKassa payment, CRM webhook synchronization, or bilingual RU/EN switch?)"
        )
        suggestions = (
            [
                "Уведомления в Telegram + Email + CRM",
                "Онлайн-оплата + Автоматический расчет сметы",
                "Двуязычная локализация (RU / EN)",
                "Интерактивный AI-консультант в чате",
            ]
            if is_ru
            else [
                "Instant Telegram & Email Dispatch + CRM",
                "Online Checkout & Dynamic Estimator",
                "Full Bilingual (RU / EN) Support",
                "Interactive AI Chat Assistant Widget",
            ]
        )
        return {
            "session_id": session_id,
            "message": msg,
            "suggestions": suggestions,
            "completeness": max(completeness, 85),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    if "contact" in missing or completeness < 100:
        msg = (
            "Все технические параметры проработаны на 100%! "
            "Укажите, пожалуйста, ваше имя и удобный контакт (Telegram @username, email или телефон), "
            "чтобы мы зафиксировали бриф и отправили вам готовую спецификацию и смету реализации."
            if is_ru
            else "All technical parameters are fully architected! "
            "Please provide your name and preferred contact handle (Telegram, Email, or Phone) "
            "so we can lock in this brief and deliver your tailored architecture proposal and timeline estimate."
        )
        suggestions = (
            [
                "@username (Telegram)",
                "my.email@domain.com",
                "+7 (999) 123-45-67",
            ]
            if is_ru
            else [
                "@username (Telegram)",
                "founder@startup.io",
                "+1 (555) 234-5678",
            ]
        )
        return {
            "session_id": session_id,
            "message": msg,
            "suggestions": suggestions,
            "completeness": 95,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # All dimensions complete -> Synthesize Brief!
    brief_id = f"brief-{uuid.uuid4().hex[:8]}"
    brief_md = synthesize_brief_markdown(extracted, lang)
    created_at = datetime.now(timezone.utc).isoformat()

    record = {
        "brief_id": brief_id,
        "session_id": session_id,
        "client_ip": client_ip,
        "language": lang,
        "created_at": created_at,
        "extracted_dimensions": extracted,
        "brief_markdown": brief_md,
    }
    save_brief_record(record)

    # Trigger email dispatch
    try:
        from email_service import send_lead_notification_email

        email_lead_data = {
            "lead_id": brief_id,
            "name": extracted.get("contact", "AI Brief Client"),
            "contact": extracted.get("contact", "Specified in Brief"),
            "message": f"⚡ СИНТЕЗИРОВАННЫЙ AI-БРИФ ПРОЕКТА:\n\n{brief_md}",
            "client_ip": client_ip,
            "created_at": created_at,
        }
        send_lead_notification_email(email_lead_data)
    except Exception as email_err:
        logger.warning("Could not dispatch synthesized brief email: %s", email_err)

    completion_msg = (
        f"🎯 Отличная работа! Ваш концептуальный бриф полностью сформирован и передан ведущим разработчикам OpenClaw (ID: {brief_id}). "
        "Мы свяжемся с вами в течение рабочего дня с готовой сметой и детальным планом спринтов!"
        if is_ru
        else f"🎯 Outstanding! Your technical specification brief has been synthesized and assigned to OpenClaw engineers (ID: {brief_id}). "
        "Our team will reach out via your provided contact with the sprint breakdown and pricing estimate!"
    )

    return {
        "session_id": session_id,
        "message": completion_msg,
        "suggestions": [],
        "completeness": 100,
        "is_completed": True,
        "brief_id": brief_id,
        "brief_summary": brief_md,
        "extracted_dimensions": extracted,
    }


def synthesize_brief_markdown(extracted: Dict[str, str], lang: str) -> str:
    """Synthesize a high-fidelity Markdown technical specification."""
    is_ru = lang.lower().startswith("ru")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if is_ru:
        return f"""# 📋 ТЕХНИЧЕСКИЙ БРИФ ПРОЕКТА (OPENCLAW AI DEV STUDIO)
**ID Спецификации:** `SPEC-{uuid.uuid4().hex[:6].upper()}`
**Дата синтеза:** {now_str}

---
### 1. 🎯 Бизнес-цели и Целевая Аудитория:
{extracted.get('goals', 'Не указано')}

### 2. 📐 Архитектура страницы и Разделы:
{extracted.get('structure', 'Hero, Features, Pricing, Trust Matrix, CTA Modal')}

### 3. 🎨 Визуальная Эстетика и Референсы:
{extracted.get('style', 'Obsidian Dark Minimalist (Helias Aesthetic)')}

### 4. 🧩 Функциональные Модули и Интеграции:
{extracted.get('features', 'Асинхронные формы, Telegram/Email оповещения, SEO мета-теги')}

### 5. 👤 Контактные данные заказчика:
{extracted.get('contact', 'Не указано')}

---
### 🚀 Рекомендованный стек OpenClaw:
- **Backend:** FastAPI (Python 3.12) / Go 1.22 Microservices
- **Frontend:** Semantic HTML5, CSS3 Tokens, Vanilla JS ES6+ (No heavy build frameworks)
- **Infrastructure:** Docker, SSL TLS 1.3, Asynchronous SMTP dispatch
- **Оценка скорости реализации:** 3-5 рабочих дней при velocity x10
"""
    else:
        return f"""# 📋 PROJECT SPECIFICATION BRIEF (OPENCLAW AI DEV STUDIO)
**Specification ID:** `SPEC-{uuid.uuid4().hex[:6].upper()}`
**Synthesized At:** {now_str}

---
### 1. 🎯 Business Objectives & Target Audience:
{extracted.get('goals', 'Not specified')}

### 2. 📐 Page Structure & Section Blueprint:
{extracted.get('structure', 'Hero, Features, Pricing, Trust Matrix, Lead Intake Modal')}

### 3. 🎨 Visual Aesthetics & Reference Palette:
{extracted.get('style', 'Obsidian Dark Minimalist (Helias-inspired typography)')}

### 4. 🧩 Functional Modules & Integrations:
{extracted.get('features', 'Asynchronous lead dispatch, Telegram notifications, SEO')}

### 5. 👤 Client Contact Details:
{extracted.get('contact', 'Not specified')}

---
### 🚀 Recommended OpenClaw Architecture:
- **Backend:** FastAPI (Python 3.12) / Go 1.22 Microservices
- **Frontend:** Semantic HTML5, CSS3 Custom Properties, Vanilla ES6+
- **Infrastructure:** Docker containers, TLS 1.3, Background task workers
- **Estimated Development Sprint:** 3-5 business days at 10x velocity
"""


def save_brief_record(record: Dict[str, Any]) -> None:
    """Save brief record to local persistent JSON file."""
    try:
        data: List[Dict[str, Any]] = []
        if BRIEFS_FILE.exists():
            try:
                content = BRIEFS_FILE.read_text(encoding="utf-8").strip()
                if content:
                    data = json.loads(content)
            except Exception as read_err:
                logger.warning("Could not read briefs.json: %s", read_err)
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
    """Entry point for processing chat briefing turns."""
    return generate_autonomous_response(
        session_id=session_id,
        message=message,
        history=history,
        lang=lang,
        client_ip=client_ip,
    )
