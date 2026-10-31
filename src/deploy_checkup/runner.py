from importlib.metadata import version

import httpx

from deploy_checkup.checks.headers import check_headers
from deploy_checkup.checks.https import check_https
from deploy_checkup.checks.reachable import check_reachable
from deploy_checkup.models import Finding, Level

USER_AGENT = f"DeployCheckup/{version('deploy-checkup')}"
TIMEOUT = httpx.Timeout(60.0)  # Render's free tier can take ~50 s to wake up


def make_client() -> httpx.Client:
    """A polite client: honest User-Agent and a time limit on every request."""
    return httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})


def run_checks(
    client: httpx.Client, url: str, api_url: str | None = None
) -> dict[str, list[Finding]]:
    """Run every check and group the findings by the address they're about."""
    results = {
        url: check_reachable(client, url) + check_https(client, url) + check_headers(client, url)
    }
    if api_url:
        # An API's home page is often a 404 on purpose; Phase 2's health check covers it.
        results[api_url] = check_https(client, api_url)
    return results


def exit_code(results: dict[str, list[Finding]]) -> int:
    """1 if anything failed, otherwise 0, so CI can stop a broken deploy."""
    for findings in results.values():
        if any(finding.level == Level.FAIL for finding in findings):
            return 1
    return 0