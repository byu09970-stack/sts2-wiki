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

from text_normalize import normalize_heading_text, normalize_patch_note_text, normalize_source_text

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
    return normalize_patch_note_text(result["translatedText"])


def translate_heading(client: translate.Client, text: str) -> str:
    """見出しは既知のセクション名を優先し、未定義だけ翻訳する。"""
    normalized = normalize_heading_text(text)
    if normalized != normalize_patch_note_text(text):
        return normalized
    return normalize_heading_text(translate_text(client, text))


# STS2パッチノートの主要セクション名（全大文字）
MAJOR_SECTIONS = [
    "CONTENT", "BALANCE", "ART", "BUG FIXES", "USER INTERFACE & EXPERIENCE",
    "USER INTERFACE", "GAMEPLAY", "AUDIO", "LOCALIZATION", "MULTIPLAYER",
    "PERFORMANCE", "FEATURES", "FIXES", "CHANGES", "NEW FEATURES",
]

# アクション動詞（項目の先頭に来る語、大文字始まり）
ACTION_VERBS = [
    "Buffed", "Nerfed", "Changed", "Fixed", "Added", "Removed", "Reworked",
    "Reverted", "Deprecated", "Increased", "Decreased", "Improved", "Updated",
    "Disabled", "Enabled", "Replaced", "Redesigned", "Rebalanced", "Adjusted",
    "Moved", "Disallowed", "Allowed", "Reduced", "Raised", "Lowered",
    "Nerfed", "Redesigned", "Rebalanced",
]

# サブヘッダーとして扱わないキーワード（アクション動詞等）
_HEADER_BLACKLIST = re.compile(
    r'^(?:' + '|'.join(ACTION_VERBS) +
    r'|Now|Note|Since|For|This|Additionally|Starting|If|As|The|A|An)\b'
)
# サブヘッダー候補に動詞が1つでも含まれていたら除外
_CONTAINS_VERB = re.compile(r'\b(?:' + '|'.join(ACTION_VERBS) + r')\b')


def split_into_items(text: str) -> list[str]:
    """
    プレーンテキストの塊をアイテム単位に分割する。
    アクション動詞またはピリオドで区切る。
    """
    if not text.strip():
        return []

    # アクション動詞の前で分割（句読点がなくてもOK）
    verb_pattern = r'\b(?:' + '|'.join(re.escape(v) for v in ACTION_VERBS) + r')\b'
    # 文字/数字/引用符の後のアクション動詞前で分割
    marked = re.sub(r'(?<=[a-zA-Z0-9"\'.!?])\s+(?=' + verb_pattern + r')', '\n', text)

    items = []
    for part in marked.split('\n'):
        part = part.strip()
        if not part or len(part) < 10:
            continue
        # 長すぎる説明文はピリオドでさらに分割
        if len(part) > 400:
            sub_parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', part)
            for sp in sub_parts:
                sp = sp.strip()
                if sp and len(sp) > 10:
                    items.append(sp)
        else:
            items.append(part)

    return items if items else [text.strip()] if text.strip() else []


