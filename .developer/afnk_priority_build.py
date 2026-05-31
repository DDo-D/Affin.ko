#!/usr/bin/env python3
"""Build Adobe-aligned KO translations from afnk_extract JSON (EN + JA hints)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Adobe PS/AI/ID 한글판 기준 (내보내기·환경설정·패널)
ADOBE_MAP = {
    "Include printers marks": "프린터 마크 포함",
    "Any": "임의",
    "Spacial pixels:": "공간 픽셀:",
    "Spatial pixels:": "공간 픽셀:",
    "Ignore and clamp": "무시 및 고정",
    "Embed metadata": "메타데이터 포함",
    "Bicubic": "큐빅",
    "B44 (Lossy)": "B44(손실)",
    "Nearest Neighbor": "근접 이웃",
    "Include bleed": "도련 포함",
    "Remove line breaks": "줄 바꿈 제거",
    "Password Protection": "암호 보호",
    "Primaries:": "원색:",
    "Simplify": "단순화",
    "Use tile patterns": "타일 패턴 사용",
    "Replace with solid": "단색으로 바꾸기",
    "Preserve editability": "편집 가능성 유지",
    "Bilinear": "양선형",
    "Overprint black": "검정 오버프린트",
    "Convert bulleted lists to text": "글 머리 기호 목록을 텍스트로 변환",
    "Preserve accuracy": "정확도 유지",
    "Include hyperlinks": "하이퍼링크 포함",
    "Include notes": "노트 포함",
    "Include margins": "여백 포함",
    "Area scale:": "영역 크기:",
    "Downsample:": "다운샘플:",
    "Compression:": "압축:",
    "Quality:": "품질:",
    "Method:": "방법:",
    "Profile:": "프로필:",
    "Format:": "형식:",
    "Preset:": "사전 설정:",
    "Presets": "사전 설정",
    "Export": "내보내기",
    "Import": "가져오기",
    "Preferences": "환경 설정",
    "General": "일반",
    "User Interface": "사용자 인터페이스",
    "Performance": "성능",
    "Scratch disks": "스크래치 디스크",
    "Scratch Disks": "스크래치 디스크",
    "Type": "글자",
    "Tools": "도구",
    "Selection": "선택",
    "Colour": "색상",
    "Color": "색상",
    "Advanced": "고급",
    "Licence": "라이선스",
    "License": "라이선스",
    "Snapping": "스냅",
    "Snap to": "스냅 대상",
    "Show": "표시",
    "Hide": "숨기기",
    "Opacity": "불투명도",
    "Blend Mode": "혼합 모드",
    "Blend mode": "혼합 모드",
    "Fill": "채우기",
    "Stroke": "획",
    "Lock": "잠금",
    "Visible": "표시",
    "Unlock": "잠금 해제",
    "Duplicate": "복제",
    "Delete": "삭제",
    "Rename": "이름 바꾸기",
    "Merge": "병합",
    "Rasterize": "래스터화",
    "Expand": "확장",
    "Contract": "축소",
    "Refine": "다듬기",
    "Mask": "마스크",
    "Add Mask": "마스크 추가",
    "Add Pixel Layer": "픽셀 레이어 추가",
    "Add Adjustment": "조정 추가",
    "Add Live Filter": "라이브 필터 추가",
    "Group": "그룹",
    "Ungroup": "그룹 해제",
    "Release": "해제",
    "Detach": "분리",
    "Link": "연결",
    "Embed": "내장",
    "Place": "배치",
    "Edit": "편집",
    "Properties": "속성",
    "Transform": "변형",
    "Arrange": "배치",
    "Align": "정렬",
    "Distribute": "분배",
    "Flip Horizontal": "가로 뒤집기",
    "Flip Vertical": "세로 뒤집기",
    "Rotate": "회전",
    "Shear": "기울이기",
    "Scale": "크기",
    "Reset Transform": "변형 재설정",
    "Convert to Curves": "곡선으로 변환",
    "Convert to Shape": "모양으로 변환",
    "Geometry": "도형",
    "Swatches": "견본",
    "Global": "전역",
    "Document": "문서",
    "Application": "앱",
    "System": "시스템",
    "Recent": "최근",
    "Favorites": "즐겨찾기",
    "None": "없음",
    "Default": "기본값",
    "Custom": "사용자 지정",
    "Automatic": "자동",
    "Manual": "수동",
    "Enabled": "사용",
    "Disabled": "사용 안 함",
    "High": "높음",
    "Medium": "중간",
    "Low": "낮음",
    "Maximum": "최대",
    "Minimum": "최소",
    "Brightness": "밝기",
    "Contrast": "대비",
    "Saturation": "채도",
    "Vibrance": "색강조",
    "Exposure": "노출",
    "Highlights": "하이라이트",
    "Shadows": "그림자",
    "Whites": "흰색",
    "Blacks": "검은색",
    "Temperature": "색온도",
    "Tint": "색조",
    "Sharpen": "선명",
    "Blur": "흐림",
    "Noise": "노이즈",
    "Denoise": "노이즈 제거",
    "Clarity": "선명도",
    "Dehaze": "안개 제거",
    "Vignette": "비네팅",
    "Curves": "곡선",
    "Levels": "레벨",
    "Black & White": "흑백",
    "Channel Mixer": "채널 혼합",
    "Gradient Map": "그라데이션 맵",
    "Selective Color": "선택 색상",
    "Color Balance": "색상 균형",
    "Photo Filter": "사진 필터",
    "Invert": "반전",
    "Posterize": "포스터화",
    "Threshold": "임계값",
    "Unsharp Mask": "언샵 마스크",
    "High Pass": "하이 패스",
    "Lens Correction": "렌즈 보정",
    "Spherize": "구형 왜곡",
    "Twirl": "소용돌이",
    "Ripple": "잔물결",
    "Wave": "파동",
    "Emboss": "엠보싱",
    "Halftone": "하프톤",
    "Pixelate": "픽셀화",
    "Motion Blur": "모션 흐림",
    "Radial Blur": "방사형 흐림",
    "Gaussian Blur": "가우시안 흐림",
    "Box Blur": "박스 흐림",
    "Surface Blur": "표면 흐림",
    "Lens Blur": "렌즈 흐림",
    "Field Blur": "필드 흐림",
    "Tilt-Shift": "틸트-시프트",
    "Liquify": "액체화",
    "Develop": "보정",
    "Tone Mapping": "톤 매핑",
    "HDR Merge": "HDR 병합",
    "Focus Merge": "초점 병합",
    "Panorama": "파노라마",
    "Astro Stack": "천체 사진 스택",
    "Frequency Separation": "주파수 분리",
    "Haze Removal": "안개 제거",
    "Shadows / Highlights": "어두운/밝은 영역",
    "Shadows/Highlights": "어두운/밝은 영역",
}


def ja_hint_to_ko(japanese: str) -> str | None:
    if not japanese:
        return None
    result = japanese
    fragments = {
        "を含める": " 포함",
        "を埋め込む": " 포함",
        "を使用": " 사용",
        "を削除": " 제거",
        "を維持": " 유지",
        "を変換": " 변환",
        "を追加": " 추가",
        "プリンターマーク": "프린터 마크",
        "裁ち落とし": "도련",
        "メタデータ": "메타데이터",
        "パスワード保護": "암호 보호",
        "原色": "원색",
        "単純化": "단순화",
        "編集可能性": "편집 가능성",
        "オーバープリント": "오버프린트",
        "箇条書き": "글 머리 기호",
        "改行": "줄 바꿈",
        "どれでも": "임의",
        "空間": "공간",
        "ピクセル": "픽셀",
        "バイキュービック": "큐빅",
        "バイリニア": "양선형",
        "ニアレストネイバー": "근접 이웃",
        "非可逆": "손실",
        "単色": "단색",
        "置換": "바꾸기",
        "タイルパターン": "타일 패턴",
        "無視": "무시",
        "クランプ": "고정",
    }
    for ja, ko in sorted(fragments.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(ja, ko)
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", result):
        return None
    if re.search(r"[\uac00-\ud7a3]", result):
        return result.strip()
    return None


def translate_row(english: str, japanese: str) -> str | None:
    if english in ADOBE_MAP:
        return ADOBE_MAP[english]
    core = english.rstrip(".…")
    if core in ADOBE_MAP:
        suffix = english[len(core):]
        return ADOBE_MAP[core] + suffix.replace("...", "…")
    if japanese:
        hint = ja_hint_to_ko(japanese)
        if hint:
            return hint
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    translations: dict[str, str] = {}
    for path in args.inputs:
        rows = json.loads(path.read_text())
        for row in rows:
            english = row["english"]
            japanese = row.get("japanese", "")
            ko = translate_row(english, japanese)
            if ko and ko != english:
                translations[english] = ko

    args.output.write_text(json.dumps(translations, ensure_ascii=False, indent=2) + "\n")
    print(f"Translated {len(translations)} from {len(args.inputs)} input files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
