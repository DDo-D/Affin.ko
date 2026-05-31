#!/usr/bin/env python3
"""Auto-translate missing Affinity strings using Adobe-aligned glossary."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = REPO_ROOT / ".affin.ko.dictionary"
DEFAULT_GLOSSARY = REPO_ROOT / ".developer/adobe_glossary.json"
DEFAULT_APP = Path("/Applications/Affinity.app")

RESOURCE_ROOTS = (
    "Contents/Resources",
    "Contents/Frameworks/libcocoaui.framework/Versions/A/Resources",
)

SUFFIX_RULES = (
    (" Presets", " 사전 설정"),
    (" Preset", " 사전 설정"),
    (" Options", " 옵션"),
    (" Settings", " 설정"),
    (" Manager", " 관리자"),
    (" Toolbar", " 도구 모음"),
    (" Panel", " 패널"),
    (" Layers", " 레이어"),
    (" Layer", " 레이어"),
    (" Masks", " 마스크"),
    (" Mask", " 마스크"),
    (" Filters", " 필터"),
    (" Filter", " 필터"),
    (" Effects", " 효과"),
    (" Effect", " 효과"),
    (" Tools", " 도구"),
    (" Tool", " 도구"),
    (" Brush", " 브러시"),
    (" Colors", " 색상"),
    (" Color", " 색상"),
    (" Channels", " 채널"),
    (" Channel", " 채널"),
    (" Guides", " 가이드"),
    (" Guide", " 가이드"),
    (" Margins", " 여백"),
    (" Margin", " 여백"),
    (" Profiles", " 프로필"),
    (" Profile", " 프로필"),
    (" Documents", " 문서"),
    (" Document", " 문서"),
    (" Selection", " 선택"),
    (" Transform", " 변형"),
    (" Opacity", " 불투명도"),
    (" Preview", " 미리보기"),
    (" Quality", " 품질"),
    (" Format", " 형식"),
    (" Metadata", " 메타데이터"),
    (" Keywords", " 키워드"),
    (" Keyword", " 키워드"),
    (" Caption", " 캡션"),
    (" Hyperlinks", " 하이퍼링크"),
    (" Hyperlink", " 하이퍼링크"),
    (" Anchors", " 앵커"),
    (" Anchor", " 앵커"),
    (" Curves", " 곡선"),
    (" Curve", " 곡선"),
    (" Edges", " 가장자리"),
    (" Edge", " 가장자리"),
    (" Styles", " 스타일"),
    (" Style", " 스타일"),
    (" Assets", " 에셋"),
    (" Asset", " 에셋"),
    (" Resources", " 리소스"),
    (" Resource", " 리소스"),
    (" Templates", " 템플릿"),
    (" Template", " 템플릿"),
    (" Symbols", " 심볼"),
    (" Symbol", " 심볼"),
    (" Patterns", " 패턴"),
    (" Pattern", " 패턴"),
    (" Textures", " 텍스처"),
    (" Texture", " 텍스처"),
    (" Overlays", " 오버레이"),
    (" Overlay", " 오버레이"),
    (" Snapshots", " 스냅샷"),
    (" Snapshot", " 스냅샷"),
    (" History", " 기록"),
    (" Navigator", " 탐색기"),
    (" Histogram", " 히스토그램"),
    (" Studio", " 스튜디오"),
    (" Persona", " 페르소나"),
    (" Assistant", " 도우미"),
    (" Macro", " 매크로"),
    (" Script", " 스크립트"),
    (" Grid", " 격자"),
    (" Bleed", " 도련"),
    (" Spread", " 대지"),
    (" Pages", " 페이지"),
    (" Page", " 페이지"),
    (" Fonts", " 글꼴"),
    (" Font", " 글꼴"),
    (" Text", " 텍스트"),
    (" Table", " 표"),
    (" Cells", " 셀"),
    (" Cell", " 셀"),
    (" Rows", " 행"),
    (" Row", " 행"),
    (" Columns", " 열"),
    (" Column", " 열"),
    (" Images", " 이미지"),
    (" Image", " 이미지"),
    (" Files", " 파일"),
    (" File", " 파일"),
    (" Path", " 패스"),
    (" Paths", " 패스"),
    (" Nodes", " 노드"),
    (" Node", " 노드"),
    (" Group", " 그룹"),
    (" Mode", " 모드"),
    (" Size", " 크기"),
    (" Width", " 너비"),
    (" Height", " 높이"),
    (" Radius", " 반경"),
    (" Angle", " 각도"),
    (" Amount", " 양"),
    (" Strength", " 강도"),
    (" Tolerance", " 허용치"),
    (" Threshold", " 임계값"),
    (" Resolution", " 해상도"),
    (" Ratio", " 비율"),
    (" Scale", " 크기"),
    (" Rotation", " 회전"),
    (" Skew", " 기울이기"),
    (" Shear", " 기울이기"),
    (" Mirror", " 대칭"),
    (" Flip", " 뒤집기"),
    (" Rotate", " 회전"),
    (" Resize", " 크기 조절"),
    (" Crop", " 자르기"),
    (" Trim", " 트림"),
    (" Export", " 내보내기"),
    (" Import", " 가져오기"),
    (" Rasterize", " 래스터화"),
    (" Vectorize", " 벡터화"),
    (" Trace", " 트레이스"),
    (" Simplify", " 단순화"),
    (" Optimize", " 최적화"),
    (" Compress", " 압축"),
    (" Render", " 렌더링"),
    (" Publish", " 게시"),
    (" Share", " 공유"),
    (" Upload", " 업로드"),
    (" Download", " 다운로드"),
    (" Account", " 계정"),
    (" Help", " 도움말"),
    (" Warning", " 경고"),
    (" Error", " 오류"),
    (" Label", " 레이블"),
    (" Title", " 제목"),
    (" Description", " 설명"),
    (" Author", " 저자"),
    (" Version", " 버전"),
    (" License", " 라이선스"),
    (" Privacy", " 개인정보"),
    (" Terms", " 약관"),
    (" Tutorial", " 튜토리얼"),
    (" Feedback", " 피드백"),
    (" Debug", " 디버그"),
    (" Sample", " 샘플"),
    (" Library", " 라이브러리"),
    (" Collection", " 컬렉션"),
    (" Category", " 범주"),
    (" Tag", " 태그"),
    (" Rating", " 등급"),
    (" Favorites", " 즐겨찾기"),
    (" Favorite", " 즐겨찾기"),
    (" Cloud", " 클라우드"),
    (" Upgrade", " 업그레이드"),
    (" Trial", " 체험판"),
    (" Subscription", " 구독"),
    (" Horizontal", " 가로"),
    (" Vertical", " 세로"),
    (" Both", " 양쪽"),
    (" All", " 모두"),
    (" None", " 없음"),
    (" Default", " 기본값"),
    (" Custom", " 사용자 지정"),
    (" Automatic", " 자동"),
    (" Manual", " 수동"),
    (" Enabled", " 사용"),
    (" Disabled", " 사용 안 함"),
    (" Visible", " 표시"),
    (" Hidden", " 숨김"),
    (" Locked", " 잠금"),
    (" Linked", " 연결"),
    (" Embedded", " 내장"),
    (" Selected", " 선택됨"),
    (" Active", " 활성"),
    (" Current", " 현재"),
    (" Previous", " 이전"),
    (" Next", " 다음"),
    (" First", " 처음"),
    (" Last", " 마지막"),
)

PREFIX_RULES = (
    ("Toggle ", ""),
    ("Add ", ""),
    ("New ", "새 "),
    ("Delete ", ""),
    ("Remove ", ""),
    ("Show ", ""),
    ("Hide ", ""),
    ("Enable ", ""),
    ("Disable ", ""),
    ("Edit ", ""),
    ("Create ", ""),
    ("Import ", ""),
    ("Export ", ""),
    ("Save ", ""),
    ("Load ", ""),
    ("Open ", ""),
    ("Close ", ""),
    ("Apply ", ""),
    ("Reset ", ""),
    ("Restore ", ""),
    ("Update ", ""),
    ("Refresh ", ""),
    ("Sync ", ""),
    ("Link ", ""),
    ("Unlink ", ""),
    ("Place ", ""),
    ("Embed ", ""),
    ("Convert ", ""),
    ("Transform ", ""),
    ("Merge ", ""),
    ("Flatten ", ""),
    ("Group ", ""),
    ("Ungroup ", ""),
    ("Duplicate ", ""),
    ("Rename ", ""),
    ("Copy ", ""),
    ("Paste ", ""),
    ("Cut ", ""),
    ("Select ", ""),
    ("Deselect ", ""),
    ("Invert ", ""),
    ("Lock ", ""),
    ("Unlock ", ""),
    ("Expand ", ""),
    ("Collapse ", ""),
    ("Sort ", ""),
    ("Filter ", ""),
    ("Search ", ""),
    ("Find ", ""),
    ("Replace ", ""),
    ("Insert ", ""),
    ("Move ", ""),
    ("Align ", ""),
    ("Distribute ", ""),
    ("Snap ", "스냅 "),
    ("Fit ", ""),
    ("Fill ", "채우기 "),
    ("Stroke ", "획 "),
    ("Draw ", ""),
    ("Erase ", ""),
    ("Liquify ", "액체화 "),
    ("Develop ", "보정 "),
    ("Manage ", ""),
    ("Assign ", ""),
    ("Set ", ""),
    ("Get ", ""),
    ("Use ", ""),
    ("Make ", ""),
    ("Build ", ""),
    ("Generate ", ""),
    ("Calculate ", ""),
    ("Measure ", ""),
    ("Calibrate ", ""),
    ("Install ", ""),
    ("Uninstall ", ""),
    ("Configure ", ""),
    ("Setup ", ""),
    ("Continue ", ""),
    ("Back ", ""),
    ("Forward ", ""),
    ("Finish ", ""),
    ("Done ", ""),
    ("Skip ", ""),
    ("Retry ", ""),
    ("Ignore ", ""),
    ("Accept ", ""),
    ("Decline ", ""),
    ("Confirm ", ""),
    ("Verify ", ""),
    ("Validate ", ""),
    ("Sign In", "로그인"),
    ("Sign Out", "로그아웃"),
    ("Check ", ""),
    ("Prompt for ", ""),
    ("Allow ", ""),
    ("Prevent ", ""),
    ("Require ", ""),
    ("Include ", ""),
    ("Exclude ", ""),
    ("Preserve ", ""),
    ("Maintain ", ""),
    ("Adjust ", ""),
    ("Increase ", ""),
    ("Decrease ", ""),
    ("Raise ", ""),
    ("Lower ", ""),
    ("Raise ", ""),
    ("Start ", ""),
    ("Stop ", ""),
    ("Pause ", ""),
    ("Resume ", ""),
    ("Cancel ", ""),
    ("Abort ", ""),
    ("Proceed ", ""),
    ("Run ", ""),
    ("Execute ", ""),
    ("Perform ", ""),
    ("Process ", ""),
    ("Analyze ", ""),
    ("Scan ", ""),
    ("Detect ", ""),
    ("Recognize ", ""),
    ("Identify ", ""),
    ("Match ", ""),
    ("Compare ", ""),
    ("Combine ", ""),
    ("Split ", ""),
    ("Separate ", ""),
    ("Join ", ""),
    ("Connect ", ""),
    ("Disconnect ", ""),
    ("Attach ", ""),
    ("Detach ", ""),
    ("Bind ", ""),
    ("Release ", ""),
    ("Capture ", ""),
    ("Record ", ""),
    ("Play ", ""),
    ("Loop ", ""),
    ("Reverse ", ""),
    ("Shuffle ", ""),
    ("Randomize ", ""),
    ("Normalize ", ""),
    ("Standardize ", ""),
    ("Optimize ", ""),
    ("Clean ", ""),
    ("Repair ", ""),
    ("Fix ", ""),
    ("Correct ", ""),
    ("Enhance ", ""),
    ("Improve ", ""),
    ("Reduce ", ""),
    ("Minimize ", ""),
    ("Maximize ", ""),
    ("Center ", ""),
    ("Offset ", ""),
    ("Shift ", ""),
    ("Nudge ", ""),
    ("Scroll ", ""),
    ("Pan ", "화면 이동 "),
    ("Zoom ", "확대/축소 "),
    ("Rotate ", "회전 "),
    ("Flip ", "뒤집기 "),
    ("Scale ", "크기 "),
    ("Resize ", "크기 조절 "),
    ("Crop ", "자르기 "),
    ("Trim ", "트림 "),
    ("Slice ", "슬라이스 "),
    ("Warp ", "변형 "),
    ("Distort ", "왜곡 "),
    ("Perspective ", "원근 "),
    ("Shear ", "기울이기 "),
    ("Skew ", "기울이기 "),
    ("Mirror ", "대칭 "),
    ("Reflect ", "반사 "),
    ("Project ", "투영 "),
    ("Extrude ", "돌출 "),
    ("Bevel ", "베벨 "),
    ("Emboss ", "엠보싱 "),
    ("Blur ", "흐림 "),
    ("Sharpen ", "선명 "),
    ("Smudge ", "번짐 "),
    ("Dodge ", "밝게 "),
    ("Burn ", "어둡게 "),
    ("Sponge ", "스펀지 "),
    ("Heal ", "수정 "),
    ("Clone ", "복제 "),
    ("Patch ", "패치 "),
    ("Stamp ", "스탬프 "),
    ("Paint ", "칠하기 "),
    ("Spray ", "스프레이 "),
    ("Airbrush ", "에어브러시 "),
    ("Gradient ", "그라데이션 "),
    ("Pattern ", "패턴 "),
    ("Texture ", "텍스처 "),
    ("Noise ", "노이즈 "),
    ("Denoise ", "노이즈 제거 "),
    ("Sharpen ", "선명 "),
    ("Smooth ", "부드럽게 "),
    ("Feather ", "페더 "),
    ("Refine ", "다듬기 "),
    ("Extract ", "추출 "),
    ("Isolate ", "분리 "),
    ("Mask ", "마스크 "),
    ("Unmask ", "마스크 해제 "),
    ("Clip ", "클리핑 "),
    ("Unclip ", "클리핑 해제 "),
    ("Wrap ", "줄 바꿈 "),
    ("Unwrap ", "줄 바꿈 해제 "),
    ("Outline ", "윤곽 "),
    ("Inline ", "인라인 "),
    ("Rasterize ", "래스터화 "),
    ("Vectorize ", "벡터화 "),
    ("Trace ", "트레이스 "),
    ("Simplify ", "단순화 "),
    ("Expand ", "확장 "),
    ("Contract ", "축소 "),
    ("Grow ", "확장 "),
    ("Similar ", "유사 "),
    ("Adjacent ", "인접 "),
    ("Connected ", "연결 "),
    ("Discontiguous ", "불연속 "),
    ("Contiguous ", "연속 "),
    ("Global ", "전역 "),
    ("Local ", "로컬 "),
    ("Document ", "문서 "),
    ("Artboard ", "아트보드 "),
    ("Layer ", "레이어 "),
    ("Pixel ", "픽셀 "),
    ("Vector ", "벡터 "),
    ("Text ", "텍스트 "),
    ("Image ", "이미지 "),
    ("Shape ", "모양 "),
    ("Path ", "패스 "),
    ("Channel ", "채널 "),
    ("Selection ", "선택 "),
    ("Brush ", "브러시 "),
    ("Effect ", "효과 "),
    ("Adjustment ", "조정 "),
    ("Preset ", "사전 설정 "),
    ("Profile ", "프로필 "),
    ("Color ", "색상 "),
    ("Tone ", "톤 "),
    ("Exposure ", "노출 "),
    ("Contrast ", "대비 "),
    ("Brightness ", "밝기 "),
    ("Saturation ", "채도 "),
    ("Vibrance ", "색강조 "),
    ("Clarity ", "선명도 "),
    ("Highlights ", "하이라이트 "),
    ("Shadows ", "그림자 "),
    ("Midtones ", "중간톤 "),
    ("Whites ", "흰색 "),
    ("Blacks ", "검은색 "),
    ("Temperature ", "색온도 "),
    ("Tint ", "색조 "),
    ("Hue ", "색상 "),
    ("Luminance ", "휘도 "),
    ("Luminosity ", "휘도 "),
    ("Gamma ", "감마 "),
    ("Curve ", "곡선 "),
    ("Level ", "레벨 "),
    ("Histogram ", "히스토그램 "),
    ("Navigator ", "탐색기 "),
    ("Preview ", "미리보기 "),
    ("History ", "기록 "),
    ("Snapshot ", "스냅샷 "),
    ("Macro ", "매크로 "),
    ("Assistant ", "도우미 "),
    ("Studio ", "스튜디오 "),
    ("Persona ", "페르소나 "),
    ("Develop ", "보정 "),
    ("Print ", "인쇄 "),
    ("Share ", "공유 "),
    ("Publish ", "게시 "),
    ("Upload ", "업로드 "),
    ("Download ", "다운로드 "),
    ("Account ", "계정 "),
    ("Help ", "도움말 "),
    ("About ", "정보 "),
    ("Warning ", "경고 "),
    ("Error ", "오류 "),
    ("Info ", "정보 "),
    ("Tip ", "팁 "),
    ("Note ", "노트 "),
    ("Debug ", "디버그 "),
    ("Test ", "테스트 "),
    ("Sample ", "샘플 "),
    ("Template ", "템플릿 "),
    ("Library ", "라이브러리 "),
    ("Collection ", "컬렉션 "),
    ("Category ", "범주 "),
    ("Tag ", "태그 "),
    ("Rating ", "등급 "),
    ("Favorite ", "즐겨찾기 "),
    ("Recent ", "최근 "),
    ("Cloud ", "클라우드 "),
    ("Online ", "온라인 "),
    ("Offline ", "오프라인 "),
    ("Upgrade ", "업그레이드 "),
    ("Trial ", "체험판 "),
    ("Subscription ", "구독 "),
    ("Purchase ", "구매 "),
)

VERB_KO = {
    "Add": "추가",
    "Delete": "삭제",
    "Remove": "제거",
    "Show": "표시",
    "Hide": "숨기기",
    "Enable": "사용",
    "Disable": "사용 안 함",
    "Edit": "편집",
    "Create": "만들기",
    "Import": "가져오기",
    "Export": "내보내기",
    "Save": "저장",
    "Load": "불러오기",
    "Open": "열기",
    "Close": "닫기",
    "Apply": "적용",
    "Reset": "재설정",
    "Restore": "복원",
    "Update": "업데이트",
    "Refresh": "새로 고침",
    "Sync": "동기화",
    "Link": "연결",
    "Unlink": "연결 해제",
    "Place": "배치",
    "Embed": "내장",
    "Convert": "변환",
    "Transform": "변형",
    "Merge": "병합",
    "Flatten": "병합",
    "Group": "그룹",
    "Ungroup": "그룹 해제",
    "Duplicate": "복제",
    "Rename": "이름 바꾸기",
    "Copy": "복사",
    "Paste": "붙여넣기",
    "Cut": "잘라내기",
    "Select": "선택",
    "Deselect": "선택 해제",
    "Invert": "반전",
    "Lock": "잠금",
    "Unlock": "잠금 해제",
    "Expand": "확장",
    "Collapse": "접기",
    "Sort": "정렬",
    "Filter": "필터",
    "Search": "검색",
    "Find": "찾기",
    "Replace": "바꾸기",
    "Insert": "삽입",
    "Move": "이동",
    "Align": "정렬",
    "Distribute": "분배",
    "Fit": "맞춤",
    "Draw": "그리기",
    "Erase": "지우기",
    "Manage": "관리",
    "Assign": "지정",
    "Set": "설정",
    "Use": "사용",
    "Make": "만들기",
    "Build": "빌드",
    "Generate": "생성",
    "Calculate": "계산",
    "Measure": "측정",
    "Calibrate": "보정",
    "Install": "설치",
    "Uninstall": "제거",
    "Configure": "구성",
    "Setup": "설정",
    "Continue": "계속",
    "Back": "뒤로",
    "Forward": "앞으로",
    "Finish": "완료",
    "Done": "완료",
    "Skip": "건너뛰기",
    "Retry": "다시 시도",
    "Ignore": "무시",
    "Accept": "수락",
    "Decline": "거부",
    "Confirm": "확인",
    "Verify": "확인",
    "Validate": "유효성 검사",
    "Check": "확인",
    "Prompt for": "요청",
    "Allow": "허용",
    "Prevent": "방지",
    "Require": "요구",
    "Include": "포함",
    "Exclude": "제외",
    "Preserve": "유지",
    "Maintain": "유지",
    "Adjust": "조정",
    "Increase": "늘리기",
    "Decrease": "줄이기",
    "Toggle": "켜기/끄기",
}


def load_glossary(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    clean: dict[str, str] = {}
    for key, value in data.items():
        if key.startswith("_") or not isinstance(value, str):
            continue
        if len(value) > 60 or " - " in value and "Adobe" in value:
            continue
        clean[key] = value
    return clean


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
    if re.fullmatch(r"[\d\s\W]+", text):
        return False
    return bool(re.search(r"[A-Za-z]{2,}", text))


def split_ellipsis(text: str) -> tuple[str, str]:
    for suffix in ("...", "…", ".."):
        if text.endswith(suffix):
            return text[: -len(suffix)], suffix
    return text, ""


def token_translate(text: str, glossary: dict[str, str]) -> str:
    result = text
    for term in sorted(glossary, key=len, reverse=True):
        if term in result:
            result = result.replace(term, glossary[term])
    return result


def suffix_translate(text: str, glossary: dict[str, str]) -> str | None:
    core, ell = split_ellipsis(text)
    for suffix, ko_suffix in sorted(SUFFIX_RULES, key=lambda x: len(x[0]), reverse=True):
        if core.endswith(suffix):
            head = core[: -len(suffix)]
            head_ko = token_translate(head, glossary) if head else ""
            if head and is_english(head_ko):
                head_ko = token_translate(head, glossary)
            if head and is_english(head_ko):
                return None
            return head_ko + ko_suffix + ell
    return None


def prefix_translate(text: str, glossary: dict[str, str]) -> str | None:
    core, ell = split_ellipsis(text)
    for prefix, forced in PREFIX_RULES:
        if not core.startswith(prefix):
            continue
        rest = core[len(prefix) :]
        if forced and not rest:
            return forced + ell
        rest_ko = suffix_translate(rest, glossary) or token_translate(rest, glossary)
        if is_english(rest_ko):
            rest_ko2 = suffix_translate(rest, glossary)
            if rest_ko2:
                rest_ko = rest_ko2
            else:
                return None
        verb = prefix.strip()
        if verb in VERB_KO and rest_ko:
            return f"{rest_ko} {VERB_KO[verb]}" + ell
        if forced:
            return forced + rest_ko + ell
        return rest_ko + ell
    return None


def translate_string(text: str, glossary: dict[str, str]) -> str | None:
    if not is_english(text):
        return None
    if "${" in text or "|CLICK|" in text or "|DRAG|" in text or "%@" in text or "%1" in text:
        return None
    if text in glossary:
        return glossary[text]
    if re.fullmatch(r"[A-Z0-9][A-Z0-9./+\- ]{0,15}", text.strip()):
        return text

    core, ell = split_ellipsis(text)
    if core in glossary:
        return glossary[core] + ell

    for splitter in (" / ", " | ", " · "):
        if splitter in core:
            parts = [translate_string(part.strip(), glossary) for part in core.split(splitter)]
            if all(part and not is_english(part) for part in parts):
                return splitter.join(parts) + ell

    if " - " in core:
        left, right = core.split(" - ", 1)
        lk = translate_string(left.strip(), glossary)
        rk = translate_string(right.strip(), glossary)
        if lk and rk and not is_english(lk) and not is_english(rk):
            return f"{lk} - {rk}" + ell

    hit = prefix_translate(text, glossary)
    if hit and not is_english(hit):
        return hit

    hit = suffix_translate(text, glossary)
    if hit and not is_english(hit):
        return hit

    tokenized = token_translate(core, glossary)
    if tokenized != core and not is_english(tokenized):
        return tokenized + ell

    return None


def iter_targets(app_root: Path, file_filter: str | None):
    for resource in RESOURCE_ROOTS:
        en_dir = app_root / resource / "en-US.lproj"
        if not en_dir.is_dir():
            continue
        for path in sorted(en_dir.glob("*.strings")):
            if file_filter and file_filter not in path.name:
                continue
            yield path


def collect_missing(app_root: Path, dictionary: Path, file_filter: str | None) -> list[str]:
    seen: set[str] = set()
    missing: list[str] = []
    for en_path in iter_targets(app_root, file_filter):
        en_content = read_utf16(en_path)
        ko_content = apply_dictionary(en_content, dictionary)
        en_pairs = parse_strings(en_content)
        ko_pairs = parse_strings(ko_content)
        for key, english in en_pairs.items():
            korean = ko_pairs.get(key, english)
            if is_english(korean) and english not in seen:
                seen.add(english)
                missing.append(english)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--file", dest="file_filter")
    parser.add_argument("--exclude-file", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    glossary = load_glossary(args.glossary)
    missing = collect_missing(args.app, args.dictionary, args.file_filter)
    translations: dict[str, str] = {}
    for english in missing:
        ko = translate_string(english, glossary)
        if ko and ko != english:
            translations[english] = ko
        if args.limit and len(translations) >= args.limit:
            break

    args.output.write_text(json.dumps(translations, ensure_ascii=False, indent=2) + "\n")
    print(f"Missing unique: {len(missing)}")
    print(f"Auto-translated: {len(translations)}")
    print(f"Wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
