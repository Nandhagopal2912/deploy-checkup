import httpx

from deploy_checkup.checks.headers import check_headers
from deploy_checkup.models import Level

URL = "https://example.com"


def run_with_headers(headers):
    """Run the check against a fake server that sends these headers."""
    transport = httpx.MockTransport(lambda request: httpx.Response(200, headers=headers))
    return check_headers(httpx.Client(transport=transport), URL)


def find(findings, header):
    return next(f for f in findings if f.title.startswith(header))


def test_hsts_one_year_passes():
    findings = run_with_headers({"Strict-Transport-Security": "max-age=31536000; includeSubDomains"})

    assert find(findings, "Strict-Transport-Security").level == Level.PASS


def test_hsts_missing_warns():
    findings = run_with_headers({})

    assert find(findings, "Strict-Transport-Security").level == Level.WARNING


def test_hsts_too_short_warns():
    findings = run_with_headers({"Strict-Transport-Security": "max-age=300"})

    assert find(findings, "Strict-Transport-Security").level == Level.WARNING


def test_hsts_garbled_value_warns():
    findings = run_with_headers({"Strict-Transport-Security": "max-age=soon"})

    assert find(findings, "Strict-Transport-Security").level == Level.WARNING


def test_nosniff_passes_in_any_case():
    findings = run_with_headers({"X-Content-Type-Options": "NoSniff"})

    assert find(findings, "X-Content-Type-Options").level == Level.PASS


def test_nosniff_missing_warns():
    findings = run_with_headers({})

    assert find(findings, "X-Content-Type-Options").level == Level.WARNING


def test_connection_error_returns_nothing():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    findings = check_headers(httpx.Client(transport=httpx.MockTransport(handler)), URL)

    assert findings == []