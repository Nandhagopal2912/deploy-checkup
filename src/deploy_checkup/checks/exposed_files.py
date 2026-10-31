import re

import httpx

from deploy_checkup.models import Finding, Level

CHECK = "exposed_files"


def _looks_like_env(body: str) -> bool:
    return re.search(r"^[A-Z][A-Z0-9_]*=", body, re.MULTILINE) is not None


def _looks_like_git_config(body: str) -> bool:
    return "[core]" in body


# Each path, and how to recognise the real file (so a friendly 200 page isn't a false alarm).
PATHS = {
    "/.env": _looks_like_env,
    "/.git/config": _looks_like_git_config,
}


def check_exposed_files(client: httpx.Client, url: str) -> list[Finding]:
    """Ask for a few files that should never be public, and check what comes back."""
    findings = []
    for path, looks_real in PATHS.items():
        try:
            response = client.get(httpx.URL(url).join(path))
        except httpx.RequestError:
            return []  # the other checks already report connection problems

        is_html = "text/html" in response.headers.get("content-type", "")
        if response.status_code == 200 and not is_html and looks_real(response.text):
            findings.append(_exposed(path))
        else:
            findings.append(Finding(check=CHECK, level=Level.PASS, title=f"{path} is not exposed"))
    return findings


def _exposed(path: str) -> Finding:
    return Finding(
        check=CHECK,
        level=Level.FAIL,
        title=f"{path} is publicly downloadable",
        why=(
            "Anyone can download this file. It usually holds passwords, API keys or "
            "your code's history, which attackers collect automatically."
        ),
        fix=(
            f"Stop serving {path} (don't copy it into your build or static folder), "
            "then change every secret it contained: assume they're already leaked."
        ),
    )


def skipped() -> Finding:
    return Finding(
        check=CHECK,
        level=Level.INFO,
        title="Exposed files check skipped (needs your permission)",
        why="It asks for files like /.env, which only the site's owner should do.",
        fix="Run again and answer yes, or pass --yes-i-own-it in CI.",
    )