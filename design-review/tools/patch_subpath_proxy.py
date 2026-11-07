from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

if "ProxyFix" not in s:
    s = s.replace("from werkzeug.utils import secure_filename",
                  "from werkzeug.utils import secure_filename\nfrom werkzeug.middleware.proxy_fix import ProxyFix", 1)
    print("ProxyFix import added")

if "app.wsgi_app = ProxyFix" not in s:
    anchor = "app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')"
    block = """# Behind Nginx the app can live under a subpath such as /ainews/.
# Nginx sends X-Forwarded-Prefix; ProxyFix turns it into SCRIPT_NAME so url_for()
# and static URLs include the prefix.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
app.config['SESSION_COOKIE_PATH'] = os.environ.get('SESSION_COOKIE_PATH', '/')

""" + anchor
    s = s.replace(anchor, block, 1)
    print("ProxyFix wrapped")

p.write_text(s, encoding="utf-8")
