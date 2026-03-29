import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "スレスパ2 敵だけ攻略",
  description: "Slay the Spire 2 敵・ボス攻略Wiki",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="min-h-screen" style={{ backgroundColor: "#0a0a0f" }}>
        <header className="border-b border-yellow-900/30 bg-[#0d0d1a]" style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 50 }}>
          <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-4">
            <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity flex-shrink-0">
              <span className="text-2xl">⚔️</span>
              <h1 className="text-xl font-bold" style={{ color: "#d4a44a", fontFamily: "'Noto Serif JP', serif" }}>
                スレスパ2 攻略Wiki
              </h1>
            </a>
            <nav className="flex items-center gap-1 ml-2">
              <a href="/" className="text-xs px-3 py-1.5 rounded transition-colors hover:opacity-80"
                style={{ color: "#9aa0a8", border: "1px solid transparent" }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#2a3050")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "transparent")}>
                👹 敵一覧
              </a>
              <a href="/patch-notes" className="text-xs px-3 py-1.5 rounded transition-colors hover:opacity-80"
                style={{ color: "#9aa0a8", border: "1px solid transparent" }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#2a3050")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "transparent")}>
                📋 パッチノート
              </a>
            </nav>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-4 py-6" style={{ paddingTop: "calc(57px + 1.5rem)" }}>
          {children}
        </main>
        <footer className="border-t border-yellow-900/20 mt-12 py-4" />
      </body>
    </html>
  );
}
