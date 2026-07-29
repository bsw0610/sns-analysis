# 페이지 13~15 그래프 재생성 절차

## 목적과 보호 원칙

`regenerate_slide_assets.py`는 확정된 평가·수치 정의로 페이지 13~15의
PNG 교체 후보와 계산 근거 JSON을 생성한다. `--output-dir`는 필수이며,
저장소 내부 경로는 거부한다. 따라서 다음 기존 최종 그래프를 자동으로
덮어쓰지 않는다.

- `data/output/slides/p13_agreement.png`
- `data/output/slides/p14_composition.png`
- `data/output/slides/p15_new_accounts.png`

검증을 통과한 임시 PNG를 실제로 열어 본 뒤에만 위 경로의 교체 후보로
제시한다. Canva와 PPTX는 이 절차의 대상이 아니다.

## 고정 입력

| 역할 | 파일 | SHA-256 |
|---|---|---|
| 보존 원본 정답셋 | `data/output/gold_standard_192.csv` | `fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815` |
| 공식 평가 정답셋 | `data/output/gold_standard_192_normalized.csv` | `ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c` |
| 하이브리드 코퍼스 | `data/output/2511-2604_hybrid.csv` | `3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e` |
| 분류 결과 | `data/output/sentiment_classified_hybrid.csv` | `f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d` |

공식 정답셋이 없거나 원본 첫 12열과 다르면
`normalize_gold_standard_192.py`의 생성 명령을 포함한 오류로 중단한다.
20열 보존 원본으로 조용히 대체하지 않는다.

## 차트 계약과 계산 정의

### 페이지 13

- 질문: 확정된 두 평가 방식의 전체 성능과 연구 핵심 카테고리 성능은
  각각 얼마인가.
- 형태: 직접 라벨이 있는 가로 막대.
- 완화 micro F1: 단일 예측이 사람 라벨 집합에 포함되면 해당
  카테고리의 TP로 처리하고, 모든 카테고리의 TP·FP·FN을 합산한다.
- 다중 라벨 micro F1: `category_scores >= 1.8`인 전체 카테고리를
  예측 집합으로 사용하고, 모든 카테고리의 TP·FP·FN을 합산한다.
- 교환·거래 완화 F1: `交換・取引` 카테고리만의 TP·FP·FN을 사용한다.
- 세 값 모두 `evaluate_v2_hybrid_192.py`의
  `calculate_evaluation_metrics()`를 직접 사용한다.

교환·거래 F1은 카테고리별 값이고 두 micro F1은 전체 카테고리 합산
값이므로, 그래프에 집계 단위가 다르다는 주석을 표시한다.

### 페이지 14

- 질문: 사람 라벨의 실제 카테고리 구성과 표본 불확실성은 어떠한가.
- 형태: 점·구간 그래프. 점은 구성비, 선과 캡은 신뢰구간이다.
- 분자: 192건 중 해당 사람 라벨이 `1`인 게시물 수.
- 분모: 192.
- 신뢰구간: `slide_number_definitions.wald_interval()`의 Wald 95%,
  `z=1.96`, 카테고리별 이진 처리, 단위 구간으로 절단.
- 반올림: 백분율 소수점 첫째 자리.
- 다중 라벨을 허용하므로 연장 라벨 수는 217개이고 구성비 합계는
  113.0%이다. 그래프에 100%를 초과할 수 있음을 표시한다.

`焦り・競争`의 분류기 참고 표시는 분류 결과의 실제
`3,272 / 110,918 = 2.949...%`를 소수점 첫째 자리로 표시한 `2.9%`다.
사람 라벨 구성비와 혼동하지 않도록 `x` 표식과 직접 라벨을 사용한다.

### 페이지 15

- 질문: 교환·거래 게시물은 어떤 계정 집중도와 정형성을 보이며,
  신규 참여 계정은 월별로 어떻게 관측됐는가.
- 계정 키: `ユーザーID`.
- 상위 1% 계정 수: `floor(10,677 × 0.01) = 106`.
- 상위 1% 게시물 비중: `3,619 / 24,316 = 14.9%`.
- 정형 교환 서식: 별도 정규식을 두지 않고
  `slide_number_definitions.is_exchange_template()`을 직접 사용한다.
- 정형 서식 비중: `12,411 / 24,316 = 51.0%`.
- 월별 신규 계정: 각 `ユーザーID`의 첫 교환·거래 게시월.

2026년 4월은 수집 종료월이다. 이후 감소 여부를 추정하지 않고, 막대의
해칭과 직접 주석으로 관측 종단임을 표시한다.

## 실행

첫 번째 임시 생성:

```bash
PYTHONDONTWRITEBYTECODE=1 \
MPLCONFIGDIR=/private/tmp/bonbon_mplconfig \
/opt/anaconda3/bin/python3 regenerate_slide_assets.py \
  --output-dir /private/tmp/bonbon_slide_assets_run1
```

두 번째 독립 생성과 반복성 검증:

```bash
PYTHONDONTWRITEBYTECODE=1 \
MPLCONFIGDIR=/private/tmp/bonbon_mplconfig \
/opt/anaconda3/bin/python3 regenerate_slide_assets.py \
  --output-dir /private/tmp/bonbon_slide_assets_run2

PYTHONDONTWRITEBYTECODE=1 \
MPLCONFIGDIR=/private/tmp/bonbon_mplconfig \
/opt/anaconda3/bin/python3 verify_slide_assets.py \
  --assets-dir /private/tmp/bonbon_slide_assets_run1 \
  --comparison-dir /private/tmp/bonbon_slide_assets_run2
```

생성 파일:

- `p13_agreement.png`, `p13_metrics.json`
- `p14_composition.png`, `p14_metrics.json`
- `p15_new_accounts.png`, `p15_metrics.json`
- `slide_assets_manifest.json`

manifest에는 입력 SHA-256, 정답셋 구조·결합 검증, 사용 글꼴,
PNG 해상도, 글리프 누락 및 캔버스 밖 텍스트 검사, 각 산출물 SHA-256을
기록한다. 모든 PNG는 1920×1080으로 생성한다.

## 최종 교체

생성·자동 검증·실제 이미지 검토가 모두 끝나도 스크립트는 저장소의
최종 PNG를 복사하거나 덮어쓰지 않는다. 검토자는 임시 PNG와 기존
PNG의 차이를 확인한 뒤 세 파일을 각각 교체할지 결정한다.