def preprocess_contents(contents: str) -> list[tuple[str, str]]:
    """
    STS2パッチノートのプレーンテキストを (type, text) のリストに変換。
    type: 'header' | 'bullet' | 'text'

    Steam APIはBBCodeなしのプレーンテキストを返す。構造は:
    - MAJOR SECTION: （全大文字、例: CONTENT:, BALANCE:）
    - Sub Section: （キャラ名・カテゴリ名 + コロン、例: Silent:, General:）
    - 個別項目（アクション動詞で始まる文）
    """
    result: list[tuple[str, str]] = []

    text = normalize_source_text(contents)

    # 全大文字セクションの前にマーカーを挿入
    major_pattern = r'\b(' + '|'.join(re.escape(s) for s in MAJOR_SECTIONS) + r'):\s'
    text = re.sub(major_pattern, r'\n__MAJOR__\1\n', text)

    chunks = re.split(r'\n__MAJOR__', text)

    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk:
            continue

        if i == 0:
            # 冒頭のイントロ文
            intro = chunk[:500].strip()
            if intro:
                result.append(("text", intro))
            continue

        lines = chunk.split("\n", 1)
        section_name = normalize_heading_text(lines[0])
        body = normalize_source_text(lines[1]) if len(lines) > 1 else ""

        result.append(("header", section_name))

        if not body:
            continue

        # サブセクションの検出:
        # 条件: 大文字始まり・最大4語・小文字接続詞(and/&)のみ許可・アクション動詞不可・40文字未満
        sub_pattern = (
            r'(?<!["\w])'
            r'([A-Z][A-Za-z]*(?:\s+(?:&|and|[A-Z][A-Za-z]*)){0,3})'
            r':\s'
        )
        parts = re.split(sub_pattern, body)

        j = 0
        while j < len(parts):
            part = parts[j].strip()
            if not part:
                j += 1
                continue

            # サブセクション名かチェック
            if (
                j + 1 < len(parts)
                and re.match(r'^[A-Z][A-Za-z]*(?:\s+(?:&|and|[A-Z][A-Za-z]*)){0,3}$', parts[j])
                and len(parts[j]) < 40
                and not _HEADER_BLACKLIST.match(parts[j])
                and not _CONTAINS_VERB.search(parts[j])
            ):
                result.append(("header", normalize_heading_text(parts[j])))
                j += 1
                continue

            # テキスト部分を項目に分割
            for item in split_into_items(part):
                item = item.strip()
                if not item:
                    continue
                result.append(("bullet", normalize_patch_note_text(item)))
            j += 1

    return result


def parse_patch_note(item: dict, client: translate.Client) -> dict | None:
    title = item.get("title", "")
    contents = normalize_source_text(item.get("contents", ""))
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
        title_ja = normalize_patch_note_text(title)

    # BBCodeを正しくパースして (type, text) リストに変換
    parsed_lines = preprocess_contents(contents)
    logger.info(f"Parsed {len(parsed_lines)} lines (bullets: {sum(1 for t,_ in parsed_lines if t=='bullet')}, headers: {sum(1 for t,_ in parsed_lines if t=='header')})")

    sections: list[dict] = []
    current_section: dict | None = None
    summary_lines: list[str] = []

    for line_type, line_text in parsed_lines:
        if line_type == "header":
            if current_section and current_section["items"]:
                sections.append(current_section)
            try:
                heading_ja = translate_heading(client, line_text)
            except Exception:
                heading_ja = normalize_heading_text(line_text)
            current_section = {"heading": heading_ja, "items": []}

        elif line_type == "bullet":
            try:
                item_ja = translate_text(client, line_text)
            except Exception:
                item_ja = normalize_patch_note_text(line_text)
            if current_section is None:
                current_section = {"heading": "変更内容", "items": []}
            current_section["items"].append(item_ja)
            if len(summary_lines) < 3:
                summary_lines.append(item_ja)

        elif line_type == "text":
            # 箇条書きがまだ始まっていない場合、冒頭説明文としてサマリーに使う
            if not any(t == "bullet" for t, _ in parsed_lines[:parsed_lines.index((line_type, line_text)) + 1]):
                if len(summary_lines) < 2:
                    try:
                        line_ja = translate_text(client, line_text[:300])
                        summary_lines.append(line_ja)
                    except Exception:
                        summary_lines.append(normalize_patch_note_text(line_text[:150]))
            # セクションの説明文として追加
            elif current_section is not None and not current_section["items"]:
                try:
                    line_ja = translate_text(client, line_text[:300])
                    current_section["items"].append(line_ja)
                except Exception:
                    pass

    if current_section and current_section["items"]:
        sections.append(current_section)

    # セクションが空の場合、全体を1セクションに
    if not sections:
        logger.warning(f"No sections parsed for {version}, falling back to raw content")
        try:
            overall_ja = translate_text(client, contents[:2000])
            sections = [{"heading": "変更内容", "items": [overall_ja]}]
        except Exception:
            sections = [{"heading": "変更内容", "items": [normalize_patch_note_text(contents[:500])]}]

    summary_ja = " / ".join(summary_lines[:3]) if summary_lines else title_ja
    summary_ja = normalize_patch_note_text(summary_ja)

    return {
        "gid": str(item.get("gid", "")),
        "version": version,
        "title": normalize_patch_note_text(title),
        "title_ja": title_ja,
        "date": date_str,
        "date_unix": date_unix,
        "is_beta": is_beta,
        "summary_ja": summary_ja[:400],
        "sections": sections,
        "url": item.get("url", ""),
    }


