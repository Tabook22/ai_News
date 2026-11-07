/* Nasser AI News — public reader (v3). No dependencies. */
(function () {
    "use strict";

    var V3 = window.V3 || { lang: "en", strings: {} };
    var S = V3.strings || {};
    var STORE_SAVED = "nan_saved";

    /* ---------------------------------------------------------------- */
    /* toast                                                            */
    /* ---------------------------------------------------------------- */
    var toastEl = document.getElementById("v3-toast");
    var toastTimer = null;

    function toast(message) {
        if (!toastEl || !message) return;
        toastEl.querySelector("span").textContent = message;
        toastEl.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
    }

    window.v3Toast = toast;

    /* ---------------------------------------------------------------- */
    /* search overlay                                                   */
    /* ---------------------------------------------------------------- */
    var sheet = document.getElementById("v3-search-sheet");
    var searchInput = document.getElementById("v3-search-input");
    var opener = document.getElementById("v3-search-open");
    var closer = document.getElementById("v3-search-close");

    function openSearch() {
        if (!sheet) return;
        sheet.classList.add("open");
        setTimeout(function () { if (searchInput) searchInput.focus(); }, 30);
    }

    function closeSearch() {
        if (!sheet) return;
        sheet.classList.remove("open");
        if (opener) opener.focus();
    }

    if (opener) opener.addEventListener("click", openSearch);
    if (closer) closer.addEventListener("click", closeSearch);
    if (sheet) {
        sheet.addEventListener("click", function (event) {
            if (event.target === sheet) closeSearch();
        });
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeSearch();
            closeAsk();
        }
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k" && sheet) {
            event.preventDefault();
            openSearch();
        }
    });

    /* ---------------------------------------------------------------- */
    /* ask the magazine                                                 */
    /* ---------------------------------------------------------------- */
    var askPanel = document.getElementById("v3-ask-panel");
    var askOpen = document.getElementById("v3-ask-open");
    var askClose = document.getElementById("v3-ask-close");
    var askForm = document.getElementById("v3-ask-form");
    var askInput = document.getElementById("v3-ask-input");
    var askLog = document.getElementById("v3-ask-log");

    function openAsk() {
        if (!askPanel) return;
        askPanel.classList.add("open");
        if (askOpen) askOpen.setAttribute("aria-expanded", "true");
        if (askInput) askInput.focus();
    }

    function closeAsk() {
        if (!askPanel) return;
        askPanel.classList.remove("open");
        if (askOpen) askOpen.setAttribute("aria-expanded", "false");
    }

    if (askOpen) askOpen.addEventListener("click", function () {
        if (askPanel && askPanel.classList.contains("open")) closeAsk();
        else openAsk();
    });
    if (askClose) askClose.addEventListener("click", closeAsk);

    document.querySelectorAll("[data-open-ask]").forEach(function (button) {
        button.addEventListener("click", function () {
            openAsk();
            var context = button.getAttribute("data-open-ask");
            if (context && askInput && !askInput.value) {
                var prefix = V3.lang === "ar" ? "اشرح لي: " : "Explain this: ";
                askInput.value = prefix + context;
            }
        });
    });

    function bubble(text, role, sources) {
        if (!askLog) return;
        var div = document.createElement("div");
        div.className = "ask-msg " + role;
        div.textContent = text;
        (sources || []).forEach(function (source) {
            var a = document.createElement("a");
            a.className = "src";
            a.href = source.url;
            a.target = "_blank";
            a.rel = "noopener";
            a.textContent = "\u{1F4C4} " + (source.title || source.url);
            div.appendChild(a);
        });
        askLog.appendChild(div);
        askLog.scrollTop = askLog.scrollHeight;
        return div;
    }

    if (askForm) {
        askForm.addEventListener("submit", function (event) {
            event.preventDefault();
            var question = (askInput.value || "").trim();
            if (!question) return;
            bubble(question, "user");
            askInput.value = "";
            askInput.disabled = true;
            var thinking = bubble(S.thinking || "Thinking…", "bot");

            fetch("/api/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: question, lang: V3.lang })
            })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (thinking) thinking.remove();
                    askInput.disabled = false;
                    askInput.focus();
                    if (data.status === "success") {
                        bubble(data.answer, "bot", data.sources);
                    } else {
                        bubble(data.message || S.error, "bot");
                    }
                })
                .catch(function () {
                    if (thinking) thinking.remove();
                    askInput.disabled = false;
                    bubble(S.error, "bot");
                });
        });
    }

    /* ---------------------------------------------------------------- */
    /* save for later                                                   */
    /* ---------------------------------------------------------------- */
    function readSaved() {
        try {
            return JSON.parse(localStorage.getItem(STORE_SAVED) || "[]");
        } catch (error) {
            return [];
        }
    }

    function writeSaved(list) {
        try { localStorage.setItem(STORE_SAVED, JSON.stringify(list)); } catch (error) { }
    }

    document.querySelectorAll("[data-save-story]").forEach(function (button) {
        var id = button.getAttribute("data-save-story");
        var label = button.querySelector("span");
        var saved = readSaved().indexOf(id) !== -1;
        button.setAttribute("aria-pressed", String(saved));
        if (label) label.textContent = saved
            ? (V3.lang === "ar" ? "محفوظة" : "Saved")
            : (V3.lang === "ar" ? "حفظ" : "Save");

        button.addEventListener("click", function () {
            var now = button.getAttribute("aria-pressed") !== "true";
            button.setAttribute("aria-pressed", String(now));
            if (label) label.textContent = now
                ? (V3.lang === "ar" ? "محفوظة" : "Saved")
                : (V3.lang === "ar" ? "حفظ" : "Save");
            var list = readSaved().filter(function (item) { return item !== id; });
            if (now) list.push(id);
            writeSaved(list);
            toast(now ? S.saved : S.removed);
        });
    });

    /* ---------------------------------------------------------------- */
    /* copy link / share                                                */
    /* ---------------------------------------------------------------- */
    document.querySelectorAll("[data-copy-link]").forEach(function (button) {
        button.addEventListener("click", function () {
            var url = button.getAttribute("data-copy-link") || window.location.href;
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(function () { toast(S.copied); });
            } else {
                window.prompt("URL", url);
            }
        });
    });

    /* ---------------------------------------------------------------- */
    /* reading progress (article)                                       */
    /* ---------------------------------------------------------------- */
    var progress = document.querySelector(".progress");
    if (progress) {
        var update = function () {
            var top = window.scrollY || document.documentElement.scrollTop;
            var height = document.documentElement.scrollHeight - window.innerHeight;
            progress.style.width = Math.min(100, Math.max(0, (top / Math.max(1, height)) * 100)) + "%";
        };
        document.addEventListener("scroll", update, { passive: true });
        window.addEventListener("resize", update);
        update();
    }
})();

