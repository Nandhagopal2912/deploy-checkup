import httpx

from deploy_checkup.checks.exposed_files import PATHS, check_exposed_files
from deploy_checkup.models import Level

URL = "https://example.com"


def site(files):
    """A fake site that serves these paths as plain text and 404s everything else."""

    def handler(request):
        if request.url.path in files:
            return httpx.Response(200, text=files[request.url.path])
        return httpx.Response(404)

    return handler


def check(handler):
    return check_exposed_files(httpx.Client(transport=httpx.MockTransport(handler)), URL)


def find(findings, path):
    return next(f for f in findings if f.title.startswith(path + " "))


def test_nothing_exposed_passes():
    findings = check(site({}))

    assert len(findings) == len(PATHS)
    assert all(f.level == Level.PASS for f in findings)


def test_exposed_env_fails():
    findings = check(site({"/.env": "SECRET_KEY=abc123\n"}))

    assert find(findings, "/.env").level == Level.FAIL


def test_exposed_git_config_fails():
    findings = check(site({"/.git/config": "[core]\n\trepositoryformatversion = 0\n"}))

    assert find(findings, "/.git/config").level == Level.FAIL


def test_friendly_html_page_for_every_path_is_not_a_false_alarm():
    def handler(request):
        return httpx.Response(200, html="<html><body>SECRET=not really</body></html>")

    findings = check(handler)

    assert all(f.level == Level.PASS for f in findings)


def test_secret_values_are_never_shown():
    findings = check(site({"/.env": "SECRET_KEY=abc123\n"}))

    for finding in findings:
        assert "abc123" not in finding.title + finding.why + finding.fix