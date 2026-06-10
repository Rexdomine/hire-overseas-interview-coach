# Hire Overseas Interview Coach

Mini web app for Rex's real-world implementation assessment.

## Architecture

Vercel frontend -> /api/coach Vercel proxy -> VPS FastAPI backend -> Hermes/Groot AI Brain prompt via OpenRouter -> structured interview guide JSON.

## Local backend

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Backend health: `curl http://127.0.0.1:8791/health`

## Vercel env

- `HERMES_BRAIN_URL`: public VPS backend URL, e.g. `http://<vps-ip>:8791`
- `HERMES_BRAIN_TOKEN`: shared secret token from backend `.env`

No login required. Do not paste secrets into the UI.
