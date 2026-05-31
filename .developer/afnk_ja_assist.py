#!/usr/bin/env python3
"""Generate Korean candidates from EN+JA string pairs using Adobe terminology."""

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

# Common JA UI fragments -> Adobe-style Korean
JA_FRAGMENTS = {
    "レイヤー": "레이어",
    "マスク": "마스크",
    "ブラシ": "브러시",
    "カラー": "색상",
    "色": "색상",
    "チャンネル": "채널",
    "フィルター": "필터",
    "フィルタ": "필터",
    "エフェクト": "효과",
    "効果": "효과",
    "調整": "조정",
    "プリセット": "사전 설정",
    "スナップ": "스냅",
    "スワッチ": "견본",
    "パターン": "패턴",
    "テクスチャ": "텍스처",
    "グラデーション": "그라데이션",
    "グラディエント": "그라데이션",
    "透明度": "불투명도",
    "不透明度": "불투명도",
    "変形": "변형",
    "回転": "회전",
    "拡大": "확대",
    "縮小": "축소",
    "切り抜き": "자르기",
    "トリミング": "트림",
    "書き出し": "내보내기",
    "読み込み": "가져오기",
    "環境設定": "환경 설정",
    "設定": "설정",
    "オプション": "옵션",
    "パネル": "패널",
    "ツール": "도구",
    "ツールバー": "도구 모음",
    "ドキュメント": "문서",
    "アートボード": "아트보드",
    "テキスト": "텍스트",
    "文字": "문자",
    "段落": "단락",
    "フォント": "글꼴",
    "ガイド": "가이드",
    "グリッド": "격자",
    "余白": "여백",
    "塗り": "채우기",
    "線": "획",
    "ストローク": "획",
    "選択": "선택",
    "パス": "패스",
    "アンカー": "앵커",
    "ノード": "노드",
    "履歴": "기록",
    "スナップショット": "스냅샷",
    "ヒストグラム": "히스토그램",
    "ナビゲーター": "탐색기",
    "プレビュー": "미리보기",
    "開発": "보정",
    "現像": "보정",
    "液化": "액체화",
    "ぼかし": "흐림",
    "シャープ": "선명",
    "ノイズ": "노이즈",
    "露出": "노출",
    "コントラスト": "대비",
    "明るさ": "밝기",
    "彩度": "채도",
    "色相": "색상",
    "トーン": "톤",
    "ハイライト": "하이라이트",
    "シャドウ": "그림자",
    "中間調": "중간톤",
    "ホワイトバランス": "화이트 밸런스",
    "レンズ": "렌즈",
    "パノラマ": "파노라마",
    "マクロ": "매크로",
    "アシスタント": "도우미",
    "スタジオ": "스튜디오",
    "ペルソナ": "페르소나",
    "エクスポート": "내보내기",
    "インポート": "가져오기",
    "リンク": "연결",
    "埋め込み": "내장",
    "ラスタライズ": "래스터화",
    "ベクター": "벡터",
    "ピクセル": "픽셀",
    "シンボル": "심볼",
    "アセット": "에셋",
    "リソース": "리소스",
    "テンプレート": "템플릿",
    "ライブラリ": "라이브러리",
    "カテゴリ": "범주",
    "タグ": "태그",
    "名前": "이름",
    "タイトル": "제목",
    "説明": "설명",
    "作者": "저자",
    "日付": "날짜",
    "バージョン": "버전",
    "アカウント": "계정",
    "ヘルプ": "도움말",
    "警告": "경고",
    "エラー": "오류",
    "追加": "추가",
    "削除": "삭제",
    "削除…": "삭제…",
    "編集": "편집",
    "編集…": "편집…",
    "作成": "만들기",
    "保存": "저장",
    "開く": "열기",
    "閉じる": "닫기",
    "適用": "적용",
    "キャンセル": "취소",
    "リセット": "재설정",
    "復元": "복원",
    "更新": "업데이트",
    "同期": "동기화",
    "複製": "복제",
    "名前を変更": "이름 바꾸기",
    "表示": "표시",
    "非表示": "숨기기",
    "ロック": "잠금",
    "解除": "해제",
    "グループ": "그룹",
    "結合": "병합",
    "整列": "정렬",
    "分布": "분배",
    "検索": "검색",
    "置換": "바꾸기",
    "挿入": "삽입",
    "移動": "이동",
    "変換": "변환",
    "有効": "사용",
    "無効": "사용 안 함",
    "自動": "자동",
    "手動": "수동",
    "既定": "기본값",
    "カスタム": "사용자 지정",
    "すべて": "모두",
    "なし": "없음",
    "新規": "새",
    "上": "위",
    "下": "아래",
    "左": "왼쪽",
    "右": "오른쪽",
    "中央": "가운데",
    "水平": "가로",
    "垂直": "세로",
    "幅": "너비",
    "高さ": "높이",
    "サイズ": "크기",
    "解像度": "해상도",
    "品質": "품질",
    "形式": "형식",
    "プロファイル": "프로필",
    "メタデータ": "메타데이터",
    "キーワード": "키워드",
    "キャプション": "캡션",
    "ハイパーリンク": "하이퍼링크",
    "表": "표",
    "セル": "셀",
    "行": "행",
    "列": "열",
    "ページ": "페이지",
    "見開き": "대지",
    "ノート": "노트",
    "脚注": "각주",
    "索引": "색인",
    "目次": "목차",
    "参照": "참조",
    "アンカー": "앵커",
    "曲線": "곡선",
    "レベル": "레벨",
    "しきい値": "임계값",
    "ぼかし…": "흐림…",
    "シャープ…": "선명…",
    "…": "…",
    "...": "...",
}


