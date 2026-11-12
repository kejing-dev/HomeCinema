#!/usr/bin/env python3
"""Explain that .rdc conversion is intentionally outside this skill."""
from __future__ import annotations

import argparse
import pathlib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rdc", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if not args.rdc.is_file():
        raise FileNotFoundError(args.rdc)
    raise SystemExit(
        "Direct .rdc analysis is not supported. Open the capture in RenderDoc, "
        "manually export XML, and provide the XML file."
    )


if __name__ == "__main__":
    main()
