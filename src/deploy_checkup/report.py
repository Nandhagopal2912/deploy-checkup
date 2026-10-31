import json
from importlib.metadata import version

from rich.console import Console
from rich.markup import escape

from deploy_checkup.models import Finding, Level

COLOURS = {
    Level.PASS: "green",
    Level.WARNING: "yellow",
    Level.FAIL: "red",
    Level.INFO: "blue",
}


def count_levels(results: dict[str, list[Finding]]) -> dict[Level, int]:
    """How many findings there are at each level, across every address."""
    counts = {level: 0 for level in Level}
    for findings in results.values():
        for finding in findings:
            counts[finding.level] += 1
    return counts


def print_report(results: dict[str, list[Finding]], console: Console | None = None) -> None:
    """Print each address's findings, then a one-line summary."""
    console = console or Console()

    for target, findings in results.items():
        console.rule(escape(target))
        for finding in findings:
            colour = COLOURS[finding.level]
            label = finding.level.value.upper()
            console.print(f"[bold {colour}]{label:<7}[/] {escape(finding.title)}")
            if finding.why:
                console.print(f"        [dim]Why:[/] {escape(finding.why)}")
            if finding.fix:
                console.print(f"        [dim]Fix:[/] {escape(finding.fix)}")
        console.print()

    counts = count_levels(results)
    summary = ", ".join(
        f"[{COLOURS[level]}]{counts[level]} {level.value}[/]" for level in Level
    )
    console.print(f"Summary: {summary}")


def to_json(results: dict[str, list[Finding]]) -> str:
    """The same findings as JSON, for scripts, CI and other tools."""
    report = {
        "tool": "deploy-checkup",
        "version": version("deploy-checkup"),
        "targets": [
            {
                "url": target,
                "findings": [
                    {
                        "check": f.check,
                        "level": f.level.value,
                        "title": f.title,
                        "why": f.why,
                        "fix": f.fix,
                    }
                    for f in findings
                ],
            }
            for target, findings in results.items()
        ],
        "summary": {level.value: count for level, count in count_levels(results).items()},
    }
    return json.dumps(report, indent=2)