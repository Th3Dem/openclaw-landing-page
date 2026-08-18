/**
 * OpenClaw AI Dev Studio - Interactive JavaScript
 * Handles language switching, state persistence, smooth scrolling,
 * and the interactive lead intake modal.
 */

document.addEventListener("DOMContentLoaded", () => {
    initLanguageSwitcher();
    initSmoothScrolling();
    initLeadModal();
    initChatModal();
});

/**
 * Initialize Language Switcher with localStorage and cookie persistence.
 */
function initLanguageSwitcher() {
    const langButtons = document.querySelectorAll(".lang-btn");
    const currentLang = document.documentElement.lang || "en";
    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get("lang");

    // If query param is explicitly set, update localStorage to match
    if (urlLang && (urlLang === "en" || urlLang === "ru")) {
        try {
            localStorage.setItem("openclaw_lang", urlLang);
            document.cookie = `openclaw_lang=${urlLang};path=/;max-age=2592000;SameSite=Lax`;
        } catch (e) {
            console.warn("Could not save language preference to storage", e);
        }
    } else {
        // If no query param in URL, check if user had a saved preference different from server render
        try {
            const savedLang = localStorage.getItem("openclaw_lang");
            if (savedLang && (savedLang === "en" || savedLang === "ru") && savedLang !== currentLang) {
                const targetUrl = new URL(window.location.href);
                targetUrl.searchParams.set("lang", savedLang);
                window.location.replace(targetUrl.toString());
                return;
            }
        } catch (e) {
            console.warn("Could not read language preference from storage", e);
        }
    }

    // Attach click listeners to language toggle buttons
    langButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const targetLang = btn.getAttribute("data-lang");
            if (targetLang) {
                try {
                    localStorage.setItem("openclaw_lang", targetLang);
                    document.cookie = `openclaw_lang=${targetLang};path=/;max-age=2592000;SameSite=Lax`;
                } catch (err) {
                    console.warn("Could not save language to storage", err);
                }
            }
        });
    });
}

/**
 * Enhanced smooth scrolling for internal section anchors.
 */
function initSmoothScrolling() {
    const navLinks = document.querySelectorAll('a.nav-link[href^="#"]');
    navLinks.forEach((link) => {
        link.addEventListener("click", (e) => {
            const targetId = link.getAttribute("href");
            if (!targetId || targetId === "#") return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
                history.pushState(null, "", targetId);
            }
        });
    });
}

/**
 * Initialize Interactive Lead Intake Modal Dialog
 */
