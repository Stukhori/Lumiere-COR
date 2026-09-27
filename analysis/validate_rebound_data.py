"""Validate all trial-level source files before figure generation."""

from __future__ import annotations

import sys

from rebound_common import load_data, validate_frames, write_validation_report


def main() -> int:
    try:
        master, audit, session2 = load_data()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result = validate_frames(master, audit, session2)
    report = write_validation_report(result)
    print(f"Validation report: {report}")
    print(f"Critical errors: {len(result.critical_errors)}")
    print(f"Warnings: {len(result.warnings)}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if not result.ok:
        for error in result.critical_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
