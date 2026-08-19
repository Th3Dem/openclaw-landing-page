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
import sqlite3
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("openclaw.briefing")

BRIEFS_FILE = Path(__file__).resolve().parent / "briefs.json"
DB_FILE = Path(__file__).resolve().parent / "sessions.db"

# Core Dimension Keys required for production-ready brief
DIMENSIONS = ["goals", "structure", "style", "features", "contact"]


def init_sqlite_db() -> None:
    """Initialize SQLite database for persistent session memory."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    language TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    completeness INTEGER DEFAULT 10,
                    is_completed INTEGER DEFAULT 0,
                    brief_id TEXT,
                    brief_markdown TEXT
                )
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id)
                )
                """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)"
            )
            conn.commit()
    except Exception as err:
        logger.error("Failed to initialize SQLite DB: %s", err)


def persist_chat_message(
    session_id: str, role: str, content: str, lang: str = "ru"
) -> None:
    """Persist message in SQLite session memory."""
    try:
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions (session_id, language, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET updated_at = ?
                """,
                (session_id, lang, now_str, now_str, now_str),
            )
            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, now_str),
            )
            conn.commit()
    except Exception as err:
        logger.warning("Could not persist message to SQLite: %s", err)


def get_persisted_session_history(session_id: str) -> List[Dict[str, str]]:
    """Retrieve full chronological conversation history from SQLite."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content FROM chat_messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            )
            rows = cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in rows]
    except Exception as err:
        logger.warning("Could not retrieve session from SQLite: %s", err)
        return []


init_sqlite_db()

SYSTEM_PROMPT_RU = """Role & Persona:
Ты — Senior Web Solutions Consultant и Главный Технический Аналитик (Web Architect) студии OpenClaw AI Dev Studio. Твоя единственная цель — собрать исчерпывающие требования от потенциального клиента для составления полноценного Технического Задания (ТЗ) на разработку конверсионного сайта или веб-продукта.

Behavioral Rules & Guidelines:
1. Настойчивость и въедливость (Persistence & Scrutiny):
   - НЕ принимай размытые, неполные или бессмысленные ответы (например: "хочу просто красивый красный сайт для продаж", "сделайте красиво", "хз", "123").
   - Если ответ не содержит конкретики, вежливо укажи на это и задай фокусирующий уточняющий вопрос под другим углом, пока не получишь четкие детали.
2. Неограниченное глубокое интервью (Uncapped, Deep Interviewing):
   - Не спеши завершать диалог и не ограничивай количество вопросов. Задавай столько вопросов, сколько необходимо для формирования безупречного ТЗ.
   - Задавай не более 1-2 сфокусированных вопросов за раз (2-3 коротких предложения: экспертный комментарий + вопрос), чтобы пользователю было комфортно отвечать.
3. Контроль контекста и память (Context Control & Memory):
   - Держи в активной памяти всю историю текущей сессии (session_id).
   - Сопоставляй новые ответы с предыдущими утверждениями, подмечай противоречия или белые пятна.
4. 5 Обязательных Столпов Исследования (Mandatory Discovery Pillars):
   - Столп A: Бизнес-цели, сегмент ЦА и ключевые конкуренты (20%).
   - Столп B: Детальная структура страницы (Hero, ценности, социальные доказательства, динамические блоки, размещение CTA) (20%).
   - Столп C: Визуальная айдентика, цветовая гамма, типографика и сайты-референсы (20%).
   - Столп D: Технические требования (интеграции, платежные шлюзы, мультиязычность, CRM-синхронизация, Telegram) (20%).
   - Столп E: Сроки проекта, бюджетные ориентиры и контакты лица, принимающего решения (20%).
5. Триггер завершения (Completion Trigger):
   - ТОЛЬКО когда все 5 столпов детально раскрыты и проверены (completeness = 100%), составь структурированное "Итоговое Техническое Задание (ТЗ Summary)" и запроси у клиента финальное подтверждение.
6. ВАРИАНТЫ ОТВЕТА (suggestions):
   - Всегда генерируй 3-4 интерактивные кнопки (чипсы по 2-5 слов), идеально подходящие к текущему вопросу.
7. ФОРМАТ: Возвращай исключительно валидный JSON:
{
  "reply": "Текст короткого ответа (2-3 предложения + 1 вопрос)...",
  "suggestions": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"],
  "completeness": 35,
  "is_completed": false
}
"""

