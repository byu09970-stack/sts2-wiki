"""
STS2 敵データ自動更新スクリプト
slaythespire2.gg から最新の敵データを取得し、パッチノートと照合して enemies.json を更新する。
使い方: python scripts/update_enemies.py
依存: pip install requests beautifulsoup4 google-cloud-translate
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
from typing import Any

import requests
from bs4 import BeautifulSoup
from google.cloud import translate_v2 as translate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sts2_enemy_updater")

REPO_ROOT = Path(__file__).parent.parent
ENEMIES_FILE = REPO_ROOT / "data" / "enemies.json"
UPDATE_LOG_FILE = REPO_ROOT / "data" / "update-log.json"
PATCH_NOTES_FILE = REPO_ROOT / "data" / "patch-notes.json"

BASE_URL = "https://slaythespire2.gg"
ENEMIES_LIST_URL = f"{BASE_URL}/enemies"

# slaythespire2.gg の enemy ID → enemies.json の id マッピング
# キーが存在しない場合は自動変換 (VANTOM → vantom)
# 複合敵（1つのencounterに複数体）はスキップし、encounter単位のIDにマッピング
ENEMY_ID_MAP: dict[str, str | None] = {
    # 個別モンスター → encounter ID にマッピング
    "INKLET": "inklets",
    "TWO_TAILED_RAT": "two-tailed-rats",
    "TOADPOLE": "toadpoles",
    "CORPSE_SLUG": "corpse-slugs",
    "CHOMPER": "chompers",
    "EXOSKELETON": "exoskeleton-pack",
    "MYTE": "mytes",
    "AXEBOT": "axebots",
    "SCROLL_OF_BITING": "scroll-of-biting-pack",
    "NIBBIT": "nibbit",
    # Ruby Raider 個別 → raider-trio
    "ASSASSIN_RUBY_RAIDER": "raider-trio",
    "AXE_RUBY_RAIDER": None,  # raider-trio に含まれる
    "BRUTE_RUBY_RAIDER": None,
    "CROSSBOW_RUBY_RAIDER": None,
    "TRACKER_RAIDER": None,
    # Slime 個別 → slime-pack
    "LEAF_SLIME_M": "slime-pack",
    "LEAF_SLIME_S": None,
    "TWIG_SLIME_M": None,
    "TWIG_SLIME_S": None,
    # Cultists
    "CALCIFIED_CULTIST": "cultists",
    "DAMP_CULTIST": None,
    # Knight Trio 個別
    "FLAIL_KNIGHT": "knight-trio",
    "SPECTRAL_KNIGHT": None,
    "MAGI_KNIGHT": None,
    # Bowlbug 個別
    "BOWLBUG_EGG": "bowlbug-duo",
    "BOWLBUG_ROCK": None,
    "BOWLBUG_SILK": None,
    "BOWLBUG_NECTAR": None,
    # Queen + Torch Head
    "TORCH_HEAD_AMALGAM": None,  # queen に含まれる
    # Doormaker パーツ
    "ROCKET": None,
    # Living Shield + Turret
    "LIVING_SHIELD": "living-shield-turret-operator",
    "TURRET_OPERATOR": None,
    # The Lost + The Forgotten
    "THE_LOST": "the-lost-the-forgotten",
    "THE_FORGOTTEN": None,
    # Punch + Cubex combo (act3)
    "PUNCH_CONSTRUCT": "punch-construct",  # act1b standalone
    # テスト・未使用
    "ATTACK_MOVE_MONSTER": None,
    "BIG_DUMMY": None,
    "FAKE_MERCHANT_MONSTER": None,
    "BATTLE_FRIEND_V1": None,
    "BATTLE_FRIEND_V2": None,
    "BATTLE_FRIEND_V3": None,
    "TOUGH_EGG": None,
    # サブ敵（encounter内のサブ）
    "BYRDONIS_NEST": None,
    "BYRDPIP": None,
    "KIN_FOLLOWER": None,
    "DECIMILLIPEDE_SEGMENT": "decimillipede",
    "SNAPPING_JAXFRUIT": None,
    "SLITHERING_STRANGLER": None,
    "GAS_BOMB": None,
    "WRIGGLER": None,
    "EYE_WITH_TEETH": None,
    "FAT_GREMLIN": None,
    "SNEAKY_GREMLIN": None,
    "FLYCONID": None,
    "CRUSHER": None,
    "SLUMBERING_BEETLE": None,
    "ARCHITECT": None,
}

# Act マッピング
ACT_MAP: dict[str, str] = {
    "Overgrowth": "act1a",
    "Underdocks": "act1b",
    "Hive": "act2",
    "Glory": "act3",
}

# タイプマッピング
TYPE_MAP: dict[str, str] = {
    "Boss": "boss",
    "Elite": "elite",
    "Normal": "normal",
    "Weak": "normal",
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "STS2-Wiki-Updater/1.0 (personal wiki bot)",
    "Accept": "text/html,application/xhtml+xml",
})


def fetch_enemy_list() -> list[dict[str, str]]:
    """slaythespire2.gg の敵一覧からスラッグリストを取得"""
    resp = SESSION.get(ENEMIES_LIST_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    enemies = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("/enemies/") and href.count("/") == 2:
            slug = href.split("/")[-1]
            if slug and slug != "enemies":
                enemies.append({"slug": slug, "url": f"{BASE_URL}{href}"})

    # 重複排除
    seen = set()
    unique = []
    for e in enemies:
        if e["slug"] not in seen:
            seen.add(e["slug"])
            unique.append(e)

    logger.info(f"敵一覧から {len(unique)} 件のスラッグを取得")
    return unique


def fetch_enemy_detail(slug: str) -> dict[str, Any] | None:
    """個別敵ページからデータを取得"""
    url = f"{BASE_URL}/enemies/{slug}"
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"取得失敗 ({slug}): {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    # ページ内の __NEXT_DATA__ や埋め込みJSONを探す
    data: dict[str, Any] = {"slug": slug, "raw_text": text[:5000]}

    # 名前
    h1 = soup.find("h1")
    if h1:
        data["nameEn"] = h1.get_text(strip=True)

    # HP抽出（テキストから）
    hp_match = re.search(r"HP[:\s]*(\d+(?:\s*[-–]\s*\d+)?)", text)
    if hp_match:
        data["hp_text"] = hp_match.group(1).strip()

    hp_asc_match = re.search(r"(?:Asc|A\d+|Ascension)[:\s]*(\d+(?:\s*[-–]\s*\d+)?)", text)
    if hp_asc_match:
        data["hp_asc_text"] = hp_asc_match.group(1).strip()

    # Move情報の抽出
    moves = []
    # テーブルからmoveを探す
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                move_text = " | ".join(c.get_text(strip=True) for c in cells)
                moves.append(move_text)

    if moves:
        data["moves_raw"] = moves

    # Power/ability情報
    powers = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        heading_text = heading.get_text(strip=True).lower()
        if any(kw in heading_text for kw in ["power", "ability", "innate", "passive"]):
            sibling = heading.find_next_sibling()
            if sibling:
                powers.append(sibling.get_text(strip=True)[:500])
    if powers:
        data["powers_raw"] = powers

    return data


def map_enemy_id(sts2gg_id: str) -> str | None:
    """slaythespire2.gg の ID を enemies.json の id に変換"""
    upper_id = sts2gg_id.upper().replace("-", "_")

    if upper_id in ENEMY_ID_MAP:
        return ENEMY_ID_MAP[upper_id]

    # 自動変換: lowercase + hyphen
    return sts2gg_id.lower().replace("_", "-")


def extract_hp_from_text(text: str) -> str | None:
    """テキストからHP情報を抽出"""
    # "173" or "173 (A8: 183)" or "173-183" パターン
    patterns = [
        r"(\d+(?:\s*[-–]\s*\d+)?(?:\s*\(A\d+:\s*\d+(?:\s*[-–]\s*\d+)?\))?)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1).strip()
    return None


def extract_move_damage(text: str) -> tuple[str | None, str | None]:
    """テキストからダメージ値を抽出 (base, ascension)"""
    # "7 (8)" or "6×2 (7×2)" パターン
    m = re.search(r"(\d+(?:×\d+)?)\s*(?:\((\d+(?:×\d+)?)\))?", text)
    if m:
        return m.group(1), m.group(2)
    return None, None


def compare_and_update(
    existing: dict,
    scraped_data: dict[str, dict],
    translate_client: translate.Client,
) -> list[dict]:
    """既存データとスクレイプデータを比較し、変更があれば更新"""
    changes: list[dict] = []
    enemies = existing["enemies"]

    for enemy in enemies:
        enemy_id = enemy.get("id", "")
        name_en = enemy.get("nameEn", "")

        # スクレイプデータとマッチング
        matched = None
        for slug, data in scraped_data.items():
            mapped_id = map_enemy_id(slug)
            if mapped_id == enemy_id:
                matched = data
                break
            if data.get("nameEn", "").lower() == name_en.lower():
                matched = data
                break

        if not matched:
            continue

        enemy_changes: list[str] = []

        # HP比較
        scraped_hp = matched.get("hp_text")
        if scraped_hp:
            current_hp = enemy.get("hp", "")
            # 数値のみ抽出して比較
            scraped_nums = re.findall(r"\d+", scraped_hp)
            current_nums = re.findall(r"\d+", current_hp.split("(")[0] if "(" in current_hp else current_hp)
            if scraped_nums and current_nums and scraped_nums[0] != current_nums[0]:
                old_hp = current_hp
                # アセンション値も取得
                hp_asc = matched.get("hp_asc_text", "")
                new_hp = scraped_hp
                if hp_asc:
                    new_hp = f"{scraped_hp} (A8: {hp_asc})"
                enemy["hp"] = new_hp
                enemy_changes.append(f"HP: {old_hp} → {new_hp}")

        # Move/ダメージ比較
        moves_raw = matched.get("moves_raw", [])
        if moves_raw and enemy.get("phases"):
            for phase in enemy["phases"]:
                for move in phase.get("moves", []):
                    current_damage = move.get("damage", "")
                    if current_damage == "-":
                        continue
                    # スクレイプデータ内にダメージ変更があるか探す
                    action_name = move.get("action", "")
                    for raw_move in moves_raw:
                        if action_name.lower() in raw_move.lower():
                            base, asc = extract_move_damage(raw_move)
                            if base:
                                current_base = re.findall(r"\d+", current_damage)
                                if current_base and current_base[0] != re.findall(r"\d+", base)[0]:
                                    old_dmg = current_damage
                                    new_dmg = base
                                    if asc:
                                        new_dmg = f"{base} (A: {asc})"
                                    move["damage"] = new_dmg
                                    enemy_changes.append(f"{action_name}ダメージ: {old_dmg} → {new_dmg}")

        if enemy_changes:
            changes.append({
                "enemy_id": enemy_id,
                "name": enemy.get("name", name_en),
                "nameEn": name_en,
                "changes": enemy_changes,
            })
            logger.info(f"更新: {name_en} - {', '.join(enemy_changes)}")

    return changes


def check_patch_note_changes() -> list[str]:
    """最新パッチノートからバランス変更に関する内容を抽出"""
    try:
        with open(PATCH_NOTES_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    notes = data.get("patch_notes", [])
    if not notes:
        return []

    latest = notes[0]
    balance_keywords = ["balance", "バランス", "buff", "nerf", "damage", "hp", "health",
                        "ダメージ", "体力", "筋力", "strength"]

    relevant_items: list[str] = []
    for section in latest.get("sections", []):
        heading = section.get("heading", "").lower()
        if any(kw in heading for kw in balance_keywords):
            relevant_items.extend(section.get("items", []))
            continue
        for item in section.get("items", []):
            if any(kw in item.lower() for kw in balance_keywords):
                relevant_items.append(item)

    return relevant_items[:20]


def save_update_log(changes: list[dict], patch_changes: list[str]) -> None:
    """更新ログを保存"""
    try:
        with open(UPDATE_LOG_FILE, encoding="utf-8") as f:
            log_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_data = {"updates": []}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if changes:
        details = []
        for c in changes:
            for ch in c["changes"]:
                details.append(f"{c['name']}({c['nameEn']}): {ch}")
        log_data["updates"].insert(0, {
            "date": today,
            "type": "enemy_update",
            "summary": f"{len(changes)}体の敵データを更新",
            "details": details,
            "source": "slaythespire2.gg",
        })

    if patch_changes:
        log_data["updates"].insert(0, {
            "date": today,
            "type": "patch_note",
            "summary": "パッチノートのバランス変更を検出",
            "details": patch_changes[:10],
            "source": "Steam",
        })

    # 最新100件のみ保持
    log_data["updates"] = log_data["updates"][:100]

    with open(UPDATE_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    logger.info(f"更新ログを保存: {UPDATE_LOG_FILE}")


def rebuild_site() -> bool:
    """Next.jsサイトを再ビルドしてPM2リスタート"""
    try:
        logger.info("Next.jsサイトをビルド中...")
        result = subprocess.run(
            "npm run build",
            cwd=REPO_ROOT,
            capture_output=True, text=True, timeout=300,
            shell=True,
        )
        if result.returncode != 0:
            logger.error(f"ビルド失敗:\n{result.stderr[-2000:]}")
            return False
        logger.info("ビルド成功")
        subprocess.run("pm2 restart sts2-wiki", check=True, timeout=30, shell=True)
        logger.info("PM2リスタート完了")
        return True
    except Exception as e:
        logger.error(f"リビルド失敗: {e}")
        return False


def git_push_changes(changes: list[dict]) -> bool:
    """変更をgit commit & pushする"""
    try:
        subprocess.run(
            ["git", "add", "data/enemies.json", "data/update-log.json"],
            cwd=REPO_ROOT, check=True, timeout=30,
        )
        summary = f"{len(changes)}体の敵データを更新" if changes else "定期更新チェック"
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
        subprocess.run(
            ["git", "push"],
            cwd=REPO_ROOT, check=True, timeout=60,
        )
        logger.info("git push完了")
        return True
    except Exception as e:
        logger.error(f"git push失敗: {e}")
        return False


def main() -> None:
    import time

    translate_client = translate.Client()

    # 1. slaythespire2.gg から敵リストを取得
    logger.info("slaythespire2.gg から敵データを取得中...")
    try:
        enemy_slugs = fetch_enemy_list()
    except Exception as e:
        logger.error(f"敵リスト取得失敗: {e}")
        sys.exit(1)

    # 2. 各敵の詳細データを取得（レートリミット対応）
    scraped: dict[str, dict] = {}
    for i, entry in enumerate(enemy_slugs):
        slug = entry["slug"]
        mapped = map_enemy_id(slug)
        if mapped is None:
            continue  # スキップ対象

        detail = fetch_enemy_detail(slug)
        if detail:
            scraped[slug] = detail

        if i % 10 == 9:
            time.sleep(2)  # 10件ごとに2秒待機

    logger.info(f"詳細データ取得完了: {len(scraped)} 件")

    # 3. 既存データと比較
    with open(ENEMIES_FILE, encoding="utf-8") as f:
        existing = json.load(f)

    changes = compare_and_update(existing, scraped, translate_client)

    # 4. パッチノートからバランス変更を確認
    patch_changes = check_patch_note_changes()
    if patch_changes:
        logger.info(f"パッチノートからバランス変更 {len(patch_changes)} 件を検出")

    # 5. 変更があれば保存
    if changes or patch_changes:
        # enemies.json 保存
        if changes:
            with open(ENEMIES_FILE, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            logger.info(f"enemies.json を更新: {len(changes)} 体")

        # 更新ログ保存
        save_update_log(changes, patch_changes)

        # git push
        if git_push_changes(changes):
            logger.info("GitHub へプッシュ完了（GitHub Actions で Firebase にデプロイされます）")

        # ローカルビルド＆PM2リスタート
        if rebuild_site():
            logger.info("サイト更新完了")
        else:
            logger.error("ビルド失敗。手動確認してください。")
            sys.exit(1)
    else:
        logger.info("敵データに変更はありませんでした。")
        # 変更なしでもログに実行記録を残す（ただしupdate-logには追加しない）


if __name__ == "__main__":
    main()
