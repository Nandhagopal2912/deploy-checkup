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