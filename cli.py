#!/usr/bin/env python3
"""CLI: python cli.py [--file path] or pipe stdin."""

from __future__ import annotations

import argparse
import json
import sys

from strata_triage.errors import TriageError
from strata_triage.facade import process_enquiry


def main() -> None:
    p = argparse.ArgumentParser(description="Triage a strata client enquiry via OpenAI.")
    p.add_argument("--file", "-f", help="Read enquiry text from file")
    args = p.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    else:
        if sys.stdin.isatty():
            print(
                "Enter enquiry text, then Ctrl+D (Unix) or Ctrl+Z Enter (Windows):",
                file=sys.stderr,
            )
        text = sys.stdin.read()

    try:
        out = process_enquiry(text)
    except TriageError as e:
        print(f"Error: {e.user_message}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
