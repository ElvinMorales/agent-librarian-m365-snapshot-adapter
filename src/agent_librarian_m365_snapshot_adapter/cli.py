from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .config import ConfigError, load_config
from .exporter import ExportError, export_synthetic


LIVE_DISABLED = (
    "Live Microsoft 365 export is not implemented in this prototype. "
    "Use export-synthetic or complete the documented security gates first."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="m365-snapshot-adapter")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check-config", help="validate approved-scope configuration")
    check.add_argument("config", type=Path)
    synthetic = subparsers.add_parser("export-synthetic", help="export bundled offline fixture data")
    synthetic.add_argument("--config", type=Path, required=True)
    synthetic.add_argument("--out", type=Path, required=True)
    live = subparsers.add_parser("export", help="disabled live export boundary")
    live.add_argument("--config", type=Path)
    live.add_argument("--out", type=Path)
    subparsers.add_parser("version", help="show package version")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "version":
            print(__version__)
            return 0
        if args.command == "export":
            print(LIVE_DISABLED, file=sys.stderr)
            return 2
        config = load_config(args.config)
        if args.command == "check-config":
            print(f"Approved-scope config is valid: {args.config}")
            return 0
        export_synthetic(config, args.out)
        print(f"Synthetic snapshot written: {args.out}")
        return 0
    except (ConfigError, ExportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
