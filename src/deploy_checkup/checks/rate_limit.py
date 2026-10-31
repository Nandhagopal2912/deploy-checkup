import httpx

from deploy_checkup.models import Finding, Level, could_not_finish

CHECK = "rate_limit"
MAX_REQUESTS = 60  # never send more than this to find the limit
FAKE_IP = "203.0.113.7"  # TEST-NET-3: reserved for documentation, never a real visitor


def check_rate_limit(client: httpx.Client, url: str, path: str) -> list[Finding]:
    """Hit the rate limit, then pretend to be someone else with a fake X-Forwarded-For.

    If the fake header gets through while a normal request is still blocked, anyone
    can bypass the limit by writing a new fake IP into every request.
    """
    target = httpx.URL(url).join(path)
    try:
        for sent in range(1, MAX_REQUESTS + 1):
            if client.get(target).status_code == 429:
                break
        else:
            return [_no_limit_found(target.path)]

        spoofed = client.get(target, headers={"X-Forwarded-For": FAKE_IP})
        again = client.get(target)
    except httpx.RequestError as error:
        return [could_not_finish(CHECK, error)]

    if spoofed.status_code == 429:
        return [
            Finding(
                check=CHECK,
                level=Level.PASS,
                title=(
                    f"Rate limit on {target.path} can't be bypassed with a fake "
                    f"X-Forwarded-For (limited after {sent} requests)"
                ),
            )
        ]
    if again.status_code == 429:
        return [_bypassable(target.path)]
    return [_inconclusive(target.path)]


def _bypassable(path: str) -> Finding:
    return Finding(
        check=CHECK,
        level=Level.FAIL,
        title=f"Rate limit on {path} can be bypassed with a fake X-Forwarded-For",
        why=(
            "Anyone can send unlimited requests by writing a different fake IP into each one, "
            "so the limit doesn't protect you from abuse or from surprise bills."
        ),
        fix=(
            "Read the visitor's IP from the right of X-Forwarded-For, skipping exactly as many "
            "entries as your host's proxies add. Never trust the first entry: the visitor wrote it."
        ),
        render_fix=(
            "On Render a request passes Cloudflare, Render's load balancer and an internal proxy, "
            "so the visitor is 3rd from the right of X-Forwarded-For (measured October 2026). "
            "Take that entry, never the first one."
        ),
    )


def _no_limit_found(path: str) -> Finding:
    return Finding(
        check=CHECK,
        level=Level.INFO,
        title=f"No rate limit hit on {path} after {MAX_REQUESTS} requests",
        why="Either there's no limit, or it's higher than this test goes.",
        fix=(
            "If this endpoint does real work, such as sending email or calling a paid API, "
            "add a per-visitor rate limit. Use --rate-limit-path to test a limited endpoint."
        ),
    )


def _inconclusive(path: str) -> Finding:
    return Finding(
        check=CHECK,
        level=Level.WARNING,
        title=f"Couldn't tell whether the rate limit on {path} can be bypassed",
        why="The limit reset during the test, so the fake X-Forwarded-For result doesn't prove anything.",
        fix="Run the test again in a minute.",
    )


def skipped() -> Finding:
    return Finding(
        check=CHECK,
        level=Level.INFO,
        title="Rate limit test skipped (needs your permission)",
        why="It sends a burst of requests and fake headers, which only the site's owner should do.",
        fix="Run again and answer yes, or pass --yes-i-own-it together with --active.",
    )