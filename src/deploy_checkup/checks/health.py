from statistics import median
from time import perf_counter

import httpx

from deploy_checkup.checks.cold_start import check_cold_start
from deploy_checkup.models import Finding, Level

CHECK = "health"
ATTEMPTS = 3
SLOW_MS = 1000


def check_health(client: httpx.Client, api_url: str, path: str = "/health") -> list[Finding]:
    """Call the health path a few times: does it exist, and how fast does it answer?"""
    health_url = httpx.URL(api_url).join(path)
    times_ms = []

    for _ in range(ATTEMPTS):
        start = perf_counter()
        try:
            response = client.get(health_url)
        except httpx.RequestError:
            return [_unreachable(health_url)]
        elapsed_ms = (perf_counter() - start) * 1000

        if response.status_code == 404:
            return [_missing(health_url)]
        if response.status_code >= 400:
            return [_unhealthy(health_url, response.status_code)]

        times_ms.append(elapsed_ms)

    # The first request may include waking the server up, so judge speed on the rest.
    return [_latency(times_ms[1:]), check_cold_start(times_ms)]


def _unreachable(health_url: httpx.URL) -> Finding:
    return Finding(
        check=CHECK,
        level=Level.FAIL,
        title=f"Couldn't connect to the API at {health_url.host}",
        why="Your frontend can't load any data if the API doesn't answer.",
        fix="Check the --api address is right, then look at your API's deploy status and logs.",
        render_fix=(
            "Check the --api address is right, then open the API service in the Render "
            "dashboard and look at the Events and Logs tabs."
        ),
    )


def _missing(health_url: httpx.URL) -> Finding:
    return Finding(
        check=CHECK,
        level=Level.WARNING,
        title=f"No health endpoint found at {health_url.path}",
        why=(
            "Hosts use a health check to know when a new deploy is ready and "
            "to restart your app if it stops responding."
        ),
        fix=(
            f"Add a GET {health_url.path} route that returns 200 quickly, and point "
            "your host's health check at it."
        ),
        render_fix=(
            f"Add a GET {health_url.path} route that returns 200 quickly, then set it as "
            "the Health Check Path in the service's Settings on Render."
        ),
    )


def _unhealthy(health_url: httpx.URL, status: int) -> Finding:
    return Finding(
        check=CHECK,
        level=Level.FAIL,
        title=f"Health endpoint {health_url.path} answered with status {status}",
        why="Your app reports itself as broken, so your host may keep restarting it.",
        fix="Check your API's logs to see why the health route is failing.",
        render_fix="Open the service's Logs tab on Render to see why the health route is failing.",
    )


def _latency(times_ms: list[float]) -> Finding:
    """Judge already-measured response times. Kept separate so tests can pass in numbers."""
    typical = round(median(times_ms))
    if typical < SLOW_MS:
        return Finding(
            check=CHECK,
            level=Level.PASS,
            title=f"API answered in {typical} ms (median of {len(times_ms)})",
        )

    return Finding(
        check=CHECK,
        level=Level.WARNING,
        title=f"API is slow: {typical} ms (median of {len(times_ms)})",
        why="Every page that loads data waits this long, and visitors notice anything over a second.",
        fix=(
            "Look for slow database calls in the health route, and check whether the "
            "server is short of CPU or memory."
        ),
        render_fix=(
            "Check the Metrics tab on Render for CPU or memory limits, and look for "
            "slow database calls in the health route."
        ),
    )