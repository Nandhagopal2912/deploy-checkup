import argparse
import sys
from collections.abc import Callable
from importlib.metadata import version

import httpx

from deploy_checkup.report import print_report, to_json
from deploy_checkup.runner import exit_code, make_client, run_checks


def main(
    argv: list[str] | None = None,
    client: httpx.Client | None = None,
    ask: Callable[[str], str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether your deployed app is set up safely.",
        epilog="Only test apps you own or have permission to test.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=version("deploy-checkup"),
        help="show the program's version number",
    )
    parser.add_argument("url", help="your frontend's address")
    parser.add_argument("--api", help="your API's address, if it is separate")
    parser.add_argument(
        "--health-path",
        default="/health",
        help="the API's health check path (default: /health)",
    )
    parser.add_argument(
        "--yes-i-own-it",
        action="store_true",
        help="skip the permission question and run the probing checks (for CI)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of a coloured report",
    )
    args = parser.parse_args(argv)

    probe = _has_permission(args.url, args.yes_i_own_it, ask)
    with client or make_client() as http:
        results = run_checks(http, args.url, args.api, args.health_path, probe)

    if args.json:
        print(to_json(results))
    else:
        print_report(results)
    return exit_code(results)


def _has_permission(url: str, yes_i_own_it: bool, ask: Callable[[str], str] | None) -> bool:
    """Probing checks run only with a flag or a typed "yes"; never by accident."""
    if yes_i_own_it:
        return True
    if ask is None:
        if not sys.stdin.isatty():
            return False  # nobody is there to answer, for example in CI
        ask = _ask_on_stderr
    try:
        answer = ask(
            f"Also check {url} for exposed files like /.env? "
            "Only say yes if you own this site or have permission to test it. [y/N] "
        )
    except EOFError:
        return False  # input ran out without an answer, so treat it as "no"
    return answer.strip().lower() in ("y", "yes")


def _ask_on_stderr(prompt: str) -> str:
    """Like input(), but the question goes to stderr so it never mixes into --json output."""
    print(prompt, end="", file=sys.stderr, flush=True)
    return input()


if __name__ == "__main__":
    raise SystemExit(main())