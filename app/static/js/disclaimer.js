(function () {
    var KEY = 'nasser-ai-disclaimer-v1';
    var overlay = document.getElementById('disclaimer-overlay');
    if (!overlay) return;

    function accepted() {
        try {
            return localStorage.getItem(KEY) === '1';
        } catch (e) {
            return false;
        }
    }

    function remember() {
        try {
            localStorage.setItem(KEY, '1');
        } catch (e) {
            /* private mode: show again next time */
        }
    }

    function open() {
        overlay.hidden = false;
        document.body.classList.add('disclaimer-open');
        var button = overlay.querySelector('[data-disclaimer-close].btn');
        if (button) button.focus({ preventScroll: true });
    }

    function close() {
        remember();
        overlay.hidden = true;
        document.body.classList.remove('disclaimer-open');
    }

    if (!accepted()) open();

    overlay.querySelectorAll('[data-disclaimer-close]').forEach(function (button) {
        button.addEventListener('click', close);
    });

    overlay.addEventListener('click', function (event) {
        if (event.target === overlay) close();
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && !overlay.hidden) close();
    });

    document.querySelectorAll('[data-disclaimer-open]').forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            open();
        });
    });
})();
