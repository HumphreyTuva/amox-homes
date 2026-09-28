# AMOXHomes (Django)
Django + DRF, server-rendered templates, Tailwind (CDN in dev) + Alpine.js, SQLite dev / PostgreSQL prod.

## Run locally
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo      # optional sample listings
python manage.py runserver
```
Site: http://127.0.0.1:8000 · Admin: /admin/ · Staff dashboard: /dashboard/ · API: /api/ · Sitemap: /sitemap.xml

## How it works
- Every form saves a **Lead** (status: New > Contacted > House suggested > Viewing arranged > Connected > Completed > Closed), then offers a WhatsApp click-to-chat with the details pre-filled.
- Landlord submissions arrive as **pending** properties with 2 photos. In Admin use the actions: approve, reject, mark AMOX Verified, feature, mark unavailable.
- Photos are converted to WebP (max 1400px) with 480px thumbnails on upload.
- Institution pages (`/houses/near/<slug>/`) sort by distance. Add institutions and per-house distances in Admin.
- API for mobile apps: `GET /api/properties/?type=Bedsitter&max_rent=8000&near=mku-malindi`, `GET /api/institutions/`, `POST /api/leads/` (throttled).

## Production
Set `DEBUG=0`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL=postgres://...`, then `collectstatic` and run `gunicorn amox.wsgi`. Serve `media/` via your host or object storage.
Replace the Tailwind CDN script in `base.html` with a compiled CSS file (Tailwind standalone CLI) for faster loads on cheap phones.

## Not built yet (Phase 2)
Landlord/user accounts and dashboards, reviews, maps, search-term analytics, notifications.

## Building the CSS
The site uses compiled Tailwind CSS (`core/static/core/site.css`). After changing templates or `forms.py`, rebuild it:

    npm i -D tailwindcss@3
    npx tailwindcss -c tailwind.config.js -i core/static/src/input.css -o core/static/core/site.css --minify

Hero images live in `core/static/core/` (`hero-desktop.webp`, `hero-mobile.webp`, `og.jpg`).

## Quick start (local)
    python -m venv venv && venv\Scripts\activate     # Windows (use: source venv/bin/activate on Mac/Linux)
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py seed_demo          # sample houses
    python manage.py seed_partners      # sample partners (labelled "demo", delete before launch)
    python manage.py runserver

Admin: /admin/  ·  Staff dashboard: /dashboard/

## Going live (environment variables)
SECRET_KEY, ALLOWED_HOSTS (comma separated), CSRF_TRUSTED_ORIGINS (https URL of the site), DATABASE_URL (optional),
EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD (lead alert emails). The live server will not start without SECRET_KEY and ALLOWED_HOSTS.
