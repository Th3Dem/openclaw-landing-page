from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import (
    LEADS_FILE,
    LEADS_STORE,
    LOCALIZATION_DATA,
    LeadRequest,
    app,
    get_landing_context,
    save_lead,
)


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI TestClient instance."""
    return TestClient(app)


class TestLandingPageApp:
    """Test suite for OpenClaw AI Dev Team Landing Page FastAPI application."""

    def test_localization_data_integrity(self) -> None:
        """Verify supported languages and essential keys in LOCALIZATION_DATA."""
        assert "en" in LOCALIZATION_DATA
        assert "ru" in LOCALIZATION_DATA
        assert LOCALIZATION_DATA["en"]["lang_code"] == "en"
        assert LOCALIZATION_DATA["ru"]["lang_code"] == "ru"

        # Check CTA buttons
        assert "cta_button" in LOCALIZATION_DATA["en"]["hero"]
        assert "cta_button" in LOCALIZATION_DATA["ru"]["hero"]
        assert LOCALIZATION_DATA["en"]["hero"]["cta_button"] == "Apply for AI Dev Team"
        assert LOCALIZATION_DATA["ru"]["hero"]["cta_button"] == "ПОДАТЬ ЗАЯВКУ"

        # Check modal data integrity
        for lang_code in ["en", "ru"]:
            modal = LOCALIZATION_DATA[lang_code]["modal"]
            assert "badge" in modal
            assert "title" in modal
            assert "subtitle" in modal
            assert "name_label" in modal
            assert "contact_label" in modal
            assert "message_label" in modal
            assert "submit_btn" in modal
            assert "submitting_btn" in modal
            assert "success_title" in modal
            assert "success_msg" in modal
            assert "success_close_btn" in modal

    def test_get_landing_context_default_en(self) -> None:
        """Verify the data structure returned by get_landing_context for English default."""
        context = get_landing_context("en")
        assert isinstance(context, dict)
        assert context["lang"] == "en"
        assert context["lang_code"] == "en"
        assert context["app_name"] == "OpenClaw AI Dev Team"
        assert "version" in context
        assert "metrics" in context
        assert "team_roster" in context
        assert "capabilities" in context
        assert "workflow" in context
        assert "roster" in context
        assert "trust" in context
        assert "modal" in context
        assert context["modal"]["title"] == "Apply for AI Dev Team"

        # Check metrics
        metrics = context["metrics"]
        assert metrics["velocity"] == "10x"
        assert metrics["qa_pass_rate"] == "100%"
        assert metrics["bad_commits"] == "0"
        assert metrics["uptime_readiness"] == "24/7"

        # Check all 5 bots are in team roster
        bot_ids = {agent["id"] for agent in context["team_roster"]}
        expected_bots = {"pm_bot", "dev_bot", "py_bot", "qa_bot", "git_bot"}
        assert expected_bots.issubset(bot_ids)

        # Check capabilities count
        assert len(context["capabilities"]) >= 6

    def test_get_landing_context_russian(self) -> None:
        """Verify the data structure returned by get_landing_context for Russian."""
        context = get_landing_context("ru")
        assert isinstance(context, dict)
        assert context["lang"] == "ru"
        assert context["lang_code"] == "ru"
        assert "Инженерная команда OpenClaw AI" in context["html_title"]
        assert context["nav"]["overview"] == "Обзор"
        assert context["hero"]["metrics"]["velocity_label"] == "Скорость поставки"
        assert context["workflow"]["title"] == "Автономный процесс поставки"
        assert context["modal"]["title"] == "Подать заявку на разработку"

        # Verify all 5 bots in Russian roster
        bot_ids = {agent["id"] for agent in context["team_roster"]}
        expected_bots = {"pm_bot", "dev_bot", "py_bot", "qa_bot", "git_bot"}
        assert expected_bots.issubset(bot_ids)

        # Verify 6 capabilities in Russian
        assert len(context["capabilities"]) == 6
        cap_titles = [item["title"] for item in context["capabilities"]]
        assert "Высоконагруженные Go-бэкенды" in cap_titles
        assert "Асинхронные микросервисы на FastAPI" in cap_titles

        # Verify trust matrix
        assert len(context["trust"]["rows"]) == 6
        assert context["trust"]["col_adv"] == "Преимущество"

    def test_get_landing_context_invalid_lang_fallback(self) -> None:
        """Verify invalid language code falls back safely to English."""
        context = get_landing_context("fr")
        assert context["lang"] == "en"
        assert context["lang_code"] == "en"
        assert context["modal"]["title"] == "Apply for AI Dev Team"

    def test_index_page_english_default(self, client: TestClient) -> None:
        """Verify the root index page returns 200 OK and valid English HTML content with CTA and modal."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        html = response.text

        # Verify HTML document structure & lang
        assert "<!DOCTYPE html>" in html
        assert '<html lang="en">' in html
        assert "OpenClaw AI Engineering Team" in html

        # Verify Section 1: Hero Section (EN) & CTA button
        assert 'id="hero"' in html
        assert "Human Ingenuity. Autonomous Precision." in html
        assert "Studio-Grade Output at 10x Velocity." in html
        assert 'id="openLeadModalBtn"' in html
        assert "btn-primary-green" in html
        assert "btn-pulse" in html
        assert "Apply for AI Dev Team" in html

        # Verify Modal Dialog (EN)
        assert 'id="leadModal"' in html
        assert 'id="leadForm"' in html
        assert 'id="modalTitle"' in html
        assert 'id="modalCloseBtn"' in html
        assert 'id="leadName"' in html
        assert 'id="leadContact"' in html
        assert 'id="leadMessage"' in html
        assert 'id="leadSubmitBtn"' in html
        assert 'id="leadSuccessContainer"' in html
        assert "Leave your contacts" in html
        assert "architectural proposal" in html

        # Verify Section 2: Workflow (EN)
        assert 'id="workflow"' in html
        assert "The Autonomous Delivery Flow" in html
        assert "Least Privilege Security Architecture" in html
        assert "TASK-XX.md" in html

        # Verify Section 3: Team Roster (EN)
        assert 'id="roster"' in html
        assert "Autonomous Team Roster" in html
        assert "Paula" in html
        assert "dev_bot" in html
        assert "py_bot" in html
        assert "qa_bot" in html
        assert "git_bot" in html

        # Verify Section 4: Capabilities (EN)
        assert 'id="capabilities"' in html
        assert "High-Load Go Backends" in html
        assert "FastAPI Async Microservices" in html

        # Verify Section 5: Analytics & Trust Matrix (EN)
        assert 'id="trust"' in html
        assert "AI Team vs Traditional Development" in html
        assert "10x Faster" in html
        assert "Zero-Trust" in html

        # Verify Language switcher presence
        assert 'id="langSwitcher"' in html
        assert 'href="/?lang=en"' in html
        assert 'href="/?lang=ru"' in html

    def test_index_page_english_explicit(self, client: TestClient) -> None:
        """Verify the index page with ?lang=en returns English content."""
        response = client.get("/?lang=en")
        assert response.status_code == 200
        assert '<html lang="en">' in response.text
        assert "Autonomous Multi-Agent Software Engineering" in response.text
        assert "The Autonomous Delivery Flow" in response.text

    def test_index_page_russian(self, client: TestClient) -> None:
        """Verify the index page with ?lang=ru returns valid Russian HTML content across all 5 sections and modal."""
        response = client.get("/?lang=ru")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        html = response.text

        # Verify HTML document structure & lang
        assert "<!DOCTYPE html>" in html
        assert '<html lang="ru">' in html
        assert "Инженерная команда OpenClaw AI" in html

        # Verify Section 1: Hero Section (RU) & CTA Button
        assert 'id="hero"' in html
        assert "ПАРАДИГМА НОВОГО ПОКОЛЕНИЯ" in html
        assert "Человеческий замысел. Автономная точность." in html
        assert "Результат студийного уровня с 10-кратной скоростью." in html
        assert 'id="openLeadModalBtn"' in html
        assert "ПОДАТЬ ЗАЯВКУ" in html

        # Verify Modal Dialog (RU)
        assert 'id="leadModal"' in html
        assert "Подать заявку на разработку" in html
        assert "Оставьте контакты, и мы подготовим архитектурное решение" in html
        assert "Ваше имя" in html
        assert "Контактные данные" in html
        assert "Отправить заявку" in html
        assert "Спасибо! Ваша заявка принята." in html

        # Verify Section 2: Workflow (RU)
        assert 'id="workflow"' in html
        assert "ДЕТЕРМИНИРОВАННЫЙ ПАЙПЛАЙН" in html
        assert "Автономный процесс поставки" in html
        assert "Архитектура безопасности на базе наименьших привилегий" in html

        # Verify Section 3: Team Roster (RU)
        assert 'id="roster"' in html
        assert "Состав автономной команды" in html
        assert "Ведущий архитектор и Product Owner" in html

        # Verify Section 4: Capabilities (RU)
        assert 'id="capabilities"' in html
        assert "Возможности и инженерный стек" in html
        assert "Высоконагруженные Go-бэкенды" in html

        # Verify Section 5: Analytics & Trust Matrix (RU)
        assert 'id="trust"' in html
        assert "ИИ-команда против традиционной разработки" in html
        assert "0 Дефектов" in html

        # Verify cookie is set
        assert "openclaw_lang=ru" in response.headers.get("set-cookie", "")

    def test_index_page_cookie_persistence(self, client: TestClient) -> None:
        """Verify that openclaw_lang cookie dictates language when query param is absent."""
        response = client.get("/", cookies={"openclaw_lang": "ru"})
        assert response.status_code == 200
        assert '<html lang="ru">' in response.text
        assert "Автономный процесс поставки" in response.text

    def test_index_page_invalid_param_fallback(self, client: TestClient) -> None:
        """Verify that unsupported lang query param safely falls back to English."""
        response = client.get("/?lang=invalid_lang_code")
        assert response.status_code == 200
        assert '<html lang="en">' in response.text
        assert "Human Ingenuity. Autonomous Precision." in response.text

    def test_health_check_endpoint(self, client: TestClient) -> None:
        """Verify the healthcheck endpoint returns 200 and expected telemetry JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "openclaw-ai-landing-page"
        assert data["version"] == "1.0.0"
        assert data["agents_active"] == 5
        assert data["security_model"] == "least_privilege"
        assert "supported_languages" in data
        assert "en" in data["supported_languages"]
        assert "ru" in data["supported_languages"]

    def test_static_css_served(self, client: TestClient) -> None:
        """Verify that the CSS static asset is served properly."""
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        assert "--bg-primary" in response.text
        assert ".lang-switcher" in response.text
        assert ".btn-primary-green" in response.text
        assert ".modal" in response.text
        assert ".success-checkmark" in response.text

    def test_static_js_served(self, client: TestClient) -> None:
        """Verify that the JavaScript static asset is served properly."""
        response = client.get("/static/js/main.js")
        assert response.status_code == 200
        assert (
            "text/javascript" in response.headers["content-type"]
            or "application/javascript" in response.headers["content-type"]
        )
        assert "initLanguageSwitcher" in response.text
        assert "initLeadModal" in response.text

    def test_custom_404_handler(self, client: TestClient) -> None:
        """Verify the custom 404 handler returns a styled not-found page with 404 status."""
        response = client.get("/non-existent-route-endpoint")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "404 ERROR" in response.text
        assert "Endpoint Not Found" in response.text
        assert "/non-existent-route-endpoint" in response.text

    def test_custom_404_handler_xss_protection(self, client: TestClient) -> None:
        """Verify that malicious XSS payload in 404 URL is safely escaped."""
        response = client.get("/<script>alert(1)</script>")
        assert response.status_code == 404
        assert "<script>" not in response.text
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text


class TestLeadIntakeAPI:
    """Test suite for Lead Intake model, persistence, and /api/leads endpoint."""

    def test_lead_request_model_validation(self) -> None:
        """Verify LeadRequest validation behavior with valid and edge-case inputs."""
        # Valid full payload
        lead = LeadRequest(
            name="  Dmitry Petrov  ",
            contact="  @dmitry_p  ",
            message="  Need FastAPI + Golang high-load backend  ",
        )
        assert lead.name == "Dmitry Petrov"
        assert lead.contact == "@dmitry_p"
        assert lead.message == "Need FastAPI + Golang high-load backend"

        # Valid with empty optional message
        lead_no_msg = LeadRequest(
            name="Elena", contact="elena@example.com", message="   "
        )
        assert lead_no_msg.name == "Elena"
        assert lead_no_msg.contact == "elena@example.com"
        assert lead_no_msg.message is None

        # Valid with explicit None message
        lead_none_msg = LeadRequest(
            name="Elena", contact="elena@example.com", message=None
        )
        assert lead_none_msg.message is None

        # Validation error: name too short or whitespace only
        with pytest.raises(ValueError):
            LeadRequest(name=" ", contact="@telegram")

        # Validation error: contact too short or whitespace only
        with pytest.raises(ValueError):
            LeadRequest(name="Valid Name", contact="  ")

    def test_submit_lead_success_full_payload(self, client: TestClient) -> None:
        """Verify successful lead submission with all fields."""
        payload = {
            "name": "Sarah Connor",
            "contact": "@sarah_c",
            "message": "We need an autonomous AI engineering pipeline for our fintech startup.",
        }
        response = client.post("/api/leads", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "lead_id" in data
        assert data["lead_id"].startswith("lead-")
        assert "successfully" in data["message"]

        # Verify in-memory storage contains the lead
        matching_leads = [
            item for item in LEADS_STORE if item["lead_id"] == data["lead_id"]
        ]
        assert len(matching_leads) == 1
        assert matching_leads[0]["name"] == "Sarah Connor"
        assert matching_leads[0]["contact"] == "@sarah_c"

    def test_submit_lead_success_minimal_payload(self, client: TestClient) -> None:
        """Verify successful lead submission without optional message."""
        payload = {
            "name": "John Doe",
            "contact": "john.doe@enterprise.com",
        }
        response = client.post("/api/leads", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "lead_id" in data

    def test_submit_lead_validation_errors(self, client: TestClient) -> None:
        """Verify validation errors for missing or invalid lead fields."""
        # Missing name
        resp = client.post("/api/leads", json={"contact": "user@mail.com"})
        assert resp.status_code == 422

        # Empty/whitespace name
        resp = client.post(
            "/api/leads", json={"name": "   ", "contact": "user@mail.com"}
        )
        assert resp.status_code == 422

        # Name too short (<2 chars)
        resp = client.post("/api/leads", json={"name": "A", "contact": "user@mail.com"})
        assert resp.status_code == 422

        # Missing contact
        resp = client.post("/api/leads", json={"name": "Valid User"})
        assert resp.status_code == 422

        # Empty/whitespace contact
        resp = client.post("/api/leads", json={"name": "Valid User", "contact": "   "})
        assert resp.status_code == 422

        # Contact too short (<3 chars)
        resp = client.post("/api/leads", json={"name": "Valid User", "contact": "ab"})
        assert resp.status_code == 422

        # Non-JSON payload
        resp = client.post(
            "/api/leads",
            content="invalid non json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_save_lead_disk_resilience(self, tmp_path: Path) -> None:
        """Verify save_lead handles file write errors gracefully without crashing."""
        lead = LeadRequest(name="Resilient Tester", contact="@resilient")

        with patch(
            "pathlib.Path.write_text", side_effect=IOError("Simulated disk error")
        ):
            record = save_lead(lead, client_ip="127.0.0.1")
            assert record["lead_id"].startswith("lead-")
            assert record["name"] == "Resilient Tester"

    def test_save_lead_corrupted_json_handling(self) -> None:
        """Verify save_lead safely handles corrupted existing leads file."""
        test_file = LEADS_FILE
        original_content = (
            test_file.read_text(encoding="utf-8") if test_file.exists() else None
        )

        try:
            test_file.write_text("NOT_VALID_JSON{{{", encoding="utf-8")
            lead = LeadRequest(name="Recovery Test", contact="@recovery")
            record = save_lead(lead, client_ip="127.0.0.1")
            assert record["lead_id"].startswith("lead-")

            # Check that file was rewritten with valid JSON list
            content = test_file.read_text(encoding="utf-8")
            data = json.loads(content)
            assert isinstance(data, list)
        finally:
            if original_content is not None:
                test_file.write_text(original_content, encoding="utf-8")
