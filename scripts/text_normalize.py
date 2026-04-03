from __future__ import annotations

import html
import re

MOJIBAKE_RE = re.compile(r"[縺繧繝螟譁譛謨蜿鬮逕縲]{2,}")
WHITESPACE_RE = re.compile(r"[ \t]+")

HEADING_JA_MAP = {
    "CONTENT": "コンテンツ",
    "BALANCE": "バランス調整",
    "ART": "アート",
    "BUG FIXES": "不具合修正",
    "USER INTERFACE & EXPERIENCE": "UI / UX",
    "USER INTERFACE": "UI",
    "GAMEPLAY": "ゲームプレイ",
    "AUDIO": "オーディオ",
    "LOCALIZATION": "ローカライズ",
    "MULTIPLAYER": "マルチプレイ",
    "PERFORMANCE": "パフォーマンス",
    "FEATURES": "新機能",
    "FIXES": "修正",
    "CHANGES": "変更",
    "NEW FEATURES": "新機能",
    "GENERAL": "全般",
    "SILENT": "サイレント",
    "IRONCLAD": "アイアンクラッド",
    "DEFECT": "ディフェクト",
    "WATCHER": "ウォッチャー",
    "NEOW": "ネオウ",
    "EVENTS": "イベント",
    "EVENT": "イベント",
    "POTIONS": "ポーション",
    "RELICS": "レリック",
    "ENEMIES": "敵",
    "MODDING": "MOD",
    "静けさ": "サイレント",
    "鉄壁装甲": "アイアンクラッド",
    "欠陥": "ディフェクト",
    "一般的な": "全般",
}

TEXT_REPLACEMENTS = (
    ("&#39;", "'"),
    ("&quot;", '"'),
    ("&amp;", "&"),
    ("&lt;", "<"),
    ("&gt;", ">"),
    (" -&gt; ", " → "),
    ("-&gt;", "→"),
    (" -> ", " → "),
    ("->", "→"),
    ("　", " "),
    ("廃止された準備と準備完了の戻り値", "Prepared / Prepared+ を以前の性能に戻しました"),
    ("一般:", "全般:"),
    ("Silent", "サイレント"),
    ("Ironclad", "アイアンクラッド"),
    ("The Defect", "ディフェクト"),
    ("Watcher", "ウォッチャー"),
    ("Neow", "ネオウ"),
    ("Strength", "筋力"),
    ("Dexterity", "敏捷性"),
    ("Block", "ブロック"),
)


def _decode_html_entities(text: str) -> str:
    decoded = text
    for _ in range(3):
        next_decoded = html.unescape(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    return decoded


def _repair_mojibake(text: str) -> str:
    if not MOJIBAKE_RE.search(text):
        return text

    try:
        repaired = text.encode("cp932").decode("utf-8")
    except UnicodeError:
        return text

    # 直した結果のほうが疑わしい文字列が減る場合だけ採用する
    if len(MOJIBAKE_RE.findall(repaired)) <= len(MOJIBAKE_RE.findall(text)):
        return repaired
    return text


def normalize_source_text(text: str) -> str:
    cleaned = _repair_mojibake(_decode_html_entities(text))
    cleaned = cleaned.replace(" -&gt; ", " → ").replace("-&gt;", "→").replace(" -> ", " → ").replace("->", "→").replace("　", " ")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+([、。！？,.!?）」\]】])", r"\1", cleaned)
    cleaned = re.sub(r"([（(「\[])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s*→\s*", " → ", cleaned)
    cleaned = re.sub(r"\s*:\s*", ": ", cleaned)
    cleaned = re.sub(r"\s*：\s*", "：", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_patch_note_text(text: str) -> str:
    cleaned = normalize_source_text(text)
    for before, after in TEXT_REPLACEMENTS:
        cleaned = cleaned.replace(before, after)
    return cleaned.strip()


def normalize_heading_text(text: str) -> str:
    cleaned = normalize_patch_note_text(text)
    heading_key = cleaned.strip().rstrip(":：").upper()
    return HEADING_JA_MAP.get(heading_key, cleaned)
