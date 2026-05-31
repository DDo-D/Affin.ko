#!/usr/bin/env python3
"""Review Affin.ko dictionary entries for awkward or inconsistent Korean."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = REPO_ROOT / ".affin.ko.dictionary"

# Known fixes: English value -> suggested Korean replacement
SUGGESTED_FIXES: dict[str, str] = {
    "Add Artistic Text": "아트 텍스트 추가",
    "Add Application Palette": "앱 팔레트 추가",
    "Add Chord to Swatch": "스와치에 코드 추가",
    "Add Color to Swatch": "스와치에 색상 추가",
    "Add for snapping": "스냅 대상에 추가",
    "Add to Swatches…": "스와치에 추가…",
    "Application is about to close.": "앱을 종료합니다.",
    "As Application Palette": "앱 팔레트로",
    "Enable snapping": "스냅 사용",
    "Exclude From Snapping": "스냅에서 제외",
    "On App Screen": "앱 화면",
    "Snapping Manager…": "스냅 관리자…",
    "Snapping Options": "스냅 옵션",
    "Snapping axis setup": "스냅 축 설정",
    "Snapping": "스냅",
    "Swatches": "스와치",
    "Toggle Snapping": "스냅 켜기/끄기",
    "Toggle Swatches Panel": "스와치 패널 켜기/끄기",
    "Samples": "스와치",
    "Show Samples": "스와치 보기",
    "View Samples": "스와치 보기",
    "Action:": "동작:",
    "Alignment Handles": "정렬 핸들",
    "New": "새로 만들기",
    "New…": "새로 만들기…",
    "New Document": "새 문서",
    "New Layer": "새 레이어",
    "New Group": "새 그룹",
    "New View": "새 보기",
    "New Adjustment": "새 조정",
    "New Adjustment Layer": "새 조정 레이어",
    "New Pixel Layer": "새 픽셀 레이어",
    "New layer": "새 레이어",
    "Add New Category...": "새 범주 추가...",
    "Add New Category…": "새 범주 추가…",
    "Create New Category": "새 범주 만들기",
    "Add Registration Color": "등록 색상 추가",
    "About…": "Affinity 정보",
    "About Designer": "Designer 정보",
    "Arrange": "배치",
    "Assistant": "도우미",
    "Assistant Options": "도우미 옵션",
    "Assistant Manager…": "도우미 관리자…",
    "Add Crop Preset": "자르기 프리셋 추가",
    "Add Gradient Overlay": "그라디언트 오버레이 추가",
    "|DRAG| to pan view.": "|DRAG|하여 화면 이동.",
    "Saving TIFF": "TIFF 저장 중",
    "Tilt": "기울임",
}


@dataclass
class ReviewIssue:
    english: str
    korean: str
    rule: str
    suggestion: str | None = None


def parse_dictionary(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for line in path.read_text().splitlines():
        match = re.match(r's/\\"(.+?)\\";/\\"(.+?)\\";/', line.strip())
        if match:
            rows.append((line.strip(), match.group(1), match.group(2)))
    return rows


def review_entry(english: str, korean: str) -> list[ReviewIssue]:
    issues: list[ReviewIssue] = []

    if english in SUGGESTED_FIXES and korean != SUGGESTED_FIXES[english]:
        issues.append(
            ReviewIssue(
                english=english,
                korean=korean,
                rule="suggested_fix",
                suggestion=SUGGESTED_FIXES[english],
            )
        )

    if "에술" in korean:
        issues.append(
            ReviewIssue(english, korean, "typo_artistic", korean.replace("에술", "아트"))
        )

    if "스내핑" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_snapping", korean.replace("스내핑", "스냅"))
        )

    if re.search(r"^신규", korean) or " 신규" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_new", re.sub(r"신규", "새", korean))
        )

    if "유효화" in korean:
        issues.append(
            ReviewIssue(
                english,
                korean,
                "terminology_enable",
                korean.replace("유효화", "사용"),
            )
        )

    if "응용프로그램" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_application", korean.replace("응용프로그램", "앱"))
        )

    if korean.endswith("관하여") or "에 관하여" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_about", korean.replace("에 관하여", " 정보").replace("관하여", "정보"))
        )

    if "켜고 끄기" in korean:
        issues.append(
            ReviewIssue(english, korean, "style_toggle", korean.replace("켜고 끄기", "켜기/끄기"))
        )

    if "초점이동" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_pan", korean.replace("초점이동", "화면 이동"))
        )

    if "그레이디언트" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_gradient", korean.replace("그레이디언트", "그라디언트"))
        )

    if "크롭" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_crop", korean.replace("크롭", "자르기"))
        )

    if english == "Add Chord to Swatch" and "코드" in korean:
        issues.append(
            ReviewIssue(english, korean, "terminology_chord", korean.replace("코드", "코드"))  # chord vs code - keep note
        )

    return issues


def sed_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("/", "\\/")


def apply_fixes(path: Path, fixes: dict[str, str]) -> int:
    lines = path.read_text().splitlines()
    changed = 0
    updated: list[str] = []

    for line in lines:
        match = re.match(r's/\\"(.+?)\\";/\\"(.+?)\\";/', line.strip())
        if match and match.group(1) in fixes:
            english = match.group(1)
            new_korean = sed_escape(fixes[english])
            if match.group(2) != new_korean.replace("\\/", "/"):
                updated_line = f's/\\"{english}\\";/\\"{new_korean}\\";/'
                updated.append(updated_line)
                changed += 1
                continue
        updated.append(line)

    if changed:
        path.write_text("\n".join(updated) + "\n")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--apply", action="store_true", help="Apply suggested fixes to dictionary")
    parser.add_argument("--rule", help="Filter by rule id")
    args = parser.parse_args()

    rows = parse_dictionary(args.dictionary)
    all_issues: list[ReviewIssue] = []
    for _, english, korean in rows:
        all_issues.extend(review_entry(english, korean))

    if args.rule:
        all_issues = [issue for issue in all_issues if issue.rule == args.rule]

    dedup: dict[tuple[str, str, str], ReviewIssue] = {}
    for issue in all_issues:
        key = (issue.english, issue.rule, issue.suggestion or "")
        dedup[key] = issue
    all_issues = list(dedup.values())

    if args.apply:
        fixes = {issue.english: issue.suggestion for issue in all_issues if issue.suggestion}
        count = apply_fixes(args.dictionary, fixes)
        print(f"Applied {count} fixes to {args.dictionary}")
        return 0

    print(f"Found {len(all_issues)} review items in {len(rows)} dictionary entries\n")
    for issue in sorted(all_issues, key=lambda item: (item.rule, item.english)):
        print(f"[{issue.rule}] {issue.english}")
        print(f"  current: {issue.korean}")
        if issue.suggestion:
            print(f"  suggest: {issue.suggestion}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
