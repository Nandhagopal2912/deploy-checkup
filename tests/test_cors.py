import httpx

from deploy_checkup.checks.cors import MADE_UP_SITE, _origin, check_cors
from deploy_checkup.models import Level

API = "https://api.example.com"
FRONTEND = "https://app.example.com"


def api_allowing(*origins, credentials=False):
    """A fake API that allows only these origins, like a real CORS setup."""

    def handler(request):
        origin = request.headers.get("Origin")
        headers = {}
        if "*" in origins:
            headers["Access-Control-Allow-Origin"] = "*"
        elif origin in origins:
            headers["Access-Control-Allow-Origin"] = origin
            if credentials:
                headers["Access-Control-Allow-Credentials"] = "true"
        return httpx.Response(200, headers=headers)

    return handler


def own(findings):
    return next(f for f in findings if "your frontend" in f.title)


def others(findings):
    return next(f for f in findings if "your frontend" not in f.title)


def check(handler):
    return check_cors(httpx.Client(transport=httpx.MockTransport(handler)), API, FRONTEND)


def test_correct_setup_passes_both():
    findings = check(api_allowing(FRONTEND))

    assert own(findings).level == Level.PASS
    assert others(findings).level == Level.PASS


def test_frontend_missing_from_allowed_origins_warns():
    findings = check(api_allowing("https://old-frontend.example.com"))

    assert own(findings).level == Level.WARNING
    assert FRONTEND in own(findings).fix


def test_wildcard_warns():
    findings = check(api_allowing("*"))

    assert own(findings).level == Level.PASS
    assert others(findings).level == Level.WARNING


def test_reflecting_any_origin_with_cookies_fails():
    findings = check(api_allowing(FRONTEND, MADE_UP_SITE, credentials=True))

    assert others(findings).level == Level.FAIL


def test_sends_frontend_origin_then_made_up_origin():
    seen = []

    def handler(request):
        seen.append(request.headers.get("Origin"))
        return httpx.Response(200)

    check(handler)

    assert seen == [FRONTEND, MADE_UP_SITE]


def test_origin_drops_path_and_keeps_unusual_port():
    assert _origin("https://app.example.com/dashboard?x=1") == "https://app.example.com"
    assert _origin("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"