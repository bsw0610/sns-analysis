# X/Twitter 데이터 분석 폴더 설명

이 폴더는 X/Twitter 投稿 데이터를 정리하고, 일본어 텍스트를 단어 단위로 분석해 Word2Vec 단어 임베딩 모델을 만든 작업 폴더입니다.

주요 분석 대상은 `ボンボンドロップシール` 관련 投稿 데이터로 보입니다.

## 전체 작업 흐름

```text
월별 CSV
  -> INPUT.csv
  -> INPUT_new.csv
  -> clean.csv
  -> clean.wakati
  -> clean.model
  -> vector.tsv / metadata.tsv
  -> 발표 자료
```

쉽게 말하면, 원본 投稿 데이터를 모아서 필요한 텍스트만 뽑고, 글자를 정리한 뒤, 일본어 문장을 단어 단위로 나누고, 마지막으로 단어의 의미 관계를 숫자 벡터로 만든 구조입니다.

## 원본 데이터

### `202511.csv` ~ `202604.csv`

2025년 11월부터 2026년 4월까지의 월별 X/Twitter 投稿 데이터입니다.

각 파일에는 다음과 같은 정보가 들어 있습니다.

- 投稿ID
- 키워드
- 계정 ID
- 사용자 이름
- 投稿 시간
- 投稿 내용
- URL
- 리포스트 수
- 좋아요 수
- 조회 수
- 답글 수

이 파일들이 가장 처음 단계의 원본 데이터입니다.

### `INPUT.csv`

월별 CSV 파일들을 하나로 합친 파일로 보입니다.

여러 달의 投稿 데이터를 한 번에 처리하기 위해 만든 통합 데이터입니다.

### `INPUT_new.csv`

`INPUT.csv`에서 `内容` 컬럼, 즉 投稿 본문만 뽑아낸 파일입니다.

분석에 필요한 텍스트만 남긴 중간 파일입니다.

## 텍스트 정제 결과

### `clean.csv`

投稿 본문에서 기호, URL, 불필요한 문자 등을 제거한 정제 텍스트 파일입니다.

예를 들어 느낌표, 특수문자, 분석에 방해되는 문자를 줄여서 모델이 더 잘 학습할 수 있게 만든 파일입니다.

### `clean.wakati`

`clean.csv`의 일본어 문장을 단어 단위로 띄어쓴 파일입니다.

일본어는 일반적으로 띄어쓰기가 없기 때문에, 컴퓨터가 단어를 인식하려면 먼저 단어 단위로 나누는 과정이 필요합니다.

예시는 다음과 같습니다.

```text
シルバニア の ボンボンドロップシール とか で たら 気 が 狂う な
```

이런 형태를 일본어 처리에서는 `分かち書き`라고 부릅니다.

## Word2Vec 모델 관련 파일

### `clean.model`

Gensim Word2Vec 모델 본체입니다.

Word2Vec은 단어를 숫자 벡터로 바꾸는 모델입니다. 비슷한 문맥에서 자주 등장하는 단어들은 서로 가까운 벡터를 갖게 됩니다.

예를 들어 같은 주제에서 자주 같이 쓰이는 단어들은 모델 안에서 의미적으로 가까운 위치에 놓입니다.

### `clean.model.wv.vectors.npy`

각 단어의 벡터값이 저장된 NumPy 파일입니다.

쉽게 말해, 단어 하나하나를 숫자 배열로 바꾼 결과입니다.

### `clean.model.syn1neg.npy`

Word2Vec 학습 내부에서 사용하는 추가 가중치 파일입니다.

`clean.model`을 정상적으로 불러올 때 함께 필요한 보조 파일입니다.

## TensorFlow Embedding Projector용 파일

### `vector.tsv`

TensorFlow Embedding Projector에 업로드할 수 있는 벡터 파일입니다.

한 줄이 한 단어의 숫자 벡터를 의미합니다.

### `metadata.tsv`

`vector.tsv`의 각 줄이 어떤 단어인지 알려주는 라벨 파일입니다.

예를 들어 `vector.tsv`의 첫 번째 줄이 어떤 단어의 벡터인지, `metadata.tsv`의 첫 번째 줄에서 확인할 수 있습니다.

## Jupyter Notebook

### `2026_Twitter用データクリーニング .ipynb`

Twitter/X 데이터를 정리하는 Jupyter Notebook입니다.

주요 역할은 다음과 같습니다.

