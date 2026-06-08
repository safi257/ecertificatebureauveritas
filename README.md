# CertVerify — Digital Certificate Verification System

A Bureau Veritas-style certificate verification platform.

## Quick Start (Local)

```bash
pip install flask gunicorn
python app.py
# Admin:  http://localhost:5000/admin
# Dashboard: http://localhost:5000/dashboard
```

## Deploy to Railway

1. Push this folder to a GitHub repo.
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo.
3. Select your repo. Railway auto-detects Python.
4. Set these environment variables in Railway dashboard:
   - `SECRET_KEY` — any random secret string
   - `ADMIN_USERNAME` — your admin login
   - `ADMIN_PASSWORD` — your admin password
5. Deploy. Your app gets a public URL automatically.

> **Note on the database:** Railway's filesystem is ephemeral. For persistent storage, attach a Railway PostgreSQL plugin or use an external DB. See the README section below.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `certsys-secret-2026-xK9mP3qL` | Flask session secret |
| `ADMIN_USERNAME` | `admin` | Admin login username |
| `ADMIN_PASSWORD` | `CertAdmin2026!` | Admin login password |
| `DB_PATH` | `certificates.db` | SQLite DB path |
| `PORT` | set by Railway | Port (auto-set by Railway) |

## Form Fields

All fields are **required** — the form blocks submission if any field is empty:

- **Deliverable ID** — shown as "Deliverable Id" on the certificate
- **ID / Barcode** — shown as "ID" on the certificate  
- **Person Name**, **Company**
- **Certificate Type**, **Model**
- **Issue Date**, **Expiry Date**
- **Training Location**, **Trainer**

## Routes

| Route | Access | Description |
|---|---|---|
| `/admin` | Protected | Issue certificate form |
| `/submit` | Protected POST | Process form |
| `/dashboard` | Protected | Manage all certificates |
| `/certificate/<uuid>` | Public | Certificate verification page |
| `/api/verify/<uuid>` | Public | JSON API |