function initLeadModal() {
    const modal = document.getElementById("leadModal");
    const openBtn = document.getElementById("openLeadModalBtn");
    const closeBtn = document.getElementById("modalCloseBtn");
    const backdrop = document.getElementById("modalBackdrop");
    const successCloseBtn = document.getElementById("successCloseBtn");
    const leadForm = document.getElementById("leadForm");
    const leadSuccessContainer = document.getElementById("leadSuccessContainer");
    const formAlert = document.getElementById("formAlert");
    const submitBtn = document.getElementById("leadSubmitBtn");
    const btnSpinner = document.getElementById("btnSpinner");
    const btnSubmitText = document.getElementById("btnSubmitText");

    const nameInput = document.getElementById("leadName");
    const contactInput = document.getElementById("leadContact");
    const messageInput = document.getElementById("leadMessage");

    const nameError = document.getElementById("nameError");
    const contactError = document.getElementById("contactError");

    if (!modal || !openBtn) {
        return;
    }

    const originalSubmitText = btnSubmitText ? btnSubmitText.textContent : "Submit";
    const submittingText = submitBtn ? submitBtn.getAttribute("data-submitting-text") || "Submitting..." : "Submitting...";

    function clearValidationErrors() {
        if (formAlert) {
            formAlert.textContent = "";
            formAlert.style.display = "none";
        }
        if (nameError) {
            nameError.textContent = "";
            nameError.style.display = "none";
        }
        if (contactError) {
            contactError.textContent = "";
            contactError.style.display = "none";
        }
        if (nameInput) nameInput.classList.remove("input-invalid");
        if (contactInput) contactInput.classList.remove("input-invalid");
    }

    function openModal() {
        modal.classList.add("active", "is-active");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";

        // Reset views: show form, hide success container
        if (leadForm) leadForm.style.display = "block";
        if (leadSuccessContainer) leadSuccessContainer.style.display = "none";
        clearValidationErrors();

        // Focus first input field
        setTimeout(() => {
            if (nameInput) nameInput.focus();
        }, 150);
    }

    function closeModal() {
        modal.classList.remove("active", "is-active");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
        clearValidationErrors();
    }

    // Event listeners for modal open and close
    openBtn.addEventListener("click", openModal);

    if (closeBtn) {
        closeBtn.addEventListener("click", closeModal);
    }

    if (backdrop) {
        backdrop.addEventListener("click", closeModal);
    }

    if (successCloseBtn) {
        successCloseBtn.addEventListener("click", closeModal);
    }

    // Close on Escape key press
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && (modal.classList.contains("active") || modal.classList.contains("is-active"))) {
            closeModal();
        }
    });

    // Form submission handler
    if (leadForm) {
        leadForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearValidationErrors();

            const name = nameInput ? nameInput.value.trim() : "";
            const contact = contactInput ? contactInput.value.trim() : "";
            const message = messageInput ? messageInput.value.trim() : "";

            let hasError = false;
            const currentLang = document.documentElement.lang || "en";

            if (name.length < 2) {
                hasError = true;
                if (nameInput) nameInput.classList.add("input-invalid");
                if (nameError) {
                    nameError.textContent = currentLang === "ru"
                        ? "Пожалуйста, введите ваше имя (минимум 2 символа)."
                        : "Please enter your name (at least 2 characters).";
                    nameError.style.display = "block";
                }
            }

            if (contact.length < 3) {
                hasError = true;
                if (contactInput) contactInput.classList.add("input-invalid");
                if (contactError) {
                    contactError.textContent = currentLang === "ru"
                        ? "Пожалуйста, укажите Telegram, email или телефон."
                        : "Please enter a valid contact (Telegram, email or phone).";
                    contactError.style.display = "block";
                }
            }

            if (hasError) {
                return;
            }

            // Set loading state
            if (submitBtn) submitBtn.disabled = true;
            if (btnSpinner) btnSpinner.style.display = "inline-block";
            if (btnSubmitText) btnSubmitText.textContent = submittingText;

            try {
                const response = await fetch("/api/leads", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    body: JSON.stringify({
                        name: name,
                        contact: contact,
                        message: message.length > 0 ? message : null,
                    }),
                });

                const result = await response.json();

                if (response.ok && result.status === "success") {
                    // Success transition
                    leadForm.reset();
                    leadForm.style.display = "none";
                    if (leadSuccessContainer) {
                        leadSuccessContainer.style.display = "block";
                    }
                } else {
                    // Handle validation or server error
                    const errorMessage = result.message || (
                        currentLang === "ru"
                            ? "Не удалось отправить заявку. Проверьте данные и попробуйте снова."
                            : "Failed to submit application. Please check your inputs and try again."
                    );
                    if (formAlert) {
                        formAlert.textContent = errorMessage;
                        formAlert.style.display = "block";
                    }
                }
            } catch (err) {
                console.error("Lead submission error:", err);
                const networkErrorMessage = currentLang === "ru"
                    ? "Сетевая ошибка при отправке заявки. Попробуйте еще раз."
                    : "Network error occurred while submitting. Please try again.";
                if (formAlert) {
                    formAlert.textContent = networkErrorMessage;
                    formAlert.style.display = "block";
                }
            } finally {
                // Restore submit button state
                if (submitBtn) submitBtn.disabled = false;
                if (btnSpinner) btnSpinner.style.display = "none";
                if (btnSubmitText) btnSubmitText.textContent = originalSubmitText;
            }
        });
    }
}