def load_glossary(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    return {k: v for k, v in data.items() if not k.startswith("_") and isinstance(v, str) and len(v) < 60}


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


def ja_to_ko(japanese: str) -> str:
    result = japanese
    for ja, ko in sorted(JA_FRAGMENTS.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(ja, ko)
    # leftover kana-only labels: keep if still japanese - skip
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", result) and not re.search(r"[\uac00-\ud7a3]", result):
        return ""
    return result


def translate_pair(english: str, japanese: str, glossary: dict[str, str]) -> str | None:
    if english in glossary:
        return glossary[english]
    if japanese:
        ja_ko = ja_to_ko(japanese)
        if ja_ko and re.search(r"[\uac00-\ud7a3]", ja_ko) and not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", ja_ko):
            return ja_ko
    # fallback: token replace EN
    result = english
    for term in sorted(glossary, key=len, reverse=True):
        if term in result:
            result = result.replace(term, glossary[term])
    if result != english and not is_english(result):
        return result
    return None


def collect_pairs(app_root: Path, dictionary: Path, file_filter: str | None) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for resource in RESOURCE_ROOTS:
        en_dir = app_root / resource / "en-US.lproj"
        ja_dir = app_root / resource / "ja.lproj"
        if not en_dir.is_dir() or not ja_dir.is_dir():
            continue
        for en_path in sorted(en_dir.glob("*.strings")):
            if file_filter and file_filter not in en_path.name:
                continue
            ja_path = ja_dir / en_path.name
            if not ja_path.exists():
                continue
            en_content = read_utf16(en_path)
            ja_content = read_utf16(ja_path)
            ko_content = apply_dictionary(en_content, dictionary)
            en_pairs = parse_strings(en_content)
            ja_pairs = parse_strings(ja_content)
            ko_pairs = parse_strings(ko_content)
            for key, english in en_pairs.items():
                if english in seen:
                    continue
                if not is_english(ko_pairs.get(key, english)):
                    continue
                japanese = ja_pairs.get(key, "")
                seen.add(english)
                rows.append((english, japanese))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--file", dest="file_filter")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    glossary = load_glossary(args.glossary)
    pairs = collect_pairs(args.app, args.dictionary, args.file_filter)
    translations: dict[str, str] = {}
    for english, japanese in pairs:
        ko = translate_pair(english, japanese, glossary)
        if ko and ko != english:
            translations[english] = ko
        if args.limit and len(translations) >= args.limit:
            break

    args.output.write_text(json.dumps(translations, ensure_ascii=False, indent=2) + "\n")
    print(f"Missing pairs: {len(pairs)}")
    print(f"JA-assisted translations: {len(translations)}")
    print(f"Wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
