# 하이브리드 최종 기준선 재현

이 문서는 2025년 11월부터 2026년 4월까지의 월별 원본에서 최종
하이브리드 코퍼스와 v2.0.0 분류 결과를 재현하고, 기존 기준 파일을
덮어쓰지 않은 채 검증하는 절차를 고정한다.

## 입력과 기준 파일

재생성 입력:

- `202511.csv` ~ `202604.csv`: 월별 원본 6개
- `filter_ads_202511_202604.py`: 보존된 키워드 및 추가 광고 필터
- `baselines/hybrid_final_exclusions.csv`: 소스가 남아 있지 않은 final
  필터 결정 391건의 ID 잠금
- `classify_sns_rule_based.py`: 변경하지 않은 v2.0.0 분류기
- `data/output/gold_standard_192.csv`: 수동 라벨을 보존할 정답셋 원본
- `data/output/gold_supplement_11.csv`: 보충 표본 ID의 출처

읽기 전용 비교 기준:

- `data/output/2511-2604_hybrid.csv`
  - SHA-256:
    `3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e`
- `data/output/sentiment_classified_hybrid.csv`
  - SHA-256:
    `f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d`
- `data/output/gold_standard_192.csv`
  - SHA-256:
    `fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815`

빌드 및 정규화 스크립트는 위 기준 파일 경로로 출력하려 하면
중단한다. 재생성 파일은 `/private/tmp/bonbon_rebuild/`에만 만든 뒤
비교한다.

## 하이브리드 선택 규칙의 복원 근거

월별 원본 136,288건은 `投稿ID_文字列` 기준으로 모두 유일하며, old,
final, hybrid는 모두 이 원본 순서를 유지한다. 실제 ID 집합을 대조하면
다음 관계가 성립한다.

- 보존된 광고 필터 결과(old): 109,037건
- `final − old`: 5,615건
- `old − final`: 134건
- 기존 추가 광고 ID: 5,874건
- `additional ∩ final`: 3,600건
- `hybrid = final − additional`: 110,918건이며 순서도 동일
- `hybrid − old`: 2,015건

보존된 필터의 키워드 판정을 행별로 대조한 결과, hybrid가 old에 복원한
2,015건은 다음 세 경우로 정확히 분해된다.

- 다른 키워드 없이 `第弾` 확장 판정만 받은 행: 2,002건
- `本日…抽選開始…ラインナップ` 확장 판정만 받은 행: 12건
- NFKC 정규화 후에만 `リポスト`가 되는 반각 문자열 행: 1건

현재 저장소에는 `2511-2604_final.csv`를 만든 필터 버전의 소스가 없다.
따라서 남아 있지 않은 규칙을 정규식으로 추측하지 않았다. 실제 ID
차이에서 확인된 아래 391건을
`baselines/hybrid_final_exclusions.csv`에 고정했다.

- 완화 대상이지만 final에서도 제외된 ID: 257건
- old에는 남고 final에서 새로 제외된 ID: 134건

최종 재생성의 상호 배타적 선택 계수는 다음과 같다.

- 기존 키워드 제외: 19,105건
- 완화 후보 중 ID 잠금 제외: 257건
- 기존 추가 광고 분류 제외: 5,874건
- final 전용 ID 잠금 제외: 134건
- 유지: 110,918건

앞의 두 제외를 합치면 기존 문서의 “final 키워드 제외” 19,362건과
일치한다. 빌드 스크립트는 각 계수와 잠금 파일의 사유별 건수를 모두
검사하며 하나라도 달라지면 출력하지 않는다.

## 정답셋 12열 정규화

기준 `gold_standard_192.csv`는 CSV상 20열이지만 의미 있는 열은 앞의
12열이고 뒤의 이름 없는 8열은 모든 행에서 비어 있다.
`normalize_gold_standard_192.py`는 다음 조건에서만 앞 12열을 그대로
복사한다.

- 192행
- 정상 12개 열 이름과 순서 일치
- 뒤의 8개 열 이름과 값이 모두 빈 값
- `post_id` 중복 0건

보충 3건의 ID는 다음과 같다.

- `ID:2013861610389966862`
- `ID:2015459135006126271`
- `ID:2046838197989282094`

`gold_supplement_11.csv`에는 이 3건의 수동 라벨이 비어 있지만, 현재
기준 `gold_standard_192.csv`에는 세 행 모두 `交換取引=1`로 저장되어
있다. 저장소 안에서는 이 수동 라벨을 부여한 별도 근거 파일을 찾을 수
없으므로 출처는 불명이다. 정규화 스크립트는 보충 파일에서 라벨을
재생성하지 않고, 기준 정답셋의 기존 12개 값을 그대로 보존한다. 기존
`make_task5_task6_files.py`는 보충 3건을 빈 라벨로 쓰므로 이 정규화
절차에는 사용하지 않는다.

## 실행 절차

프로젝트 루트에서 지정된 Python으로 실행한다.

```bash
/opt/anaconda3/bin/python3 build_hybrid_corpus.py \
  --root /Users/bsw0610/Desktop/data \
  --output /private/tmp/bonbon_rebuild/2511-2604_hybrid.csv

/opt/anaconda3/bin/python3 classify_sns_rule_based.py \
  --input /private/tmp/bonbon_rebuild/2511-2604_hybrid.csv \
  --output /private/tmp/bonbon_rebuild/sentiment_classified_hybrid.csv

/opt/anaconda3/bin/python3 normalize_gold_standard_192.py \
  --input data/output/gold_standard_192.csv \
  --output /private/tmp/bonbon_rebuild/gold_standard_192_normalized.csv \
  --supplement data/output/gold_supplement_11.csv \
  --hybrid /private/tmp/bonbon_rebuild/sentiment_classified_hybrid.csv

/opt/anaconda3/bin/python3 verify_hybrid_rebuild.py \
  --root /Users/bsw0610/Desktop/data \
  --rebuild-dir /private/tmp/bonbon_rebuild
```

검증 스크립트는 코퍼스와 분류 결과의 행 수, 열, 모든 셀, ID 집합,
ID 순서, 전체 SHA-256을 기준과 대조한다. 또한 정답셋의 192행 × 12열,
ID 유일성, 192/192 결합, 보충 3건의 `交換取引=1`, 전체 수동 라벨
보존을 검사한다. 마지막으로 별도 `repeat/` 디렉터리에 전 과정을 다시
실행해 세 출력의 SHA-256이 첫 실행과 같은지 확인한다.

정규화 결과의 고정 SHA-256은 다음과 같다.

`ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c`
