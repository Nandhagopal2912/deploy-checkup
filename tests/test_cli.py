from importlib.metadata import version

import httpx
import pytest

from deploy_checkup.cli import main

SAFE_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
}


def healthy_site(request):
    if request.url.scheme == "http":
        return httpx.Response(301, headers={"Location": str(request.url.copy_with(scheme="https"))})
    return httpx.Response(200, headers=SAFE_HEADERS)


def fake_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_healthy_site_reports_both_addresses_and_exits_0(capsys):
    exit_code = main(
        ["https://example.com", "--api", "https://api.example.com"],
        client=fake_client(healthy_site),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "https://example.com" in output
    assert "https://api.example.com" in output
    assert "FAIL" not in output


def test_broken_site_exits_1(capsys):
    exit_code = main(["https://example.com"], client=fake_client(lambda request: httpx.Response(500)))

    assert exit_code == 1
    assert "FAIL" in capsys.readouterr().out


def test_missing_url_exits_with_code_2():
    with pytest.raises(SystemExit) as exc:
        main([])

    assert exc.value.code == 2


def test_version_prints_installed_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 0
    assert version("deploy-checkup") in capsys.readouterr().out