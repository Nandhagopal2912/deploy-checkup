from collections import defaultdict

import httpx

from deploy_checkup.checks.rate_limit import FAKE_IP, MAX_REQUESTS, check_rate_limit
from deploy_checkup.models import Level

URL = "https://api.example.com"
LIMIT = 5


def limiter(trusts_first_entry):
    """A fake API with a 5-request limit per visitor.

    trusts_first_entry=True copies the bug: it believes the first X-Forwarded-For entry.
    """
    hits = defaultdict(int)

    def handler(request):
        forwarded = request.headers.get("x-forwarded-for")
        visitor = forwarded.split(",")[0] if trusts_first_entry and forwarded else "real-visitor"
        hits[visitor] += 1
        return httpx.Response(429 if hits[visitor] > LIMIT else 200)

    return handler


def check(handler):
    return check_rate_limit(httpx.Client(transport=httpx.MockTransport(handler)), URL, "/health")


def test_limit_that_trusts_the_first_entry_fails():
    [finding] = check(limiter(trusts_first_entry=True))

    assert finding.level == Level.FAIL
    assert "/health" in finding.title


def test_limit_that_ignores_fake_entries_passes():
    [finding] = check(limiter(trusts_first_entry=False))

    assert finding.level == Level.PASS
    assert f"limited after {LIMIT + 1} requests" in finding.title


def test_no_limit_stops_at_the_cap():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200)

    [finding] = check(handler)

    assert finding.level == Level.INFO
    assert len(calls) == MAX_REQUESTS


def test_fake_ip_is_a_documentation_address():
    seen = []
    api = limiter(trusts_first_entry=False)

    def handler(request):
        seen.append(request.headers.get("x-forwarded-for"))
        return api(request)

    check(handler)

    assert FAKE_IP.startswith("203.0.113.")
    assert seen.count(FAKE_IP) == 1


def test_limit_resetting_mid_test_is_inconclusive():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429 if len(calls) == LIMIT + 1 else 200)

    [finding] = check(handler)

    assert finding.level == Level.WARNING


def test_network_error_is_reported_not_hidden():
    def handler(request):
        raise httpx.ReadTimeout("timed out", request=request)

    [finding] = check(handler)

    assert finding.level == Level.INFO
    assert "Couldn't finish the rate_limit check" in finding.title