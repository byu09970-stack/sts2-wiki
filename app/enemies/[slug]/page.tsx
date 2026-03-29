import { notFound } from "next/navigation";
import Link from "next/link";
import MemoSection from "@/components/MemoSection";
import enemiesData from "@/data/enemies.json";
import { Enemy } from "@/types/enemy";

const TYPE_LABELS: Record<string, string> = {
  boss: "ボス",
  elite: "エリート",
  normal: "通常",
};

const TYPE_STYLES: Record<string, { badge: string; header: string }> = {
  boss: {
    badge: "bg-red-900/60 text-red-300 border border-red-800/50",
    header: "border-red-900/40",
  },
  elite: {
    badge: "bg-purple-900/60 text-purple-300 border border-purple-800/50",
    header: "border-purple-900/40",
  },
  normal: {
    badge: "bg-slate-800/60 text-slate-300 border border-slate-700/50",
    header: "border-slate-700/30",
  },
};

export async function generateStaticParams() {
  return (enemiesData.enemies as Enemy[]).map((e) => ({ slug: e.id }));
}

export default async function EnemyDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const enemy = (enemiesData.enemies as Enemy[]).find(
    (e) => e.id === slug
  );

  if (!enemy) notFound();

  const styles = TYPE_STYLES[enemy.type];

  return (
    <div className="max-w-3xl mx-auto">
      {/* パンくず */}
      <nav className="mb-4 text-sm flex items-center gap-2" style={{ color: "#606070" }}>
        <Link href="/" className="hover:underline" style={{ color: "#a0a0b0" }}>
          敵一覧
        </Link>
        <span>›</span>
        <span style={{ color: "#e0e0e0" }}>{enemy.name}</span>
      </nav>

      {/* ヘッダーカード */}
      <div
        className={`rounded-xl p-5 mb-5 border ${styles.header}`}
        style={{ backgroundColor: "#16213e" }}
      >
        <div className="flex gap-4">
          {/* 画像 */}
          <div
            className="w-24 h-24 rounded-lg flex-shrink-0 flex items-center justify-center overflow-hidden"
            style={{ backgroundColor: "#0d1527" }}
          >
            {enemy.imageUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={enemy.imageUrl}
                alt={enemy.name}
                className="w-full h-full object-contain p-1"
              />
            ) : (
              <span className="text-5xl">
                {enemy.type === "boss" ? "👹" : enemy.type === "elite" ? "💀" : "🐾"}
              </span>
            )}
          </div>

          {/* 名前・バッジ */}
          <div className="flex-1">
            <h1 className="text-2xl font-bold mb-1" style={{ color: "#e0e0e0" }}>
              {enemy.name}
            </h1>
            <div className="flex flex-wrap gap-2 mb-3">
              <span className={`text-xs px-2.5 py-1 rounded font-medium ${styles.badge}`}>
                {TYPE_LABELS[enemy.type]}
              </span>
              <span
                className="text-xs px-2.5 py-1 rounded"
                style={{ backgroundColor: "#0d1527", color: "#a0a0b0", border: "1px solid #2a3050" }}
              >
                {enemy.biome}
              </span>
              {enemy.hp && enemy.hp !== "-" && (
                <span
                  className="text-xs px-2.5 py-1 rounded"
                  style={{ backgroundColor: "#1a2a1a", color: "#86efac", border: "1px solid #2a4a2a" }}
                >
                  HP: {enemy.hp}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 特殊能力 */}
      {enemy.abilities.length > 0 && (
        <section className="mb-5">
          <h2 className="text-base font-bold mb-2" style={{ color: "#d4a44a" }}>
            ⚡ 特殊能力
          </h2>
          <div className="space-y-2">
            {enemy.abilities.map((ab, i) => (
              <div
                key={i}
                className="rounded-lg p-3"
                style={{ backgroundColor: "#1a1a2e", border: "1px solid #2a3050" }}
              >
                <p className="text-sm font-bold mb-1" style={{ color: "#e8c272" }}>
                  {ab.name}
                </p>
                <p className="text-sm" style={{ color: "#a0a0b0" }}>
                  {ab.description}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 行動パターン */}
      {enemy.phases.length > 0 && (
        <section className="mb-5">
          <h2 className="text-base font-bold mb-2" style={{ color: "#d4a44a" }}>
            🗡️ 行動パターン
          </h2>
          <div className="space-y-4">
            {enemy.phases.map((phase, pi) => (
              <div key={pi}>
                <p className="text-sm font-medium mb-2" style={{ color: "#a0a0b0" }}>
                  {phase.name}
                </p>
                <div className="rounded-lg overflow-hidden" style={{ border: "1px solid #2a3050" }}>
                  <table className="w-full text-sm">
                    <thead>
                      <tr>
                        <th className="text-left py-2 px-3 text-xs" style={{ backgroundColor: "#111827", color: "#d4a44a", width: "4rem" }}>
                          ターン
                        </th>
                        <th className="text-left py-2 px-3 text-xs" style={{ backgroundColor: "#111827", color: "#d4a44a", width: "8rem" }}>
                          行動名
                        </th>
                        <th className="text-left py-2 px-3 text-xs" style={{ backgroundColor: "#111827", color: "#d4a44a" }}>
                          効果
                        </th>
                        <th className="text-left py-2 px-3 text-xs" style={{ backgroundColor: "#111827", color: "#d4a44a", width: "6rem" }}>
                          ダメージ
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {phase.moves.map((move, mi) => (
                        <tr key={mi}>
                          <td className="py-2 px-3 text-xs" style={{ color: "#a0a0b0", borderColor: "#1e2a3e" }}>
                            {move.turn}
                          </td>
                          <td className="py-2 px-3 text-xs font-medium" style={{ color: "#e0e0e0", borderColor: "#1e2a3e" }}>
                            {move.action}
                          </td>
                          <td className="py-2 px-3 text-xs" style={{ color: "#a0a0b0", borderColor: "#1e2a3e" }}>
                            {move.effect}
                          </td>
                          <td
                            className="py-2 px-3 text-xs font-mono"
                            style={{
                              color: move.damage === "-" ? "#444" : "#fca5a5",
                              borderColor: "#1e2a3e",
                            }}
                          >
                            {move.damage}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 攻略メモ（プリセット） */}
      {enemy.tips && (
        <section className="mb-5">
          <h2 className="text-base font-bold mb-2" style={{ color: "#d4a44a" }}>
            💡 攻略メモ
          </h2>
          <div
            className="rounded-lg p-4 text-sm leading-relaxed"
            style={{ backgroundColor: "#1a2a1a", border: "1px solid #2a4a2a", color: "#a0c4a0" }}
          >
            {enemy.tips}
          </div>
        </section>
      )}

      {/* 自分用メモ */}
      <section className="mb-5">
        <MemoSection enemyId={enemy.id} />
      </section>

      {/* 戻るボタン */}
      <div className="mt-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm transition-colors"
          style={{ color: "#a0a0b0" }}
        >
          ← 敵一覧に戻る
        </Link>
      </div>
    </div>
  );
}
