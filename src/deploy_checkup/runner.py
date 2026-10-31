from importlib.metadata import version

import httpx

from deploy_checkup.checks import exposed_files
from deploy_checkup.checks.cors import check_cors
from deploy_checkup.checks.headers import check_headers
from deploy_checkup.checks.health import check_health
from deploy_checkup.checks.https import check_https
from deploy_checkup.checks.reachable import check_reachable
from deploy_checkup.hosts import detect_host, fixes_for_host
from deploy_checkup.models import Finding, Level

USER_AGENT = f"DeployCheckup/{version('deploy-checkup')}"
TIMEOUT = httpx.Timeout(60.0)  # Render's free tier can take ~50 s to wake up


def make_client() -> httpx.Client:
    """A polite client: honest User-Agent and a time limit on every request."""
    return httpx.Client(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})


def run_checks(
    client: httpx.Client,
    url: str,
    api_url: str | None = None,
    health_path: str = "/health",
    probe: bool = False,
) -> dict[str, list[Finding]]:
    """Run every check and group the findings by the address they're about.

    probe=True also runs the probing checks, which only the site's owner should run.
    """
    frontend = check_reachable(client, url) + check_https(client, url) + check_headers(client, url)
    if probe:
        frontend += exposed_files.check_exposed_files(client, url)
    else:
        frontend.append(exposed_files.skipped())
    results = {url: fixes_for_host(frontend, detect_host(client, url))}

    if api_url and api_url != url:
        # Health goes first: its first request is the one that can catch a cold start.
        api = (
            check_health(client, api_url, health_path)
            + check_https(client, api_url)
            + check_cors(client, api_url, url)
        )
        if probe:
            api += exposed_files.check_exposed_files(client, api_url)
        results[api_url] = fixes_for_host(api, detect_host(client, api_url))

    return results


def exit_code(results: dict[str, list[Finding]]) -> int:
    """1 if anything failed, otherwise 0, so CI can stop a broken deploy."""
    for findings in results.values():
        if any(finding.level == Level.FAIL for finding in findings):
            return 1
    return 0