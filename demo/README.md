# Broken demo app

A small FastAPI app that is **misconfigured on purpose**, so deploy-checkup has something to catch. Every planted problem is marked `FLAW` in [app.py](app.py). Do not copy its settings into a real app.

| Flaw | What's wrong | Caught by |
|---|---|---|
| CORS | Any website can call the API from a visitor's browser, with their cookies | cors check: FAIL "API lets any website read it with your visitors' cookies" |
| Headers | No security headers at all | headers check |
| Exposed files | `/.env` is served to anyone (with a fake password) | exposed_files check: FAIL "/.env is publicly downloadable" (answer yes to the prompt) |
| Rate limit | `/api/limited` allows 5 requests a minute, but trusts the first `X-Forwarded-For` entry | rate_limit check: FAIL "Rate limit on /api/limited can be bypassed with a fake X-Forwarded-For" (`--active --rate-limit-path /api/limited`, answer yes) |
| Health | No `/health` endpoint | health check: WARNING "No health endpoint found at /health" |

## Run it locally

From the repository root, with the project's virtual environment active:

```bash
pip install -r demo/requirements.txt
cd demo
uvicorn app:app --port 8000
```

Then, in a second terminal:

```bash
deploy-checkup http://127.0.0.1:8000 --api http://127.0.0.1:8000/api/notes
```

Locally the HTTPS check also fails, because uvicorn serves plain HTTP. Deployed on Render, the platform adds the HTTPS redirect. On Render's free tier, the first run after 15 idle minutes also shows the cold start hint.

## Deploy on Render

Create a Web Service from this repository with:

- **Root Directory:** `demo`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
