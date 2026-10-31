import json

from deploy_checkup.models import Finding, Level
from deploy_checkup.report import count_levels, to_json

RESULTS = {
    "https://app.example.com": [
        Finding(check="https", level=Level.PASS, title="Plain HTTP redirects to HTTPS (301)"),
        Finding(
            check="headers",
            level=Level.WARNING,
            title="Content-Security-Policy is missing",
            why="Scripts could be injected.",
            fix="Send a policy.",
            render_fix="Render-only text",
        ),
    ],
    "https://api.example.com": [
        Finding(check="cors", level=Level.FAIL, title="API lets any website read it"),
    ],
}


def test_count_levels_covers_every_level():
    counts = count_levels(RESULTS)

    assert counts == {Level.PASS: 1, Level.WARNING: 1, Level.FAIL: 1, Level.INFO: 0}


def test_json_has_targets_findings_and_summary():
    report = json.loads(to_json(RESULTS))

    assert report["tool"] == "deploy-checkup"
    assert [t["url"] for t in report["targets"]] == [
        "https://app.example.com",
        "https://api.example.com",
    ]
    warning = report["targets"][0]["findings"][1]
    assert warning == {
        "check": "headers",
        "level": "warning",
        "title": "Content-Security-Policy is missing",
        "why": "Scripts could be injected.",
        "fix": "Send a policy.",
    }
    assert report["summary"] == {"pass": 1, "warning": 1, "fail": 1, "info": 0}