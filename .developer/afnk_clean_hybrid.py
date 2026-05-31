#!/usr/bin/env python3
"""Remove dictionary entries with Japanese/hybrid Korean or non-Adobe terms."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = REPO_ROOT / ".affin.ko.dictionary"
AUTO = REPO_ROOT / ".developer/afnk_auto_translate.py"
OVERRIDES = REPO_ROOT / ".developer/translations/manual_overrides.json"
LINE_RE = re.compile(r'^s/\\"(.+?)\\";/\\"(.+?)\\";/$')


def load_translate():
    spec = importlib.util.spec_from_file_location("afnk_auto_translate", AUTO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def has_japanese(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text))


def has_bad_terms(text: str) -> bool:
    if any(x in text for x in ("에술", "스내핑", "응용프로그램", "신규", "미리 설정")):
        return True
    if "액화" in text and "액체화" not in text:
        return True
    if re.search(r"(?<![가-힣])칠(?![가-힣])", text):
        return True
    return False


def sed_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("/", "\\/")
        .replace("[", "\\[")
        .replace('"', '\\"')
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mod = load_translate()
    glossary = mod.load_glossary(REPO_ROOT / ".developer/adobe_glossary.json")
    overrides = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}

    kept = fixed = removed = skipped = 0
    out: list[str] = []

    for raw in args.dictionary.read_text().splitlines():
        line = raw.strip()
        match = LINE_RE.match(line)
        if not match:
            if line:
                skipped += 1
            continue

        english = match.group(1)
        korean = match.group(2).replace("\\/", "/")
        if not has_japanese(korean) and not has_bad_terms(korean):
            out.append(line)
            kept += 1
            continue

        candidate = overrides.get(english) or mod.translate_string(english, glossary)
        if candidate and not has_japanese(candidate) and not has_bad_terms(candidate):
            out.append(f's/\\"{sed_escape(english)}\\";/\\"{sed_escape(candidate)}\\";/')
            fixed += 1
        else:
            removed += 1

    print(f"Kept: {kept}, fixed: {fixed}, removed: {removed}, skipped malformed: {skipped}")
    if not args.dry_run:
        args.dictionary.write_text("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
