import httpx

from deploy_checkup.checks.health import ATTEMPTS, _latency, check_health
from deploy_checkup.models import Level

API = "https://api.example.com/api/notes"


def check(handler, path="/health"):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return check_health(client, API, path)


def test_healthy_endpoint_reports_latency():
    findings = check(lambda request: httpx.Response(200))

    assert findings[0].level == Level.PASS
    assert "ms" in findings[0].title


def test_calls_health_path_at_the_root_a_few_times():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200)

    check(handler)

    assert seen == ["https://api.example.com/health"] * ATTEMPTS


def test_custom_health_path_is_used():
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return httpx.Response(200)

    check(handler, path="/api/healthz")

    assert seen[0] == "/api/healthz"


def test_missing_endpoint_warns_and_stops():
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return httpx.Response(404)

    findings = check(handler)

    assert findings[0].level == Level.WARNING
    assert "/health" in findings[0].fix
    assert len(seen) == 1


def test_failing_endpoint_fails():
    findings = check(lambda request: httpx.Response(503))

    assert findings[0].level == Level.FAIL
    assert "503" in findings[0].title


def test_fast_times_pass():
    finding = _latency([120.0, 95.0, 110.0])

    assert finding.level == Level.PASS
    assert "110 ms" in finding.title


def test_one_slow_outlier_doesnt_matter():
    finding = _latency([4000.0, 100.0, 120.0])

    assert finding.level == Level.PASS


def test_slow_times_warn():
    finding = _latency([1500.0, 1800.0, 1600.0])

    assert finding.level == Level.WARNING