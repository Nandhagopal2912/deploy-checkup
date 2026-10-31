from dataclasses import dataclass
from enum import Enum


class Level(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    check: str
    level: Level
    title: str
    why: str = ""
    fix: str = ""  # works on any host
    render_fix: str = ""  # replaces fix when the site is on Render
    


def could_not_finish(check: str, error: Exception) -> Finding:
    """A check that hit a network error says so, instead of quietly disappearing."""
    return Finding(
        check=check,
        level=Level.INFO,
        title=f"Couldn't finish the {check} check ({type(error).__name__})",
        why="The site stopped answering partway through, so this part wasn't checked.",
        fix="Run deploy-checkup again. If it keeps happening, check your site's logs.",
    )