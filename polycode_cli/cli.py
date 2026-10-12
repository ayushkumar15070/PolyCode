
import argparse
import sys
from pathlib import Path

from core.config import *


VERSION = "0.0.1"


def run_file(file_path):
    """Execute a PolyCode source file."""
    from core.engine import PolyCodeEngine

    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        print(f"PolyCode error: File not found: {path}", file=sys.stderr)
        return 1

    if not path.is_file():
        print(f"PolyCode error: Not a file: {path}", file=sys.stderr)
        return 1

    if path.suffix.lower() != ".poly":
        print(
            "PolyCode error: Source files must use the .poly extension.",
            file=sys.stderr,
        )
        return 1

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"PolyCode error: Cannot read file: {error}", file=sys.stderr)
        return 1

    engine = PolyCodeEngine()
    output = engine.run(source)

    if output:
        print(output)

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="polycode",
        description="PolyCode — multi-language programming environment",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"PolyCode {VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Execute a .poly source file",
    )
    run_parser.add_argument(
        "file",
        help="Path to the .poly source file",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        return run_file(args.file)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
