/* Learn, glossary, and student-board behaviour. No dependencies. Progress lives in the
   reader's own browser (localStorage) — nothing is sent to the server. */
(function () {
    'use strict';

    var KEY = 'nasser-learn-v1';
    var ar = !!(window.V3 && window.V3.lang === 'ar');

    function $(sel, root) { return (root || document).querySelector(sel); }
    function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
    function json(id) {
        var node = document.getElementById(id);
        if (!node) return null;
        try { return JSON.parse(node.textContent); } catch (e) { return null; }
    }
    function fmt(text, values) {
        return String(text || '').replace(/\{(\w+)\}/g, function (_m, k) { return values[k] != null ? values[k] : ''; });
    }

    /* ---------- saved progress ---------- */
    function load() {
        var s = {};
        try { s = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { s = {}; }
        return {
            known: s.known || {}, best: s.best || 0, bestOf: s.bestOf || 0,
            streak: s.streak || 0, last: s.last || '', quizzes: s.quizzes || 0
        };
    }
    function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* private mode */ } }
    function dayKey(d) {
        function p(n) { return (n < 10 ? '0' : '') + n; }
        return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
    }
    function touchStreak(s) {
        var now = new Date(), t = dayKey(now);
        if (s.last === t) return;
        var y = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
        s.streak = (s.last === dayKey(y)) ? (s.streak || 0) + 1 : 1;
        s.last = t;
    }
    function knownCount(s, slugs) {
        var n = 0;
        Object.keys(s.known).forEach(function (k) {
            if (s.known[k] && (!slugs || slugs.indexOf(k) !== -1)) n++;
        });
        return n;
    }
    function shuffle(list) {
        var a = list.slice();
        for (var i = a.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var t = a[i]; a[i] = a[j]; a[j] = t;
        }
        return a;
    }

    /* ---------- moving news bar: a visible pause control ---------- */
    $all('[data-ticker]').forEach(function (bar) {
        var btn = $('[data-ticker-pause]', bar);
        if (!btn) return;
        btn.addEventListener('click', function () {
            var paused = bar.classList.toggle('is-paused');
            btn.setAttribute('aria-pressed', paused ? 'true' : 'false');
            btn.setAttribute('aria-label', btn.getAttribute(paused ? 'data-label-play' : 'data-label-pause'));
        });
    });

    /* ---------- front page tiles ---------- */
    $all('[data-learn-line]').forEach(function (el) {
        var s = load(), kind = el.getAttribute('data-learn-line'), tpl = el.getAttribute('data-template') || '';
        if (kind === 'known') {
            var n = knownCount(s);
            if (n) el.textContent = fmt(tpl, { n: n, total: el.getAttribute('data-total') });
        } else if (kind === 'best' && s.bestOf) {
            el.textContent = fmt(tpl, { n: s.best });
        }
    });

    /* ---------- glossary page: search and filter ---------- */
    var search = $('[data-gl-search]');
    if (search) {
        var cards = $all('.gl-term'), chips = $all('[data-gl-cat]'), countEl = $('[data-gl-count]'),
            emptyEl = $('[data-gl-empty]'), activeCat = '';
        var norm = function (v) { return String(v || '').toLowerCase().replace(/[ً-ْ]/g, '').trim(); };
        var apply = function () {
            var q = norm(search.value), shown = 0;
            cards.forEach(function (c) {
                var ok = (!activeCat || c.getAttribute('data-cat') === activeCat) &&
                    (!q || (c.getAttribute('data-text') || '').indexOf(q) !== -1);
                c.hidden = !ok;
                if (ok) shown++;
            });
            if (countEl) {
                countEl.textContent = (q || activeCat)
                    ? shown + (ar ? ' مصطلح' : (shown === 1 ? ' term' : ' terms'))
                    : '';
            }
            if (emptyEl) emptyEl.hidden = shown > 0;
        };
        search.addEventListener('input', apply);
        chips.forEach(function (chip) {
            chip.addEventListener('click', function () {
                activeCat = chip.getAttribute('data-gl-cat') || '';
                chips.forEach(function (c) {
                    var on = c === chip;
                    c.classList.toggle('is-on', on);
                    c.setAttribute('aria-pressed', on ? 'true' : 'false');
                });
                apply();
            });
        });
    }

    /* ---------- learn page ---------- */
    var terms = json('learn-data'), cats = json('learn-cats'), S = json('learn-strings');
    var learnRoot = $('[data-learn-stats]');
    if (terms && cats && S && learnRoot) {
        var catMap = {};
        cats.forEach(function (c) { catMap[c.key] = c; });
        var slugs = terms.map(function (t) { return t.slug; });
        var primary = function (t) { return ar ? (t.ar_name || t.en) : t.en; };
        var alt = function (t) { return ar ? t.en : t.ar_name; };
        var definition = function (t) { return ar ? (t.def_ar || t.def_en) : t.def_en; };
        var example = function (t) { return ar ? (t.ex_ar || t.ex_en) : t.ex_en; };

        var state = load();
        var renderStats = function () {
            var set = function (name, value) { var n = $('[data-stat="' + name + '"]', learnRoot); if (n) n.textContent = value; };
            set('known', knownCount(state, slugs) + ' / ' + slugs.length);
            set('best', state.bestOf ? state.best + '/' + state.bestOf : '–');
            set('streak', state.streak || 0);
        };
        renderStats();

        /* flashcards */
        var fc = $('[data-fc]');
        if (fc) {
            var card = $('[data-fc-card]', fc), emptyMsg = $('[data-fc-empty]', fc), posEl = $('[data-fc-pos]', fc),
                stage = $('.fc-stage', fc), controls = $('.fc-controls', fc);
            var deck = [], idx = 0, cat = '', onlyLearning = false;
            var buildDeck = function (keepSlug) {
                deck = terms.filter(function (t) {
                    return (!cat || t.cat === cat) && (!onlyLearning || !state.known[t.slug]);
                });
                idx = 0;
                if (keepSlug) {
                    for (var i = 0; i < deck.length; i++) if (deck[i].slug === keepSlug) { idx = i; break; }
                }
                render();
            };
            var render = function () {
                var has = deck.length > 0;
                if (stage) stage.hidden = !has;
                if (controls) controls.hidden = !has;
                if (emptyMsg) emptyMsg.hidden = has;
                if (posEl) posEl.hidden = !has;
                if (!has) return;
                if (idx >= deck.length) idx = 0;
                if (idx < 0) idx = deck.length - 1;
                var t = deck[idx], c = catMap[t.cat];
                card.classList.remove('is-flipped');
                card.setAttribute('aria-pressed', 'false');
                card.style.setProperty('--cc', 'var(' + (c ? c.color : '--brand') + ')');
                card.classList.toggle('is-known', !!state.known[t.slug]);
                $('[data-fc-cat-label]', card).textContent = c ? (ar ? c.ar : c.en) : '';
                $('[data-fc-term]', card).textContent = primary(t);
                var altEl = $('[data-fc-alt]', card), a = alt(t);
                altEl.textContent = a || '';
                altEl.setAttribute('dir', ar ? 'ltr' : 'rtl');
                altEl.setAttribute('lang', ar ? 'en' : 'ar');
                $('[data-fc-def]', card).textContent = definition(t);
                var ex = example(t), exEl = $('[data-fc-ex]', card);
                exEl.textContent = ex ? ((ar ? 'مثال: ' : 'Example: ') + ex) : '';
                posEl.textContent = fmt(S.cardOf, { n: idx + 1, total: deck.length });
            };
            card.addEventListener('click', function () {
                var on = card.classList.toggle('is-flipped');
                card.setAttribute('aria-pressed', on ? 'true' : 'false');
            });
            var step = function (d) { idx += d; render(); };
            $('[data-fc-next]', fc).addEventListener('click', function () { step(1); });
            $('[data-fc-prev]', fc).addEventListener('click', function () { step(-1); });
            $('[data-fc-shuffle]', fc).addEventListener('click', function () { deck = shuffle(deck); idx = 0; render(); });
            $all('[data-fc-mark]', fc).forEach(function (btn) {
                btn.addEventListener('click', function () {
                    if (!deck.length) return;
                    var t = deck[idx];
                    state.known[t.slug] = btn.getAttribute('data-fc-mark') === 'known';
                    touchStreak(state);
                    save(state);
                    renderStats();
                    if (onlyLearning && state.known[t.slug]) {
                        deck.splice(idx, 1);
                        render();
                    } else {
                        step(1);
                    }
                });
            });
            $all('[data-fc-cat]', fc).forEach(function (chip) {
                chip.addEventListener('click', function () {
                    cat = chip.getAttribute('data-fc-cat') || '';
                    $all('[data-fc-cat]', fc).forEach(function (c) {
                        var on = c === chip;
                        c.classList.toggle('is-on', on);
                        c.setAttribute('aria-pressed', on ? 'true' : 'false');
                    });
                    buildDeck();
                });
            });
            $('[data-fc-learning]', fc).addEventListener('change', function (e) { onlyLearning = e.target.checked; buildDeck(); });
            fc.addEventListener('keydown', function (e) {
                if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
                var forward = ar ? 'ArrowLeft' : 'ArrowRight', back = ar ? 'ArrowRight' : 'ArrowLeft';
                if (e.key === forward) { e.preventDefault(); step(1); }
                else if (e.key === back) { e.preventDefault(); step(-1); }
            });
            buildDeck();
        }

        /* quiz */
        var qz = $('[data-qz]');
        if (qz) {
            var startBox = $('[data-qz-start]', qz), runBox = $('[data-qz-run]', qz), doneBox = $('[data-qz-done]', qz),
                bestLine = $('[data-qz-best-line]', qz), barEl = $('[data-qz-bar]', qz), posQ = $('[data-qz-pos]', qz),
                qEl = $('[data-qz-q]', qz), optsEl = $('[data-qz-opts]', qz), fbEl = $('[data-qz-feedback]', qz),
                nextBtn = $('[data-qz-next]', qz);
            var QN = Math.min(10, terms.length), questions = [], qi = 0, score = 0, missed = [];

            var showBest = function () {
                bestLine.textContent = state.bestOf ? fmt(S.bestLine, { best: state.best, of: state.bestOf }) : S.noBest;
            };
            showBest();

            var makeQuestions = function () {
                var pool = shuffle(terms.filter(function (t) { return definition(t); })).slice(0, QN);
                return pool.map(function (t) {
                    var same = shuffle(terms.filter(function (o) { return o.slug !== t.slug && o.cat === t.cat; }));
                    var other = shuffle(terms.filter(function (o) { return o.slug !== t.slug && o.cat !== t.cat; }));
                    var wrong = same.concat(other).slice(0, 3);
                    return { term: t, options: shuffle([t].concat(wrong)) };
                });
            };

            var showQuestion = function () {
                var q = questions[qi];
                barEl.style.width = (qi / questions.length * 100) + '%';
                posQ.textContent = fmt(S.pos, { n: qi + 1, total: questions.length });
                qEl.textContent = definition(q.term);
                optsEl.innerHTML = '';
                fbEl.hidden = true;
                nextBtn.hidden = true;
                q.options.forEach(function (opt) {
                    var b = document.createElement('button');
                    b.type = 'button';
                    b.className = 'qz-opt';
                    b.textContent = primary(opt);
                    b.setAttribute('data-slug', opt.slug);
                    b.addEventListener('click', function () { answer(opt, b); });
                    optsEl.appendChild(b);
                });
            };

            var answer = function (opt, btn) {
                var q = questions[qi], right = opt.slug === q.term.slug;
                $all('.qz-opt', optsEl).forEach(function (b) {
                    b.disabled = true;
                    if (b.getAttribute('data-slug') === q.term.slug) b.classList.add('is-right');
                });
                if (right) { score++; }
                else { btn.classList.add('is-wrong'); missed.push(q.term); }
                fbEl.hidden = false;
                fbEl.className = 'qz-feedback ' + (right ? 'is-right' : 'is-wrong');
                fbEl.textContent = right ? S.correct : fmt(S.wrong, { term: primary(q.term) });
                nextBtn.textContent = (qi === questions.length - 1) ? S.finish : S.next;
                nextBtn.hidden = false;
                nextBtn.focus();
            };

            var finish = function () {
                runBox.hidden = true;
                doneBox.hidden = false;
                barEl.style.width = '100%';
                if (!state.bestOf || score > state.best || (score === state.best && questions.length > state.bestOf)) {
                    state.best = score; state.bestOf = questions.length;
                }
                state.quizzes = (state.quizzes || 0) + 1;
                touchStreak(state);
                save(state);
                renderStats();
                showBest();
                $('[data-qz-score]', doneBox).textContent = score;
                $('[data-qz-total]', doneBox).textContent = questions.length;
                var ratio = score / questions.length;
                $('[data-qz-msg]', doneBox).textContent = ratio >= 0.9 ? S.msgTop : (ratio >= 0.6 ? S.msgMid : S.msgLow);
                var text = fmt(S.share, { score: score, total: questions.length, name: S.name }) + ' ' + location.href.split('#')[0];
                $('[data-qz-share]', doneBox).setAttribute('href', 'https://wa.me/?text=' + encodeURIComponent(text));
                var review = $('[data-qz-review]', doneBox), list = $('[data-qz-review-list]', doneBox);
                list.innerHTML = '';
                missed.forEach(function (t) {
                    var li = document.createElement('li');
                    var b = document.createElement('b'); b.textContent = primary(t);
                    li.appendChild(b);
                    li.appendChild(document.createTextNode(' — ' + definition(t)));
                    list.appendChild(li);
                });
                review.hidden = missed.length === 0;
            };

            nextBtn.addEventListener('click', function () {
                if (qi >= questions.length - 1) { finish(); return; }
                qi++;
                showQuestion();
            });

            var begin = function () {
                questions = makeQuestions(); qi = 0; score = 0; missed = [];
                startBox.hidden = true; doneBox.hidden = true; runBox.hidden = false;
                showQuestion();
                qz.scrollIntoView({ behavior: 'smooth', block: 'start' });
            };
            $('[data-qz-begin]', qz).addEventListener('click', begin);
            $('[data-qz-again]', qz).addEventListener('click', begin);
        }
    }

    /* ---------- student board form ---------- */
    var form = $('[data-bd-form]');
    if (form) {
        var body = $('#bd-body', form), counter = $('[data-bd-count]', form), linkRow = $('[data-bd-link-row]', form),
            linkInput = $('#bd-link', form);
        var count = function () { if (counter) counter.textContent = body.value.length; };
        if (body) { body.addEventListener('input', count); count(); }
        var syncKind = function () {
            var kind = ($('input[name="kind"]:checked', form) || {}).value;
            var isLink = kind === 'link';
            if (linkRow) linkRow.hidden = !isLink;
            if (linkInput) linkInput.required = isLink;
        };
        $all('input[name="kind"]', form).forEach(function (r) { r.addEventListener('change', syncKind); });
        syncKind();

        // The server answers with a message at the top of the page; bring it into view.
        var flash = $('.flash');
        if (flash && !location.hash) {
            flash.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
})();
