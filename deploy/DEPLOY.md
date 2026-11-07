# Deploy Nasser AI News at https://nasserdiary.com/ainews/

> **Important — check the current live site first.** As of 7 November 2026,
> https://nasserdiary.com/ainews/ is serving **AR-Guide Dhofar**, a separate Vite app.
> Adding the magazine proxy below will replace it at that path. Move AR-Guide to another
> path or subdomain first, or choose a different path for the magazine. Do not overwrite it
> without a backup and the owner’s confirmation.

This is the Hostinger VPS deployment. The app is served by **Gunicorn on 127.0.0.1:8022** and
published by **Nginx under `/ainews/`**. Nginx strips the prefix before proxying and sends
`X-Forwarded-Prefix: /ainews`; Flask's `ProxyFix` adds it back to `url_for()`, static files
and redirects.

```
Browser → https://nasserdiary.com/ainews/
        → Nginx (443) location /ainews/
        → proxy_pass http://127.0.0.1:8022/
        → Gunicorn → Flask
```

## 0. What you need

- SSH access to `76.13.243.173` (root or a sudo user).
- DNS: `nasserdiary.com` and `www` A records pointing to `76.13.243.173`.
- The GitHub repository containing this code.
- Ports 80 and 443 open; port 8022 must stay private.

## 1. DNS and firewall

In Hostinger → DNS, point both records to the VPS:

```
A    @      76.13.243.173
A    www    76.13.243.173
```

On the server:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx git
sudo ufw allow 'Nginx Full'
```

Check DNS from your laptop:

```bash
dig +short nasserdiary.com
```

## 2. Put the code on the server

```bash
sudo mkdir -p /var/www/ainews
sudo chown -R $USER:$USER /var/www/ainews
git clone https://github.com/Tabook22/ai_News.git /var/www/ainews
cd /var/www/ainews
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

If the repository is private, use a deploy key or a GitHub personal access token.

## 3. Create the production `.env`

```bash
cp deploy/env.production.example .env
nano .env
```

Fill in:

- `SECRET_KEY` — a long random string;
- `ADMIN_USERNAME` and a strong `ADMIN_PASSWORD`;
- `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `SEARCH_ENGINE_ID`, `YOUTUBE_API_KEY`;
- leave `DATABASE_URL=sqlite:////var/www/ainews/data/ainews.db`;
- keep `APPLICATION_ROOT=/ainews` and `SESSION_COOKIE_PATH=/ainews`.

Then:

```bash
mkdir -p data app/instance app/static/uploads/images app/static/uploads/docs app/static/uploads/resources
chmod 600 .env
sudo chown -R www-data:www-data /var/www/ainews
sudo chown www-data:www-data .env
```

The database is SQLite; it is created automatically on first start.

### Optional: load the starter content

```bash
cd /var/www/ainews
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_tools.py'
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_tools_extra.py'
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_coding.py'
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_platforms.py'
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_ratings.py'
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_models.py'
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_projects.py'
sudo -u www-data bash -c 'cd /var/www/ainews && venv/bin/python design-review/tools/seed_reels.py'
```

## 4. Run Gunicorn as a service

```bash
sudo cp deploy/ainews.service /etc/systemd/system/ainews.service
sudo systemctl daemon-reload
sudo systemctl enable --now ainews
sudo systemctl status ainews --no-pager
```

Test locally on the VPS:

```bash
curl -I http://127.0.0.1:8022/login
```

You should get `200 OK` (or a redirect). Logs:

```bash
sudo journalctl -u ainews -f
```

## 5. Add `/ainews/` to Nginx

Find the server block for the domain:

```bash
sudo nginx -T | grep -n "server_name nasserdiary.com"
```

Create a snippet:

```bash
sudo mkdir -p /etc/nginx/snippets
sudo cp deploy/nginx-ainews.location.conf /etc/nginx/snippets/ainews.location.conf
```

Edit the **HTTPS (443)** `server { ... }` block for `nasserdiary.com` and add:

```nginx
include /etc/nginx/snippets/ainews.location.conf;
```

Do **not** replace an existing `location /` block — the longer `/ainews/` prefix wins.

Test and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

The snippet contains:

- `location = /ainews` → permanent redirect to `/ainews/`;
- `location /ainews/` → proxy to `127.0.0.1:8022/`;
- `X-Forwarded-Prefix: /ainews`;
- 512 MB upload limit and 120 s timeouts.

## 6. HTTPS

If the domain already has a certificate, skip this. Otherwise:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d nasserdiary.com -d www.nasserdiary.com
```

If you use Cloudflare, set SSL/TLS mode to **Full (strict)**, not Flexible.

## 7. Test

```bash
curl -I https://nasserdiary.com/ainews/
curl -I https://nasserdiary.com/ainews/login
```

In a browser:

- `https://nasserdiary.com/ainews/` → magazine;
- `/ainews/login` → admin;
- `/ainews/directory` → AI tools;
- `/ainews/campus/projects` → student projects;
- `/ainews/watch` → Worth Watching.

Check that CSS loads from:

```
https://nasserdiary.com/ainews/static/css/...
```

If it loads from `/static/...` instead, the `X-Forwarded-Prefix` header or `ProxyFix` is missing.

## 8. Updating after a push

From your laptop:

```bash
git add .
git commit -m "Update magazine"
git push origin main
```

On the VPS:

```bash
cd /var/www/ainews
sudo -u www-data git pull
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo systemctl restart ainews
sudo systemctl reload nginx
```

Back up before updates:

```bash
sudo cp /var/www/ainews/data/ainews.db /var/www/ainews/data/ainews-$(date +%F).db
```

## 9. Troubleshooting

| Symptom | Check |
|---|---|
| 404 at `/ainews/` | Location has trailing slash? Exact redirect present? |
| CSS/JS 404 | `X-Forwarded-Prefix: /ainews` passed; `ProxyFix` enabled; HTML contains `/ainews/static` |
| 502 Bad Gateway | `sudo systemctl status ainews`; Gunicorn on 127.0.0.1:8022 |
| Login loop | `SECRET_KEY` stable; `SESSION_COOKIE_PATH=/ainews`; HTTPS cookie |
| 413 upload | `client_max_body_size 512M` in Nginx |
| Long AI request 504 | `proxy_read_timeout 120s`; Gunicorn `--timeout 120` |
| Root site broke | Only added the `/ainews/` location; `location /` untouched |

## 10. Security

- Never commit `.env`.
- Keep Gunicorn bound to `127.0.0.1`, not `0.0.0.0`.
- Do not expose port 8022 in the firewall.
- Use a strong admin password and rotate API keys if `.env` was ever pushed.
- Keep the VPS and Python packages updated.
