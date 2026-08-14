# スライド13〜16 PNG再生成・検証手順

## 目的

`regenerate_slide_assets.py`は、Canva「ボンドロ最終発表」の
10〜16ページ差し替え計画のうち、データ図版が必要な13〜16ページを
同じ確定入力から再生成する。

生成物は候補であり、リポジトリ内の既存PNG、Canva、PPTXを自動で
置き換えない。出力先はリポジトリ外だけを許可する。

## 確定入力

| 用途 | ファイル | SHA-256 |
|---|---|---|
| 正解セット原本 | `data/output/gold_standard_192.csv` | `fbaa615cf9dc2599df93287857be584223f46f3f20ca901ca09fe5fb7d305815` |
| 正規化正解セット | `data/output/gold_standard_192_normalized.csv` | `ed4afaadf102e21973d4b7cbfd1b4cbdd49040230ac5c26f6d0d2750e3982c2c` |
| ハイブリッドコーパス | `data/output/2511-2604_hybrid.csv` | `3bf78817892b356b0a4b1ea693a3f66d94e78f03196401832fd2b6e397b51c8e` |
| 分類結果 | `data/output/sentiment_classified_hybrid.csv` | `f273c9306507804ae0dc1e2ed28292f9b2bc5f4100f7564c984117a3a8b6371d` |

ページ16の固定98件標本は次の2ファイルを投稿IDで重複除去して使う。
これらの実ファイルSHAは`p16_metrics.json`とmanifestに記録し、
検証時に再照合する。

- `outputs/negotiation-unclassified-20260728/negotiation_expressions_not_exchange_random50.csv`
- `data/output/random_sample_50_negotiation_not_exchange_202511_202604.csv`

## 出力

1回の生成で次の9ファイルを出力する。

- `p13_agreement.png`
- `p13_metrics.json`
- `p14_composition.png`
- `p14_metrics.json`
- `p15_new_accounts.png`
- `p15_metrics.json`
- `p16_expressions.png`
- `p16_metrics.json`
- `slide_assets_manifest.json`

PNGはすべて1920×1080。metrics JSONは計算値、分母、定義、表示文字列、
入力SHAを保持し、manifestは各PNG・JSONのSHAとレンダー検査結果を
まとめる。

## ページ別計算

### ページ13

`evaluate_v2_hybrid_192.calculate_evaluation_metrics()`を使って、
公式192件の緩和基準カテゴリ別F1を7カテゴリすべて計算する。
交換・取引0.869を主強調、中立0.625を補助強調とし、情報共有0.000も
非表示にしない。緩和基準micro F1 0.577と多ラベル基準micro F1
0.595は補助値として表示する。

### ページ14

公式192件の各カテゴリを独立した二値比率として計算し、
`slide_number_definitions.wald_interval()`で`z=1.96`のWald 95%区間を
出す。複数ラベル合計217、構成比合計113.0%、分類器の焦り・競争
3,272/110,918=2.9%も同じ根拠JSONに保存する。PNGには情報共有の
広告除去バイアス注記を組み込む。

### ページ15

分類結果の交換・取引24,316件を`ユーザーID`で集計する。KPIは
投稿24,316件、アカウント10,677、1回のみ7,198/67.4%、上位1%
106アカウント・3,619件・14.9%を表示する。定型書式51.0%は
このページのKPIに使わず、ページ16へ移す。

### ページ16

交換投稿の定型書式は
`slide_number_definitions.is_exchange_template()`で12,411件、
51.0%と計算する。固定98件標本では共通定義関数を使い、
リプライ79件、定型的な挨拶48件、`ご検討／御検討`42件、
交換比率17件を計算する。

二つの原文例は画面に表示しない。固定標本中の連続した文字列との
完全一致と匿名化根拠は`p16_metrics.json`にのみ保持する。

## 生成

出力先を省略すると、`tempfile.mkdtemp()`で新しい一時ディレクトリが
作られる。

```bash
/opt/anaconda3/bin/python3 regenerate_slide_assets.py
```

明示した一時ディレクトリへ出す場合:

```bash
/opt/anaconda3/bin/python3 regenerate_slide_assets.py \
  --output-dir /private/tmp/bonbon_slides_10_16_rework_run1
```

リポジトリ内部を`--output-dir`に指定すると、既存PNGの誤上書きを
防ぐため停止する。

## 検証

単独実行:

```bash
/opt/anaconda3/bin/python3 verify_slide_assets.py \
  --assets-dir /private/tmp/bonbon_slides_10_16_rework_run1
```

再現性検証:

```bash
/opt/anaconda3/bin/python3 regenerate_slide_assets.py \
  --output-dir /private/tmp/bonbon_slides_10_16_rework_run2

/opt/anaconda3/bin/python3 verify_slide_assets.py \
  --assets-dir /private/tmp/bonbon_slides_10_16_rework_run1 \
  --comparison-dir /private/tmp/bonbon_slides_10_16_rework_run2
```

検証項目:

- 正解セット192行×12列、ID一意192件、分類結果結合192/192
- 原本先頭12列の全セル一致、補充3件の交換ラベル保存
- 確定4入力のSHA-256一致
- ページ13の2つのmicro F1と7カテゴリF1
- ページ14の7区間、217ラベル、113.0%、焦り・競争2.9%
- ページ15の12項目 12/12
- ページ16の7数値と匿名化引用2件の原文根拠
- PNG形式、1920×1080、非空、幅1,720px以上
- 日本語グリフ欠落0、キャンバス外テキスト0
- manifestのPNG・JSON SHA
- 二つの出力ディレクトリにある9ファイルのSHA完全一致

追加回帰検証:

```bash
/opt/anaconda3/bin/python3 verify_slide_numbers.py \
  --output /private/tmp/slide_numbers_check_after.md

/opt/anaconda3/bin/python3 -m unittest -v \
  test_slide_number_definitions.py test_sentiment_classifier.py

/opt/anaconda3/bin/ruff check \
  regenerate_slide_assets.py verify_slide_assets.py \
  slide_number_definitions.py verify_slide_numbers.py \
  test_slide_number_definitions.py test_sentiment_classifier.py

git diff --check
```

生成後は13〜16ページのPNGを実際に開き、タイトル、数値、軸、
注記、引用、余白、折返し、重なりを確認してからCanvaの差し替え候補と
する。
