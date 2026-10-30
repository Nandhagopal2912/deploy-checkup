#cli.py
import argparse
from importlib.metadata import version

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="deploy-checkup",
        epilog="Only test apps you own or have permission to test.")

    parser.add_argument(
    "-V","--version",
    action="version",
    version=version("deploy-checkup"),
    help="show the program's version number"
    )
    
    parser.add_argument(
        "url",
        type=str,
        help="the target url"
    )
    
    parser.add_argument(
        "--api",
        type=str,
        help="the target api url"
    )
    
    args = parser.parse_args(argv)
    
    print("Target url",{args.url})
    if args.api:
        print("Target api url",{args.api})
    
    return 0


if __name__=="__main__":
    main()