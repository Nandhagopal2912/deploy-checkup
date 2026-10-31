import httpx

from deploy_checkup.models import Finding, Level
from deploy_checkup.runner import USER_AGENT, exit_code, make_client, run_checks


def fake_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_api_is_only_checked_when_given():
    client = fake_client(lambda request: httpx.Response(200))

    assert list(run_checks(client, "https://example.com")) == ["https://example.com"]
    assert list(run_checks(client, "https://example.com", "https://api.example.com")) == [
        "https://example.com",
        "https://api.example.com",
    ]


def test_headers_check_runs_on_frontend_only():
    client = fake_client(lambda request: httpx.Response(200))

    results = run_checks(client, "https://example.com", "https://api.example.com")

    assert any(f.check == "headers" for f in results["https://example.com"])
    assert not any(f.check == "headers" for f in results["https://api.example.com"])


def test_exit_code_is_1_only_when_something_fails():
    passed = Finding(check="x", level=Level.PASS, title="ok")
    warned = Finding(check="x", level=Level.WARNING, title="hmm")
    failed = Finding(check="x", level=Level.FAIL, title="bad")

    assert exit_code({"a": [passed, warned]}) == 0
    assert exit_code({"a": [passed], "b": [failed]}) == 1


def test_client_sends_honest_user_agent():
    with make_client() as client:
        assert client.headers["User-Agent"] == USER_AGENT
    assert USER_AGENT.startswith("DeployCheckup/")