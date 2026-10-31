"""A deliberately broken app for testing deploy-checkup.

Every setting marked FLAW is wrong on purpose. Do not copy them into a real app.
"""

import time
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

app = FastAPI()

# FLAW (cors): any website can call this API from a visitor's browser, with their cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FLAW (headers): no security headers are set anywhere.
# FLAW (health): there is no /health endpoint.


@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>Broken demo</h1><p>This app is misconfigured on purpose.</p>"


@app.get("/api/notes")
def notes():
    return [{"id": 1, "text": "hello"}]


# FLAW (exposed files): a .env file is served to anyone who asks.
@app.get("/.env", response_class=PlainTextResponse)
def leaked_env():
    return "DATABASE_URL=postgres://demo:not-a-real-password@localhost/demo\n"


LIMIT = 5  # requests per visitor
WINDOW_SECONDS = 60
recent_requests: dict[str, list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    # FLAW (rate limit): trusts the first X-Forwarded-For entry, which any visitor can write.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


@app.get("/api/limited")
def limited(request: Request):
    ip = client_ip(request)
    now = time.monotonic()
    recent = [t for t in recent_requests[ip] if now - t < WINDOW_SECONDS]
    if len(recent) >= LIMIT:
        recent_requests[ip] = recent
        return JSONResponse({"detail": "Too many requests"}, status_code=429)
    recent_requests[ip] = recent + [now]
    return {"ok": True}