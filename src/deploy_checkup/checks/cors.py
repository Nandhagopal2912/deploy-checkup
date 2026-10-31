import httpx

from deploy_checkup.models import Finding, Level

CHECK = "cors"
MADE_UP_SITE = "https://deploy-checkup-test.invalid"  # .invalid can never be a real website


def check_cors(client: httpx.Client, api_url: str, frontend_url: str) -> list[Finding]:
    """Ask the API as your frontend, then as a made-up site, and compare the answers."""
    frontend = _origin(frontend_url)
    try:
        as_frontend = client.get(api_url, headers={"Origin": frontend})
        as_stranger = client.get(api_url, headers={"Origin": MADE_UP_SITE})
    except httpx.RequestError:
        return []  # the other checks already report connection problems

    return [
        _check_own_frontend(as_frontend, frontend),
        _check_other_sites(as_stranger),
    ]


def _origin(url: str) -> str:
    """The part of a URL a browser sends as Origin: scheme, host and (if unusual) port."""
    parsed = httpx.URL(url)
    origin = f"{parsed.scheme}://{parsed.host}"
    if parsed.port is not None:
        origin += f":{parsed.port}"
    return origin


def _check_own_frontend(response: httpx.Response, frontend: str) -> Finding:
    allowed = response.headers.get("access-control-allow-origin")
    if allowed in (frontend, "*"):
        return Finding(check=CHECK, level=Level.PASS, title=f"API allows your frontend ({frontend})")

    return Finding(
        check=CHECK,
        level=Level.WARNING,
        title=f"API doesn't allow your frontend ({frontend})",
        why=(
            "Browsers will block your frontend from reading the API's answers, "
            "so pages that load data will break."
        ),
        fix=(
            f"Add {frontend} to your API's allowed origins (often set through an "
            "environment variable), then redeploy."
        ),
        render_fix=(
            f"Add {frontend} to your API's allowed origins, for example through an "
            "environment variable in the Render dashboard, then redeploy."
        ),
    )


def _check_other_sites(response: httpx.Response) -> Finding:
    allowed = response.headers.get("access-control-allow-origin")
    with_cookies = response.headers.get("access-control-allow-credentials", "").lower() == "true"

    if allowed is None:
        return Finding(check=CHECK, level=Level.PASS, title="API blocks other websites")

    if allowed == MADE_UP_SITE and with_cookies:
        return Finding(
            check=CHECK,
            level=Level.FAIL,
            title="API lets any website read it with your visitors' cookies",
            why=(
                "A stranger's site can call your API from a logged-in visitor's browser "
                "and read their private data."
            ),
            fix=(
                "List your real frontend address as the only allowed origin. "
                "Never combine 'allow every origin' with allow_credentials."
            ),
        )

    return Finding(
        check=CHECK,
        level=Level.WARNING,
        title=f"API accepts requests from any website (Access-Control-Allow-Origin: {allowed})",
        why="Any site can read your API's answers. That's fine for public data, risky for anything else.",
        fix="If the API isn't meant to be public, allow only your frontend's address.",
    )