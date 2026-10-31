import httpx

from deploy_checkup.models import Finding, Level

CHECK = "https"
PERMANENT_REDIRECTS = (301, 308)


def check_https(client: httpx.Client, url: str) -> list[Finding]:
    """Check that the plain http:// address sends visitors to https://."""
    http_url = httpx.URL(url).copy_with(scheme="http")

    try:
        response = client.get(http_url, follow_redirects=True)
    except httpx.RequestError:
        if not _answers(client, url):
            return []  # the whole site is down; the reachable or health check says so
        return [
            Finding(
                check=CHECK,
                level=Level.INFO,
                title="Plain HTTP isn't served at all",
                why="Nothing can be sent unencrypted, because the http:// address doesn't answer.",
            )
        ]

    if response.url.scheme == "http":
        return [
            Finding(
                check=CHECK,
                level=Level.FAIL,
                title="Your site is served over plain HTTP",
                why=(
                    "Visitors who type your address without https:// get an unencrypted page. "
                    "Anyone on the same Wi-Fi can read or change what they see and send."
                ),
                fix=(
                    "Turn on your host's 'redirect HTTP to HTTPS' setting, or redirect in "
                    "your app, and make sure your domain has a TLS certificate."
                ),
                render_fix=(
                    "Render redirects to HTTPS automatically on its own addresses. If you use a "
                    "custom domain, check it shows as Verified with a certificate under "
                    "Settings > Custom Domains."
                ),
            )
        ]

    first_hop = response.history[0].status_code
    if first_hop in PERMANENT_REDIRECTS:
        return [
            Finding(
                check=CHECK,
                level=Level.PASS,
                title=f"Plain HTTP redirects to HTTPS ({first_hop})",
            )
        ]

    return [
        Finding(
            check=CHECK,
            level=Level.WARNING,
            title=f"Plain HTTP redirects to HTTPS, but only temporarily ({first_hop})",
            why=(
                "Browsers don't remember a temporary redirect, so every visit still starts "
                "with an unencrypted request."
            ),
            fix="Make the redirect permanent: use status 301 or 308 instead of 302 or 307.",
        )
    ]


def _answers(client: httpx.Client, url: str) -> bool:
    """True if the site answers at all on its normal address."""
    try:
        client.get(url)
    except httpx.RequestError:
        return False
    return True