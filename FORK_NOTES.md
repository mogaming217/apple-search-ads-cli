# Fork Notes (mogaming217)

このリポジトリは [cameronehrlich/apple-search-ads-cli](https://github.com/cameronehrlich/apple-search-ads-cli) の個人フォークです。Apple Search Ads API 認証情報を扱うツールなので、サプライチェーンリスク（上流が悪意あるアップデートを受けた場合にローカルの credential が抜かれる等）を抑える運用にしています。

## 運用方針

- **upstream を自動追従しない**。`main` は upstream と同期せず、レビュー済みの SHA のみを使う
- **使用バージョンは SHA 固定**でインストールする
- 新しい upstream コミットを取り込むときは、毎回差分を目視レビューしてから新しい pinned タグを打つ

## 現在のピン

- タグ: `pinned-2026-04-22-multi-org`
- SHA: `f253ef2`（fork 側 JPY + multi-org + budget order 対応パッチ適用済み）

### インストール

```bash
uv tool install --force --no-cache "git+https://github.com/mogaming217/apple-search-ads-cli.git@f253ef2"
```

> `--no-cache` 必須。uv のビルドキャッシュが効くと古い版が入ったままになる現象を確認（2026-04-22）。

### 過去のピン

| タグ | SHA | 内容 |
| --- | --- | --- |
| `pinned-2026-04-15` | `db483db` | upstream `main` 時点の HEAD（2026-02-24）|
| `pinned-2026-04-15-jpy` | `0ec9995` | 上記 + 非 USD 組織対応パッチ |
| `pinned-2026-04-22-multi-org` | `f253ef2` | 上記 + ASA_CREDENTIALS_FILE env 対応 + Budget Order ID (campaign group) 指定対応 |

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

### Multi-Org 並行運用 + Budget Order 指定（2026-04-22, SHA `f253ef2`）

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
- 親ディレクトリが存在しなくても `save_credentials()` は 0o700 相当でディレクトリを作るが、共有 path（`/tmp` や他ユーザーから読める場所）は避ける

credentials ファイルは Org ごとに別名で保存する運用（例: `credentials-makasete.json`、`credentials-recipitta.json`）。秘密鍵・公開鍵も Org ごとに別ファイル（例: `private-key-makasete.pem`）に分離し、`credentials.json` 内の `private_key_path` で参照する。

## 運用上の追加推奨

- Apple Ads ダッシュボードで **read-only 権限の API ユーザー**を別途作り、普段はそちらで運用する
- write 権限が必要な操作（キャンペーン作成・入札変更等）をする時だけ write キーに切り替える
- `~/.asa-cli/` は macOS の FileVault 配下であることを前提とする