- 원본 CSV 불러오기
- 投稿 본문 추출
- 불필요한 문자 제거
- 정제된 텍스트 파일 생성

### `Gemsim40_26_3年ゼミ【TensorFlow_Embedding Projector】Vector_meta.tsvファイル生成  (6).ipynb`

Word2Vec 모델을 학습하고, TensorFlow Embedding Projector용 파일을 만드는 Jupyter Notebook입니다.

주요 역할은 다음과 같습니다.

- `clean.wakati` 파일 읽기
- Word2Vec 모델 학습
- `clean.model` 저장
- `vector.tsv` 생성
- `metadata.tsv` 생성

노트북 기록상 Word2Vec 모델은 대략 다음 설정으로 학습되었습니다.

- 벡터 차원: 350
- window 크기: 15
- 학습 epoch: 10
- 최소 등장 횟수: 5

## 발표 자료

### `outputs/bonbon_drop_seal_analysis.pptx`

분석 결과를 정리한 PowerPoint 발표 자료입니다.

제목과 내용상 `ボンボンドロップシール` 관련 投稿 데이터를 바탕으로 구매층, 매력, 소비자 심리 등을 정리한 자료로 보입니다.

### `outputs/bonbon_drop_seal_analysis.pptx.inspect.ndjson`

PowerPoint 파일의 내부 구조를 검사한 JSON Lines 형식 파일입니다.

슬라이드 안의 텍스트, 도형, 위치 정보 등이 들어 있습니다. 일반 분석에는 필수 파일은 아니고, PPT 구조를 확인하거나 자동으로 검증할 때 쓰는 보조 파일입니다.

## 자동 생성 파일

### `.ipynb_checkpoints/`

Jupyter Notebook이 자동으로 만든 백업 폴더입니다.

노트북이나 CSV의 중간 저장본이 들어 있습니다.

### `.DS_Store`

macOS Finder가 폴더 보기 설정을 저장하는 시스템 파일입니다.

데이터 분석에는 필요하지 않습니다.

## 파일별 한 줄 요약

| 파일 또는 폴더 | 역할 |
| --- | --- |
| `202511.csv` ~ `202604.csv` | 월별 X/Twitter 원본 投稿 데이터 |
| `INPUT.csv` | 월별 데이터를 합친 통합 CSV |
| `INPUT_new.csv` | 投稿 본문만 뽑은 CSV |
| `clean.csv` | 불필요한 문자를 제거한 정제 텍스트 |
| `clean.wakati` | 일본어 문장을 단어 단위로 나눈 텍스트 |
| `clean.model` | Word2Vec 학습 모델 |
| `clean.model.wv.vectors.npy` | 단어 벡터값 저장 파일 |
| `clean.model.syn1neg.npy` | Word2Vec 내부 학습 가중치 파일 |
| `vector.tsv` | Embedding Projector용 벡터 파일 |
| `metadata.tsv` | Embedding Projector용 단어 라벨 파일 |
| `2026_Twitter用データクリーニング .ipynb` | 데이터 클리닝용 노트북 |
| `Gemsim40_26_3年ゼミ...ipynb` | Word2Vec 및 벡터 파일 생성 노트북 |
| `outputs/bonbon_drop_seal_analysis.pptx` | 분석 결과 발표 자료 |
| `.ipynb_checkpoints/` | Jupyter 자동 백업 폴더 |
| `.DS_Store` | macOS 시스템 파일 |

## 초보자를 위한 핵심 개념

### CSV

표 형태의 데이터를 저장하는 파일입니다. 엑셀처럼 행과 열로 구성되어 있습니다.

### 데이터 클리닝

분석에 방해되는 문자, 빈값, 불필요한 정보를 제거해서 데이터를 깨끗하게 만드는 과정입니다.

### 分かち書き

일본어 문장을 단어 단위로 나누는 작업입니다. Word2Vec 같은 텍스트 분석 모델을 만들기 전에 필요한 전처리입니다.

### Word2Vec

단어를 숫자 벡터로 바꾸는 기계학습 모델입니다. 단어의 의미나 문맥상 가까움을 숫자로 표현할 수 있게 해줍니다.

### Embedding Projector

단어 벡터를 시각적으로 확인할 수 있는 TensorFlow 도구입니다. 단어들이 의미적으로 얼마나 가까운지 2D 또는 3D 공간에서 볼 수 있습니다.
