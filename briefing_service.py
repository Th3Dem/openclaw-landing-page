"""Autonomous Context-Aware AI Briefing Consultant for OpenClaw AI Dev Studio.

Operates as a Senior Product Manager & Web Architect conducting organic,
adaptive briefing interviews. Maintains full conversational context, performs
active clarification loops, tracks specification completeness (0-100%),
and synthesizes comprehensive architectural briefs.
"""

from __future__ import annotations

import html
import json
import logging
import os
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

ENV_FILE = Path(__file__).resolve().parent / ".env"


def load_env() -> None:
    """Load local .env into environment if exists."""
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v
        except Exception as e:
            logger.debug("Could not parse .env: %s", e)


load_env()

NICHE_KNOWLEDGE_RU: Dict[str, Dict[str, Any]] = {
    "food": {
        "keywords": [
            "торт",
            "еда",
            "ресторан",
            "доставк",
            "кафе",
            "выпечк",
            "десерт",
            "кондитер",
            "пицц",
            "суши",
            "бургер",
        ],
        "insights": "В нише доставки еды и десертов решающее значение имеет аппетитный визуальный wow-контент, видео-разрезы и прозрачный расчет времени доставки.",
        "features": [
            "Интерактивный конфигуратор вкусов/начинок",
            "Экспресс-заказ в 1 клик с выбором времени",
            "Интеграция с Яндекс.Доставкой / Telegram-ботом кухни",
        ],
        "next_q": "Как клиентам будет удобнее выбирать продукцию — через онлайн-каталог с фильтрами и корзиной прямо на сайте, или вы хотите сразу переводить покупателя на оформление заказа в Telegram/WhatsApp?",
        "chips": [
            "Каталог с корзиной и оплатой",
            "Конструктор начинок и веса",
            "Быстрый заказ в Telegram",
            "Экспресс-доставка по городу",
        ],
    },
    "auto": {
        "keywords": [
            "авто",
            "машин",
            "автоподбор",
            "детейлинг",
            "сервис",
            "ремонт авто",
            "запчаст",
            "шиномонтаж",
            "тюнинг",
        ],
        "insights": "Для автомобильной тематики ключевыми триггерами доверия выступают прозрачные кейсы с фото/видео до/после, калькулятор стоимости и проверка по базам.",
        "features": [
            "Квиз-калькулятор параметров авто",
            "Интерактивная карта филиалов/мастеров",
            "Виджет мгновенной оценки стоимости",
        ],
        "next_q": "Планируете ли вы интерактивный квиз/калькулятор (например, подбор авто по бюджету или расчет стоимости детейлинга) для захвата горячих лидов?",
        "chips": [
            "Квиз-подбор по бюджету",
            "Калькулятор стоимости услуг",
            "Кейсы с фото до/после",
            "Запись на диагностику в 1 клик",
        ],
    },
    "saas": {
        "keywords": [
            "saas",
            "сервис",
            "платформ",
            "app",
            "приложен",
            "b2b",
            "crm",
            "ai",
            "финтех",
            "стартап",
            "аналитик",
            "софт",
        ],
        "insights": "Для SaaS и технологических стартапов основа конверсии — понятная интерактивная демонстрация интерфейса, прозрачная тарифная сетка и быстрый онбординг.",
        "features": [
            "Интерактивный дашборд-превью",
            "Переключатель тарифов (месяц/год)",
            "Бесплатный демо-доступ в 1 клик",
        ],
        "next_q": "Какая механика первого касания вам ближе: бесплатный триал без привязки карты, запись на интерактивное демо с продуктовым экспертом или мгновенный доступ через Google/GitHub?",
        "chips": [
            "Бесплатный триал (14 дней)",
            "Запись на Live-демо",
            "Тарифы с ежемесячной оплатой",
            "Документация и API",
        ],
    },
    "realty": {
        "keywords": [
            "недвижим",
            "квартир",
            "дом",
            "аренд",
            "строительств",
            "жк",
            "риелтор",
            "ипотек",
            "участок",
            "интерьер",
        ],
        "insights": "В недвижимости клиент покупает статус и надежность. Важны 3D-планировки, динамический калькулятор ипотеки и подборка объектов под бюджет.",
        "features": [
            "Каталог объектов с фильтрами по районам",
            "Ипотечный калькулятор с графиком платежей",
            "Запись на персональный просмотр",
        ],
        "next_q": "Нужен ли на сайте интерактивный фильтр объектов с параметрами (площадь, бюджет, район) и возможность скачать презентацию в PDF в обмен на контакт?",
        "chips": [
            "Каталог объектов с фильтрами",
            "Ипотечный калькулятор",
            "Скачать PDF-презентацию",
            "Запись на просмотр в WhatsApp",
        ],
    },
    "education": {
        "keywords": [
            "курс",
            "обучен",
            "школ",
            "вебинар",
            "ментор",
            "репетитор",
            "марафон",
            "лекци",
            "интенсив",
            "академи",
        ],
        "insights": "В онлайн-образовании конверсию драйвят подробная программа обучения по модулям, профили экспертов и реальные видео-отзывы выпускников.",
        "features": [
            "Интерактивная программа по неделям",
            "Таймер до старта потока со скидкой",
            "Лид-магнит (пробный урок за контакт)",
        ],
        "next_q": "Как будет выстроена воронка продаж: прямая покупка тарифов с сайта (с рассрочкой), или сначала бесплатный вводный урок/вебинар для сбора базы?",
        "chips": [
            "Бесплатный первый урок",
            "Тарифы с банковской рассрочкой",
            "Программа по модулям",
            "Видео-отзывы выпускников",
        ],
    },
    "ecommerce": {
        "keywords": [
            "магазин",
            "одежд",
            "товар",
            "купить",
            "бренд",
            "витрин",
            "дропшиппинг",
            "маркетплейс",
            "аксессуар",
        ],
        "insights": "В e-commerce решают скорость загрузки, стильный лукбук, моментальный поиск и удобная корзина без лишних шагов регистрации.",
        "features": [
            "Быстрый просмотр товаров",
            "Подключение эквайринга (СБП, карты, Долями)",
            "Синхронизация остатков со складом/МойСклад",
        ],
        "next_q": "Планируете ли вы полноценную интеграцию онлайн-оплаты (карты, СБП, сервисы рассрочки вроде 'Долями') и интеграцию с CRM для учета остатков?",
        "chips": [
            "Онлайн-оплата (СБП / Долями)",
            "Каталог с умными фильтрами",
            "Синхронизация с 1С/МойСклад",
            "Быстрый заказ без регистрации",
        ],
    },
}

