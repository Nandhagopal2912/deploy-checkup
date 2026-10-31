from importlib.metadata import version
import json
import httpx
import pytest
from deploy_checkup.cli import _ask_on_stderr, main

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
    
def test_probing_is_skipped_without_permission(capsys):
    main(["https://example.com"], client=fake_client(healthy_site), ask=lambda prompt: "n")

    assert "skipped" in capsys.readouterr().out


def test_answering_yes_runs_probing(capsys):
    main(["https://example.com"], client=fake_client(healthy_site), ask=lambda prompt: "yes")

    assert "/.env is not exposed" in capsys.readouterr().out


def test_flag_runs_probing_without_asking(capsys):
    def never_ask(prompt):
        raise AssertionError("should not ask when --yes-i-own-it is given")

    main(["https://example.com", "--yes-i-own-it"], client=fake_client(healthy_site), ask=never_ask)

    assert "/.env is not exposed" in capsys.readouterr().out


def test_no_answer_at_all_counts_as_no(capsys):
    def input_ran_out(prompt):
        raise EOFError

    main(["https://example.com"], client=fake_client(healthy_site), ask=input_ran_out)

    assert "skipped" in capsys.readouterr().out

def test_json_output_is_valid_json_with_the_same_exit_code(capsys):
    exit_code = main(
        ["https://example.com", "--json"],
        client=fake_client(lambda request: httpx.Response(500)),
        ask=lambda prompt: "n",
    )

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert report["summary"]["fail"] >= 1


def test_permission_question_goes_to_stderr(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "y")

    answer = _ask_on_stderr("Own it? ")

    captured = capsys.readouterr()
    assert answer == "y"
    assert captured.err == "Own it? "
    assert captured.out == ""