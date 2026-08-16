# Fork Notes (mogaming217)

このリポジトリは [cameronehrlich/apple-search-ads-cli](https://github.com/cameronehrlich/apple-search-ads-cli) の個人フォークです。Apple Search Ads API 認証情報を扱うツールなので、サプライチェーンリスク（上流が悪意あるアップデートを受けた場合にローカルの credential が抜かれる等）を抑える運用にしています。

## 運用方針

- **upstream を自動追従しない**。`main` は upstream と同期せず、レビュー済みの SHA のみを使う
- **使用バージョンは SHA 固定**でインストールする
- 新しい upstream コミットを取り込むときは、毎回差分を目視レビューしてから新しい pinned タグを打つ

## 現在のピン

- タグ: `pinned-2026-08-17-kw-research`
- 内容: 下記 platform-v1 ピンに `asa workflows keywords`（pop / genres / sugg、キーワードリサーチ）を追加
- 追加は fork 独自機能（workflows 配下、read-only、in-process で Platform API v1 を呼ぶ）。詳細は `asa workflows keywords --help`

### 過去のピン: pinned-2026-08-16-platform-v1

- タグ: `pinned-2026-08-16-platform-v1`
- 内容: upstream/main（`064d7b5`、Apple Ads Platform API v1 全面対応・Apple 公式 SDK `apple-ads-platform==1.109.0` ラップ）を取り込み + fork 独自パッチ再ポート（multi-org / budget order / direct mode / 表示通貨）+ Codex レビュー 2 巡反映版
- **旧コマンドは `asa v5` プレフィックス配下に移動**（例: `asa v5 reports keywords ...`）。Platform API v1 リソース（`asa insights search-term-popularity` 等）がトップレベル
- **Python 3.12+ 必須**。依存に Apple 公式 SDK `apple-ads-platform==1.109.0`（PEP 740 attestation 検証済み、下記監査ログ参照）

### インストール

```bash
uv tool install --force --no-cache "git+https://github.com/mogaming217/apple-search-ads-cli.git@pinned-2026-08-17-kw-research"
```

> `--no-cache` 必須。uv のビルドキャッシュが効くと古い版が入ったままになる現象を確認（2026-04-22）。

### 過去のピン

| タグ | SHA | 内容 |
| --- | --- | --- |
| `pinned-2026-04-15` | `db483db` | upstream `main` 時点の HEAD（2026-02-24）|
| `pinned-2026-04-15-jpy` | `0ec9995` | 上記 + 非 USD 組織対応パッチ |
| `pinned-2026-04-22-multi-org` | `a57d95a` | 上記 + ASA_CREDENTIALS_FILE env 対応 + Budget Order ID 指定対応（Codex レビュー反映版） |
| `pinned-2026-05-10-direct-keyword` | `ed3c327` | 上記 + `asa keywords add` に direct mode（`--campaign --ad-group --match`）追加（Codex レビュー反映版、PR #2）|

## 初回監査ログ（2026-04-15, SHA db483db）

約 4,900 行の Python コードを全体チェック。結果：**問題なし**。

### チェック項目と結果

| 項目 | 結果 |
| --- | --- |
| 外部通信先 | `appleid.apple.com`（OAuth）と `api.searchads.apple.com`（API v5）のみ。第三者サーバーへの送信なし |
| 危険な動的実行 | `eval` / `exec` / `compile` / `__import__` なし |
| シリアライズ | `pickle` 使用なし（`json` のみ） |
| プロセス起動 | `subprocess` / `os.system` / `os.popen` なし |
| ネットワーク API | `requests` のみ。生の `socket` / `urllib` 使用なし |
| 難読化・base64 decode 経由のコード実行 | なし |
| ファイル書き込み先 | `~/.asa-cli/credentials.json` と `~/.asa-cli/config.json` のみ（パーミッション 600） |
| JWT 署名 | 標準 `pyjwt` の ES256。秘密鍵は `credentials.private_key_path` からローカル読み込み |
| 依存パッケージ | `typer`, `rich`, `pyjwt[crypto]`, `requests`, `pydantic`, `python-dotenv` — すべて妥当 |

### 結論

- 認証情報はローカルに留まり、Apple 以外へは送信されない
- コード自体に不審な挙動は見当たらず、透明性が高い
- 残存リスクは「上流がアップデートで悪意あるコードを入れた場合」のみ → 本フォーク + SHA ピン留めで緩和

## Platform API v1 取り込み監査ログ（2026-08-16, upstream `064d7b5`）

upstream の大規模刷新（+42,950 行 / 135 ファイル。大半は生成マニフェスト JSON・テスト・生成ドキュメント）を、Claude サブエージェント 4 系統の並列レビュー + Codex レビュー 2 巡で監査してから取り込んだ。

### 1. 手書きコードのセキュリティ監査 — 問題なし

| 項目 | 結果 |
| --- | --- |
| 外部通信先 | Apple のみ。v5: `appleid.apple.com` / `api.searchads.apple.com`、v1: 公式 SDK 経由で `api.ads.apple.com`（**新ホスト**）。第三者送信なし |
| 動的実行 / pickle / subprocess / 生 socket / 難読化 | すべてなし |
| ファイル書き込み | credentials.json は 0600 明示。config.json は非秘密情報のみ |
| credential 到達点 | PyJWT の ES256 署名と Apple 公式 SDK builder の 2 箇所のみ。ログ・例外への漏出なし |
| ビルド | setup.py なし（setuptools.build_meta、install 時の任意コード実行なし） |
| 軽微な注意 | GitHub Actions がタグ固定（SHA 未固定）/ uv.lock 非コミット（意図的）/ python-dotenv が宣言のみ未使用 / SKILL.md に作者個人パス |

### 2. Apple 公式 SDK `apple-ads-platform==1.109.0` のサプライチェーン検証 — 公式性を暗号学的に確認

- PyPI の PEP 740 attestation が「`apple` org（GitHub org ID 10639145 = Apple 本体）の `apple-ads-platform-api-python` リポジトリ、workflow `publish-pypi.yml`、tag v1.109.0」からの発行であることを証明。`pypi-attestations verify` で wheel/sdist とも OK
- 配布物と GitHub ソースは**バイト単位で完全一致**（差分はバージョンスタンプのみ）
- Apple 公式ドキュメント（Client Libraries ページ）がこのリポジトリを公式ライブラリとして明記
- SDK コード監査: 通信先は `api.ads.apple.com` / `appleid.apple.com` の 2 ドメインのみ。危険パターンなし。build backend は poetry-core（宣言的）
- **注意: attestation が保証するのは 1.109.0 のみ**。SDK バージョンを上げる際は同じ手順（attestation + ソース照合）で再検証すること

### 3. platform 層の品質レビュー — 良好

- mutation（create/update/delete/apply/dismiss/upload）はデフォルトでプレビューのみ、`--confirm` 必須。read/mutation 境界は HTTP メソッド + パスベースで全 99 操作の誤分類なし
- SDK response drift フォールバックは fail-closed（既知ミスマッチ 3 条件に全一致した場合のみ受容、パッチ済みコピーで再検証）
- チェックイン済みマニフェスト JSON は PyPI 配布物から決定論的に再生成できることを実機確認
- v5 の通貨は `get_org_currency()`（ACL から動的取得・fail-closed）に刷新されており、fork の静的 `currency` フィールド方式の上位互換

### 4. fork 独自パッチの棚卸し

| パッチ | 対応 |
| --- | --- |
| 非 USD 組織対応（write 経路） | **廃棄**。upstream の `get_org_currency()` が上位互換 |
| 非 USD 組織対応（表示） | `format_money` を再適用。表示通貨は ACL 正、失敗時に `credentials.currency` へフォールバック |
| Multi-Org `ASA_CREDENTIALS_FILE` | **維持**（マージで自動生存）。platform 層も `load_credentials()` 共用のため v1 コマンドにも効く |
| Budget Order 指定 create | `v5/api.py` + `commands/campaigns.py` に再ポート |
| keywords add direct mode | `commands/keywords.py` に再ポート + Codex 指摘で強化（bid=0 の falsy バグ修正、bid 省略時の ad group default 明示解決、`--match` 単独指定の fail-closed 化、失敗時 exit 1） |

Codex レビュー（2 巡、いずれも反映済み・最終承認取得）: bid 契約 / fail-closed / 表示通貨 / localSpend 通貨伝播 / ACL キャッシュ / ruff。契約テスト 10 件追加、全 437 テストパス。

### 運用メモ

- Platform API v1 の利用には `~/.asa-cli/credentials.json` への `ad_account_id` 追記が必要（`asa access advertiser-resources` で AD_ACCOUNT の resourceId を確認）。org_id は v1 では使われない
- `asa config setup` を再実行すると credentials.json の未知フィールド（`currency` 等）が消えるため、フィールド追加は手編集を推奨
- Campaign Management API v5 は **2027-01-26 廃止**。それまでに PDCA 運用を v1 レポート系へ移行する

## upstream 更新を取り込む手順

```bash
cd ~/workspace/clones/apple-search-ads-cli
git remote add upstream https://github.com/cameronehrlich/apple-search-ads-cli.git  # 初回のみ
git fetch upstream
git log --oneline <現在のpinned-SHA>..upstream/main    # 差分確認
git diff <現在のpinned-SHA>..upstream/main             # 変更内容をレビュー
```

レビューで問題なければ：

```bash
git checkout main
git merge --ff-only upstream/main
git push origin main

NEW_SHA=$(git rev-parse HEAD)
TODAY=$(date +%Y-%m-%d)
git tag "pinned-$TODAY" "$NEW_SHA"
git push origin "pinned-$TODAY"

uv tool upgrade asa-cli  # もしくは再 install
```

## Fork 独自パッチ

upstream に無い、このフォークで追加した変更：

### 非 USD 組織対応（2026-04-15, SHA `0ec9995`）

upstream は `currency: "USD"` をハードコードしており、JPY など USD 以外の組織では bid/budget が正しく送信できない。以下を修正：

- `Credentials` モデルに `currency: str = "USD"` フィールドを追加（デフォルト USD で後方互換）
- `SearchAdsClient.currency` プロパティを追加し、API へ送る全 payload（campaign budget / ad group default bid / keyword bid / CPA goal）で使用
- `config.format_money()` ヘルパーを追加。JPY/KRW/VND/CLP/HUF/ISK は小数なし、`$/¥/€/£/₩` 等の通貨記号対応
- コマンド側の表示から `$` ハードコードを除去、`format_money` 経由に差し替え
- `--bid` / `--budget` のヘルプ文言を `(USD)` → `(in org currency)` に変更

JPY 組織で使う場合は `credentials.json` に `"currency": "JPY"` を追記するだけ。

### Multi-Org 並行運用 + Budget Order 指定（2026-04-22, SHA `a57d95a`）

同一マシンで複数 Apple Ads Org を並行で運用するケース（例: 個人 Org と法人 Org）と、Basic → Advanced 切替等で campaign 作成時に Budget Order / Campaign Group 指定が必要なケースへの対応。

- `asa_cli/config.py`: `get_credentials_file()` 関数で credentials path を**呼び出しごとに**解決（環境変数 `ASA_CREDENTIALS_FILE` で上書き可能、未指定時は `~/.asa-cli/credentials.json`）。`CREDENTIALS_FILE` 定数は削除（プロセス内で env が差し替わっても追従できるようにするため）
- `asa_cli/config.py`: `save_credentials()` は credentials path の**親ディレクトリを自動作成**する（`~/.asa-cli` 以外のパス指定でも `FileNotFoundError` にならない）
- `asa_cli/api.py`: `create_campaign` に `budget_order_ids: Optional[list[int]]` 引数を追加。`is not None` 判定で指定時のみ payload に `"budgetOrders": [...]` を含める（`0` を明示指定した場合はそのまま送信）
- `asa_cli/commands/campaigns.py`: `campaigns create` に `--budget-order-id / -g` オプションを追加。正の整数のみ受け付け、0 以下はエラーで弾く。`help="Daily budget"` の `(USD)` 表記と `$` ハードコード表示を除去、`format_money()` 経由の表示に差し替え

使用例:
```bash
# 法人 Org に切り替えて furikan を操作
env ASA_CREDENTIALS_FILE=~/.asa-cli/credentials-makasete.json \
    asa --app furikan campaigns list --all

# Budget Order ID 指定で campaign 作成（必要な Org のみ）
asa campaigns create "MyCampaign" -b 500 -c JP -g 21450441
```

**credentials 書き込み先に関する注意**（2026-04-15 初回監査時の「書き込み先は `~/.asa-cli/credentials.json` のみ」という記述は、env override 使用時は成立しない）:
- `ASA_CREDENTIALS_FILE` で指定したパスが、読み取り/書き込み両方の対象になる
- 推奨は **絶対 path**（例: `/Users/.../credentials-makasete.json`）か、`~/.asa-cli/` 配下への相対配置
- 親ディレクトリが存在しなくても `save_credentials()` はディレクトリを自動作成する。ただし作成時のパーミッションは**実行環境の `umask` に依存**する（`mkdir(parents=True, exist_ok=True)` のみ）ため、他ユーザーから読める場所（`/tmp` など）は避ける。credentials ファイル本体は常に 0o600 で書き出す

credentials ファイルは Org ごとに別名で保存する運用（例: `credentials-makasete.json`、`credentials-recipitta.json`）。秘密鍵・公開鍵も Org ごとに別ファイル（例: `private-key-makasete.pem`）に分離し、`credentials.json` 内の `private_key_path` で参照する。

### `asa keywords add` direct mode（2026-05-10, SHA `ed3c327`, PR #2）

upstream の `asa keywords add` はキャンペーン名に `brand` / `category` / `competitor` / `discovery` のいずれかを含むことを要求する自動ルーティング前提だった。日本語名のキャンペーン（例: 「キーワード」「探索」「競合」）では `--type` ベースの追加ができず、ad group を直接指定して KW を追加する手段がなかった。後方互換のまま 2 モード化で対応:

- **Routing mode（既存・default）**: `--type brand|category|competitor` で対応キャンペーンに EXACT 追加 + Discovery に BROAD/NEGATIVE。挙動変更なし
- **Direct mode（新規）**: `--campaign <ID> --ad-group <ID>` で type ルーティングをバイパスし、対象 ad group に bulk add
  - `--match exact|broad`（default `exact`、case-insensitive）
  - `--bid <N>`（任意、ad group default を使うなら省略）
  - Discovery への broad / negative 連動追加は行わない（直接指定の意図に反するため）
  - ガード: `--campaign` と `--ad-group` 両方必須、片方のみはエラー
- 新規テスト 5 ケース追加（`tests/test_keywords_direct.py`）

使用例:
```bash
asa keywords add "新ワード1,新ワード2" --campaign 2143367006 --ad-group 2145315824 --match exact --bid 300
```

upstream にも有用な機能なので、安定後に upstream PR 検討候補。

## 運用上の追加推奨

- Apple Ads ダッシュボードで **read-only 権限の API ユーザー**を別途作り、普段はそちらで運用する
- write 権限が必要な操作（キャンペーン作成・入札変更等）をする時だけ write キーに切り替える
- `~/.asa-cli/` は macOS の FileVault 配下であることを前提とする