NICHE_KNOWLEDGE_EN: Dict[str, Dict[str, Any]] = {
    "food": {
        "keywords": [
            "cake",
            "food",
            "restaurant",
            "delivery",
            "bakery",
            "dessert",
            "pizza",
            "sushi",
            "coffee",
        ],
        "insights": "For food & dessert delivery, sensory visual appeal (video cuts, ingredients showcase) and real-time delivery estimates drive conversions.",
        "features": [
            "Interactive flavor/ingredient customizer",
            "1-click express checkout with time slot",
            "Live delivery tracking & Telegram sync",
        ],
        "next_q": "How would you prefer customers to order: an interactive customizer with instant online checkout, or direct handover to WhatsApp/Telegram support?",
        "chips": [
            "Online Catalog & Checkout",
            "Flavor Customizer Builder",
            "Fast WhatsApp/Telegram Order",
            "Same-Day Delivery Widget",
        ],
    },
    "saas": {
        "keywords": [
            "saas",
            "platform",
            "app",
            "software",
            "b2b",
            "crm",
            "ai",
            "fintech",
            "startup",
            "analytics",
        ],
        "insights": "For SaaS & Tech products, the key conversion levers are interactive UI previews, clear transparent pricing tiers, and frictionless onboarding.",
        "features": [
            "Interactive live product sandbox",
            "Monthly/Annual pricing toggle",
            "1-click Google/GitHub Auth",
        ],
        "next_q": "What primary onboarding flow fits your model: a 14-day free trial without credit card, a live product demo with an expert, or instant self-service sign-up?",
        "chips": [
            "14-Day Free Trial (No Card)",
            "Book a Live Product Demo",
            "Transparent Pricing Tiers",
            "Interactive Dashboard Sandbox",
        ],
    },
    "realty": {
        "keywords": [
            "real estate",
            "property",
            "apartment",
            "house",
            "villa",
            "construction",
            "interior",
            "realtor",
            "mortgage",
        ],
        "insights": "In real estate, trust and visualization reign supreme. Interactive 3D floor plans and instant mortgage estimators generate high-intent inquiries.",
        "features": [
            "Filterable property listings grid",
            "Mortgage payment calculator",
            "VIP Viewing schedule form",
        ],
        "next_q": "Should we include an interactive property filter with neighborhood maps and an instant downloadable PDF investment brochure?",
        "chips": [
            "Filterable Property Grid",
            "Mortgage Estimator Tool",
            "Download PDF Brochure",
            "Private Viewing Booking",
        ],
    },
}


