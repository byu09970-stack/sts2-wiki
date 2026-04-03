"use client";

import { useEffect, useRef, useState } from "react";

export default function MemoSection({ enemyId }: { enemyId: string }) {
  const [memo, setMemo] = useState("");
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const saveResetTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(`memo_${enemyId}`);
    const storedAt = localStorage.getItem(`memo_${enemyId}_at`);
    setMemo(stored ?? "");
    setSavedAt(storedAt ?? null);
    setSaved(false);
  }, [enemyId]);

  useEffect(() => {
    return () => {
      if (saveResetTimerRef.current) {
        clearTimeout(saveResetTimerRef.current);
        saveResetTimerRef.current = null;
      }
    };
  }, []);

  const handleSave = () => {
    const now = new Date().toLocaleString("ja-JP");
    localStorage.setItem(`memo_${enemyId}`, memo);
    localStorage.setItem(`memo_${enemyId}_at`, now);
    setSavedAt(now);
    setSaved(true);
    if (saveResetTimerRef.current) {
      clearTimeout(saveResetTimerRef.current);
    }
    saveResetTimerRef.current = setTimeout(() => {
      setSaved(false);
      saveResetTimerRef.current = null;
    }, 2000);
  };

  const handleClear = () => {
    if (!confirm("メモをクリアしますか？")) return;
    localStorage.removeItem(`memo_${enemyId}`);
    localStorage.removeItem(`memo_${enemyId}_at`);
    setMemo("");
    setSavedAt(null);
  };

  return (
    <div className="rounded-lg p-4" style={{ backgroundColor: "#16213e", border: "1px solid #2a3050" }}>
      <h3 className="font-bold mb-3" style={{ color: "#d4a44a" }}>
        📝 自分用メモ
      </h3>
      <textarea
        value={memo}
        onChange={(e) => setMemo(e.target.value)}
        placeholder="攻略メモ、気づいた点、デッキ構成など..."
        rows={5}
        className="w-full rounded p-3 text-sm outline-none transition-colors"
        style={{
          backgroundColor: "#0d1527",
          border: "1px solid #2a3050",
          color: "#e0e0e0",
          fontFamily: "'Noto Sans JP', sans-serif",
        }}
        onFocus={(e) => (e.target.style.borderColor = "#d4a44a66")}
        onBlur={(e) => (e.target.style.borderColor = "#2a3050")}
      />
      <div className="flex items-center gap-2 mt-2">
        <button
          onClick={handleSave}
          className="px-4 py-1.5 rounded text-sm font-medium transition-colors"
          style={{
            backgroundColor: saved ? "#2d5a2d" : "#d4a44a22",
            color: saved ? "#86efac" : "#d4a44a",
            border: `1px solid ${saved ? "#4ade80" : "#d4a44a"}`,
          }}
        >
          {saved ? "✓ 保存しました" : "保存"}
        </button>
        {memo && (
          <button
            onClick={handleClear}
            className="px-4 py-1.5 rounded text-sm transition-colors"
            style={{
              backgroundColor: "#1a1010",
              color: "#a07070",
              border: "1px solid #503030",
            }}
          >
            クリア
          </button>
        )}
        {savedAt && (
          <span className="text-xs ml-auto" style={{ color: "#606070" }}>
            最終更新: {savedAt}
          </span>
        )}
      </div>
    </div>
  );
}
