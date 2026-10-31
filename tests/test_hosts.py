import httpx

from deploy_checkup.hosts import RENDER, UNKNOWN, detect_host, fixes_for_host
from deploy_checkup.models import Finding, Level

URL = "https://example.com"


def client_with_headers(headers):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, headers=headers))
    return httpx.Client(transport=transport)


def test_render_is_detected_from_its_header():
    client = client_with_headers({"x-render-origin-server": "uvicorn"})

    assert detect_host(client, URL) == RENDER


def test_other_hosts_are_unknown():
    client = client_with_headers({"server": "nginx"})

    assert detect_host(client, URL) == UNKNOWN


def test_unreachable_site_is_unknown():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))

    assert detect_host(client, URL) == UNKNOWN


FINDING = Finding(
    check="x",
    level=Level.FAIL,
    title="broken",
    fix="Check your logs.",
    render_fix="Open the Logs tab on Render.",
)


def test_render_gets_the_render_fix():
    [finding] = fixes_for_host([FINDING], RENDER)

    assert finding.fix == "Open the Logs tab on Render."


def test_other_hosts_keep_the_general_fix():
    [finding] = fixes_for_host([FINDING], UNKNOWN)

    assert finding.fix == "Check your logs."


def test_finding_without_render_fix_keeps_its_fix_on_render():
    general_only = Finding(check="x", level=Level.FAIL, title="broken", fix="Use 301.")

    [finding] = fixes_for_host([general_only], RENDER)

    assert finding.fix == "Use 301."