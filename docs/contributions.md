# Contributions, source material, and AI workflow

[Back to the repository README](../README.md) · [Documentation index](README.md)

<a id="ai-workflow"></a>

## AIに実装を任せ、別の目で確かめた進め方

このリポジトリのコード・テスト・文書は、AIコーディングエージェントが私の指示と承認のもとで書きました（[My Contributions](#my-contributions)）。ここでは、AIが作った結果をどこまで信じてよいかをどう確かめたか、確かめる仕組みが弱まったときに何をしたかを書きます。私が自分で判定したのは正解データ192件で、コードや検査の判定はAIが行いました。

**1. 検査の分担と、その崩れ**

- 分類器のベンチマーク（下記4）は、計画をClaude、実装をCodex、検査を会話の文脈を引き継がない別のCodexセッションが担う分担で進めました。この分担を誰が決めたかは記録にありません。
- 最初の4回の検査は、いずれも計画側のClaudeが見落としたものを見つけました（例：何も検査していないテスト7件を、計画側は0件と報告していました）。見つけたのは検査側のAIです。
- 2026-08-29に、Codexの利用量の制約から、検査をClaudeの別セッションに、実装の代行をClaudeに移す取り決めに変わりました。記録上は「改善ではなく制約による後退」です。以後、計画・実装・検査の大部分が同じ系列のモデルになり、2026-09の実装はClaudeが担いました。記録は、この後の検査結果をそれ以前と同じ信頼度では扱わないとしています。

**2. 弱まった仕組みに対して私がしたこと**

- 私は、GitHubで公開するつもりだったので、別のモデルが入る確認が必要だと考えました。ただしCodexの利用量では元の分担を続けられなかったため、賄える形として、学習モデルの最初の実行前に一度だけ別モデルのレビューを依頼しました。
- 依頼した別モデル（Codex）のレビューの7件の指摘は、すべて修正されました。修正後の再レビューはしないと私が決めました。7件の一例：学習モデルは、採点に使う投稿の情報を学習のときに使ってはいけません。それを見張る仕組みが投稿の文章しか見ておらず、正解ラベルなどを全データから計算してしまう誤りをわざと入れたコードでも、既存のテストを通ってしまいました（実際のコードにそうした漏れは確認されていません）。
- 分析を始める前に、別セッションでの検査を私が開始しました。7件の指摘があり、その中に、分析の前に決めておくべき点（結果のぶれ幅を計算する手順の細部が決まっておらず、同じ規則に従っても違う幅が出うる）がありました。修正後に分析を承認しました。この検査は同じ系列のモデルによるもので、モデルの多様性はありません。
- 各段階は、実行する前に私が承認しました。学習モデルとの比較の段階で、私がベンチマークの終了を決めました。
- どの点数で比べ、どうなったら「差がある」と言うかの規則と、学習モデルの設定は、そのコードを書く前に記録されました。ただし、結果のぶれ幅を計算する手順の細部は、点数を見た後、その計算のコードを書く前に決めています。「先に決めた」ことの根拠は、外部の登録所ではなく、このリポジトリの記録の順序です。

**3. 人が持つ基準：正解データ192件**

- 192件はすべて私が1件ずつ手で判定しました。ただし補充の3件は、いつどの手順で判定したかの記録がなく、189件の結果も併記しています。
- 判定者は私一人で、一致率は測っていません。また192件は現在のコーパスの無作為標本ではありません（広告除去の確認に使った無作為抽出とは別のものです）。
- 規則ベース分類器のカテゴリ別F1（見落としと誤りの両方を見る0〜1の点数。いちばん当てはまる1カテゴリで判定）は0.869〜0.000でした。「交換・取引」が0.869、次に高い「中立」が0.625、「情報共有」は0.000（正解データに5件）です。使える・使えないを分ける基準値を事前に決めてはいませんでした。
- 最終発表（2026-07-30）の直前に、「情報共有」の分類精度がほぼ0だと分かりました。チームに伝えたうえで、担当部分では、いちばん点数の高かった「交換・取引」の範囲の結果だけを使うと決め、広告除去の見直しと正解データによる評価をやり直した資料（公開版の、広告除去をやり直したデータ110,918件と、正解データ192件による評価）を、私の担当部分にだけ使いました。

**4. ベンチマーク：規則分類器の的中率は良いのか**

- 規則分類器の的中率0.615（118/192）は、単独では良い値か判断できませんでした。そこで、同じ正解データで、当て推量2種（いちばん多いカテゴリを毎回答える：0.281、カテゴリの割合どおりに無作為に答える：平均0.206）と、簡単な学習モデル（文字の並びの特徴からカテゴリを当てる基本的な手法。名称はTF-IDF＋ロジスティック回帰）と比べました。
- 規則分類器は当て推量より明確に高く、学習モデルは規則分類器を上回りませんでした。的中率は規則0.615に対して学習モデル0.542でしたが、偶然でも起こりうる範囲の差だったため、判断保留としました。カテゴリごとのF1を平均した点数（macro F1）では、学習モデルの方が明確に低く（0.340対0.450）、その差の約6割は、14件しかない「不満・怒り」1カテゴリから生じています。
- 言えるのは、この小さなデータ・1つの設定・調整なしという条件で、簡単な学習モデルは規則に勝てなかったことまでです。規則が学習モデルより優れているとは言えません。
- 文章を読むLLMが「不満・怒り」と「中立」を拾えるかを比べる計画がありましたが、依存していたローカルモデルを廃止したため実施していません。

**5. 限界と公開範囲**

- 判定者1人・一致率未測定・小さなデータに加え、規則分類器が正解ラベルを見た後に変更されたかどうかは記録がなく、確認できません。もし変更されていれば、規則側の点数はこのデータに合わせたものになります。
- ベンチマークの設計・実装・検査の大部分を同じ系列のAIが行い、別モデルのレビューは学習モデルの段階で1回でした。
- ベンチマークのコード・投稿ごとの出力・作業履歴は公開していません。公開しているのは集計結果と要約です。上の1・2の経緯は非公開の作業記録に基づき、公開リポジトリからは確認できません。その記録自体もAIが書いたものです。
- AIが担った作業と私の判断の範囲は、[My Contributions](#my-contributions)と[docs/classifier_benchmark.md](classifier_benchmark.md)に分けて示しています。


## Team Project Context

This research originated as a four-person university seminar project. The
dataset preparation, the initial advertising removal, the exploratory analysis,
and the seminar presentation were team work.

This repository is maintained by the repository owner as a portfolio and
reproducibility project. It documents both the original seminar workflow and
the additional investigation, revision, validation, and reproducibility work.
That work did not start after the seminar ended. The classifier evaluation and
the corpus rebuild were done in the last days before the final presentation on
2026-07-30, and the repository owner's own section of that presentation used
them. The audit, documentation, publication, and further verification followed
afterward.

It should therefore not be read as claiming sole authorship of the original
seminar project.

The repository's own evidence sets the boundary between the two phases. Version
control begins on 2026-07-30, so the earlier seminar work carries no per-file
authorship record here; the [Project Timeline](01_PROJECT_TIMELINE.md)
marks that period accordingly rather than assigning it to an individual.

## My Contributions

This section covers the individual follow-up phase represented by the scripts,
documents, and figures in this repository.

**Who wrote the code.** The code, tests, CI, and documents in this repository
were written by AI coding agents (Codex, later Claude Code) at the repository
owner's direction and with the owner's approval.

**The repository owner's own part** is the judgments that shaped the work:

- Deciding to try an AI coding agent on the analysis
- Labelling all 192 Gold rows by hand, one by one
- Deciding which results to trust: checking the accuracy of the team's
  advertising removal against random samples reviewed by hand
  (`sample_100_posts.py`, and the filter-check extract in
  `make_task5_task6_files.py`), then extending the corpus work on that basis
- Deciding not to reconstruct by guesswork the 391 filter decisions whose
  original implementation is missing, and to lock them by post ID instead
- Deciding what this repository publishes and how the history of the work is handled

**Work carried out by the agents under that direction:**

- The advertising keyword filter (`filter_ads_202511_202604.py`) and the
  rule-based classifier (`classify_sns_rule_based.py`) that the repository retains
- Investigation of the existing notebooks, scripts, and data lineage
- Audit of the advertising-filter workflow, which identified over-filtering
  against `情報共有`, and revision and validation of the filtering logic
- Reconstruction and validation of the 110,918-post hybrid corpus, with the 391
  decisions above locked by post ID
- The tooling around the human labels, from drawing the original 200-post sample
  (`make_gold_standard_200.py`) through to normalizing Gold 192, and the scoring
  of the classifier against those labels under both criteria
- Classifier error analysis by category, tracing each error to a specific rule
  defect
- Exchange-activity and account-concentration analysis
  (`make_task3_exchange_accounts.py`)
- Audit of the presentation metrics, and regeneration of the analytical assets
  from validated data
- The reproducibility checks: deterministic rebuild verification, SHA-256
  baselines, and the 28 regression cases in `test_sentiment_classifier.py`, each
  recording a real misclassification that was found and fixed
- The synthetic runnable sample and GitHub Actions CI
- The documentation and the public repository

**How the agents' output was checked.** The [Japanese section above](#ai-workflow)
gives the full account; the facts are these.

- The benchmark work began with a split of roles: Claude planned, Codex implemented,
  and separate Codex sessions with no shared conversation context reviewed. Who set
  up that split is not recorded. The first four reviews each found something the
  planning model had missed; the reviewers found it, not the owner.
- On 2026-08-29, because of Codex usage limits, the review moved to a separate Claude
  session and Claude could stand in as implementer. The record calls this a retreat
  forced by the limit, not an improvement. From then on most planning, implementation
  and review was done by the same model family.
- The owner had wanted a different model in the loop because the repository was going to
  be public. Codex usage could not sustain the original split, so as an affordable form the
  owner asked a different model (Codex) once, before the first TF-IDF run, to review that
  stage (seven findings, all fixed; the owner decided not to have the fixes re-reviewed),
  started a separate review session before the analysis (seven findings, one of which
  had to be settled before the analysis could proceed; that session shares the model
  family), approved each stage before it ran, and closed the benchmark at this step.
- The scoring rules and TF-IDF settings were committed before the TF-IDF code was
  written; the remaining bootstrap details were fixed after the point scores were seen.
  "Fixed in advance" means the order of commits in this repository, not an external
  registry.
- All 192 Gold rows were labelled by hand by the owner, one annotator, with no
  agreement measure; for three supplemental rows no record of when or how they were
  labelled remains. Just before the final presentation, the owner found that the
  information-sharing category scored about zero, told the team, decided to use only the highest-scoring
  exchange/trade category's results in the owner's own section, and used the rebuilt corpus
  (110,918 posts) and the Gold 192 evaluation only there.
- A comparison with a large language model was planned but not run, because the local
  model it depended on was retired.
- The account of the split and the reviews comes from working records that are not
  published, and those records were themselves written by AI, so it cannot be verified
  from this repository. The published, checkable material is in
  [Classifier Benchmark](classifier_benchmark.md).

The original seminar research, the initial data preparation, the initial
advertising removal, and the seminar presentation were team work and are not
claimed here. The owner's individual contribution to the filtering is the later
accuracy check and the decision to redo the corpus on that basis, not the
original removal decision; the rebuild itself was carried out by the AI coding
agents.

## Source Material and Contribution Boundaries

The material here falls into three categories.

**1. Lab- or seminar-provided reference notebooks.** Two notebooks used in the
original workflow were supplied through a university seminar or lab and were not
authored from scratch by the repository owner. One cleaned extracted post text
with regular expressions; the other trained a Gensim Word2Vec model and exported
`vector.tsv` and `metadata.tsv` for TensorFlow Embedding Projector. Their
redistribution terms could not be verified, so the notebook files and their full
source code or cell outputs are not included in the public Git history. This
repository documents only their observed role in the historical workflow.

**2. Four-person seminar team work.** The dataset preparation, the initial
advertising removal, the exploratory analysis, and the seminar presentation were
carried out by the team as a whole. The repository holds no record of who
performed which task within that phase, and none is attributed here. One step
from it left no source at all: the code that produced `2511-2604_final.csv` is
missing, which is why its 391 remaining decisions are locked by post ID rather
than reimplemented.
Version control begins after that phase, so this repository holds no evidence of
who performed any individual task within it, and it does not attribute those
tasks to one person.

**3. The later individual phase.** The advertising-filter audit, hybrid-corpus
reconstruction, Gold 192 normalization and evaluation, classifier error
analysis, exchange-account analysis, presentation-metric verification,
reproducibility checks, regression tests, synthetic sample, CI, and public
repository organization were not team work: they belong to the repository
owner's later individual phase. In that phase AI coding agents wrote the
scripts, tests, and documents retained here, and the owner's own part was the
judgments listed under [My Contributions](#my-contributions).
