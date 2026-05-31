# Affin.ko 번역 스타일 가이드

## 원칙

1. **일본식 한자 표기 지양** — 改, 見本 같은 일본 UI 표기를 그대로 쓰지 않습니다.
2. **디자인 툴 관용어 우선** — 포토샵·일러스트레이터·피그마 등 국내 사용자에게 익숙한 용어를 따릅니다.
3. **원문 유지** — 마땅한 대체어가 없으면 Affinity, RGB, EXIF 같은 고유명사·약어는 영문을 유지합니다.

## 용어 표

| English | 권장 | 피하기 |
|---------|------|--------|
| New | 새 / 새로 만들기 | 신규 |
| Snapping | 스냅 | 스내핑 |
| Swatches | 스와치 | 견본 (Swatches 맥락) |
| Application | 앱 | 응용프로그램 |
| Artistic Text | 아트 텍스트 | 에술 텍스트 |
| Enable | 사용 / 활성화 | 유효화 |
| About | … 정보 | …에 관하여 |
| Toggle | … 켜기/끄기 | … 켜고 끄기 |
| Crop | 자르기 | 크롭 |
| Gradient | 그라디언트 | 그레이디언트 |
| Pan (view) | 화면 이동 | 초점이동 |
| Action | 동작 | 행동 |
| Assistant | 도우미 | 손쉬운 사용 |

## 수정 방법

1. `.affin.ko.dictionary`에서 해당 `s/"English";/"한국어";/` 줄을 수정
2. 또는 `.developer/afnk_review.py`로 후보를 확인:

```sh
python3 .developer/afnk_review.py
python3 .developer/afnk_review.py --apply   # 제안 일괄 반영
```

3. `~/Affin.ko/Affinity-ko` 재실행

## 검수 도구

| 스크립트 | 용도 |
|---------|------|
| `.developer/afnk_extract.py` | 미번역 문자열 추출 (일본어 참고) |
| `.developer/afnk_review.py` | 어색한 번역·용어 불일치 검출 |
| `.developer/afnk_dictionary.command` | 항목 하나씩 추가 |

## PR/기여 시

- 한 커밋에 관련 용어만 묶어서 수정 (예: Snapping 일괄, New 일괄)
- UI에서 실제로 보이는 문맥을 스크린샷과 함께 남기면 리뷰에 도움이 됩니다.
