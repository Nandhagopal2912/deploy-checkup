import httpx

from deploy_checkup.checks.https import check_https
from deploy_checkup.models import Level

URL = "https://example.com"


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def redirect_to_https(status):
    """A fake server that answers http:// with a redirect and https:// with 200."""

    def handler(request):
        if request.url.scheme == "http":
            return httpx.Response(status, headers={"Location": "https://example.com/"})
        return httpx.Response(200)

    return handler


def test_permanent_redirect_passes():
    client = make_client(redirect_to_https(301))

    findings = check_https(client, URL)

    assert findings[0].level == Level.PASS


def test_temporary_redirect_warns():
    client = make_client(redirect_to_https(302))

    findings = check_https(client, URL)

    assert findings[0].level == Level.WARNING
    assert "302" in findings[0].title


def test_plain_http_served_fails():
    client = make_client(lambda request: httpx.Response(200))

    findings = check_https(client, URL)

    assert findings[0].level == Level.FAIL
    assert findings[0].fix != ""


def test_http_not_served_is_info():
    def handler(request):
        if request.url.scheme == "http":
            raise httpx.ConnectError("connection refused", request=request)
        return httpx.Response(200)

    client = make_client(handler)

    findings = check_https(client, URL)

    assert findings[0].level == Level.INFO


def test_site_completely_down_reports_nothing():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    findings = check_https(make_client(handler), URL)

    assert findings == []

def test_requests_the_http_address():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200)

    check_https(make_client(handler), URL)

    assert seen[0] == "http://example.com"