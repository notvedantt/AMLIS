"""AMLIS command-line entry point. Paper trading only (DEMO mode)."""

from __future__ import annotations

import argparse

MODE = "DEMO"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="amlis", description="AMLIS decision-support CLI (DEMO mode only)")
    parser.add_argument("--version", action="store_true", help="print version and mode")
    args = parser.parse_args(argv)
    if args.version:
        print(f"amlis 0.1.0 [{MODE}]")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
