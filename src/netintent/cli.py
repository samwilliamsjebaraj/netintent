"""Validate network intent before it reaches a device."""

from __future__ import annotations

import argparse
import sys

import yaml
from pydantic import ValidationError

from netintent import __version__
from netintent.loader import load_fabric


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="netintent", description=__doc__)
    parser.add_argument("--version", action="version", version=f"netintent {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    val = sub.add_parser("validate", help="validate a fabric intent file")
    val.add_argument("file")
    args = parser.parse_args(argv)

    if args.command == "validate":
        try:
            fabric = load_fabric(args.file)
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            return 2
        except yaml.YAMLError as exc:
            print(f"error: invalid YAML: {exc}", file=sys.stderr)
            return 2
        except ValidationError as exc:
            print(f"INVALID: {args.file}", file=sys.stderr)
            for err in exc.errors():
                loc = ".".join(str(p) for p in err["loc"]) or "fabric"
                print(f"  - {loc}: {err['msg']}", file=sys.stderr)
            return 1
        print(
            f"OK: fabric '{fabric.name}' - {len(fabric.devices)} devices, {len(fabric.links)} links"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
