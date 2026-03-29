import Link from "next/link";
import { Enemy } from "@/types/enemy";


const TYPE_STYLES: Record<string, string> = {
  boss: "bg-red-900/60 text-red-300 border border-red-800/50",
  elite: "bg-purple-900/60 text-purple-300 border border-purple-800/50",
  normal: "bg-slate-800/60 text-slate-300 border border-slate-700/50",
};

function getTypeLabel(enemy: Enemy): string {
  if (enemy.type === "boss") return "ボス";
  if (enemy.type === "elite") return "エリート";
  if (enemy.encounterPool === "weak") return "通常（序盤）";
  if (enemy.encounterPool === "normal") return "通常（後半）";
  return "通常";
}

const CARD_BORDER: Record<string, string> = {
  boss: "border-red-900/40 hover:border-red-700/60",
  elite: "border-purple-900/40 hover:border-purple-700/60",
  normal: "border-slate-700/30 hover:border-slate-500/50",
};

const PLACEHOLDER_EMOJI: Record<string, string> = {
  boss: "👹",
  elite: "💀",
  normal: "🐾",
};

export default function EnemyCard({ enemy }: { enemy: Enemy }) {
  return (
    <Link href={`/enemies/${enemy.id}`}>
      <div
        className={`rounded-lg border p-4 transition-all duration-200 cursor-pointer fade-in ${CARD_BORDER[enemy.type]}`}
        style={{ backgroundColor: "#16213e" }}
      >
        {/* 画像エリア */}
        <div
          className="w-full h-20 rounded mb-3 flex items-center justify-center overflow-hidden"
          style={{ backgroundColor: "#0d1527" }}
        >
          {enemy.imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={enemy.imageUrl}
              alt={enemy.name}
              className="w-full h-full object-contain p-1"
              onError={(e) => {
                const target = e.currentTarget;
                target.style.display = "none";
                const parent = target.parentElement;
                if (parent) parent.innerHTML = `<span style="font-size:1.875rem">${PLACEHOLDER_EMOJI[enemy.type]}</span>`;
              }}
            />
          ) : (
            <span className="text-3xl">{PLACEHOLDER_EMOJI[enemy.type]}</span>
          )}
        </div>

        {/* 名前 */}
        <div className="mb-2">
          <p className="font-bold text-sm leading-tight" style={{ color: "#e0e0e0" }}>
            {enemy.name}
          </p>
        </div>

        {/* バッジ行 */}
        <div className="flex items-center gap-1 flex-wrap">
          <span className={`text-xs px-2 py-0.5 rounded font-medium ${TYPE_STYLES[enemy.type]}`}>
            {getTypeLabel(enemy)}
          </span>
          <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: "#0d1527", color: "#a0a0b0", border: "1px solid #2a3050" }}>
            {enemy.biome}
          </span>
        </div>

      </div>
    </Link>
  );
}
