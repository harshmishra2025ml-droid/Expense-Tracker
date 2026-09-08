# Expense Tracker — Cloud Deployment Package

This package keeps the existing FastAPI + Streamlit architecture but makes it cloud-ready.

## Recommended deployment

- **Backend:** Render Web Service
- **Frontend:** Streamlit Community Cloud
- **Source control:** GitHub

No terminal is needed after the initial GitHub upload. Future pushes to GitHub can trigger automatic redeploys.

## 1. Deploy the backend on Render

Create a GitHub repository containing this folder, then in Render create a Web Service from that repository.

Use:

- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn backend:api --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Set these environment variables:

- `JWT_SECRET_KEY` — use a long random value. Render can generate one.
- `FRONTEND_ORIGIN` — after the Streamlit app is created, set this to its full URL, e.g. `https://your-app.streamlit.app`

The backend will receive a public URL such as `https://expense-tracker-api.onrender.com`.

### Database note

The default cloud package still uses SQLite so the first deployment is simple. Render Free web services have an ephemeral filesystem, so SQLite data can disappear after a restart/spin-down/redeploy. For a real persistent deployment, set `DATABASE_URL` to a PostgreSQL connection string instead. The code already supports PostgreSQL through `psycopg`.

## 2. Deploy the frontend on Streamlit Community Cloud

Create/deploy the Streamlit app from GitHub and choose `ui.py` as the entrypoint.

In Streamlit's Advanced settings → Secrets, add:

```toml
API_URL = "https://YOUR-BACKEND.onrender.com"
```

Replace the URL with the actual Render backend URL.

## 3. Test

Open the Streamlit URL and register a test account. The UI should call the Render FastAPI backend over HTTPS.

You can also test the backend directly:

- `/health`
- `/docs`

## Local use

The original local launcher is still included:

```text
start_expense_tracker.bat
```

## Security

Do not commit passwords, JWT secrets, database passwords, or `.streamlit/secrets.toml` to GitHub.