SYSTEM_PROMPT_EN = """Role & Persona:
You are a Senior Web Solutions Consultant and Technical Analyst at OpenClaw AI Dev Studio. Your sole purpose is to collect exhaustive specifications from a potential client to build a complete Technical Assignment (ТЗ) for their website/landing page.

Behavioral Rules & Guidelines:
1. Persistence & Scrutiny:
   - Do NOT accept vague, incomplete, or illogical responses (e.g., "I just want a nice red page to sell things", "asdf", "idk").
   - If an answer lacks substance, politely challenge it or ask targeted follow-up/clarifying questions from different angles until you get concrete details.
2. Uncapped, Deep Interviewing:
   - Do not rush the dialogue or cap the number of questions. Ask as many questions as necessary to form a bulletproof specification.
   - Ask 1 to 2 focused questions per turn (2-3 short sentences total) to avoid overwhelming the user, but keep probing continuously.
3. Context Control & Memory:
   - Maintain complete active memory of the current session history (session_id).
   - Cross-reference new answers with previous statements to spot contradictions or missing gaps.
4. Mandatory Discovery Pillars (Must Cover All 5):
   - Pillar A: Core Business Goals, Target Audience & Key Competitors (20%).
   - Pillar B: Detailed Page Structure (Hero, Features, Social Proof, Dynamic Components, CTA placement) (20%).
   - Pillar C: Visual Identity, Color Schemes, Typography Preferences, and Reference Sites (20%).
   - Pillar D: Technical Requirements (Integrations, Payment Gateways, Multilingual Support, CRM sync) (20%).
   - Pillar E: Project Timeline, Budget Range, and Decision-Maker Contact Info (20%).
5. Completion Trigger:
   - Only when all 5 pillars are thoroughly detailed and verified (completeness = 100%), compile a structured "Final Technical Assignment (ТЗ Summary)" and ask the client for final approval before handing off to the team.
6. CONTEXTUAL SUGGESTIONS:
   - Always generate 3-4 interactive quick-reply chips (2-5 words each) strictly relevant to the exact question asked.
7. FORMAT: Return strictly valid JSON:
{
  "reply": "Short answer + 1 focused question...",
  "suggestions": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "completeness": 35,
  "is_completed": false
}
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
    """Detect if user response is meaningless, too vague, or lacks context."""
    cleaned = text.strip().lower()
    if len(cleaned) < 3:
        return True
    if re.match(r"^([a-zа-я0-9\s])\1+$", cleaned):
        return True
    vague_phrases = {
        "asdasd",
        "qwerty",
        "test",
        "hz",
        "хз",
        "123",
        "idk",
        "asdf",
        "не знаю",
        "хз честно",
        "без разницы",
        "любой",
        "сделайте красиво",
        "просто сайт",
        "мне просто сайт",
        "сделай сам",
        "сделайте сами",
        "сам делай",
        "сам сделай",
        "красиво",
        "хз вообще",
        "без понятия",
        "ладно",
        "ок",
        "норм",
        "no idea",
        "whatever",
        "anything",
        "just a site",
        "make it cool",
        "do it yourself",
        "idk really",
        "dont know",
        "don't know",
    }
    return cleaned in vague_phrases


def is_valid_contact(text: str) -> bool:
    """Validate that text contains a genuine contact identifier (email, phone, telegram)."""
    t = text.strip()
    if len(t) < 3:
        return False
    if "@" in t:
        return True
    if "telegram" in t.lower() or "t.me" in t.lower():
        return True
    digits = re.sub(r"\D", "", t)
    if len(digits) >= 7:
        return True
    if any(k in t.lower() for k in [".com", ".ru", ".io", ".org", ".net", ".dev"]):
        return True
    return False


def is_meaningful_content(text: str) -> bool:
    """Check if the text has actual substantive content beyond gibberish."""
    if is_vague_or_gibberish(text):
        return False
    cleaned = text.strip().lower()
    if re.match(r"^[бвгджзйклмнпрстфхцчшщьъ\s]+$", cleaned) and len(cleaned) <= 6:
        return False
    if re.match(r"^[bcdfghjklmnpqrstvwxyz\s]+$", cleaned) and len(cleaned) <= 6:
        return False
    return len(cleaned) >= 3


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


def parse_llm_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON or extract JSON block from LLM output."""
    clean = raw_text.strip()
    if "```json" in clean:
        clean = clean.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in clean:
        clean = clean.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        data = json.loads(clean)
        if isinstance(data, dict) and "reply" in data:
            return data
    except Exception:
        pass

    m = re.search(r"\{[\s\S]*\}", clean)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict) and "reply" in data:
                return data
        except Exception:
            pass

    return None


