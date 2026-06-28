# GritTrack by Rustler Ranch

Workout tracker for weight training and cardio. Multi-user, cross-device, PWA-installable on iPhone and iPad.

**Stack:** Flask · SQLAlchemy · Flask-Login · PostgreSQL (prod) / SQLite (dev) · Vanilla JS PWA

---

## Local Setup (Fedora / macOS)

```bash
# 1. Clone your repo
git clone https://github.com/jaspervolf/GritTrack_RR.git
cd GritTrack_RR

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the dev server
FLASK_DEBUG=true python app.py
```

Open `http://localhost:5000` in your browser. SQLite database (`grittrack.db`) is created automatically.

---

## Git Setup

```bash
git init
git add .
git commit -m "Initial commit — GritTrack v1"

git remote add origin https://github.com/jaspervolf/GritTrack_RR.git
git branch -M main
git push -u origin main
```

---

## Deploy to Railway (Recommended)

Railway auto-deploys every push to your main branch. Free tier is plenty for personal use.

### First deploy

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project → Deploy from GitHub repo**
3. Select your `grittrack` repo
4. Railway detects Python + Procfile automatically — click **Deploy**

### Add PostgreSQL (required for data persistence)

1. In your Railway project, click **+ New → Database → PostgreSQL**
2. Railway automatically sets `DATABASE_URL` in your app's environment — nothing else needed
3. Redeploy (or it picks up on next push)

### Set your secret key

1. Go to your app service → **Variables** tab
2. Add: `SECRET_KEY` = a long random string (use `python3 -c "import secrets; print(secrets.token_hex(32))"`)
3. Railway redeploys automatically

Your app is now live at `https://YOUR-APP.up.railway.app`

---

## Deploy to Render (Alternative)

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Set **Build Command:** `pip install -r requirements.txt`
4. Set **Start Command:** `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`
5. Add a **PostgreSQL** database service, copy the Internal Database URL
6. Add environment variable: `DATABASE_URL` = (paste the URL)
7. Add environment variable: `SECRET_KEY` = (your random string)
8. Click **Create Web Service**

---

## Install as iPhone / iPad App

1. Open your Railway URL in **Safari** (must be Safari)
2. Tap the **Share** button (box with arrow)
3. Tap **Add to Home Screen**
4. Tap **Add** — GritTrack now lives on your home screen like a native app

For the custom icon, add two PNG files to the `static/` folder:
- `static/icon-192.png` — 192×192px
- `static/icon-512.png` — 512×512px

A simple dark background with "GT" in flame orange works great. Free tools like [favicon.io](https://favicon.io) or Figma can generate these.

---

## Environment Variables

| Variable       | Required | Description                                      |
|----------------|----------|--------------------------------------------------|
| `SECRET_KEY`   | Yes      | Random string for session signing. Change this.  |
| `DATABASE_URL` | Prod only| Set automatically by Railway/Render PostgreSQL.  |
| `FLASK_DEBUG`  | Dev only | Set to `true` for hot reload during development. |

---

## Project Structure

```
grittrack/
├── app.py              # Flask app — models, auth API, sessions API
├── requirements.txt
├── Procfile            # For Railway / Render
├── .gitignore
├── static/
│   ├── manifest.json   # PWA manifest
│   ├── sw.js           # Service worker (offline support)
│   ├── icon-192.png    # Add this — PWA icon
│   └── icon-512.png    # Add this — PWA icon
└── templates/
    ├── auth.html       # Login / Register page
    └── app.html        # Main GritTrack app
```

---

## Roadmap Ideas

- Personal stats / progress charts
- Body weight tracking
- Workout templates / programs
- Rest day / workout streak tracking
- Export to CSV
- Admin view (see all users' aggregate stats, no personal data)
