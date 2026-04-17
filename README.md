# Zumba Classes Website

A cloud-ready Zumba class website built with Python, Flask, SQLite, and APScheduler.

## Features

- Landing page with class schedule and booking form
- SQLite-backed booking capture
- Automation dashboard for recent bookings and scheduled job activity
- Background automation jobs for lead follow-up and schedule digests
- Deployment files for Render, Docker, and Gunicorn

## Run locally

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Automation flow

- `Lead Follow-up`: checks for fresh bookings and marks them as queued for callback.
- `Schedule Digest`: records the latest studio schedule every 6 hours for internal use.

## Cloud deployment

### Render

1. Push this folder to GitHub.
2. Create a new Web Service on Render.
3. Point Render at the repo and let it detect `render.yaml`.
4. Set any custom environment variables you want in the Render dashboard.

Important:

- Render deploys Python web services from a Git repo, so GitHub, GitLab, or Bitbucket is required.
- Render's filesystem is ephemeral by default, so SQLite data can reset on redeploy unless you attach a persistent disk or move to a managed database.
- If you keep SQLite on Render, set `DATABASE_PATH` to a persistent mount path when you add a disk.

### Docker

```powershell
docker build -t zumba-site .
docker run -p 5000:5000 zumba-site
```
