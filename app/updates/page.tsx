import updateLogData from "@/data/update-log.json";

type UpdateEntry = {
  date: string;
  type: "enemy_update" | "patch_note" | "new_enemy";
  summary: string;
  details: string[];
  source?: string;
};

export const metadata = {
  title: "更新履歴 | スレスパ2 攻略Wiki",
  description: "サイトの更新履歴",
};

const TYPE_LABELS: Record<string, { label: string; color: string; bg: string; border: string }> = {
  enemy_update: { label: "敵データ更新", color: "#e0a040", bg: "#2a2010", border: "#4a3a10" },
  patch_note: { label: "パッチノート", color: "#60a0e0", bg: "#102030", border: "#1a3050" },
  new_enemy: { label: "新規追加", color: "#60c060", bg: "#102a10", border: "#1a4a1a" },
};

const MAX_VISIBLE_UPDATES = 10;

export default function UpdatesPage() {
  const allUpdates = updateLogData.updates as UpdateEntry[];
  const updates = allUpdates.slice(0, MAX_VISIBLE_UPDATES);

  // 日付でグループ化
  const grouped = updates.reduce<Record<string, UpdateEntry[]>>((acc, entry) => {
    if (!acc[entry.date]) acc[entry.date] = [];
    acc[entry.date].push(entry);
    return acc;
  }, {});

  const sortedDates = Object.keys(grouped).sort((a, b) => b.localeCompare(a));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-1" style={{ color: "#d4a44a" }}>
            🔄 更新履歴
          </h2>
          <p className="text-sm" style={{ color: "#9aa0a8" }}>
            攻略サイト巡回による敵データ更新・パッチノート反映の記録
          </p>
        </div>
        {updates.length > 0 && (
          <span
            className="text-xs px-2 py-1 rounded"
            style={{ backgroundColor: "#111827", color: "#606070", border: "1px solid #2a3050" }}
          >
            最新{updates.length}件 / 全{allUpdates.length}件
          </span>
        )}
      </div>

      {sortedDates.length === 0 ? (
        <div className="text-center py-16" style={{ color: "#606070" }}>
          <p className="text-2xl mb-2">📭</p>
          <p>まだ更新履歴はありません</p>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {sortedDates.map((date) => (
            <div key={date}>
              {/* 日付ヘッダー */}
              <div className="flex items-center gap-3 mb-3">
                <span className="text-sm font-bold" style={{ color: "#d4a44a" }}>
                  {new Date(date + "T00:00:00").toLocaleDateString("ja-JP", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </span>
                <div className="flex-1 h-px" style={{ backgroundColor: "#2a3050" }} />
              </div>

              {/* その日の更新一覧 */}
              <div className="flex flex-col gap-2 ml-2">
                {grouped[date].map((entry, i) => {
                  const typeInfo = TYPE_LABELS[entry.type] || TYPE_LABELS.enemy_update;
                  return (
                    <div
                      key={i}
                      className="rounded-lg p-4"
                      style={{
                        backgroundColor: "#0d1117",
                        border: "1px solid #2a3050",
                      }}
                    >
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span
                          className="text-xs px-2 py-0.5 rounded"
                          style={{
                            backgroundColor: typeInfo.bg,
                            color: typeInfo.color,
                            border: `1px solid ${typeInfo.border}`,
                          }}
                        >
                          {typeInfo.label}
                        </span>
                        <span className="text-sm" style={{ color: "#c0c8d8" }}>
                          {entry.summary}
                        </span>
                        {entry.source && (
                          <span className="text-xs" style={{ color: "#505060" }}>
                            ({entry.source})
                          </span>
                        )}
                      </div>
                      {entry.details.length > 0 && (
                        <ul className="flex flex-col gap-1">
                          {entry.details.map((detail, j) => (
                            <li
                              key={j}
                              className="flex items-start gap-2 text-xs"
                              style={{ color: "#7a8090" }}
                            >
                              <span className="flex-shrink-0 mt-0.5" style={{ color: "#404060" }}>
                                ・
                              </span>
                              <span>{detail}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
