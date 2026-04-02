# sts2-wiki

**概要**: Slay the Spire 2の敵・ボス攻略Wiki。全Act・全敵データを日本語で管理。GCP VMでNext.js静的ビルドをserveで配信。

## コマンド

```bash
npm run dev    # 開発
npm run build  # 静的ビルド（out/に出力）
# GCP VM: PM2プロセス名 sts2-wiki（npx serve out -l 3000）
```

## アーキテクチャ

- `app/` — Next.js App Router
- `data/enemies.json` — 敵データ（JSON管理、DBなし）
- `components/` — UIコンポーネント
- メモはlocalStorageに保存（バックエンドなし）

## GCP VM

- ホスト: `ktyto@34.85.122.108`
- PM2プロセス名: `sts2-wiki`（`npx serve out -l 3000`）