def git_push_changes(new_notes: list[dict]) -> bool:
    """patch-notes.jsonをgit commit & pushする"""
    try:
        subprocess.run(
            ["git", "add", "data/patch-notes.json"],
            cwd=REPO_ROOT, check=True, timeout=30,
        )
        summary = f"{len(new_notes)}件のパッチノートを追加" if new_notes else "パッチノート定期チェック"
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        msg = f"auto: {date_str} {summary}"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            if "nothing to commit" in result.stdout + result.stderr:
                logger.info("コミットする変更なし")
                return True
            logger.error(f"git commit失敗: {result.stderr}")
            return False
        # commitが済んでからrebase（uncommitted changesがないのでrebaseが通る）
        try:
            subprocess.run(
                ["git", "pull", "--rebase", "origin", "master"],
                cwd=REPO_ROOT, check=True, timeout=60,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"git rebase失敗: {e}")
            subprocess.run(["git", "rebase", "--abort"], cwd=REPO_ROOT, timeout=30)
            return False
        subprocess.run(
            ["git", "push"],
            cwd=REPO_ROOT, check=True, timeout=60,
        )
        logger.info("git push完了")
        return True
    except Exception as e:
        logger.error(f"git push失敗: {e}")
        return False


def rebuild_site() -> bool:
    try:
        logger.info("Building Next.js site...")
        result = subprocess.run(
            "npm run build",
            cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=300,
            shell=True,
        )
        if result.returncode != 0:
            logger.error(f"Build failed:\n{result.stderr[-2000:]}")
            return False
        logger.info("Build succeeded")
        subprocess.run("pm2 restart sts2-wiki", check=True, timeout=30, shell=True)
        logger.info("PM2 restarted")
        return True
    except Exception as e:
        logger.error(f"Rebuild failed: {e}")
        return False


def main() -> None:
    # --reparse オプション: 既存データも含めて全件再処理（BBCode修正後の再取得用）
    reparse_all = "--reparse" in sys.argv

    translate_client = translate.Client()

    logger.info("Steam APIからニュースを取得中...")
    try:
        steam_items = fetch_steam_news()
    except Exception as e:
        logger.error(f"Steam API取得失敗: {e}")
        sys.exit(1)

    logger.info(f"取得件数: {len(steam_items)}")

    data = load_existing()
    existing_gids = set() if reparse_all else {n["gid"] for n in data["patch_notes"]}

    if reparse_all:
        logger.info("--reparse モード: 全件再処理します")

    new_notes = []
    for item in steam_items:
        gid = str(item.get("gid", ""))
        if gid in existing_gids:
            logger.debug(f"Skip (already exists): {item.get('title')}")
            continue

        logger.info(f"パッチノートを処理中: {item.get('title')}")
        parsed = parse_patch_note(item, translate_client)
        if parsed:
            new_notes.append(parsed)
            logger.info(f"処理完了: {parsed['version']} (セクション数: {len(parsed['sections'])}, 合計項目数: {sum(len(s['items']) for s in parsed['sections'])})")

    if not new_notes:
        logger.info("新しいパッチノートはありませんでした。")
        return

    if reparse_all:
        # 再処理時は既存を新データで上書き（gidで照合）
        new_gids = {n["gid"] for n in new_notes}
        kept = [n for n in data["patch_notes"] if n["gid"] not in new_gids]
        data["patch_notes"] = new_notes + kept
    else:
        data["patch_notes"] = new_notes + data["patch_notes"]

    save_data(data)
    logger.info(f"{len(new_notes)}件のパッチノートを{'再処理' if reparse_all else '追加'}しました。")

    if git_push_changes(new_notes):
        logger.info("GitHub へプッシュ完了")
    else:
        logger.error("git push失敗。手動確認してください。")

    if rebuild_site():
        logger.info("サイトの更新が完了しました。")
    else:
        logger.error("ビルドに失敗しました。手動で確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