def call_llm_if_available(
    system_prompt: str, history: List[Dict[str, str]], user_message: str
) -> Optional[Dict[str, Any]]:
    """Invoke Google Gemini, OpenAI, OpenRouter, or Groq API if configured in environment."""
    load_env()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        raw_turns: List[Dict[str, str]] = []
        for msg in history:
            r = "user" if msg.get("role") == "user" else "model"
            t = msg.get("content", "").strip()
            if t:
                raw_turns.append({"role": r, "text": t})
        if user_message and user_message.strip():
            raw_turns.append({"role": "user", "text": user_message.strip()})

        # Gemini requires the conversation to start with a user turn
        while raw_turns and raw_turns[0]["role"] != "user":
            raw_turns.pop(0)

        if not raw_turns:
            raw_turns.append(
                {"role": "user", "text": user_message.strip() or "Здравствуйте"}
            )

        # Merge consecutive identical roles to guarantee strict alternating user/model
        merged_turns: List[Dict[str, str]] = []
        for turn in raw_turns:
            if merged_turns and merged_turns[-1]["role"] == turn["role"]:
                merged_turns[-1]["text"] += "\n" + turn["text"]
            else:
                merged_turns.append({"role": turn["role"], "text": turn["text"]})

        contents = [
            {"role": turn["role"], "parts": [{"text": turn["text"]}]}
            for turn in merged_turns
        ]

        first_user_text = (
            merged_turns[0]["text"]
            if merged_turns
            else (user_message.strip() or "Здравствуйте")
        )
        configs = [
            # Config 1: System instruction + JSON response MIME type
            {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": contents,
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.7,
                    "maxOutputTokens": 800,
                },
            },
            # Config 2: System prompt embedded in first user turn if system_instruction is rejected
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": f"{system_prompt}\n\n[USER INSTRUCTION]:\n{first_user_text}"
                            }
                        ],
                    }
                ]
                + contents[1:],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 800,
                },
            },
        ]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={gemini_key}"
        import time

        for attempt, payload in enumerate(configs):
            for retry in range(2):
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        if "candidates" in data and len(data["candidates"]) > 0:
                            candidate = data["candidates"][0]
                            parts = candidate.get("content", {}).get("parts", [])
                            if parts:
                                answer = str(parts[0].get("text", "")).strip()
                                parsed = parse_llm_json_response(answer)
                                if parsed:
                                    logger.info(
                                        "Successfully generated structured response with Gemini LLM"
                                    )
                                    return parsed
                                return {"reply": answer, "suggestions": []}
                except urllib.error.HTTPError as http_err:
                    logger.warning(
                        "Gemini HTTP attempt %d retry %d returned: %s",
                        attempt + 1,
                        retry + 1,
                        http_err,
                    )
                    if http_err.code in (503, 500, 429):
                        time.sleep(1.0)
                    else:
                        break
                except Exception as gem_err:
                    logger.warning(
                        "Gemini call attempt %d retry %d failed: %s",
                        attempt + 1,
                        retry + 1,
                        gem_err,
                    )
                    time.sleep(0.8)

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
        "max_tokens": 600,
    }

    try:
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
                parsed = parse_llm_json_response(answer)
                if parsed:
                    return parsed
                return {"reply": answer, "suggestions": []}
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

    for idx, text in enumerate(all_user_texts):
        t_low = text.lower()
        if is_meaningful_content(text):
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
                    "доставк",
                    "торты",
                    "бургер",
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
                    "glass",
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
                    "фильтр",
                ]
            ):
                extracted["features"] = text

        if is_valid_contact(text):
            extracted["contact"] = text

    # Positional mapping fallback ONLY if entries are meaningful
    valid_texts = [t for t in all_user_texts if is_meaningful_content(t)]
    for i, dim in enumerate(DIMENSIONS):
        if dim not in extracted and i < len(valid_texts):
            candidate = valid_texts[i]
            if dim == "contact":
                if is_valid_contact(candidate):
                    extracted[dim] = candidate
            else:
                extracted[dim] = candidate

    return extracted


