# Fork Notes (mogaming217)

このリポジトリは [cameronehrlich/apple-search-ads-cli](https://github.com/cameronehrlich/apple-search-ads-cli) の個人フォークです。Apple Search Ads API 認証情報を扱うツールなので、サプライチェーンリスク（上流が悪意あるアップデートを受けた場合にローカルの credential が抜かれる等）を抑える運用にしています。

## 運用方針

- **upstream を自動追従しない**。`main` は upstream と同期せず、レビュー済みの SHA のみを使う
- **使用バージョンは SHA 固定**でインストールする
- 新しい upstream コミットを取り込むときは、毎回差分を目視レビューしてから新しい pinned タグを打つ

## 現在のピン

- タグ: `pinned-2026-04-15`
- SHA: `db483db`（upstream `main` の 2026-02-24 時点 HEAD）

### インストール

```bash
uv tool install "git+https://github.com/mogaming217/apple-search-ads-cli.git@db483db"
```

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

## 運用上の追加推奨

- Apple Ads ダッシュボードで **read-only 権限の API ユーザー**を別途作り、普段はそちらで運用する
- write 権限が必要な操作（キャンペーン作成・入札変更等）をする時だけ write キーに切り替える
- `~/.asa-cli/` は macOS の FileVault 配下であることを前提とする
