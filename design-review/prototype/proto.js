/* Prototype behaviour: language, search, save, quiz, progress. Vanilla JS, no framework. */
(function () {
    "use strict";

    var STORE_LANG = "nan_proto_lang";
    var STORE_SAVED = "nan_proto_saved";

    /* ------------------------------------------------------------------ */
    /* Language                                                            */
    /* ------------------------------------------------------------------ */
    function applyLang(lang) {
        var root = document.documentElement;
        root.lang = lang;
        root.dir = lang === "ar" ? "rtl" : "ltr";

        document.querySelectorAll("[data-en]").forEach(function (el) {
            var value = el.getAttribute("data-" + lang);
            if (value === null) return;
            if (el.dataset.html === "1") {
                el.innerHTML = value;
            } else {
                el.textContent = value;
            }
        });

        document.querySelectorAll("[data-placeholder-en]").forEach(function (el) {
            var value = el.getAttribute("data-placeholder-" + lang);
            if (value !== null) el.setAttribute("placeholder", value);
        });

        document.querySelectorAll("[data-aria-en]").forEach(function (el) {
            var value = el.getAttribute("data-aria-" + lang);
            if (value !== null) el.setAttribute("aria-label", value);
        });

        document.querySelectorAll("[data-lang]").forEach(function (btn) {
            btn.setAttribute("aria-pressed", String(btn.getAttribute("data-lang") === lang));
        });

        try { localStorage.setItem(STORE_LANG, lang); } catch (e) { }
        document.dispatchEvent(new CustomEvent("langchange", { detail: lang }));
    }

    document.querySelectorAll("[data-lang]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            applyLang(btn.getAttribute("data-lang"));
        });
    });

    var savedLang = "en";
    try { savedLang = localStorage.getItem(STORE_LANG) || "en"; } catch (e) { }
    if (savedLang === "ar") applyLang("ar");

    /* ------------------------------------------------------------------ */
    /* Toast                                                               */
    /* ------------------------------------------------------------------ */
    var toastEl = document.getElementById("toast");
    var toastTimer = null;
    function toast(message) {
        if (!toastEl) return;
        toastEl.querySelector("span").textContent = message;
        toastEl.classList.add("show");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
    }
    window.protoToast = toast;

    /* ------------------------------------------------------------------ */
    /* Search                                                              */
    /* ------------------------------------------------------------------ */
    var INDEX = [
        { en: "Perplexity launches its own take on AI agents for work", ar: "بيربليكسيتي تطلق رؤيتها الخاصة لوكلاء الذكاء الاصطناعي في العمل", src: "The Verge", href: "article.html" },
        { en: "Nasdaq sees worst day in 19 months as investors bet on AI slowdown", ar: "ناسداك يشهد أسوأ يوم منذ ١٩ شهرًا", src: "The Guardian", href: "article.html" },
        { en: "A tiny supercurrent could unlock quantum information", ar: "تيار فائق صغير يفتح المعلومات الكمومية", src: "ScienceDaily", href: "article.html" },
        { en: "OpenAI to acquire Pierre Computer Company", ar: "OpenAI تستحوذ على شركة Pierre", src: "OpenAI", href: "article.html" },
        { en: "Clearing up a robot's fuzzy memory", ar: "تنظيف ذاكرة الروبوت الغامضة", src: "MIT News", href: "article.html" },
        { en: "Google turns off Search for schools that reject AI", ar: "جوجل توقف البحث للمدارس التي ترفض الذكاء الاصطناعي", src: "The Guardian", href: "article.html" },
        { en: "Nexus Mods makes AI disclosure mandatory", ar: "Nexus Mods تفرض الإفصاح عن الذكاء الاصطناعي", src: "The Verge", href: "article.html" },
        { en: "Reverse game theory could keep AI agents in check", ar: "نظرية الألعاب العكسية تكبح الوكلاء", src: "MIT Technology Review", href: "article.html" },
        { en: "Agentic system — glossary term", ar: "نظام وكيلي — مصطلح", src: "Glossary", href: "article.html" },
        { en: "COMP 340 — Software Engineering", ar: "COMP 340 — هندسة البرمجيات", src: "Course", href: "article.html" },
        { en: "Workshop: build an app without writing code", ar: "ورشة: ابنِ تطبيقًا دون كتابة شيفرة", src: "Department", href: "article.html" }
    ];

    var sheet = document.getElementById("search-sheet");
    var input = document.getElementById("search-input");
    var results = document.getElementById("search-results");
    var lastFocus = null;

    function renderResults(q) {
        if (!results) return;
        var lang = document.documentElement.lang === "ar" ? "ar" : "en";
        var query = (q || "").trim().toLowerCase();
        var items = INDEX.filter(function (item) {
            if (!query) return true;
            return (item.en + " " + item.ar + " " + item.src).toLowerCase().indexOf(query) !== -1;
        }).slice(0, 7);

        results.innerHTML = "";
        if (!items.length) {
            var empty = document.createElement("p");
            empty.className = "search-empty";
            empty.textContent = lang === "ar" ? "لا نتائج. جرّب كلمة أخرى." : "No results. Try another word.";
            results.appendChild(empty);
            return;
        }
        items.forEach(function (item) {
            var a = document.createElement("a");
            a.href = item.href;
            var b = document.createElement("b");
            b.textContent = item[lang];
            var s = document.createElement("span");
            s.textContent = item.src;
            a.appendChild(b);
            a.appendChild(s);
            results.appendChild(a);
        });
    }

    function openSearch() {
        if (!sheet) return;
        lastFocus = document.activeElement;
        sheet.classList.add("open");
        renderResults("");
        setTimeout(function () { if (input) input.focus(); }, 30);
    }

    function closeSearch() {
        if (!sheet) return;
        sheet.classList.remove("open");
        if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    ["search-open", "search-open-mobile"].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.addEventListener("click", openSearch);
    });

    if (input) {
        input.addEventListener("input", function () { renderResults(input.value); });
    }

    if (sheet) {
        sheet.addEventListener("click", function (event) {
            if (event.target === sheet) closeSearch();
        });
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeSearch();
        }
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            openSearch();
        }
    });

    /* ------------------------------------------------------------------ */
    /* Save for later                                                      */
    /* ------------------------------------------------------------------ */
    var saveBtn = document.getElementById("save-story");
    if (saveBtn) {
        var saved = [];
        try { saved = JSON.parse(localStorage.getItem(STORE_SAVED) || "[]"); } catch (e) { }
        var key = saveBtn.getAttribute("data-story") || "demo";
        var isSaved = saved.indexOf(key) !== -1;
        saveBtn.setAttribute("aria-pressed", String(isSaved));
        saveBtn.querySelector("span").textContent = isSaved
            ? (document.documentElement.lang === "ar" ? "محفوظة" : "Saved")
            : (document.documentElement.lang === "ar" ? "حفظ" : "Save");

        saveBtn.addEventListener("click", function () {
            var now = saveBtn.getAttribute("aria-pressed") !== "true";
            saveBtn.setAttribute("aria-pressed", String(now));
            var lang = document.documentElement.lang === "ar" ? "ar" : "en";
            saveBtn.querySelector("span").textContent = now
                ? (lang === "ar" ? "محفوظة" : "Saved")
                : (lang === "ar" ? "حفظ" : "Save");
            var list = [];
            try { list = JSON.parse(localStorage.getItem(STORE_SAVED) || "[]"); } catch (e) { }
            if (now) list.push(key);
            else list = list.filter(function (k) { return k !== key; });
            try { localStorage.setItem(STORE_SAVED, JSON.stringify(list)); } catch (e) { }
            toast(lang === "ar" ? (now ? "أضيفت إلى قائمة القراءة" : "أُزيلت من القائمة") : (now ? "Added to your reading list" : "Removed from your reading list"));
        });
    }

    /* ------------------------------------------------------------------ */
    /* Article: progress, quiz                                             */
    /* ------------------------------------------------------------------ */
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

    var quiz = document.getElementById("quiz");
    if (quiz) {
        var checkBtn = document.getElementById("quiz-check");
        var scoreEl = document.getElementById("quiz-score");
        if (checkBtn) {
            checkBtn.addEventListener("click", function () {
                var questions = quiz.querySelectorAll("[data-answer]");
                var correct = 0;
                var lang = document.documentElement.lang === "ar" ? "ar" : "en";
                questions.forEach(function (q) {
                    var answer = q.getAttribute("data-answer");
                    var chosen = q.querySelector("input:checked");
                    var feedback = q.querySelector(".answer");
                    var ok = chosen && chosen.value === answer;
                    if (ok) correct += 1;
                    if (feedback) {
                        feedback.classList.add("show");
                        feedback.textContent = ok
                            ? (lang === "ar" ? "✓ صحيح" : "✓ Correct")
                            : (lang === "ar" ? "✗ ليس بعد — راجع الشرح أعلاه." : "✗ Not quite — re-read the section above.");
                        feedback.style.color = ok ? "var(--campus)" : "var(--accent)";
                    }
                });
                if (scoreEl) {
                    scoreEl.textContent = lang === "ar"
                        ? correct + " من " + questions.length
                        : correct + " of " + questions.length;
                }
            });
        }
    }
})();