def calculate_completeness(extracted: Dict[str, str]) -> Tuple[int, List[str]]:
    """Calculate brief completeness percentage (0 to 100) and identify missing dimensions."""
    weights = {
        "goals": 20,
        "structure": 20,
        "style": 15,
        "features": 20,
        "contact": 25,
    }
    score = 0
    missing = []
    for dim, weight in weights.items():
        val = extracted.get(dim, "")
        if dim == "contact":
            if is_valid_contact(val):
                score += weight
            else:
                missing.append(dim)
        else:
            if is_meaningful_content(val):
                score += weight
            else:
                missing.append(dim)
    return min(100, score), missing


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
            f"Ответ «{last_user_msg}» звучит слишком абстрактно и не дает конкретики. "
            "Чтобы сайт приносил целевые заявки и окупал вложения, давайте уточним: "
            "кто ваши клиенты и какую главную задачу они решают на сайте?"
            if is_ru
            else (
                f"The response '{last_user_msg}' is too vague. To ensure high "
                "conversion and solid architecture, let's specify: who are your "
                "target users and what core problem does the website solve for them?"
            )
        )
        suggestions = (
            [
                "B2B клиенты и оптовые заказчики",
                "Розничные покупатели (B2C)",
                "Стартапы и технологический бизнес",
                "Премиальный / VIP сегмент",
            ]
            if is_ru
            else [
                "B2B Enterprise & Mid-Market",
                "Direct-to-Consumer (B2C)",
                "Tech Startups & Founders",
                "High-Ticket Premium Clients",
            ]
        )
        base_score, _ = calculate_completeness(extracted)
        return {
            "session_id": session_id,
            "message": clarification,
            "suggestions": suggestions,
            "completeness": max(10, base_score),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # 3. Assess verified dimensions and completeness score
    verified_score, missing_dims = calculate_completeness(extracted)
    contact_val = extracted.get("contact", "")
    has_valid_contact_val = is_valid_contact(contact_val)

    # 4. Try LLM Call first if key exists
    system_prompt = SYSTEM_PROMPT_RU if is_ru else SYSTEM_PROMPT_EN
    llm_dict = call_llm_if_available(system_prompt, history, last_user_msg)
    if llm_dict:
        reply_text = llm_dict.get("reply", "")
        llm_suggestions = llm_dict.get("suggestions", [])
        llm_completeness = int(llm_dict.get("completeness", max(10, verified_score)))

        # STRICT COMPLETION CONDITION: Only finish if all dimensions are substantive and contact is valid
        is_truly_completed = (
            verified_score >= 95
            and has_valid_contact_val
            and not is_vague_or_gibberish(last_user_msg)
            and bool(llm_dict.get("is_completed", False))
        )

        # If LLM prematurely marked completion without valid contact or full scope, override it!
        if llm_dict.get("is_completed", False) and not is_truly_completed:
            llm_completeness = min(90, max(verified_score, llm_completeness))
            if not has_valid_contact_val:
                extra_q = (
                    "\n\nПожалуйста, укажите ваши контактные данные (Telegram @username, email или телефон), чтобы мы могли направить вам проектную смету и ТЗ."
                    if is_ru
                    else "\n\nPlease provide your contact details (Telegram @handle, Email, or Phone) so we can dispatch the specification."
                )
                reply_text += extra_q
                llm_suggestions = (
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

        brief_id = f"brief-{uuid.uuid4().hex[:8]}" if is_truly_completed else None
        brief_md = (
            synthesize_brief_markdown(extracted, lang) if is_truly_completed else None
        )

        if is_truly_completed and brief_id:
            record = {
                "brief_id": brief_id,
                "session_id": session_id,
                "client_ip": client_ip,
                "language": lang,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "extracted_dimensions": extracted,
                "brief_markdown": brief_md,
            }
            save_brief_record(record)
            try:
                from email_service import send_lead_notification_email

                email_lead_data = {
                    "lead_id": brief_id,
                    "name": extracted.get("contact", "AI Brief Client"),
                    "contact": extracted.get("contact", "Specified in Brief"),
                    "message": f"⚡ СИНТЕЗИРОВАННЫЙ ТЕХНИЧЕСКИЙ БРИФ ПРОЕКТА:\n\n{brief_md}",
                    "client_ip": client_ip,
                    "created_at": record["created_at"],
                }
                send_lead_notification_email(email_lead_data)
            except Exception as email_err:
                logger.warning("Could not dispatch brief email: %s", email_err)

        if not llm_suggestions and not is_truly_completed:
            niche_name, niche_info = detect_niche(all_text, is_ru)
            llm_suggestions = (
                niche_info["chips"]
                if niche_info
                else (
                    [
                        "Hero + Кейсы + Тарифы + Форма",
                        "Интерактивный калькулятор стоимости",
                        "Темный минимализм со свечением (Helias)",
                        "Синхронизация с Telegram и CRM",
                    ]
                    if is_ru
                    else [
                        "Hero + Proof + Pricing + Form",
                        "Interactive Pricing Estimator",
                        "Obsidian Dark Minimalist (Helias)",
                        "Telegram Alerts & CRM Sync",
                    ]
                )
            )

        final_score = (
            100
            if is_truly_completed
            else max(10, min(95, max(verified_score, llm_completeness)))
        )
        return {
            "session_id": session_id,
            "message": reply_text,
            "suggestions": [] if is_truly_completed else llm_suggestions,
            "completeness": final_score,
            "is_completed": is_truly_completed,
            "brief_id": brief_id,
            "extracted_dimensions": extracted,
            "brief_summary": brief_md,
        }

    # 5. Deep Contextual Reasoning & Free-Form Organic Conversation Engine
    msg_low = last_user_msg.lower()

    # Check if user explicitly requests completion
    user_requests_completion = any(
        k in msg_low
        for k in [
            "зафиксировать",
            "оформляй",
            "формируй тз",
            "согласен",
            "отправляй",
            "готово",
            "готов",
            "давай тз",
            "сформируй бриф",
            "finalize",
            "complete brief",
            "submit brief",
        ]
    )

    can_complete = (
        verified_score >= 95
        and has_valid_contact_val
        and not is_vague_or_gibberish(last_user_msg)
    ) or (
        user_requests_completion
        and verified_score >= 80
        and has_valid_contact_val
        and not is_vague_or_gibberish(last_user_msg)
    )

    if can_complete:
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
            f"🎯 Готово! Ваше Техническое Задание (ID: {brief_id}) успешно сформировано"
            " и направлено архитектору OpenClaw. Нажмите кнопку «📋 Посмотреть ТЗ»"
            " или «💾 Скачать ТЗ», чтобы ознакомиться со спецификацией. Мы свяжемся с вами"
            " для презентации проекта и сметы!"
            if is_ru
            else (
                f"🎯 Done! Your Technical Specification (ID: {brief_id}) has"
                " been synthesized and delivered to OpenClaw Lead Architect. Click"
                " '📋 View ТЗ' or '💾 Download ТЗ' below to inspect the full specification."
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

    # Intent 1: Pricing, Budget, Timeline & Speed
    if any(
        k in msg_low
        for k in [
            "цен",
            "стоим",
            "сколько",
            "срок",
            "бюджет",
            "быстро",
            "скорост",
            "price",
            "cost",
            "timeline",
            "budget",
            "how much",
            "how long",
            "deadline",
        ]
    ):
        reply = (
            "Благодаря нашей мультиагентной архитектуре разработка идет со скоростью x10:"
            " рабочий прототип и MVP мы собираем за 3–5 рабочих дней. Стоимость зависит от объема"
            " кастомных модулей (калькуляторы, платежные шлюзы, интеграции с CRM/Telegram)."
            " Есть ли у вас конкретные дедлайны по запуску или пожелания по бюджетным ориентирам?"
            if is_ru
            else (
                "With our autonomous multi-agent engineering, we deliver with 10x velocity:"
                " working MVP is ready in 3-5 business days. Pricing depends on bespoke modules"
                " (dynamic calculators, checkout gateways, CRM/Telegram sync)."
                " Do you have a strict launch deadline or specific budget range in mind?"
            )
        )
        chips = (
            [
                "Запуск за 1-2 недели",
                "Нужен расчет точной сметы",
                "Хочу минимальный MVP",
                "Обсудить стек и архитектуру",
            ]
            if is_ru
            else [
                "Launch within 1-2 weeks",
                "Need exact budget quote",
                "Lean MVP launch first",
                "Discuss tech stack & architecture",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": min(95, max(30, verified_score)),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Intent 2: Visual Style, Design Aesthetics, References & Colors
    if any(
        k in msg_low
        for k in [
            "дизайн",
            "стил",
            "цвет",
            "темн",
            "светл",
            "палитр",
            "шрифт",
            "референс",
            "красив",
            "aesthetic",
            "design",
            "dark",
            "light",
            "font",
            "color",
        ]
    ):
        reply = (
            "По дизайну сейчас отлично работают два направления: глубокий обсидиановый"
            " минимализм со светящимися неоновыми акцентами (стиль Helias — идеален для IT и премиум)"
            " или чистая светлая премиум-эстетика в духе Apple. Какое визуальное ощущение"
            " ближе вашему бренду, и есть ли сайты-референсы, которые вам нравятся?"
            if is_ru
            else (
                "Design-wise, two primary trends drive peak engagement: deep obsidian dark"
                " minimalism with glowing neon accents (Helias aesthetic — ideal for tech & luxury)"
                " versus crisp spacious light minimalism (Apple aesthetic)."
                " Which visual atmosphere better resonates with your brand identity?"
            )
        )
        chips = (
            [
                "Темный неоновый минимализм (Helias)",
                "Светлый чистый премиум (Apple)",
                "Стеклянный Glassmorphism с анимацией",
                "Строгий корпоративный стиль",
            ]
            if is_ru
            else [
                "Obsidian Dark Neon (Helias)",
                "Clean Light Minimalist (Apple)",
                "Cyber Glassmorphism FX",
                "High-Trust Corporate",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": min(95, max(50, verified_score)),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Intent 3: Features, Quizzes, Calculators, Payments & Integrations
    if any(
        k in msg_low
        for k in [
            "квиз",
            "калькулятор",
            "оплат",
            "интеграц",
            "telegram",
            "crm",
            "бот",
            "уведомлен",
            "amo",
            "bitrix",
            "feature",
            "quiz",
            "payment",
        ]
    ):
        reply = (
            "Интерактивный квиз или калькулятор стоимости вовлекает посетителя и дает"
            " рост конверсии до +35-40%! Данные моментально направляются в Telegram вашей команды"
            " и в CRM (AmoCRM, Bitrix24), а оплата подключается через СБП/эквайринг."
            " Какие из этих каналов и сервисов для вас в приоритете?"
            if is_ru
            else (
                "An interactive quiz or dynamic pricing estimator increases conversions by +35-40%!"
                " Qualified leads are dispatched instantly to your team Telegram and CRM"
                " (AmoCRM, Bitrix24), with direct card/Stripe checkout integration."
                " Which integrations are top priority for your workflow?"
            )
        )
        chips = (
            [
                "Квиз-калькулятор + Telegram-оповещения",
                "Онлайн-оплата (карты / СБП)",
                "Интеграция с CRM (AmoCRM/Bitrix24)",
                "Мультиязычность (RU / ENG)",
            ]
            if is_ru
            else [
                "Quiz Estimator + Instant Telegram",
                "Stripe / Card Online Checkout",
                "CRM Webhook Synchronization",
                "Multilingual Support (EN / RU)",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": min(95, max(65, verified_score)),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # Intent 4: Page Structure, Sections, Customer Journey
    if any(
        k in msg_low
        for k in [
            "структур",
            "раздел",
            "блок",
            "hero",
            "секц",
            "лендинг",
            "сайт",
            "страниц",
            "меню",
            "каталог",
            "тариф",
            "отзыв",
            "section",
            "page",
            "catalog",
        ]
    ):
        reply = (
            "Для конверсионной структуры страницы идеально подходит связка: сильный Hero с УТП"
            " и оффером -> блок ключевых ценностей и боли клиента -> интерактивный"
            " блок выбора/квиз -> блок кейсов и социального доверия -> прозрачные тарифы"
            " -> финальный CTA. Какие блоки для вас ключевые?"
            if is_ru
            else (
                "For high conversion velocity, the optimal page flow is: High-impact Hero with core USP"
                " -> Value Proposition & pain point resolution -> Interactive Quiz/Configurator"
                " -> Case studies & Proof Matrix -> Transparent pricing -> Final CTA."
                " Which sections are essential for your launch?"
            )
        )
        chips = (
            [
                "Hero + Кейсы + Тарифы + Заявка",
                "Интерактивный квиз / конфигуратор",
                "Демонстрация продукта + FAQ",
                "Лид-магнит с мгновенным доступом",
            ]
            if is_ru
            else [
                "Hero + Proof + Pricing + Form",
                "Interactive Quiz / Configurator",
                "Product Demo + FAQ Matrix",
                "Lead Magnet Instant Access",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": min(95, max(40, verified_score)),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # If contact is still missing, we gently probe for contact details while summarizing
    if not has_valid_contact_val:
        reply = (
            "Отлично, картина по проекту становится четкой и целостной! Подскажите ваше имя"
            " и контактные данные (Telegram @username, email или телефон) — чтобы мы могли"
            " подготовить детальный расчет сметы и архитектурное ТЗ."
            if is_ru
            else (
                "Great, project vision is shaping up clearly! Please provide your name"
                " and contact handle (Telegram @username, Email, or Phone) so we can"
                " synthesize the technical specification and project estimate."
            )
        )
        chips = (
            [
                "@username (Telegram)",
                "my.email@domain.com",
                "+7 (999) 000-00-00",
                "Хочу обсудить еще детали",
            ]
            if is_ru
            else [
                "@username (Telegram)",
                "founder@startup.io",
                "+1 (555) 019-2834",
                "Want to discuss more details",
            ]
        )
        return {
            "session_id": session_id,
            "message": reply,
            "suggestions": chips,
            "completeness": min(90, max(75, verified_score)),
            "is_completed": False,
            "extracted_dimensions": extracted,
            "brief_summary": None,
        }

    # If all dimensions & contact are available, provide conversational checkpoint:
    reply = (
        "Мы собрали ключевые требования: цели, структуру, дизайн, функционал и контакты."
        " Вы хотите зафиксировать итоговое ТЗ и получить расчет сметы от инженера, или"
        " обсудим дополнительные идеи и пожелания?"
        if is_ru
        else (
            "We have gathered all core specifications: goals, architecture, design, features, and contacts."
            " Would you like to finalize the Technical Specification and get the engineering estimate,"
            " or explore additional features?"
        )
    )
    chips = (
        [
            "📋 Зафиксировать ТЗ и получить смету",
            "Обсудить еще функционал",
            "Уточнить стек технологий",
            "Посмотреть примеры",
        ]
        if is_ru
        else [
            "📋 Finalize ТЗ & Get Estimate",
            "Discuss more features",
            "Check engineering tech stack",
            "View reference examples",
        ]
    )
    return {
        "session_id": session_id,
        "message": reply,
        "suggestions": chips,
        "completeness": min(95, max(85, verified_score)),
        "is_completed": False,
        "extracted_dimensions": extracted,
        "brief_summary": None,
    }


def synthesize_brief_markdown(extracted: Dict[str, str], lang: str) -> str:
    """Synthesize a high-fidelity Markdown technical specification."""
    is_ru = lang.lower().startswith("ru")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if is_ru:
        return f"""# 📋 ИТОГОВОЕ ТЕХНИЧЕСКОЕ ЗАДАНИЕ (ТЗ) — OPENCLAW AI DEV STUDIO
**ID Спецификации:** `SPEC-{uuid.uuid4().hex[:6].upper()}`
**Дата формирования:** {now_str}
**Статус:** Согласовано с архитектором (100% готовность)

---
### 1. 🎯 Столп A: Бизнес-цели, Целевая Аудитория и Конкуренты
{extracted.get('goals', 'Не указано')}

### 2. 📐 Столп B: Детальная Архитектура страницы и Разделы
{extracted.get('structure', 'Hero с УТП, Интерактивный калькулятор/квиз, Кейсы, Тарифы, Социальные доказательства, CTA-форма')}

### 3. 🎨 Столп C: Визуальная Айдентика, Стилистика и Референсы
{extracted.get('style', 'Obsidian Dark Minimalist (Helias Aesthetic) со светящимися неоновыми акцентами')}

### 4. 🧩 Столп D: Технические Требования, Интеграции и CRM
{extracted.get('features', 'Асинхронная отправка лидов, Telegram-бот команды, онлайн-оплата, вебхук CRM')}

### 5. 👤 Столп E: Сроки, Бюджетные ориентиры и Контакты ЛПР
{extracted.get('contact', 'Не указано')}

---
### 🚀 Рекомендованный инженерный стек OpenClaw:
- **Backend Core:** FastAPI (Python 3.12) / Go 1.22 Microservices
- **Frontend Architecture:** Semantic HTML5, CSS3 Custom Tokens, Vanilla JS ES6+ (No heavy JS bundle overhead)
- **Security & Dispatch:** Docker isolation, SSL TLS 1.3, Background asynchronous SMTP worker
- **Оценка срока реализации:** 3-5 рабочих дней при скорости разработки x10
"""
    else:
        return f"""# 📋 FINAL TECHNICAL SPECIFICATION (ТЗ) — OPENCLAW AI DEV STUDIO
**Specification ID:** `SPEC-{uuid.uuid4().hex[:6].upper()}`
**Generated At:** {now_str}
**Status:** Approved by Lead Architect (100% Complete)

---
### 1. 🎯 Pillar A: Core Business Goals, Target Audience & Competitors
{extracted.get('goals', 'Not specified')}

### 2. 📐 Pillar B: Detailed Page Structure & Section Hierarchy
{extracted.get('structure', 'Hero CTA, Interactive Calculator/Quiz, Proof Matrix, Pricing Tiers, Lead Intake Modal')}

### 3. 🎨 Pillar C: Visual Identity, Aesthetics & Reference Sites
{extracted.get('style', 'Obsidian Dark Minimalist (Helias-inspired typography & neon glow accents)')}

### 4. 🧩 Pillar D: Technical Requirements, Integrations & CRM
{extracted.get('features', 'Asynchronous lead intake, Telegram team bot, online payment gateways, CRM sync')}

### 5. 👤 Pillar E: Timeline, Budget Range & Decision-Maker Contacts
{extracted.get('contact', 'Not specified')}

---
### 🚀 Recommended OpenClaw Engineering Stack:
- **Backend Core:** FastAPI (Python 3.12) / Go 1.22 Microservices
- **Frontend Architecture:** Semantic HTML5, CSS3 Custom Properties, Vanilla ES6+
- **Security & Dispatch:** Docker containerization, TLS 1.3 encryption, Async background SMTP worker
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
    """Entry point for processing chat briefing turns with SQLite session persistence."""
    if message and message.strip():
        persist_chat_message(session_id, "user", message.strip(), lang)

    res = generate_autonomous_response(
        session_id=session_id,
        message=message,
        history=history,
        lang=lang,
        client_ip=client_ip,
    )

    if res.get("message"):
        persist_chat_message(session_id, "assistant", res["message"], lang)

    return res