def sanitize_text(text: str) -> str:
    """Sanitize user inputs to prevent XSS and formatting artifacts."""
    cleaned = text.strip()
    return html.escape(cleaned)


def is_vague_or_gibberish(text: str) -> bool:
    """Detect if user response is meaningless or lacks context."""
    cleaned = text.strip().lower()
    if len(cleaned) < 3:
        return True
    if re.match(r"^([a-zа-я0-9])\1+$", cleaned) or cleaned in {
        "asdasd",
        "qwerty",
        "test",
        "hz",
        "хз",
        "123",
        "idk",
        "asdf",
    }:
        return True
    return False


def detect_niche(
    text: str, is_ru: bool = True
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Identify business niche from text using semantic keywords."""
    knowledge = NICHE_KNOWLEDGE_RU if is_ru else NICHE_KNOWLEDGE_EN
    text_low = text.lower()
    for niche_name, niche_data in knowledge.items():
        for kw in niche_data["keywords"]:
            if kw in text_low:
                return niche_name, niche_data
    return None, None


def call_llm_if_available(
    system_prompt: str, history: List[Dict[str, str]], user_message: str
) -> Optional[str]:
    """Invoke OpenAI / OpenRouter / Gemini API if API key is configured in environment."""
    api_key = (
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GROQ_API_KEY")
    )
    if not api_key:
        return None

    api_url = "https://api.openai.com/v1/chat/completions"
    model = "gpt-4o-mini"

    if os.environ.get("OPENROUTER_API_KEY"):
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        model = "google/gemini-2.0-flash-lite:free"
    elif os.environ.get("GROQ_API_KEY"):
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append(
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
        )
    messages.append({"role": "user", "content": user_message})

    req_data = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 450,
    }

    try:
        import urllib.request

        req = urllib.request.Request(
            api_url,
            data=json.dumps(req_data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "OpenClaw-Studio/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "choices" in data and len(data["choices"]) > 0:
                answer = data["choices"][0]["message"]["content"].strip()
                logger.info(
                    "Successfully generated response using LLM provider (%s)", model
                )
                return str(answer)
    except Exception as err:
        logger.warning("LLM API call failed, using advanced semantic engine: %s", err)

    return None


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
    """Deep Context-Aware conversational engine with niche intelligence."""
    is_ru = lang.lower().startswith("ru")
    user_turns = [
        m["content"].strip()
        for m in history
        if m.get("role") == "user" and m.get("content")
    ]
    if message and message.strip():
        user_turns.append(message.strip())

    turn_count = len(user_turns)
    extracted = analyze_extracted_dimensions(history, message)
    all_text = " ".join(user_turns)

    # 1. First Turn (Initial Greeting)
    if turn_count == 0:
        greeting = (
            "Приветствую! Я Senior Product Manager и Главный Архитектор OpenClaw. "
            "Я помогу глубоко проработать идею вашего сайта, выстроить сильную"
            " структуру и упаковать УТП для максимальной конверсии. Расскажите,"
            " какой продукт или сервис вы хотите запустить и в чем его главная"
            " ценность для клиентов?"
            if is_ru
            else (
                "Hello! I am OpenClaw's Senior Product Manager & Lead Web"
                " Architect. I'm here to help you architect a high-converting web"
                " presence tailored specifically to your business vision. Tell me"
                " about the product or service you're building and the core value"
                " proposition you want to convey."
            )
        )
        suggestions = (
            [
                "Конверсионный Landing Page для B2B",
                "SaaS-сервис / Web App платформа",
                "Интернет-магазин / E-commerce витрина",
                "Корпоративный сайт для компании",
            ]
            if is_ru
            else [
                "High-Converting B2B Landing Page",
                "SaaS Platform / Web App",
                "Modern E-Commerce Storefront",
                "Corporate Brand Website",
            ]
        )
        return {
            "session_id": session_id,
            "message": greeting,
            "suggestions": suggestions,
            "completeness": 10,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    last_user_msg = user_turns[-1]

    # 2. Check for vague or gibberish input
    if is_vague_or_gibberish(last_user_msg):
        clarification = (
            f"Ответ «{last_user_msg}» звучит слишком абстрактно. Чтобы сайт приносил"
            " реальные заявки, давайте конкретизируем: кто ваша ключевая"
            " целевая аудитория и какую главную проблему клиентов решает ваш"
            " продукт?"
            if is_ru
            else (
                f"The input '{last_user_msg}' is quite brief. To ensure high"
                " conversion, let's specify: who is your core target audience"
                " and what primary problem does your product solve?"
            )
        )
        suggestions = (
            [
                "B2B клиенты и компании",
                "Розничные покупатели (B2C)",
                "Стартапы и технологический бизнес",
                "Премиальный сегмент",
            ]
            if is_ru
            else [
                "B2B Enterprise & Mid-Market",
                "Direct-to-Consumer (B2C)",
                "Tech Startups & Founders",
                "High-Ticket Premium Clients",
            ]
        )
        return {
            "session_id": session_id,
            "message": clarification,
            "suggestions": suggestions,
            "completeness": max(15, (turn_count * 15)),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # 3. Try LLM Call first if key exists
    system_prompt = SYSTEM_PROMPT_RU if is_ru else SYSTEM_PROMPT_EN
    llm_reply = call_llm_if_available(system_prompt, history, last_user_msg)
    if llm_reply:
        completeness = min(100, turn_count * 22)
        is_done = turn_count >= 5 or (
            "@" in all_text
            or "telegram" in all_text.lower()
            or "phone" in all_text.lower()
        )
        brief_md = synthesize_brief_markdown(extracted, lang) if is_done else None
        return {
            "session_id": session_id,
            "message": llm_reply,
            "suggestions": [],
            "completeness": 100 if is_done else completeness,
            "is_completed": is_done,
            "extracted_dimensions": extracted,
            "brief_summary": brief_md,
        }

    # 4. Deep Niche Analysis & Contextual Reasoning Engine
    niche_name, niche_info = detect_niche(all_text, is_ru)
    first_user_goal = user_turns[0]

    # Turn 1 Response: Deep Dive into Product Concept & Niche Architecture
    if turn_count == 1:
        if niche_info:
            reply = (
                f"Отличная ниша («{first_user_goal}»)! {niche_info['insights']}\n\n"
                "Для максимальной конверсии я рекомендую внедрить такие решения: "
                f"{', '.join(niche_info['features'])}.\n\n"
                f"{niche_info['next_q']}"
                if is_ru
                else (
                    f"Great niche concept ('{first_user_goal}')!"
                    f" {niche_info['insights']}\n\nTo maximize conversions, I"
                    " recommend architectural highlights:"
                    f" {', '.join(niche_info['features'])}.\n\n{niche_info['next_q']}"
                )
            )
            chips = niche_info["chips"]
        else:
            reply = (
                f"Принято, идея «{first_user_goal}» звучит очень перспективно! "
                "Чтобы спроектировать правильный пользовательский путь (Customer"
                " Journey Map), какие ключевые смысловые блоки критически важно"
                " показать на странице? (Например: Hero с оффером, интерактивный"
                " калькулятор/квиз, блок кейсов, прозрачные тарифы и отзывы?)"
                if is_ru
                else (
                    f"Understood, '{first_user_goal}' is a compelling concept!"
                    " To engineer an optimal Customer Journey Map, what core"
                    " page sections are essential? (E.g., High-impact Hero CTA,"
                    " Interactive Calculator/Quiz, Case Studies, Pricing Tiers,"
                    " and Proof Matrix?)"
                )
            )
            chips = (
                [
                    "Hero + Кейсы + Тарифы + Заявка",
                    "Интерактивный калькулятор стоимости",
                    "Демонстрация продукта + Отзывы + FAQ",
                    "Лид-магнит с мгновенным доступом",
                ]
                if is_ru
                else [
                    "Hero + Cases + Pricing + Form",
                    "Interactive Pricing Estimator",
                    "Product Demo + Proof + FAQ",
                    "Lead Magnet Quiz Flow",
                ]
            )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": 35,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Turn 2 Response: Visual Identity, Brand Vibe & References
    if turn_count == 2:
        structure_choice = last_user_msg
        reply = (
            f"Структура и логика блоков («{structure_choice}») отлично подходят"
            " для вашей задачи! Теперь определим визуальную атмосферу бренда."
            " Какая эстетика вам ближе: глубокий обсидиановый минимализм со"
            " светящимися неоновыми акцентами (как Helias), чистый просторный"
            " Apple-стиль или высокотехнологичный Glassmorphism с плавными"
            " микро-анимациями?"
            if is_ru
            else (
                f"The section blueprint ('{structure_choice}') aligns perfectly"
                " with your goals! Now let's establish the visual brand identity."
                " What aesthetic atmosphere do you envision: deep obsidian dark"
                " minimalism with glowing accents (Helias aesthetic), clean"
                " spacious Apple-like light theme, or high-tech glassmorphism with"
                " fluid micro-interactions?"
            )
        )
        chips = (
            [
                "Темный минимализм со свечением (Helias)",
                "Светлый лаконичный стиль (Apple)",
                "Студийный Glassmorphism с анимацией",
                "Премиальный строгий корпоративный",
            ]
            if is_ru
            else [
                "Obsidian Dark Minimalist (Helias style)",
                "Clean Spacious Light (Apple style)",
                "Cyber Glassmorphism with Smooth FX",
                "High-Trust Corporate Editorial",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": 60,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Turn 3 Response: Integrations, Tech Workflow & Notifications
    if turn_count == 3:
        style_choice = last_user_msg
        reply = (
            f"Визуальный стиль «{style_choice}» будет выглядеть премиально и"
            " современно! Какие технические интеграции и каналы обработки лидов"
            " потребуются? Например: мгновенные уведомления о заявках в"
            " Telegram-чат вашей команды, онлайн-оплата (карты/СБП/Долями),"
            " синхронизация с CRM (AmoCRM, Bitrix24) или мультиязычность"
            " (RU/EN)?"
            if is_ru
            else (
                f"Visual aesthetic '{style_choice}' will look outstanding and"
                " premium! What technical integrations and backend workflows are"
                " required? For example: instant Telegram team alerts,"
                " Stripe/credit card checkout, CRM webhook sync, or bilingual"
                " (EN/RU) localization?"
            )
        )
        chips = (
            [
                "Telegram-оповещения + Email + CRM",
                "Онлайн-оплата + Авто-расчет цены",
                "Двуязычная локализация (RU / ENG)",
                "Интерактивный AI-консультант на сайте",
            ]
            if is_ru
            else [
                "Instant Telegram & Email Dispatch + CRM",
                "Online Checkout & Dynamic Calculator",
                "Full Bilingual (RU / EN) Support",
                "Interactive AI Chat Assistant Widget",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": 80,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Turn 4 Response: Contact Information
    if turn_count == 4:
        reply = (
            "Супер! Концепт, архитектура и функционал вашего проекта полностью"
            " согласованы. Пожалуйста, укажите ваше имя и удобный контакт для"
            " связи (Telegram @username, email или телефон) — я сразу сформирую"
            " итоговую спецификацию и отправлю ее вам и нашей инженерной"
            " команде."
            if is_ru
            else (
                "Superb! All technical architecture and functional requirements"
                " are fully defined. Please provide your name and preferred contact"
                " handle (Telegram, Email, or Phone) — I will immediately"
                " synthesize the complete technical specification and dispatch it"
                " to you and our engineering team."
            )
        )
        chips = (
            [
                "@username (Telegram)",
                "my.email@domain.com",
                "+7 (999) 000-00-00",
            ]
            if is_ru
            else [
                "@username (Telegram)",
                "founder@startup.io",
                "+1 (555) 019-2834",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": 95,
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Turn 5+ Response: Brief Completion & Synthesis
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

    # Email dispatch
    try:
        from email_service import send_lead_notification_email

        email_lead_data = {
            "lead_id": brief_id,
            "name": extracted.get("contact", "AI Brief Client"),
            "contact": extracted.get("contact", "Specified in Brief"),
            "message": f"⚡ СИНТЕЗИРОВАННЫЙ ТЕХНИЧЕСКИЙ БРИФ ПРОЕКТА:\n\n{brief_md}",
            "client_ip": client_ip,
            "created_at": created_at,
        }
        send_lead_notification_email(email_lead_data)
    except Exception as email_err:
        logger.warning("Could not dispatch brief email: %s", email_err)

    completion_msg = (
        f"🎯 Готово! Ваш технический бриф (ID: {brief_id}) успешно синтезирован"
        " и направлен архитектору OpenClaw. Нажмите кнопку «📋 Посмотреть бриф»"
        " ниже, чтобы ознакомиться с полной спецификацией. Мы свяжемся с вами"
        " в течение рабочего дня с готовой оценкой!"
        if is_ru
        else (
            f"🎯 Done! Your technical specification brief (ID: {brief_id}) has"
            " been synthesized and delivered to OpenClaw Lead Architect. Click"
            " '📋 View Brief' below to inspect the full specification. We will"
            " reach out shortly with the development timeline and pricing!"
        )
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
