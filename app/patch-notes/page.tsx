import Link from "next/link";
import patchNotesData from "@/data/patch-notes.json";

type PatchNote = {
  gid: string;
  version: string;
  title: string;
  title_ja: string;
  date: string;
  date_unix: number;
  is_beta: boolean;
  summary_ja: string;
  sections: { heading: string; items: string[] }[];
  url: string;
};

export const metadata = {
  title: "パッチノート | スレスパ2 攻略Wiki",
  description: "Slay the Spire 2 パッチノート一覧（日本語）",
};

export default function PatchNotesPage() {
  const notes = patchNotesData.patch_notes as PatchNote[];
  const lastUpdated = new Date(patchNotesData.last_updated).toLocaleDateString("ja-JP", {
    year: "numeric", month: "long", day: "numeric",
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-1" style={{ color: "#d4a44a" }}>
            📋 パッチノート
          </h2>
          <p className="text-sm" style={{ color: "#9aa0a8" }}>
            公式パッチノートの日本語まとめ（Steam公式より自動取得）
          </p>
        </div>
        <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: "#111827", color: "#606070", border: "1px solid #2a3050" }}>
          最終更新: {lastUpdated}
        </span>
      </div>

      <div className="flex flex-col gap-3">
        {notes.map((note) => (
          <Link
            key={note.gid}
            href={`/patch-notes/${encodeURIComponent(note.version)}`}
            className="block rounded-lg p-4 transition-colors"
            style={{
              backgroundColor: "#0d1117",
              border: "1px solid #2a3050",
              textDecoration: "none",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#d4a44a66")}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#2a3050")}
          >
            <div className="flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-sm font-bold" style={{ color: "#d4a44a" }}>
                    {note.version}
                  </span>
                  {note.is_beta && (
                    <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: "#1a2a1a", color: "#6aaa6a", border: "1px solid #2a4a2a" }}>
                      BETA
                    </span>
                  )}
                  <span className="text-xs" style={{ color: "#606070" }}>
                    {note.date}
                  </span>
                </div>
                <p className="text-sm font-medium mb-1" style={{ color: "#c0c8d8" }}>
                  {note.title_ja}
                </p>
                <p className="text-xs leading-relaxed" style={{ color: "#7a8090" }}>
                  {note.summary_ja}
                </p>
              </div>
              <span className="text-xs flex-shrink-0 mt-1" style={{ color: "#404050" }}>
                →
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
