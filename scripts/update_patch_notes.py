"""
STS2 パッチノート自動更新スクリプト
使い方: python scripts/update_patch_notes.py
依存: pip install requests anthropic python-dotenv
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sts2_updater")

STEAM_APP_ID = 2868840
STEAM_NEWS_URL = (
    f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/"
    f"?appid={STEAM_APP_ID}&count=20&maxlength=30000&format=json"
    f"&feeds=steam_community_announcements"
)
REPO_ROOT = Path(__file__).parent.parent
DATA_FILE = REPO_ROOT / "data" / "patch-notes.json"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def fetch_steam_news() -> list[dict]:
    """Steam APIからニュースを取得（公式アナウンスのみ）"""
    resp = requests.get(STEAM_NEWS_URL, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("appnews", {}).get("newsitems", [])
    # パッチノートのみ絞り込み（タイトルで判定）
    keywords = ["patch notes", "hotfix", "update", "beta patch"]
    return [
        item for item in items
        if any(kw in item.get("title", "").lower() for kw in keywords)
    ]


def load_existing() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict) -> None:
    data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {DATA_FILE}")


def translate_patch_note(client: Anthropic, item: dict) -> dict | None:
    """Claude APIでパッチノートを日本語化"""
    title = item.get("title", "")
    contents = item.get("contents", "")
    date_unix = item.get("date", 0)
    date_str = datetime.fromtimestamp(date_unix, tz=timezone.utc).strftime("%Y-%m-%d")

    # バージョン番号を抽出
    import re
    version_match = re.search(r"v\d+\.\d+[\.\d\-\w]*", title)
    version = version_match.group(0) if version_match else title
    is_beta = "beta" in title.lower()

    prompt = f"""以下はSlay the Spire 2の公式パッチノート（英語）です。
これを日本語に翻訳・整理して、以下のJSON形式で返してください。
JSON以外のテキストは出力しないでください。

英語タイトル: {title}
英語内容:
{contents[:8000]}

出力形式（JSONのみ）:
{{
  "title_ja": "日本語タイトル（例: ベータパッチノート - v0.101.0）",
  "summary_ja": "2〜4文の日本語要約。主な変更点を簡潔に。",
  "sections": [
    {{
      "heading": "セクション名（例: バランス調整、バグ修正、新機能など）",
      "items": ["変更内容1", "変更内容2"]
    }}
  ]
}}

翻訳の注意:
- ゲーム用語は日本語攻略Wiki風の表記に（例: card→カード、relic→レリック、boss→ボス）
- カード名・レリック名は英語のままでもOK（日本語訳が不明な場合）
- 箇条書きは簡潔に、1項目1〜2文で
"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # JSON部分を抽出
        start = raw.find("{")
        end = raw.rfind("}") + 1
        translated = json.loads(raw[start:end])
    except Exception as e:
        logger.error(f"Translation failed for {title}: {e}")
        return None

    return {
        "gid": str(item.get("gid", "")),
        "version": version,
        "title": title,
        "title_ja": translated.get("title_ja", title),
        "date": date_str,
        "date_unix": date_unix,
        "is_beta": is_beta,
        "summary_ja": translated.get("summary_ja", ""),
        "sections": translated.get("sections", []),
        "url": item.get("url", ""),
    }


def rebuild_site() -> bool:
    """Next.jsサイトをビルドしてPM2を再起動"""
    try:
        logger.info("Building Next.js site...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            logger.error(f"Build failed:\n{result.stderr[-2000:]}")
            return False
        logger.info("Build succeeded")

        logger.info("Restarting PM2 process...")
        subprocess.run(["pm2", "restart", "sts2-wiki"], check=True, timeout=30)
        logger.info("PM2 restarted")
        return True
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        return False


def main() -> None:
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY が設定されていません。.envファイルを確認してください。")
        sys.exit(1)

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    logger.info("Steam APIからニュースを取得中...")
    try:
        steam_items = fetch_steam_news()
    except Exception as e:
        logger.error(f"Steam API取得失敗: {e}")
        sys.exit(1)

    logger.info(f"取得件数: {len(steam_items)}")

    data = load_existing()
    existing_gids = {n["gid"] for n in data["patch_notes"]}

    new_notes = []
    for item in steam_items:
        gid = str(item.get("gid", ""))
        if gid in existing_gids:
            logger.debug(f"Skip (already exists): {item.get('title')}")
            continue

        logger.info(f"新しいパッチノートを処理中: {item.get('title')}")
        translated = translate_patch_note(client, item)
        if translated:
            new_notes.append(translated)
            logger.info(f"翻訳完了: {translated['version']}")

    if not new_notes:
        logger.info("新しいパッチノートはありませんでした。")
        return

    # 新しいものを先頭に追加（日付降順）
    data["patch_notes"] = new_notes + data["patch_notes"]
    save_data(data)
    logger.info(f"{len(new_notes)}件の新しいパッチノートを追加しました。")

    if rebuild_site():
        logger.info("サイトの更新が完了しました。")
    else:
        logger.error("ビルドに失敗しました。手動で確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
