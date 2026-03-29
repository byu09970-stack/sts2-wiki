"use client";

import { useState, useMemo, useEffect } from "react";
import { Suspense } from "react";
import EnemyCard from "@/components/EnemyCard";
import enemiesData from "@/data/enemies.json";
import { Enemy, EnemyType, ActKey } from "@/types/enemy";

const ACT_OPTIONS: { key: ActKey; label: string }[] = [
  { key: "act1a", label: "繁茂の地" },
  { key: "act1b", label: "地下水路" },
  { key: "act2", label: "魔窟" },
  { key: "act3", label: "栄光の路" },
];

const TYPE_OPTIONS: { key: EnemyType; label: string }[] = [
  { key: "boss", label: "ボス" },
  { key: "elite", label: "エリート" },
  { key: "normal", label: "通常" },
];

function getSortKey(e: Enemy): number {
  if (e.type === "boss") return 0;
  if (e.type === "elite") return 1;
  if (e.type === "normal" && e.encounterPool === "normal") return 2;
  return 3;
}

const SESSION_KEY = "sts2-filter";

function loadSession(): { search: string; acts: ActKey[]; types: EnemyType[]; sidebarOpen: boolean } {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (raw) return { sidebarOpen: true, ...JSON.parse(raw) };
  } catch {}
  return { search: "", acts: [], types: [], sidebarOpen: true };
}

function saveSession(search: string, acts: ActKey[], types: EnemyType[], sidebarOpen: boolean) {
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({ search, acts, types, sidebarOpen }));
  } catch {}
}

const SECTIONS = [
  { key: "boss",          label: "ボス",        icon: "👹", color: "#c0392b", borderColor: "#7b1d1d", match: (e: Enemy) => e.type === "boss" },
  { key: "elite",         label: "エリート",     icon: "💀", color: "#8e44ad", borderColor: "#4a1a6a", match: (e: Enemy) => e.type === "elite" },
  { key: "normal_strong", label: "通常（後半）", icon: "⚔️", color: "#546e7a", borderColor: "#2a3a42", match: (e: Enemy) => e.type === "normal" && e.encounterPool === "normal" },
  { key: "normal_weak",   label: "通常（序盤）", icon: "🐾", color: "#455a64", borderColor: "#1e2c33", match: (e: Enemy) => e.type === "normal" && e.encounterPool === "weak" },
] as const;

const SIDEBAR_WIDTH = 248;
const HEADER_HEIGHT = 57;

