"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4" style={{ color: "#e0e0e0" }}>
      <p className="text-4xl">⚠️</p>
      <p style={{ color: "#a0a0b0" }}>エラーが発生しました: {error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 rounded text-sm"
        style={{ backgroundColor: "#d4a44a22", color: "#d4a44a", border: "1px solid #d4a44a" }}
      >
        再試行
      </button>
    </div>
  );
}
