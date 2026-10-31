import argparse
from importlib.metadata import version

import httpx

from deploy_checkup.report import print_report
from deploy_checkup.runner import exit_code, make_client, run_checks


def main(argv: list[str] | None = None, client: httpx.Client | None = None) -> int:
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
    args = parser.parse_args(argv)

    with client or make_client() as http:
        results = run_checks(http, args.url, args.api)

    print_report(results)
    return exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())