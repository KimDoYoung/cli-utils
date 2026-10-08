import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("diary-extract")
except PackageNotFoundError:
    __version__ = "0.1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="diary-extract",
        description="CLI utility for diary-extract",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print("Hello from diary-extract!")


if __name__ == "__main__":
    main()