function EnemyListContent() {
  const [search, setSearch] = useState("");
  const [selectedActs, setSelectedActs] = useState<Set<ActKey>>(new Set());
  const [selectedTypes, setSelectedTypes] = useState<Set<EnemyType>>(new Set());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
    const saved = loadSession();
    if (saved.search) setSearch(saved.search);
    if (saved.acts.length > 0) setSelectedActs(new Set(saved.acts));
    if (saved.types.length > 0) setSelectedTypes(new Set(saved.types));
    setSidebarOpen(saved.sidebarOpen ?? true);
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (!loaded) return;
    saveSession(search, [...selectedActs] as ActKey[], [...selectedTypes] as EnemyType[], sidebarOpen);
  }, [search, selectedActs, selectedTypes, sidebarOpen, loaded]);

  const toggleAct = (act: ActKey) => {
    setSelectedActs((prev) => { const n = new Set(prev); n.has(act) ? n.delete(act) : n.add(act); return n; });
  };
  const toggleType = (type: EnemyType) => {
    setSelectedTypes((prev) => { const n = new Set(prev); n.has(type) ? n.delete(type) : n.add(type); return n; });
  };

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return (enemiesData.enemies as Enemy[])
      .filter((e) => {
        const matchSearch = !q || e.name.toLowerCase().includes(q) || e.nameEn.toLowerCase().includes(q);
        const matchAct = selectedActs.size === 0 || selectedActs.has(e.act);
        const matchType = selectedTypes.size === 0 || selectedTypes.has(e.type);
        return matchSearch && matchAct && matchType;
      })
      .sort((a, b) => getSortKey(a) - getSortKey(b));
  }, [search, selectedActs, selectedTypes]);

  const meta = enemiesData.biomeMeta as Record<ActKey, { label: string; weakPoolCount: number; normalPoolFrom: number }>;
  const poolActs = selectedActs.size > 0 ? [...selectedActs] : (Object.keys(meta) as ActKey[]);
  const activeFilterCount = selectedActs.size + selectedTypes.size + (search ? 1 : 0);

  return (
    <>
      {/* ━━━ 固定サイドバー ━━━ */}
      <div
        style={{
          position: "fixed",
          top: HEADER_HEIGHT,
          left: mounted ? (sidebarOpen ? 0 : -SIDEBAR_WIDTH) : 0,
          width: SIDEBAR_WIDTH,
          height: `calc(100vh - ${HEADER_HEIGHT}px)`,
          zIndex: 40,
          transition: mounted ? "left 0.25s ease" : "none",
          display: "flex",
        }}
      >
        {/* サイドバー本体 */}
        <div
          style={{
            width: SIDEBAR_WIDTH,
            height: "100%",
            backgroundColor: "#0a0d1a",
            borderRight: "1px solid #2a3050",
            overflowY: "auto",
            padding: "16px 12px",
            flexShrink: 0,
          }}
        >
          <p className="text-xs font-bold mb-4 tracking-widest" style={{ color: "#d4a44a" }}>
            🔎 検索・絞り込み
          </p>

          {/* 検索バー */}
          <div className="relative mb-5">
            <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-sm" style={{ color: "#606070" }}>🔍</span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="敵名を入力..."
              className="w-full pl-8 pr-7 py-2 rounded-lg outline-none text-xs transition-colors"
              style={{ backgroundColor: "#16213e", border: "1px solid #2a3050", color: "#e0e0e0" }}
              onFocus={(e) => (e.target.style.borderColor = "#d4a44a66")}
              onBlur={(e) => (e.target.style.borderColor = "#2a3050")}
            />
            {search && (
              <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-xs" style={{ color: "#606070" }}>✕</button>
            )}
          </div>

          {/* Act フィルター */}
          <div className="mb-5">
            <p className="text-xs mb-2 font-medium" style={{ color: "#606070" }}>Act</p>
            <div className="flex flex-col gap-1.5">
              {ACT_OPTIONS.map(({ key, label }) => (
                <button key={key} onClick={() => toggleAct(key)}
                  className="w-full text-left px-3 py-1.5 rounded text-xs transition-colors"
                  style={{
                    backgroundColor: selectedActs.has(key) ? "#d4a44a18" : "transparent",
                    color: selectedActs.has(key) ? "#d4a44a" : "#a0a0b0",
                    border: `1px solid ${selectedActs.has(key) ? "#d4a44a66" : "#1e2a3e"}`,
                  }}>
                  {selectedActs.has(key) ? "▶ " : "　"}{label}
                </button>
              ))}
            </div>
          </div>

          {/* タイプ フィルター */}
          <div className="mb-5">
            <p className="text-xs mb-2 font-medium" style={{ color: "#606070" }}>タイプ</p>
            <div className="flex flex-col gap-1.5">
              {TYPE_OPTIONS.map(({ key, label }) => {
                const colors = {
                  boss:   { on: "#e57373", bg: "#c0392b18", border: "#c0392b66" },
                  elite:  { on: "#ce93d8", bg: "#8e44ad18", border: "#8e44ad66" },
                  normal: { on: "#b0bec5", bg: "#37414f",   border: "#546e7a66" },
                };
                const c = colors[key];
                return (
                  <button key={key} onClick={() => toggleType(key)}
                    className="w-full text-left px-3 py-1.5 rounded text-xs transition-colors"
                    style={{
                      backgroundColor: selectedTypes.has(key) ? c.bg : "transparent",
                      color: selectedTypes.has(key) ? c.on : "#a0a0b0",
                      border: `1px solid ${selectedTypes.has(key) ? c.border : "#1e2a3e"}`,
                    }}>
                    {selectedTypes.has(key) ? "▶ " : "　"}{label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* リセット */}
          {activeFilterCount > 0 && (
            <button
              onClick={() => { setSearch(""); setSelectedActs(new Set()); setSelectedTypes(new Set()); }}
              className="w-full py-1.5 rounded text-xs transition-colors"
              style={{ backgroundColor: "#1a1010", color: "#a07070", border: "1px solid #503030" }}
            >
              フィルターをリセット
            </button>
          )}
        </div>

        {/* 開閉タブ（サイドバーの右端に張り付く） */}
        <button
          onClick={() => setSidebarOpen((v) => !v)}
          style={{
            position: "absolute",
            right: -28,
            top: "50%",
            transform: "translateY(-50%)",
            width: 28,
            height: 56,
            backgroundColor: "#16213e",
            border: "1px solid #2a3050",
            borderLeft: "none",
            borderRadius: "0 6px 6px 0",
            color: "#a0a0b0",
            fontSize: 10,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 2,
          }}
          title={sidebarOpen ? "サイドバーを閉じる" : "サイドバーを開く"}
        >
          <span>{sidebarOpen ? "◀" : "▶"}</span>
        </button>
      </div>

      {/* ━━━ メインコンテンツ（サイドバー分だけ左マージン） ━━━ */}
      <div
        style={{
          marginLeft: mounted ? (sidebarOpen ? SIDEBAR_WIDTH : 0) : SIDEBAR_WIDTH,
          transition: mounted ? "margin-left 0.25s ease" : "none",
        }}
      >
        {/* タイトル */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold mb-1" style={{ color: "#d4a44a" }}>敵一覧</h2>
            <p className="text-sm" style={{ color: "#9aa0a8" }}>全Act・全敵の行動パターンと攻略メモ</p>
          </div>
          <span className="text-xs px-2 py-1 rounded self-end" style={{ backgroundColor: "#111827", color: "#a0a0b0", border: "1px solid #2a3050" }}>
            ※ 数値のA表記はアセンションレベル
          </span>
        </div>

        {/* 件数 */}
        <div className="flex items-center gap-2 mb-5 text-xs" style={{ color: "#606070" }}>
          <span>{filtered.length} 件</span>
        </div>

        {/* セクション別グリッド */}
        {filtered.length === 0 ? (
          <div className="text-center py-16" style={{ color: "#606070" }}>
            <p className="text-2xl mb-2">🔍</p>
            <p>条件に一致する敵が見つかりませんでした</p>
          </div>
        ) : (
          <div className="flex flex-col gap-8">
            {SECTIONS.map((section) => {
              const enemies = filtered.filter(section.match);
              if (enemies.length === 0) return null;

              // プール情報（通常敵セクションのみ）
              const poolInfoItems = section.key === "normal_weak" || section.key === "normal_strong"
                ? poolActs.map((act) => {
                    const m = meta[act];
                    if (!m) return null;
                    const text = section.key === "normal_weak"
                      ? `${m.label}: 最初の${m.weakPoolCount}戦`
                      : `${m.label}: ${m.normalPoolFrom}戦目〜`;
                    return { act, text };
                  }).filter(Boolean)
                : [];

              return (
                <div key={section.key}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                      style={{ backgroundColor: `${section.color}18`, border: `1px solid ${section.borderColor}` }}>
                      <span className="text-base">{section.icon}</span>
                      <span className="text-sm font-bold" style={{ color: "#9aa0a8" }}>{section.label}</span>
                      <span className="text-xs" style={{ color: "#9aa0a8" }}>{enemies.length}体</span>
                    </div>
                    {poolInfoItems.length > 0 && (
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {poolInfoItems.map((item) => item && (
                          <span key={item.act} className="text-sm font-medium px-2.5 py-0.5 rounded"
                            style={{ backgroundColor: "#111827", color: "#9aa0a8", border: "1px solid #2a3a50" }}>
                            {item.text}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="flex-1 h-px" style={{ backgroundColor: section.borderColor }} />
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {enemies.map((enemy) => (
                      <EnemyCard key={enemy.id} enemy={enemy} />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

      </div>
    </>
  );
}

export default function HomePage() {
  return (
    <div>
      <Suspense fallback={<div style={{ color: "#606070" }}>読み込み中...</div>}>
        <EnemyListContent />
      </Suspense>
    </div>
  );
}
