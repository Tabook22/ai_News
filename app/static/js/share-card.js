(function () {
    var cfg = window.SHARE_CARD;
    var overlay = document.getElementById('share-card-overlay');
    if (!cfg || !overlay) return;

    var canvas = document.getElementById('share-card-canvas');
    var ctx = canvas.getContext('2d');
    var qr = null;
    var qrReady = false;

    function wrapLines(text, maxWidth) {
        var words = String(text || '').split(/\s+/).filter(Boolean);
        var lines = [];
        var line = '';
        words.forEach(function (word) {
            var next = line ? line + ' ' + word : word;
            if (ctx.measureText(next).width > maxWidth && line) {
                lines.push(line);
                line = word;
            } else {
                line = next;
            }
        });
        if (line) lines.push(line);
        return lines;
    }

    function drawCard() {
        var W = 1080, H = 1350;
        var arabic = !!cfg.arabic;
        var pad = 64;

        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = '#fbfaf7';
        ctx.fillRect(0, 0, W, H);

        // Top identity band.
        ctx.fillStyle = '#0b4f6c';
        ctx.fillRect(0, 0, W, 18);
        ctx.fillStyle = '#b45309';
        ctx.fillRect(0, 18, W * .34, 8);
        ctx.fillStyle = '#0f766e';
        ctx.fillRect(W * .34, 18, W * .28, 8);
        ctx.fillStyle = '#1e3a8a';
        ctx.fillRect(W * .62, 18, W * .38, 8);

        ctx.direction = arabic ? 'rtl' : 'ltr';
        ctx.textAlign = arabic ? 'right' : 'left';
        var x = arabic ? W - pad : pad;

        // Brand and kicker.
        ctx.fillStyle = '#0b4f6c';
        ctx.font = '800 27px Inter, "Segoe UI", sans-serif';
        ctx.fillText(cfg.brand || 'Nasser AI News', x, 112);

        ctx.fillStyle = '#b45309';
        ctx.font = '700 20px Inter, "Segoe UI", sans-serif';
        ctx.fillText((cfg.desk || '').toUpperCase(), x, 158);

        // Headline, shrinking until it fits in at most four lines.
        var title = String(cfg.title || '');
        var size = 70;
        var lines = [];
        for (var attempt = 0; attempt < 5; attempt++) {
            ctx.font = '700 ' + size + 'px "Playfair Display", Georgia, serif';
            lines = wrapLines(title, W - pad * 2);
            if (lines.length <= 4) break;
            size -= 9;
        }
        var y = 278;
        ctx.fillStyle = '#14202e';
        lines.forEach(function (line) {
            ctx.fillText(line, x, y);
            y += size * 1.08;
        });

        // Short summary, limited and clipped.
        var summary = String(cfg.summary || '');
        if (summary) {
            ctx.font = '400 29px "Source Serif 4", Georgia, serif';
            ctx.fillStyle = '#5b6b7c';
            var sLines = wrapLines(summary, W - pad * 2).slice(0, 3);
            var sy = y + 26;
            sLines.forEach(function (line) {
                ctx.fillText(line, x, sy);
                sy += 40;
            });
        }

        // Brand panel: fills the poster space between the summary and footer.
        var panelY = summary ? sy + 20 : y + 30;
        var footerY = H - 210;
        var panelH = footerY - 40 - panelY;
        if (panelH > 120) {
            ctx.fillStyle = '#0b4f6c';
            ctx.fillRect(pad, panelY, W - pad * 2, panelH);

            ctx.save();
            ctx.globalAlpha = .08;
            ctx.fillStyle = '#ffffff';
            ctx.font = '900 230px "Playfair Display", Georgia, serif';
            ctx.textAlign = 'right';
            ctx.fillText('AI', W - pad - 12, panelY + panelH - 22);
            ctx.restore();

            ctx.textAlign = arabic ? 'right' : 'left';
            ctx.fillStyle = '#99f6e4';
            ctx.font = '800 19px Inter, "Segoe UI", sans-serif';
            ctx.fillText(arabic ? 'مجلة الذكاء الاصطناعي' : 'THE AI MAGAZINE', x, panelY + 52);

            ctx.fillStyle = '#ffffff';
            ctx.font = '700 42px "Playfair Display", Georgia, serif';
            ctx.fillText(cfg.brand || 'Nasser AI News', x, panelY + 108);

            ctx.fillStyle = '#c8d7dd';
            ctx.font = '400 23px Inter, "Segoe UI", sans-serif';
            ctx.fillText(arabic ? 'جامعة ظفار · قسم علوم الحاسوب' : 'Dhofar University · Computer Science', x, panelY + 148);

            ctx.fillStyle = '#fcd34d';
            ctx.font = '700 18px Inter, "Segoe UI", sans-serif';
            ctx.fillText(arabic ? 'اقرأ القصة كاملة على الموقع' : 'READ THE FULL STORY AT THE LINK BELOW', x, panelY + panelH - 28);
        }

        // Footer.
        var footerY = H - 210;
        ctx.strokeStyle = '#d8d2c5';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(pad, footerY);
        ctx.lineTo(W - pad, footerY);
        ctx.stroke();

        ctx.fillStyle = '#14202e';
        ctx.font = '700 23px Inter, "Segoe UI", sans-serif';
        ctx.fillText(cfg.source || 'Nasser AI News', x, footerY + 55);

        ctx.fillStyle = '#5b6b7c';
        ctx.font = '400 20px Inter, "Segoe UI", sans-serif';
        ctx.fillText('Dhofar University · Computer Science', x, footerY + 93);

        ctx.fillStyle = '#0b4f6c';
        ctx.font = '600 18px Inter, "Segoe UI", sans-serif';
        var host = (cfg.url || '').replace(/^https?:\/\//, '').slice(0, 52);
        ctx.fillText(host, x, footerY + 132);

        // QR sits opposite the footer text.
        if (qrReady && qr) {
            var qx = arabic ? pad : W - pad - 160;
            var qy = H - 158;
            ctx.fillStyle = '#fff';
            ctx.fillRect(qx - 8, qy - 8, 176, 176);
            ctx.drawImage(qr, qx, qy, 160, 160);
            ctx.fillStyle = '#5b6b7c';
            ctx.font = '500 16px Inter, "Segoe UI", sans-serif';
            var qrLabel = arabic ? 'امسح للقراءة' : 'Scan to read';
            ctx.textAlign = arabic ? 'left' : 'right';
            var qxText = arabic ? qx + 0 : qx + 160;
            ctx.fillText(qrLabel, qxText, qy - 16);
            ctx.textAlign = arabic ? 'right' : 'left';
        }
    }

    if (cfg.qr) {
        qr = new Image();
        qr.crossOrigin = 'anonymous';
        qr.onload = function () { qrReady = true; drawCard(); };
        qr.onerror = function () { drawCard(); };
        qr.src = cfg.qr;
    }

    function openCard() {
        overlay.hidden = false;
        document.body.classList.add('share-card-open');
        drawCard();
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(drawCard);
        }
        var close = overlay.querySelector('[data-share-card-close]');
        if (close) close.focus({ preventScroll: true });
    }

    function closeCard() {
        overlay.hidden = true;
        document.body.classList.remove('share-card-open');
    }

    document.querySelectorAll('[data-share-card-open]').forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            openCard();
        });
    });
    overlay.querySelectorAll('[data-share-card-close]').forEach(function (button) {
        button.addEventListener('click', closeCard);
    });
    overlay.addEventListener('click', function (event) {
        if (event.target === overlay) closeCard();
    });
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !overlay.hidden) closeCard();
    });

    var download = overlay.querySelector('[data-share-card-download]');
    if (download) {
        download.addEventListener('click', function () {
            drawCard();
            canvas.toBlob(function (blob) {
                if (!blob) return;
                var a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = 'nasser-ai-news-share.png';
                a.click();
                setTimeout(function () { URL.revokeObjectURL(a.href); }, 1200);
            }, 'image/png');
        });
    }
})();
