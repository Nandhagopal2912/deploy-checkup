from statistics import median

from deploy_checkup.models import Finding, Level

CHECK = "cold_start"
COLD_MS = 5000  # a first request this slow usually means the server was asleep


def check_cold_start(times_ms: list[float]) -> Finding:
    """Compare the first response time with the ones after it."""
    first = round(times_ms[0])
    warm = round(median(times_ms[1:]))

    if first >= COLD_MS and first > 3 * warm:
        return Finding(
            check=CHECK,
            level=Level.INFO,
            title=f"First request took {first / 1000:.1f} s, later ones {warm} ms: free tier waking up?",
            why=(
                "Free hosting plans often put an app to sleep when nobody visits, "
                "and the next visitor waits while it starts again."
            ),
            fix=(
                "Say so in your README so visitors know to wait, or use a plan that "
                "keeps the server running."
            ),
            render_fix=(
                "Render's free tier sleeps after 15 minutes without visitors. Say so in "
                "your README, or move the service to a paid instance type to keep it awake."
            ),
        )

    return Finding(
        check=CHECK,
        level=Level.PASS,
        title=f"No cold start this time (first request {first} ms)",
    )