/* ---------------------------------------------------------------- */
/* listen to the story (browser speech synthesis)                   */
/* ---------------------------------------------------------------- */
(function () {
    var button = document.querySelector("[data-listen]");
    if (!button) return;
    if (!("speechSynthesis" in window)) {
        button.style.display = "none";
        return;
    }

    var speaking = false;
    var language = (window.V3 && window.V3.lang) === "ar" ? "ar-SA" : "en-US";

    function setState(on) {
        speaking = on;
        button.setAttribute("aria-pressed", String(on));
        var label = button.querySelector("span");
        if (label) {
            if (on) label.textContent = language === "ar-SA" ? "إيقاف" : "Stop";
            else label.textContent = language === "ar-SA" ? "استمع" : "Listen";
        }
    }

    button.addEventListener("click", function () {
        if (speaking) {
            window.speechSynthesis.cancel();
            setState(false);
            return;
        }
        var body = document.querySelector(".article-body");
        var text = body ? body.innerText : "";
        text = (text || "").replace(/\s+/g, " ").trim();
        if (!text) return;
        window.speechSynthesis.cancel();
        var utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language;
        utterance.rate = 0.96;
        utterance.onend = function () { setState(false); };
        utterance.onerror = function () { setState(false); };
        window.speechSynthesis.speak(utterance);
        setState(true);
    });

    window.addEventListener("beforeunload", function () {
        if (speaking) window.speechSynthesis.cancel();
    });
})();
