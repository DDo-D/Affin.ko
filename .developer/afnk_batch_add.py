#!/usr/bin/env python3
"""Append batch translations to .affin.ko.dictionary."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = REPO_ROOT / ".affin.ko.dictionary"


def sed_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("/", "\\/")
        .replace("[", "\\[")
        .replace('"', '\\"')
    )


def to_sed_line(english: str, korean: str) -> str:
    return f's/\\"{sed_escape(english)}\\";/\\"{sed_escape(korean)}\\";/'


def load_existing_english(path: Path) -> set[str]:
    existing: set[str] = set()
    for line in path.read_text().splitlines():
        match = re.match(r's/\\"(.+?)\\";/\\"(.+?)\\";/', line.strip())
        if match:
            existing.add(match.group(1))
    return existing


def append_translations(
    dictionary: Path,
    translations: dict[str, str],
    *,
    dry_run: bool,
) -> tuple[int, int]:
    existing = load_existing_english(dictionary)
    new_lines: list[str] = []
    skipped = 0

    for english, korean in sorted(translations.items()):
        if english in existing:
            skipped += 1
            continue
        new_lines.append(to_sed_line(english, korean))

    if not dry_run and new_lines:
        with dictionary.open("a") as handle:
            if dictionary.stat().st_size and not dictionary.read_text().endswith("\n"):
                handle.write("\n")
            handle.write("\n".join(new_lines) + "\n")

    return len(new_lines), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path, help="JSON object: {english: korean}")
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    translations = json.loads(args.json_file.read_text())
    if not isinstance(translations, dict):
        print("JSON must be an object", file=sys.stderr)
        return 1

    added, skipped = append_translations(args.dictionary, translations, dry_run=args.dry_run)
    print(f"Added {added}, skipped {skipped} (already present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
