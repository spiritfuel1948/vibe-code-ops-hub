# Vibe Code Ops Hub

Shared ops hub for your faceless content team: time blocks, daily tracker, video log, hook bank, analytics, accountability, pipeline, and more.

## Let your partners access it on the web

1. **Push this app to GitHub** (if you haven’t already):
   ```bash
   cd social_media_ops_hub
   git add .
   git commit -m "Deploy ops hub for partners"
   git push origin main
   ```

2. **Deploy on Render (free tier)**
   - Go to [render.com](https://render.com) and sign in (or create an account).
   - **New** → **Blueprint** and connect your GitHub repo, or **New** → **Web Service** and connect the repo.
   - If you use **Blueprint**: add a `render.yaml` file (already in this repo) and Render will create the web service + database from it.
   - If you use **Web Service** manually:
     - Build: `pip install -r requirements.txt`
     - Start: `gunicorn --bind 0.0.0.0:$PORT app:app`
     - Add a **PostgreSQL** database (free) and set `DATABASE_URL` in the web service env (Render can link it automatically).
   - Deploy. After the first deploy, Render will give you a URL like:
     **`https://vibe-code-ops-hub.onrender.com`**

3. **Share with partners**
   - Send them the **live URL** (e.g. `https://vibe-code-ops-hub.onrender.com`).
   - If you turned on **Security** in Settings (app password), share that password so they can log in.
   - They use the same hub: Dashboard, Time Blocks, Daily Tracker, Video Log, Hook Bank, etc.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. Uses SQLite by default. For production (e.g. Render), set `DATABASE_URL` to a PostgreSQL connection string.

## Optional: login

In the app: **Settings** → **Security & Automation** → set an **App password** and save. After that, anyone visiting the URL must enter that password to use the hub. Share the password only with your partners.
