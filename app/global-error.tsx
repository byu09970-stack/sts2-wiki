"use client";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="ja">
      <body style={{ backgroundColor: "#0a0a0f", color: "#e0e0e0", display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", flexDirection: "column", gap: "1rem" }}>
        <p style={{ fontSize: "2rem" }}>⚠️</p>
        <p style={{ color: "#a0a0b0" }}>致命的なエラーが発生しました</p>
        <button onClick={reset} style={{ padding: "0.5rem 1rem", backgroundColor: "#d4a44a22", color: "#d4a44a", border: "1px solid #d4a44a", borderRadius: "0.25rem", cursor: "pointer" }}>
          再試行
        </button>
      </body>
    </html>
  );
}