/**
 * Initialize Autonomous AI Briefing Chat Modal & State Machine.
 */
function initChatModal() {
    const chatModal = document.getElementById("chatModal");
    const openBtn = document.getElementById("openChatModalBtn");
    const closeBtn = document.getElementById("chatModalCloseBtn");
    const backdrop = document.getElementById("chatModalBackdrop");
    const messagesContainer = document.getElementById("chatMessages");
    const typingIndicator = document.getElementById("chatTyping");
    const suggestionsContainer = document.getElementById("chatSuggestions");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatSendBtn = document.getElementById("chatSendBtn");
    const completedActions = document.getElementById("chatCompletedActions");
    const restartBtn = document.getElementById("chatRestartBtn");
    const viewBriefBtn = document.getElementById("chatViewBriefBtn");
    const briefCard = document.getElementById("chatBriefCard");
    const briefContent = document.getElementById("chatBriefContent");
    const progressBar = document.getElementById("chatProgressBar");
    const progressText = document.getElementById("chatProgressText");

    if (!chatModal || !openBtn) {
        return;
    }

    const currentLang = document.documentElement.lang || "ru";
    let sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    let history = [];
    let isInitialized = false;
    let currentBriefSummary = "";

    function updateProgress(score) {
        const val = Math.min(Math.max(score || 10, 10), 100);
        if (progressBar) progressBar.style.width = val + "%";
        if (progressText) progressText.textContent = val + "%";
    }

    function openModal() {
        chatModal.classList.add("active", "is-active");
        chatModal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";

        if (!isInitialized) {
            isInitialized = true;
            fetchInitialGreeting();
        }

        setTimeout(() => {
            if (chatInput) chatInput.focus();
        }, 150);
    }

    function closeModal() {
        chatModal.classList.remove("active", "is-active");
        chatModal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    }

    function scrollToBottom() {
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    function renderMessage(role, text) {
        if (!messagesContainer) return;

        const msgDiv = document.createElement("div");
        msgDiv.className = role === "user" ? "chat-msg chat-msg-user" : "chat-msg chat-msg-bot";

        const avatar = document.createElement("div");
        avatar.className = "chat-avatar";
        avatar.textContent = role === "user" ? "👤" : "🤖";

        const bubble = document.createElement("div");
        bubble.className = "chat-bubble";
        bubble.textContent = text;

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        messagesContainer.appendChild(msgDiv);

        scrollToBottom();
    }

    function renderSuggestions(suggestions) {
        if (!suggestionsContainer) return;
        suggestionsContainer.innerHTML = "";

        if (!suggestions || suggestions.length === 0) {
            suggestionsContainer.style.display = "none";
            return;
        }

        suggestionsContainer.style.display = "flex";
        suggestions.forEach((chipText) => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "chat-chip";
            chip.textContent = chipText;
            chip.addEventListener("click", () => {
                handleUserSend(chipText);
            });
            suggestionsContainer.appendChild(chip);
        });

        scrollToBottom();
    }

    async function fetchInitialGreeting() {
        if (typingIndicator) typingIndicator.style.display = "flex";
        updateProgress(10);
        scrollToBottom();

        try {
            const response = await fetch("/api/chat/briefing", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: null,
                    history: [],
                    lang: currentLang,
                }),
            });

            const data = await response.json();
            if (typingIndicator) typingIndicator.style.display = "none";

            if (data && data.message) {
                renderMessage("assistant", data.message);
                history.push({ role: "assistant", content: data.message });
                renderSuggestions(data.suggestions);
                if (data.completeness !== undefined) updateProgress(data.completeness);
            }
        } catch (err) {
            console.error("Chat briefing initialization error:", err);
            if (typingIndicator) typingIndicator.style.display = "none";
            renderMessage(
                "assistant",
                currentLang === "ru"
                    ? "Здравствуйте! Я AI-архитектор OpenClaw. Какой продукт или сайт вы хотите разработать?"
                    : "Hello! I am OpenClaw's AI Architect. What product or website would you like to build?"
            );
        }
    }

    async function handleUserSend(text) {
        const cleaned = text.trim();
        if (!cleaned) return;

        // Render user message & update local state
        renderMessage("user", cleaned);
        history.push({ role: "user", content: cleaned });

        if (chatInput) chatInput.value = "";
        if (suggestionsContainer) suggestionsContainer.innerHTML = "";
        if (typingIndicator) typingIndicator.style.display = "flex";
        if (chatSendBtn) chatSendBtn.disabled = true;
        if (chatInput) chatInput.disabled = true;

        scrollToBottom();

        try {
            const response = await fetch("/api/chat/briefing", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: cleaned,
                    history: history.slice(0, -1),
                    lang: currentLang,
                }),
            });

            const data = await response.json();
            if (typingIndicator) typingIndicator.style.display = "none";

            if (data && data.message) {
                renderMessage("assistant", data.message);
                history.push({ role: "assistant", content: data.message });

                if (data.completeness !== undefined) {
                    updateProgress(data.completeness);
                }

                if (data.is_completed) {
                    currentBriefSummary = data.brief_summary || "";
                    if (chatForm) chatForm.style.display = "none";
                    if (suggestionsContainer) suggestionsContainer.style.display = "none";
                    if (completedActions) completedActions.style.display = "flex";
                    if (briefContent) briefContent.textContent = currentBriefSummary;
                    updateProgress(100);
                } else {
                    renderSuggestions(data.suggestions);
                }
            }
        } catch (err) {
            console.error("Chat message send error:", err);
            if (typingIndicator) typingIndicator.style.display = "none";
            renderMessage(
                "assistant",
                currentLang === "ru"
                    ? "Произошла сетевая ошибка. Пожалуйста, повторите ответ."
                    : "A network error occurred. Please try resending your answer."
            );
        } finally {
            if (chatSendBtn) chatSendBtn.disabled = false;
            if (chatInput) {
                chatInput.disabled = false;
                chatInput.focus();
            }
            scrollToBottom();
        }
    }

    // Event Listeners
    openBtn.addEventListener("click", openModal);

    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (backdrop) backdrop.addEventListener("click", closeModal);

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && (chatModal.classList.contains("active") || chatModal.classList.contains("is-active"))) {
            closeModal();
        }
    });

    if (chatForm) {
        chatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = chatInput ? chatInput.value : "";
            handleUserSend(text);
        });
    }

    if (viewBriefBtn) {
        viewBriefBtn.addEventListener("click", () => {
            if (briefCard) {
                const isHidden = briefCard.style.display === "none";
                briefCard.style.display = isHidden ? "block" : "none";
                if (isHidden) {
                    briefCard.scrollIntoView({ behavior: "smooth" });
                }
            }
        });
    }

    const downloadBriefBtn = document.getElementById("chatDownloadBriefBtn");
    if (downloadBriefBtn) {
        downloadBriefBtn.addEventListener("click", () => {
            const contentToDownload = currentBriefSummary || (briefContent ? briefContent.textContent : "");
            if (!contentToDownload) return;
            const blob = new Blob([contentToDownload], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `openclaw-tz-specification-${sessionId}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    if (restartBtn) {
        restartBtn.addEventListener("click", () => {
            sessionId = "session-" + Math.random().toString(36).substring(2, 10);
            history = [];
            currentBriefSummary = "";
            if (messagesContainer) messagesContainer.innerHTML = "";
            if (completedActions) completedActions.style.display = "none";
            if (briefCard) briefCard.style.display = "none";
            if (chatForm) chatForm.style.display = "block";
            fetchInitialGreeting();
        });
    }
}
