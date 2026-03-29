"""
STS2 パッチノート自動更新スクリプト
使い方: python scripts/update_patch_notes.py
依存: pip install requests google-cloud-translate
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from google.cloud import translate_v2 as translate

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

# GCPプロジェクトID（環境変数または直書き）
GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "gen-lang-client-0000940077")


def fetch_steam_news() -> list[dict]:
    resp = requests.get(STEAM_NEWS_URL, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("appnews", {}).get("newsitems", [])
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


def translate_text(client: translate.Client, text: str) -> str:
    """Google Cloud Translation APIで英語→日本語翻訳"""
    if not text.strip():
        return text
    result = client.translate(text, source_language="en", target_language="ja")
    return result["translatedText"]


def parse_patch_note(item: dict, client: translate.Client) -> dict | None:
    title = item.get("title", "")
    contents = item.get("contents", "")
    date_unix = item.get("date", 0)
    date_str = datetime.fromtimestamp(date_unix, tz=timezone.utc).strftime("%Y-%m-%d")

    version_match = re.search(r"v\d+\.\d+[\.\d\-\w]*", title)
    version = version_match.group(0) if version_match else title
    is_beta = "beta" in title.lower()

    try:
        title_ja = translate_text(client, title)
        logger.info(f"Translated title: {title_ja}")
    except Exception as e:
        logger.warning(f"Title translation failed: {e}")
        title_ja = title

    # パッチノートを行ごとに解析してセクション分け
    sections: list[dict] = []
    current_section: dict | None = None
    summary_lines: list[str] = []
    line_count = 0

    for raw_line in contents.split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("["):
            continue

        # セクションヘッダー判定（行末が:で終わる、または短くて大文字が多い）
        is_header = (
            (line.endswith(":") and len(line) < 60) or
            (len(line) < 40 and line.isupper())
        )

        if is_header:
            if current_section and current_section["items"]:
                sections.append(current_section)
            heading_en = line.rstrip(":")
            try:
                heading_ja = translate_text(client, heading_en)
            except Exception:
                heading_ja = heading_en
            current_section = {"heading": heading_ja, "items": []}
        elif line.startswith(("-", "*", "•")):
            item_text = line.lstrip("-*• ").strip()
            if item_text and len(item_text) > 3:
                try:
                    item_ja = translate_text(client, item_text)
                except Exception:
                    item_ja = item_text
                if current_section is None:
                    current_section = {"heading": "変更内容", "items": []}
                current_section["items"].append(item_ja)
                line_count += 1
                if line_count <= 3:
                    summary_lines.append(item_ja)
        elif line_count == 0 and len(line) > 20:
            # 冒頭の説明文をサマリーに使う
            try:
                line_ja = translate_text(client, line[:300])
                summary_lines.append(line_ja)
            except Exception:
                summary_lines.append(line[:100])

    if current_section and current_section["items"]:
        sections.append(current_section)

    # セクションが空の場合、全体を1セクションに
    if not sections:
        try:
            overall_ja = translate_text(client, contents[:2000])
            sections = [{"heading": "変更内容", "items": [overall_ja[:500]]}]
        except Exception:
            sections = [{"heading": "変更内容", "items": [contents[:200]]}]

    summary_ja = "　".join(summary_lines[:3]) if summary_lines else title_ja

    return {
        "gid": str(item.get("gid", "")),
        "version": version,
        "title": title,
        "title_ja": title_ja,
        "date": date_str,
        "date_unix": date_unix,
        "is_beta": is_beta,
        "summary_ja": summary_ja[:400],
        "sections": sections,
        "url": item.get("url", ""),
    }


def rebuild_site() -> bool:
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
        subprocess.run(["pm2", "restart", "sts2-wiki"], check=True, timeout=30)
        logger.info("PM2 restarted")
        return True
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        return False


def main() -> None:
    translate_client = translate.Client()

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
        parsed = parse_patch_note(item, translate_client)
        if parsed:
            new_notes.append(parsed)
            logger.info(f"処理完了: {parsed['version']}")

    if not new_notes:
        logger.info("新しいパッチノートはありませんでした。")
        return

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
