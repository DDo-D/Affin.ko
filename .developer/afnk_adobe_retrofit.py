#!/usr/bin/env python3
"""Align existing Affin.ko dictionary entries with Adobe Korean terminology."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = REPO_ROOT / ".affin.ko.dictionary"

# Korean value replacements (regex on KO side), applied after English key match
KO_REPLACEMENTS: list[tuple[str, str, str]] = [
    (r"(?<![가-힣])칠(?![가-힣])", "채우기", "fill_term"),
    (r"미리 설정", "사전 설정", "preset_term"),
    (r"액화", "액체화", "liquify_term"),
    (r"스내핑", "스냅", "snap_term"),
    (r"에술", "아트", "artistic_typo"),
    (r"응용프로그램", "앱", "application_term"),
    (r"신규", "새", "new_term"),
    (r"유효화", "사용", "enable_term"),
    (r"그레이디언트", "그라데이션", "gradient_term"),
    (r"그레이딩", "그레이딩", "grading_keep"),
    (r"관하여", "정보", "about_term"),
    (r"켜고 끄기", "켜기/끄기", "toggle_term"),
    (r"초점이동", "화면 이동", "pan_term"),
    (r"상황별", "속성", "context_term"),
    (r"상황에 맞는", "속성", "context_toolbar"),
    (r"상황:", "속성:", "context_label"),
    (r"칠 및", "채우기 및", "fill_and"),
    (r"행동:", "동작:", "action_label"),
    (r"정렬 손잡이", "정렬 핸들", "alignment_handles"),
    (r"액화 그물", "액체화 메시", "liquify_mesh"),
    (r"유효한", "사용", "enabled_state"),
    (r"들여오기", "가져오기", "import_term"),
    (r"견본 패널", "견본 패널", "swatch_keep"),
    (r"Navigator", "탐색기", "navigator_en"),
    (r"네비게이터", "탐색기", "navigator_ko"),
    (r"Develop", "보정", "develop_en_in_ko"),
    (r"현상", "보정", "develop_ko"),
    (r"미리보기 패널", "미리보기 패널", "preview_keep"),
    (r"편집 기록", "기록", "history_adobe"),
    (r"문자 패널", "문자 패널", "character_keep"),
    (r"조정 미리 설정", "조정 사전 설정", "adjustment_preset"),
    (r"자르기 미리 설정", "자르기 사전 설정", "crop_preset"),
    (r"내보내기 미리 설정", "내보내기 사전 설정", "export_preset"),
    (r"작업실", "스튜디오", "studio_term"),
    (r"페르소나", "페르소나", "persona_keep"),
    (r"프리셋", "사전 설정", "preset_alt"),
]

# Whole-string overrides: English -> Adobe-aligned Korean
EN_OVERRIDES: dict[str, str] = {
    "Navigator": "탐색기",
    "Toggle Navigator Panel": "탐색기 패널 켜기/끄기",
    "History": "기록",
    "Toggle History Panel": "기록 패널 켜기/끄기",
    "Preferences": "환경 설정",
    "Fill Tool": "채우기 도구",
    "Fill Color": "채우기 색상",
    "Fill Opacity:": "채우기 불투명도:",
    "Fill Mode": "채우기 모드",
    "Delete Fill": "채우기 삭제",
    "Edit Fill…": "채우기 편집…",
    "Reset Fills": "채우기 재설정",
    "Set Fill None": "채우기 없음",
    "Swap Line and Fill": "선과 채우기 바꾸기",
    "Toggle Fill Context": "채우기 속성 켜기/끄기",
    "Draw behind fill": "채우기 뒤에 그리기",
    "Maintain fill aspect ratio": "채우기 종횡비 유지",
    "Fill style:": "채우기 스타일:",
    "Presets": "사전 설정",
    "Preset:": "사전 설정:",
    "Preset manager": "사전 설정 관리자",
    "Manage Presets…": "사전 설정 관리…",
    "My presets": "내 사전 설정",
    "Studio Presets": "스튜디오 사전 설정",
    "Liquify Persona": "액체화 페르소나",
    "Liquify": "액체화",
    "Liquify…": "액체화…",
    "Toggle Liquify Mask Panel": "액체화 마스크 패널 켜기/끄기",
    "Toggle Liquify Mesh Panel": "액체화 메시 패널 켜기/끄기",
    "Develop…": "보정…",
    "Context Toolbar": "속성 도구 모음",
    "Show Context Toolbar": "속성 도구 모음 표시",
    "Context:": "속성:",
    "Brush Item Context Menu": "브러시 항목 맥락 메뉴",
    "Enable snapping": "스냅 사용",
    "Toggle Snapping": "스냅 켜기/끄기",
    "Snapping Manager…": "스냅 관리자…",
    "Snapping Options": "스냅 옵션",
    "Snapping": "스냅",
    "Snapping…": "스냅…",
    "Add Preset…": "사전 설정 추가…",
    "Add Preset": "사전 설정 추가",
    "Add Adjustment Preset": "조정 사전 설정 추가",
    "Add Crop Preset": "자르기 사전 설정 추가",
    "Create Preset": "사전 설정 만들기",
    "Create Preset…": "사전 설정 만들기…",
    "Delete Preset": "사전 설정 삭제",
    "Save Preset": "사전 설정 저장",
    "Rename Preset…": "사전 설정 이름 바꾸기…",
    "Import Presets…": "사전 설정 가져오기…",
    "Export User Presets…": "사용자 사전 설정 내보내기…",
    "Please either commit or cancel the liquify operation before switching to another studio.": "다른 스튜디오로 전환하기 전에 액체화 작업을 적용하거나 취소하세요.",
    "Please either commit or cancel the develop operation before switching to another studio.": "다른 스튜디오로 전환하기 전에 보정 작업을 적용하거나 취소하세요.",
}


def sed_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("/", "\\/")
        .replace("[", "\\[")
        .replace('"', '\\"')
    )


def align_korean(korean: str, english: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    if english in EN_OVERRIDES and korean != EN_OVERRIDES[english]:
        return EN_OVERRIDES[english], [f"override:{english}"]

    updated = korean
    for pattern, repl, rule in KO_REPLACEMENTS:
        if rule.endswith("_keep"):
            continue
        if rule == "develop_ko" and "현상" not in updated:
            continue
        if rule == "develop_en_in_ko":
            continue
        new = re.sub(pattern, repl, updated)
        if new != updated:
            changes.append(rule)
            updated = new

    if english in EN_OVERRIDES and updated != EN_OVERRIDES[english]:
        updated = EN_OVERRIDES[english]
        changes.append(f"override:{english}")

    return updated, changes


def retrofit_dictionary(path: Path, *, dry_run: bool) -> int:
    lines = path.read_text().splitlines()
    out: list[str] = []
    changed = 0
    report: list[str] = []

    for line in lines:
        match = re.match(r's/\\"(.+?)\\";/\\"(.+?)\\";/', line.strip())
        if not match:
            out.append(line)
            continue
        english = match.group(1)
        korean = match.group(2).replace("\\/", "/")
        new_ko, rules = align_korean(korean, english)
        if new_ko != korean:
            changed += 1
            report.append(f"{english}\n  {korean} -> {new_ko} [{', '.join(rules)}]")
            line = f's/\\"{sed_escape(english)}\\";/\\"{sed_escape(new_ko)}\\";/'
        out.append(line)

    if not dry_run and changed:
        path.write_text("\n".join(out) + "\n")

    print(f"{'Would change' if dry_run else 'Changed'} {changed} entries")
    for item in report[:30]:
        print(item)
    if len(report) > 30:
        print(f"... and {len(report) - 30} more")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    retrofit_dictionary(args.dictionary, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
