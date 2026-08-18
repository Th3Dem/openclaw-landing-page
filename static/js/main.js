/**
 * OpenClaw AI Dev Studio - Interactive JavaScript
 * Handles language switching, state persistence, smooth scrolling,
 * and the interactive lead intake modal.
 */

document.addEventListener("DOMContentLoaded", () => {
    initLanguageSwitcher();
    initSmoothScrolling();
    initLeadModal();
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
        modal.classList.add("is-active");
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
        modal.classList.remove("is-active");
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
        if (e.key === "Escape" && modal.classList.contains("is-active")) {
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
