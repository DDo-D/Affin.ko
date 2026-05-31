#!/usr/bin/env python3
"""Translate missing strings using complete JA->KO mapping (no hybrid output)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXTRACT = REPO_ROOT / ".developer/afnk_extract.py"
AUTO = REPO_ROOT / ".developer/afnk_auto_translate.py"
PRIORITY = REPO_ROOT / ".developer/afnk_priority_build.py"
JA_ASSIST = REPO_ROOT / ".developer/afnk_ja_assist.py"

# Full phrase JA -> Adobe-style KO (longest first at runtime)
PHRASES: dict[str, str] = {}


def load_modules():
    spec = importlib.util.spec_from_file_location("afnk_priority_build", PRIORITY)
    pri = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pri)
    spec2 = importlib.util.spec_from_file_location("afnk_auto_translate", AUTO)
    auto = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(auto)
    spec3 = importlib.util.spec_from_file_location("afnk_ja_assist", JA_ASSIST)
    ja = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(ja)
    return pri, auto, ja


def has_japanese(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", text))


def ja_to_ko_full(japanese: str, ja_mod) -> str | None:
    if not japanese or not has_japanese(japanese):
        return None
    result = japanese
    for ja, ko in sorted(ja_mod.JA_FRAGMENTS.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(ja, ko)
    # common endings
    replacements = {
        "します": "합니다",
        "してください": "하세요",
        "できません": "할 수 없습니다",
        "ありません": "없습니다",
        "です": "입니다",
        "である": "입니다",
        "の": " ",
        "を": " ",
        "が": " ",
        "に": " ",
        "で": " ",
        "と": " ",
        "から": "에서",
        "まで": "까지",
        "または": " 또는 ",
        "および": " 및 ",
        "オブジェクト": "개체",
        "ポイント": "포인트",
        "エッジ": "가장자리",
        "コンテンツ": "콘텐츠",
        "フレーム": "프레임",
        "ピクチャ": "그림",
        "マーキー": "선택 상자",
        "選択": "선택",
        "解除": "해제",
        "移動": "이동",
        "回転": "회전",
        "スケール": "크기 조절",
        "制約": "제약",
        "無視": "무시",
        "別の": "다른",
        "空の": "빈 ",
        "領域": "영역",
        "実행": "실행",
        "編集": "편집",
        "追加": "추가",
        "削除": "삭제",
        "設定": "설정",
        "表示": "표시",
        "非表示": "숨기기",
        "有効": "사용",
        "無効": "사용 안 함",
        "警告": "경고",
        "エラー": "오류",
        "ファイル": "파일",
        "フォルダ": "폴더",
        "ドキュメント": "문서",
        "レイヤー": "레이어",
        "マスク": "마스크",
        "ブラシ": "브러시",
        "フィルター": "필터",
        "エフェクト": "효과",
        "調整": "조정",
        "プリセット": "사전 설정",
        "スナップ": "스냅",
        "スワッチ": "견본",
        "パターン": "패턴",
        "テクスチャ": "텍스처",
        "グラデーション": "그라데이션",
        "不透明度": "불투명도",
        "変形": "변형",
        "書き出し": "내보내기",
        "読み込み": "가져오기",
        "環境設定": "환경 설정",
        "裁ち落とし": "도련",
        "メタデータ": "메타데이터",
        "パスワード": "암호",
        "品質": "품질",
        "圧縮": "압축",
        "解像度": "해상도",
        "プロファイル": "프로필",
        "カラー": "색상",
        "チャンネル": "채널",
        "ヒストグラム": "히스토그램",
        "ナビゲーター": "탐색기",
        "プレビュー": "미리보기",
        "履歴": "기록",
        "スナップショット": "스냅샷",
        "スタジオ": "스튜디오",
        "ペルソナ": "페르소나",
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
        "レンズ": "렌즈",
        "パノラマ": "파노라마",
        "アシスタント": "도우미",
        "マクロ": "매크로",
        "テキスト": "텍스트",
        "フォント": "글꼴",
        "段落": "단락",
        "文字": "문자",
        "ガイド": "가이드",
        "グリッド": "격자",
        "余白": "여백",
        "塗り": "채우기",
        "線": "획",
        "パス": "패스",
        "アンカー": "앵커",
        "ノード": "노드",
        "曲線": "곡선",
        "複製": "복제",
        "貼り付け": "붙여넣기",
        "切り取り": "잘라내기",
        "コピー": "복사",
        "元に戻す": "실행 취소",
        "やり直し": "다시 실행",
        "保存": "저장",
        "開く": "열기",
        "閉じる": "닫기",
        "適用": "적용",
        "キャンセル": "취소",
        "リセット": "재설정",
        "更新": "업데이트",
        "同期": "동기화",
        "検索": "검색",
        "置換": "바꾸기",
        "挿入": "삽입",
        "名前": "이름",
        "タイトル": "제목",
        "説明": "설명",
        "作者": "저자",
        "日付": "날짜",
        "バージョン": "버전",
        "アカウント": "계정",
        "ヘルプ": "도움말",
        "チュートリアル": "튜토리얼",
        "ライセンス": "라이선스",
        "プライバシー": "개인정보",
        "利用規約": "약관",
        "アップグレード": "업그레이드",
        "試用版": "체험판",
        "サブスクリプション": "구독",
        "クラウド": "클라우드",
        "オンライン": "온라인",
        "オフライン": "오프라인",
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
        "角度": "각도",
        "半径": "반경",
        "強度": "강도",
        "量": "양",
        "許容値": "허용치",
        "しきい値": "임계값",
        "方法": "방법",
        "形式": "형식",
        "ソース": "소스",
        "ターゲット": "대상",
        "結果": "결과",
        "進行状況": "진행률",
        "完了": "완료",
        "失敗": "실패",
        "成功": "성공",
        "待機中": "대기 중",
        "処理中": "처리 중",
        "読み込み中": "불러오는 중",
        "保存中": "저장 중",
        "エクスポート中": "내보내는 중",
        "インポート中": "가져오는 중",
        "レンダリング中": "렌더링 중",
        "分析中": "분석 중",
        "最適化中": "최적화 중",
        "圧縮中": "압축 중",
        "解凍中": "압축 해제 중",
        "アップロード中": "업로드 중",
        "ダウンロード中": "다운로드 중",
        "インストール中": "설치 중",
        "アンインストール中": "제거 중",
        "更新中": "업데이트 중",
        "同期中": "동기화 중",
        "接続中": "연결 중",
        "切断中": "연결 해제 중",
        "確認": "확인",
        "はい": "예",
        "いいえ": "아니요",
        "OK": "확인",
        "続行": "계속",
        "戻る": "뒤로",
        "次へ": "다음",
        "完了": "완료",
        "スキップ": "건너뛰기",
        "再試行": "다시 시도",
        "無視": "무시",
        "受け入れ": "수락",
        "拒否": "거부",
    }
    for ja, ko in sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(ja, ko)
    # cleanup spaces
    result = re.sub(r"\s+", " ", result).strip()
    if has_japanese(result):
        return None
    if not re.search(r"[\uac00-\ud7a3]", result):
        return None
    return result


def collect_all_missing(app, dictionary, file_filter=None):
    pri, auto, ja_mod = load_modules()
    import subprocess
    import tempfile

    RESOURCE_ROOTS = (
        "Contents/Resources",
        "Contents/Frameworks/libcocoaui.framework/Versions/A/Resources",
    )

    def read_utf16(path):
        return subprocess.check_output(
            ["iconv", "-f", "UTF-16LE", "-t", "UTF-8", str(path)],
            text=True,
            errors="replace",
        )

    def apply_dictionary(content):
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

    def parse_strings(content):
        pairs = {}
        for match in re.finditer(r'^"(.+?)"\s*=\s*"(.*?)";\s*$', content, re.MULTILINE):
            pairs[match.group(1)] = match.group(2)
        return pairs

    def is_english(text):
        if not text.strip():
            return False
        if re.search(r"[\uac00-\ud7a3]", text):
            return False
        return bool(re.search(r"[A-Za-z]{2,}", text))

    rows = []
    seen = set()
    for resource in RESOURCE_ROOTS:
        en_dir = app / resource / "en-US.lproj"
        ja_dir = app / resource / "ja.lproj"
        if not en_dir.is_dir():
            continue
        for en_path in sorted(en_dir.glob("*.strings")):
            if file_filter and file_filter not in en_path.name:
                continue
            ja_path = ja_dir / en_path.name
            ja_content = read_utf16(ja_path) if ja_path.exists() else ""
            en_content = read_utf16(en_path)
            ko_content = apply_dictionary(en_content)
            en_pairs = parse_strings(en_content)
            ja_pairs = parse_strings(ja_content)
            ko_pairs = parse_strings(ko_content)
            for key, english in en_pairs.items():
                if english in seen:
                    continue
                if not is_english(ko_pairs.get(key, english)):
                    continue
                seen.add(english)
                rows.append({"english": english, "japanese": ja_pairs.get(key, "")})
    return rows, pri, auto, ja_mod


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=Path("/Applications/Affinity.app"))
    parser.add_argument("--dictionary", type=Path, default=REPO_ROOT / ".affin.ko.dictionary")
    parser.add_argument("--file", dest="file_filter")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    rows, pri, auto, ja_mod = collect_all_missing(args.app, args.dictionary, args.file_filter)
    glossary = auto.load_glossary(REPO_ROOT / ".developer/adobe_glossary.json")
    translations: dict[str, str] = {}

    for row in rows:
        english = row["english"]
        japanese = row.get("japanese", "")
        ko = pri.translate_row(english, japanese)
        if not ko:
            ko = auto.translate_string(english, glossary)
        if not ko and japanese:
            ko = ja_mod.ja_to_ko(japanese)
        if not ko:
            ko = ja_to_ko_full(japanese, ja_mod)
        if ko and ko != english and not has_japanese(ko):
            translations[english] = ko
        if args.limit and len(translations) >= args.limit:
            break

    args.output.write_text(json.dumps(translations, ensure_ascii=False, indent=2) + "\n")
    print(f"Missing rows: {len(rows)}")
    print(f"Translated: {len(translations)}")
    print(f"Wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
