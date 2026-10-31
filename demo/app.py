"""A deliberately broken app for testing deploy-checkup.

Every setting marked FLAW is wrong on purpose. Do not copy them into a real app.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

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