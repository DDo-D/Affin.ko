# Affin.ko 패치 가이드 (Affinity 3.2.1)

이 문서는 **번역 사전으로 Affinity.app에 한국어 `ko.lproj`를 넣는 방법**을 정리합니다.  
검증된 대상: **Affinity 3.2.1 (빌드 4425)**, 단일 앱 `Affinity.app`.

## 패치가 하는 일

| 단계 | 설명 |
|------|------|
| 입력 | 앱 번들 안 `en-US.lproj/*.strings` (UTF-16LE) |
| 변환 | UTF-8 → `.affin.ko.dictionary` (sed) → UTF-8 |
| 출력 | `ko.lproj/*.strings` (**UTF-16LE + CRLF**, 공식 `ja.lproj`와 동일 형식) |
| 설치 위치 | `Contents/Resources/ko.lproj/` 및 `Contents/Frameworks/libcocoaui.framework/.../ko.lproj/` |

앱 업데이트 시 `ko.lproj`가 지워지거나 영어로 덮일 수 있습니다. 업데이트 후 **다시 패치**하면 됩니다.

## 빠른 설치 (기존과 동일)

```sh
chmod +x ~/Affin.ko/Affinity-ko ~/Affin.ko/affin-ko-apply ~/Affin.ko/affin-ko-build
AFFIN_KO_NO_PULL=1 ~/Affin.ko/Affinity-ko
```

- `AFFIN_KO_NO_PULL=1`: 실행 시 `git pull` 생략 (선택)
- Affinity는 실행 중이면 자동 종료 후 패치합니다.

설치 후: **설정 → 일반 → 언어 → 한국어**

## 권장: 빌드와 설치 분리

번역만 검증하거나, 여러 Mac에 같은 패치를 나눠 쓸 때 유용합니다.

### 1) 패치 번들 만들기 (앱은 수정하지 않음)

```sh
cd ~/Affin.ko
./affin-ko-build
# → dist/3.2.1-4425/ 에 manifest.json + ko.lproj 트리 생성
```

### 2) Affinity.app에 적용

```sh
./affin-ko-apply ~/Affin.ko/dist/3.2.1-4425
# 또는 빌드+적용 한 번에:
./affin-ko-apply --build
```

다른 경로에 Affinity가 있으면:

```sh
AFFINITY_APP=/Applications/Affinity.app ./affin-ko-apply --build
```

## 버전이 다를 때

스크립트는 **3.2.1 / 4425** 기준으로 경고를 냅니다.  
다른 빌드도 시도할 수 있지만, 문자열 키가 바뀌면 일부 UI가 영어로 남거나 깨질 수 있습니다.

## 이전 Affin.ko (Designer 2 / Photo 2 / Publisher 2)와의 차이

| 구분 | 구버전 (2.x 분리 앱) | 현재 (3.x 통합) |
|------|---------------------|-----------------|
| 앱 | Designer 2, Photo 2, Publisher 2 | `Affinity.app` 하나 |
| 원본 locale | `en.lproj` | `en-US.lproj` |
| 스크립트 | `.developer/legacy/Affin-ko` | `Affinity-ko`, `affin-ko-build` |
| 인코딩 | UTF-8로 쓰던 경우 있음 | **UTF-16LE 필수** (공식 locale 형식) |

레거시 스크립트는 `.developer/legacy/`에만 참고용으로 남겨 두었습니다.

## 번역 범위

- 사전(`.affin.ko.dictionary`)에 있는 문자열만 한국어로 바뀝니다.
- 나머지는 영어(원문) 그대로입니다.
- 진행률·검수는 `.developer/afnk_extract.py`, `afnk_review.py` 참고.

## 문제 해결

| 증상 | 확인 |
|------|------|
| 언어 목록에 한국어 없음 | `ko.lproj`가 두 경로 모두에 있는지, Affinity 완전 재시작 |
| 한글이 깨짐 | 예전 UTF-8 패치본이면 `affin-ko-apply --build`로 **UTF-16LE**로 다시 설치 |
| 메뉴만 영어 | 해당 `strings` 키가 사전에 없음 → `.developer` 도구로 추가 |
| 앱 업데이트 후 초기화 | 정상 동작 → 패치 스크립트 재실행 |

## 파일 구조 (dist 번들)

```text
dist/3.2.1-4425/
  manifest.json
  Resources/ko.lproj/*.strings
  Frameworks/libcocoaui.framework/Versions/A/Resources/ko.lproj/*.strings
```

`manifest.json`에는 빌드 시점 Affinity 버전·인코딩 정보가 들어 있습니다.
