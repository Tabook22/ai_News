/* Nasser AI News — admin control panel (v3) */
(function () {
    "use strict";

    var HELP = {
        overview: {
            title: "How the control room works",
            body: "This is the editor's home. The cards on top are the health of the magazine: how much is published, how many readers opened a story, who is subscribed, and what still needs work. Everything else in the sidebar is a room you can enter.",
            tips: [
                "Start in the morning with the attention list on the dashboard.",
                "Use New story for original writing, Find & import for the wire.",
                "The public issue is always one click away at the bottom of the sidebar."
            ]
        },
        general: {
            title: "General identity",
            body: "Sets the name readers see in the masthead, the browser tab, and the newsletter. The logo appears in the header, the favicon, and the QR page. Keep the name short — it is set in a large serif on the front page.",
            tips: [
                "The magazine title is used in every page title and share card.",
                "Upload a transparent PNG for the logo; it is shown on light and dark backgrounds.",
                "Changes apply to the public issue as soon as you save."
            ]
        },
        covers: {
            title: "Pinned covers",
            body: "Choose a department story and a world story to lead the issue. If you leave a field empty, the front page picks the newest story with a real photograph — and never a search-engine thumbnail.",
            tips: [
                "Pin the cover when a story matters more than it is new.",
                "The department cover is the first card in the department section.",
                "Clear the field to return to automatic selection."
            ]
        },
        appearance: {
            title: "Theme and colour",
            body: "The reading theme and the accent colour for the public magazine. The new issue uses the paper palette; these settings still drive the classic view, the newsletter, and some admin surfaces.",
            tips: [
                "Custom colours override the selected theme — use them deliberately.",
                "Test a colour change in the public issue before a big send.",
                "The Arabic column keeps its own typography regardless of theme."
            ]
        },
        sections: {
            title: "Bilingual section titles",
            body: "The headings of the front page: Top story, Latest news, Trending, Archives, Sponsored, and the reels shelf. Write both languages; the Arabic is shown whenever the reader chooses Arabic.",
            tips: [
                "Keep English titles to three or four words.",
                "If an Arabic title is empty, the English one is used.",
                "These titles also appear in the email digest."
            ]
        },
        content: {
            title: "Content sources",
            body: "Controls the curated video shelf and how many reels appear on the front page. A reel is a pointer to a video that already exists elsewhere; the magazine never hosts the file.",
            tips: [
                "Publish reels from the Reels room, not here.",
                "Four reels is the comfortable number for the front page.",
                "Turn the shelf off in weeks when there is nothing worth watching."
            ]
        },
        author: {
            title: "Author profile",
            body: "The editor's public identity: name, short bio, portrait, and CV. It appears in the article byline, the author page, and the menu avatar.",
            tips: [
                "Use a square portrait; it is cropped to a circle in the menu.",
                "The short bio is the one shown under the name on the author page.",
                "The CV link opens in a new tab for readers."
            ]
        },
        contact: {
            title: "Contact and social",
            body: "How readers reach the editor and follow the magazine. These appear in the footer and on the author page. Empty fields are simply hidden — no placeholder text is shown.",
            tips: [
                "Use a department email rather than a personal one.",
                "Social links must include https://.",
                "The address is shown only when filled."
            ]
        },
        gallery: {
            title: "Author gallery",
            body: "Photos shown on the author page. Useful for a department profile, a lab, or events. Each image can carry a title and a caption.",
            tips: [
                "Landscape photos work best in the gallery strip.",
                "Captions are shown under each image.",
                "Remove an image by saving the form without it."
            ]
        },
        aimodels: {
            title: "AI models and tasks",
            body: "Connect an OpenAI-compatible provider, then assign a model to each task: translation, summarising, answering readers, and drafting. This panel saves separately from the rest of the settings.",
            tips: [
                "Start with one provider and one strong model.",
                "The reader assistant uses the model assigned to Q&A.",
                "If a task is unassigned, the feature falls back to a safe default."
            ]
        },
        apikeys: {
            title: "API keys and integrations",
            body: "Search, translation, and video integrations. Keys are stored server-side and shown masked after saving. This panel saves separately from the rest of the settings.",
            tips: [
                "A missing key disables only the feature that needs it.",
                "Rotate a key immediately if it is ever pasted in a chat or a screenshot.",
                "Custom keys can be added for any OpenAI-compatible service."
            ]
        }
    };

    var ICONS = {
        general: "i-sliders",
        covers: "i-image",
        appearance: "i-palette",
        sections: "i-type",
        content: "i-layers",
        author: "i-user",
        contact: "i-phone",
        gallery: "i-image",
        aimodels: "i-cpu",
        apikeys: "i-key"
    };

    /* ------------------------------------------------------------ */
    /* sidebar on mobile                                             */
    /* ------------------------------------------------------------ */
    var shell = document.getElementById("admin-shell");
    var menuBtn = document.getElementById("admin-menu-btn");
    var backdrop = document.createElement("div");
    backdrop.className = "admin-nav-backdrop";
    document.body.appendChild(backdrop);

    function closeNav() {
        if (!shell) return;
        shell.classList.remove("nav-open");
        backdrop.classList.remove("show");
        if (menuBtn) menuBtn.setAttribute("aria-expanded", "false");
    }

    if (menuBtn && shell) {
        menuBtn.addEventListener("click", function () {
            var open = !shell.classList.contains("nav-open");
            shell.classList.toggle("nav-open", open);
            backdrop.classList.toggle("show", open);
            menuBtn.setAttribute("aria-expanded", String(open));
        });
        backdrop.addEventListener("click", closeNav);
        document.querySelectorAll(".admin-nav a").forEach(function (link) {
            link.addEventListener("click", closeNav);
        });
    }

    /* ------------------------------------------------------------ */
    /* help drawer                                                   */
    /* ------------------------------------------------------------ */
    var drawer = document.getElementById("help-drawer");
    var helpBackdrop = document.getElementById("help-backdrop");
    var helpTitle = document.getElementById("help-title");
    var helpBody = document.getElementById("help-body");

    function openHelp(key) {
        var item = HELP[key] || HELP.overview;
        if (!drawer) return;
        helpTitle.textContent = item.title;
        helpBody.innerHTML = "";
        var p = document.createElement("p");
        p.textContent = item.body;
        helpBody.appendChild(p);
        if (item.tips && item.tips.length) {
            var h = document.createElement("h4");
            h.textContent = "Practical notes";
            helpBody.appendChild(h);
            var ul = document.createElement("ul");
            item.tips.forEach(function (tip) {
                var li = document.createElement("li");
                li.textContent = tip;
                ul.appendChild(li);
            });
            helpBody.appendChild(ul);
        }
        drawer.classList.add("open");
        drawer.setAttribute("aria-hidden", "false");
        helpBackdrop.classList.add("open");
    }

    function closeHelp() {
        if (!drawer) return;
        drawer.classList.remove("open");
        drawer.setAttribute("aria-hidden", "true");
        helpBackdrop.classList.remove("open");
    }

    document.querySelectorAll("[data-help]").forEach(function (trigger) {
        trigger.addEventListener("click", function () {
            openHelp(trigger.getAttribute("data-help"));
        });
    });
    if (helpBackdrop) helpBackdrop.addEventListener("click", closeHelp);
    var helpClose = document.getElementById("help-close");
    if (helpClose) helpClose.addEventListener("click", closeHelp);

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeHelp();
            closeNav();
        }
    });

    /* ------------------------------------------------------------ */
    /* settings: icons, search, per-panel help                       */
    /* ------------------------------------------------------------ */
    var settingsNav = document.getElementById("settings-nav");
    if (settingsNav) {
        settingsNav.querySelectorAll(".settings-nav-item").forEach(function (item) {
            var key = item.getAttribute("data-tab");
            var iconName = ICONS[key];
            if (iconName) {
                var icon = document.createElement("span");
                icon.className = "nav-icon";
                icon.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#' + iconName + '"></use></svg>';
                item.insertBefore(icon, item.firstChild);
            }
            var emoji = item.querySelector(".tab-icon");
            if (emoji) emoji.remove();
        });

        var search = document.createElement("div");
        search.className = "settings-search";
        search.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-search"></use></svg>' +
            '<input type="search" placeholder="Filter settings…" aria-label="Filter settings">';
        settingsNav.insertBefore(search, settingsNav.firstChild);
        var input = search.querySelector("input");
        input.addEventListener("input", function () {
            var q = input.value.trim().toLowerCase();
            settingsNav.querySelectorAll(".settings-nav-item").forEach(function (item) {
                item.style.display = !q || item.textContent.toLowerCase().indexOf(q) !== -1 ? "" : "none";
            });
        });

        var saveBar = document.querySelector(".settings-save-bar");

        function syncSaveBar() {
            if (!saveBar) return;
            var active = document.querySelector(".settings-panel.active");
            var panelKey = active ? active.getAttribute("data-panel") : "";
            saveBar.classList.toggle("is-hidden", panelKey === "aimodels" || panelKey === "apikeys");
        }

        settingsNav.querySelectorAll(".settings-nav-item").forEach(function (item) {
            item.addEventListener("click", function () {
                window.setTimeout(syncSaveBar, 30);
            });
        });
        syncSaveBar();

        document.querySelectorAll(".settings-panel").forEach(function (panel) {
            var key = panel.getAttribute("data-panel");
            var header = panel.querySelector(".settings-panel-header");
            if (!header) return;
            var h2 = header.querySelector("h2");
            if (h2 && ICONS[key]) {
                var icon = document.createElement("span");
                icon.className = "panel-icon";
                icon.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#' + ICONS[key] + '"></use></svg>';
                header.insertBefore(icon, h2);
                if (h2.firstChild && h2.firstChild.nodeType === 3) {
                    h2.firstChild.textContent = h2.firstChild.textContent.replace(/^[^\p{L}\p{N}]+/u, "").trim();
                }
            }
            if (HELP[key]) {
                var helpBtn = document.createElement("button");
                helpBtn.type = "button";
                helpBtn.className = "panel-help";
                helpBtn.setAttribute("data-help", key);
                helpBtn.innerHTML = '<svg class="icon" style="width:15px;height:15px" aria-hidden="true"><use href="#i-help"></use></svg> Help';
                helpBtn.addEventListener("click", function () { openHelp(key); });
                header.appendChild(helpBtn);
            }
        });
    }

    /* ------------------------------------------------------------ */
    /* page heading icon (replaces the leading emoji on older pages) */
    /* ------------------------------------------------------------ */
    (function () {
        var map = {
            admin_dashboard: "i-dashboard", newsroom: "i-newspaper", dashboard: "i-globe",
            department_admin: "i-building", subscribers_page: "i-users", search_page: "i-search",
            archive_page: "i-folder", news_photos_admin: "i-image", photo_archive_admin: "i-image",
            reels_list: "i-video", tools_list: "i-wrench", qr_page: "i-qr",
            settings_page: "i-settings", template_picker: "i-palette", digest_preview: "i-mail"
        };
        var endpoint = document.body.getAttribute("data-endpoint");
        var h1 = document.querySelector(".dashboard-header h1, .newsroom-head h1");
        if (!h1 || !map[endpoint] || h1.querySelector("svg")) return;
        if (h1.firstChild && h1.firstChild.nodeType === 3) {
            h1.firstChild.textContent = h1.firstChild.textContent.replace(/^[^\p{L}\p{N}]+/u, "").trim();
        }
        var span = document.createElement("span");
        span.className = "page-icon";
        span.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#' + map[endpoint] + '"></use></svg>';
        h1.insertBefore(span, h1.firstChild);
    })();
})();
