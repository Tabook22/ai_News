from pathlib import Path

snippet = '''<script>
(function () {
    /* The app can be mounted under /ainews/ behind Nginx. Prefix absolute fetch() paths
       so the admin/public JS keeps working without editing every call. */
    var base = {{ request.script_root|tojson }};
    if (base === '/') base = '';
    if (base && base.charAt(base.length - 1) === '/') base = base.slice(0, -1);
    window.APP_BASE = base;
    if (!base || !window.fetch) return;
    var originalFetch = window.fetch;
    window.fetch = function (input, init) {
        if (typeof input === 'string' && input.charAt(0) === '/' && input.indexOf(base + '/') !== 0) {
            input = base + input;
        }
        return originalFetch.call(this, input, init);
    };
})();
</script>
'''

for name in ["app/templates/layout.html", "app/templates/public_v3.html", "app/templates/public.html"]:
    p = Path(name)
    s = p.read_text(encoding="utf-8")
    if "window.APP_BASE" in s:
        print("already patched", name)
        continue
    if '<body class="admin-v3' in s:
        anchor = s[s.index('<body class="admin-v3'):]
        line = anchor.split('\n', 1)[0]
    elif '<body class="v3">' in s:
        line = '<body class="v3">'
    elif '<body class="theme-' in s:
        line = s[s.index('<body class="theme-'):].split('\n', 1)[0]
    else:
        print("body anchor missing", name)
        continue
    s = s.replace(line, line + "\n" + snippet, 1)
    p.write_text(s, encoding="utf-8")
    print("patched", name)
