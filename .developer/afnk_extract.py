#!/usr/bin/env python3
"""Extract untranslated Affinity strings for Affin.ko dictionary updates."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = REPO_ROOT / ".affin.ko.dictionary"
DEFAULT_APP = Path("/Applications/Affinity.app")

RESOURCE_PATHS = (
    "Contents/Resources",
    "Contents/Frameworks/libcocoaui.framework/Versions/A/Resources",
)


def read_utf16(path: Path) -> str:
    return subprocess.check_output(
        ["iconv", "-f", "UTF-16LE", "-t", "UTF-8", str(path)],
        text=True,
        errors="replace",
    )


def apply_dictionary(content: str, dictionary: Path) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as handle:
        handle.write(content)
        temp_in = Path(handle.name)
    temp_out = temp_in.with_suffix(".out")
    with temp_out.open("w") as output:
        subprocess.run(["sed", "-f", str(dictionary), str(temp_in)], check=True, stdout=output)
    result = temp_out.read_text()
    temp_in.unlink(missing_ok=True)
    temp_out.unlink(missing_ok=True)
    return result


def parse_strings(content: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for match in re.finditer(r'^"(.+?)"\s*=\s*"(.*?)";\s*$', content, re.MULTILINE):
        pairs[match.group(1)] = match.group(2)
    return pairs


def is_english(text: str) -> bool:
    if not text.strip():
        return False
    if re.search(r"[\uac00-\ud7a3]", text):
        return False
    return bool(re.search(r"[A-Za-z]{3,}", text))


def sed_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("/", "\\/").replace("[", "\\[")


def to_sed_line(english: str, korean: str) -> str:
    return f's/\\"{sed_escape(english)}\\";/\\"{sed_escape(korean)}\\";/'


def iter_string_files(app_root: Path):
    for resource_path in RESOURCE_PATHS:
        en_dir = app_root / resource_path / "en-US.lproj"
        ja_dir = app_root / resource_path / "ja.lproj"
        if not en_dir.is_dir():
            continue
        for path in sorted(en_dir.glob("*.strings")):
            ja_path = ja_dir / path.name
            yield path, ja_path if ja_path.exists() else None


def collect_missing(
    app_root: Path,
    dictionary: Path,
    *,
    require_japanese: bool,
    file_filter: str | None,
) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    seen_values: set[str] = set()

    for en_path, ja_path in iter_string_files(app_root):
        if file_filter and file_filter not in en_path.name:
            continue

        en_content = read_utf16(en_path)
        ja_content = read_utf16(ja_path) if ja_path else ""
        ko_content = apply_dictionary(en_content, dictionary)

        en_pairs = parse_strings(en_content)
        ja_pairs = parse_strings(ja_content)
        ko_pairs = parse_strings(ko_content)

        for key, english in en_pairs.items():
            korean = ko_pairs.get(key, english)
            japanese = ja_pairs.get(key, "")
            if not is_english(korean):
                continue
            if require_japanese and (not japanese or is_english(japanese)):
                continue
            if english in seen_values:
                continue
            seen_values.add(english)
            missing.append(
                {
                    "file": en_path.name,
                    "key": key,
                    "english": english,
                    "japanese": japanese,
                }
            )

    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=DEFAULT_APP, help="Affinity.app path")
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--file", dest="file_filter", help="Filter by .strings filename")
    parser.add_argument(
        "--require-japanese",
        action="store_true",
        help="Only include strings that already have Japanese translations",
    )
    parser.add_argument(
        "--format",
        choices=("table", "sed", "json"),
        default="table",
        help="Output format",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of rows")
    args = parser.parse_args()

    if not args.app.exists():
        print(f"Affinity app not found: {args.app}", file=sys.stderr)
        return 1
    if not args.dictionary.exists():
        print(f"Dictionary not found: {args.dictionary}", file=sys.stderr)
        return 1

    rows = collect_missing(
        args.app,
        args.dictionary,
        require_japanese=args.require_japanese,
        file_filter=args.file_filter,
    )
    if args.limit:
        rows = rows[: args.limit]

    if args.format == "json":
        import json

        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if args.format == "sed":
        for row in rows:
            print(to_sed_line(row["english"], row["english"]))
        return 0

    print(f"Found {len(rows)} untranslated values")
    for row in rows:
        print(f"[{row['file']}] {row['english']}")
        if row["japanese"]:
            print(f"  JA: {row['japanese']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
