import { notFound } from "next/navigation";
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

export function generateStaticParams() {
  return (patchNotesData.patch_notes as PatchNote[]).map((n) => ({
    version: encodeURIComponent(n.version),
  }));
}

export async function generateMetadata({ params }: { params: Promise<{ version: string }> }) {
  const { version: rawVersion } = await params;
  const version = decodeURIComponent(rawVersion);
  const note = (patchNotesData.patch_notes as PatchNote[]).find((n) => n.version === version);
  if (!note) return { title: "パッチノート | スレスパ2 攻略Wiki" };
  return {
    title: `${note.version} パッチノート | スレスパ2 攻略Wiki`,
    description: note.summary_ja,
  };
}

export default async function PatchNoteDetailPage({ params }: { params: Promise<{ version: string }> }) {
  const { version: rawVersion } = await params;
  const version = decodeURIComponent(rawVersion);
  const notes = patchNotesData.patch_notes as PatchNote[];
  const note = notes.find((n) => n.version === version);
  if (!note) notFound();

  const idx = notes.indexOf(note);
  const prev = idx > 0 ? notes[idx - 1] : null;
  const next = idx < notes.length - 1 ? notes[idx + 1] : null;

  return (
    <div className="max-w-3xl">
      {/* パンくず */}
      <div className="flex items-center gap-2 mb-6 text-xs" style={{ color: "#606070" }}>
        <Link href="/" style={{ color: "#606070" }}>ホーム</Link>
        <span>›</span>
        <Link href="/patch-notes" style={{ color: "#606070" }}>パッチノート</Link>
        <span>›</span>
        <span style={{ color: "#a0a0b0" }}>{note.version}</span>
      </div>

      {/* ヘッダー */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2 flex-wrap">
          <h2 className="text-2xl font-bold" style={{ color: "#d4a44a" }}>
            {note.version}
          </h2>
          {note.is_beta && (
            <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: "#1a2a1a", color: "#6aaa6a", border: "1px solid #2a4a2a" }}>
              BETA
            </span>
          )}
          <span className="text-sm" style={{ color: "#606070" }}>{note.date}</span>
        </div>
        <p className="text-base font-medium mb-3" style={{ color: "#c0c8d8" }}>
          {note.title_ja}
        </p>
        <div className="rounded-lg p-4" style={{ backgroundColor: "#0d1117", border: "1px solid #1e2a3e" }}>
          <p className="text-sm leading-relaxed" style={{ color: "#9aa0a8" }}>
            {note.summary_ja}
          </p>
        </div>
      </div>

      {/* セクション */}
      <div className="flex flex-col gap-4 mb-8">
        {note.sections.map((section, i) => (
          <div key={i} className="rounded-lg overflow-hidden" style={{ border: "1px solid #2a3050" }}>
            <div className="px-4 py-2.5" style={{ backgroundColor: "#0f1628" }}>
              <h3 className="text-sm font-bold" style={{ color: "#d4a44a" }}>
                {section.heading}
              </h3>
            </div>
            <div className="px-4 py-3" style={{ backgroundColor: "#0a0d1a" }}>
              <ul className="flex flex-col gap-1.5">
                {section.items.map((item, j) => (
                  <li key={j} className="flex items-start gap-2 text-sm" style={{ color: "#b0b8c8" }}>
                    <span className="flex-shrink-0 mt-0.5" style={{ color: "#404060" }}>・</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* 公式リンク */}
      <div className="mb-8">
        <a
          href={note.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-xs px-3 py-2 rounded"
          style={{ backgroundColor: "#111827", color: "#7090b0", border: "1px solid #2a3050" }}
        >
          📄 Steam公式パッチノートを見る（英語）
        </a>
      </div>

      {/* 前後ナビ */}
      <div className="flex justify-between gap-4 pt-4" style={{ borderTop: "1px solid #1e2a3e" }}>
        {next ? (
          <Link
            href={`/patch-notes/${encodeURIComponent(next.version)}`}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded"
            style={{ backgroundColor: "#0d1117", color: "#9aa0a8", border: "1px solid #2a3050" }}
          >
            ← {next.version}（古い）
          </Link>
        ) : <div />}
        {prev ? (
          <Link
            href={`/patch-notes/${encodeURIComponent(prev.version)}`}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded"
            style={{ backgroundColor: "#0d1117", color: "#9aa0a8", border: "1px solid #2a3050" }}
          >
            {prev.version}（新しい）→
          </Link>
        ) : <div />}
      </div>
    </div>
  );
}
