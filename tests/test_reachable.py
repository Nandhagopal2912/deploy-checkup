import httpx

from deploy_checkup.checks.reachable import check_reachable
from deploy_checkup.models import Level


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_ok_response_passes():
    client = make_client(lambda request: httpx.Response(200))

    findings = check_reachable(client, "https://example.com")

    assert len(findings) == 1
    assert findings[0].level == Level.PASS
    assert "200" in findings[0].title


def test_server_error_fails():
    client = make_client(lambda request: httpx.Response(503))

    findings = check_reachable(client, "https://example.com")

    assert findings[0].level == Level.FAIL
    assert "503" in findings[0].title
    assert findings[0].fix != ""


def test_client_error_warns():
    client = make_client(lambda request: httpx.Response(404))

    findings = check_reachable(client, "https://example.com")

    assert findings[0].level == Level.WARNING
    assert "404" in findings[0].title


def test_connection_error_fails():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = make_client(handler)

    findings = check_reachable(client, "https://example.com")

    assert findings[0].level == Level.FAIL
    assert findings[0].fix != ""