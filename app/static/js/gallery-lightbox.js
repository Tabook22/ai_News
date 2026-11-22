(function () {
    var box = document.getElementById('gallery-lightbox');
    if (!box) return;
    var triggers = Array.from(document.querySelectorAll('[data-gallery-open]'));
    if (!triggers.length) return;
    var image = document.getElementById('gl-image');
    var captionEn = document.getElementById('gl-caption-en');
    var captionAr = document.getElementById('gl-caption-ar');
    var captionBox = document.getElementById('gl-caption');
    var count = document.getElementById('gl-count');
    var current = 0;
    var lastFocus = null;

    function render(index) {
        current = (index + triggers.length) % triggers.length;
        var trigger = triggers[current];
        image.src = trigger.getAttribute('data-image') || '';
        image.alt = trigger.getAttribute('data-alt') || '';
        var en = trigger.getAttribute('data-caption-en') || '';
        var ar = trigger.getAttribute('data-caption-ar') || '';
        captionEn.textContent = en;
        captionAr.textContent = ar;
        captionEn.hidden = !en;
        captionAr.hidden = !ar;
        captionBox.hidden = !en && !ar;
        count.textContent = (current + 1) + ' / ' + triggers.length;
    }

    function open(index) {
        lastFocus = document.activeElement;
        render(index);
        box.hidden = false;
        document.body.classList.add('gallery-open');
        var close = box.querySelector('[data-gallery-close]');
        if (close) close.focus({ preventScroll: true });
    }

    function close() {
        box.hidden = true;
        document.body.classList.remove('gallery-open');
        image.src = '';
        if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
    }

    triggers.forEach(function (trigger, index) {
        trigger.addEventListener('click', function () { open(index); });
    });
    box.querySelectorAll('[data-gallery-close]').forEach(function (button) {
        button.addEventListener('click', close);
    });
    box.querySelectorAll('[data-gallery-prev]').forEach(function (button) {
        button.addEventListener('click', function () { render(current - 1); });
    });
    box.querySelectorAll('[data-gallery-next]').forEach(function (button) {
        button.addEventListener('click', function () { render(current + 1); });
    });
    box.addEventListener('click', function (event) {
        if (event.target === box) close();
    });
    document.addEventListener('keydown', function (event) {
        if (box.hidden) return;
        if (event.key === 'Escape') close();
        if (event.key === 'ArrowLeft') render(current - 1);
        if (event.key === 'ArrowRight') render(current + 1);
    });
})();
