from dataclasses import replace

import httpx

from deploy_checkup.models import Finding

RENDER = "Render"
UNKNOWN = "unknown host"


def detect_host(client: httpx.Client, url: str) -> str:
    """Guess where the site is hosted from the headers its responses carry."""
    try:
        response = client.get(url)
    except httpx.RequestError:
        return UNKNOWN

    if "x-render-origin-server" in response.headers:
        return RENDER
    return UNKNOWN


def fixes_for_host(findings: list[Finding], host: str) -> list[Finding]:
    """On Render, swap in the Render-specific fix wherever a check wrote one."""
    if host != RENDER:
        return findings
    return [replace(f, fix=f.render_fix) if f.render_fix else f for f in findings]