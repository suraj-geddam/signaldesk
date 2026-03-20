import type { Insight } from "../types";

function confidenceBadge(confidence: number): { bg: string; text: string } {
  if (confidence >= 0.7)
    return { bg: "bg-confidence-high-bg", text: "text-confidence-high-text" };
  if (confidence >= 0.4)
    return { bg: "bg-confidence-mid-bg", text: "text-confidence-mid-text" };
  return { bg: "bg-confidence-low-bg", text: "text-confidence-low-text" };
}

export function InsightsCard({ insight }: { insight: Insight }) {
  const badge = confidenceBadge(insight.confidence);

  return (
    <div className="bg-white rounded-lg border border-stone-200 p-5 transition-shadow hover:shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-stone-900">
          {insight.theme}
        </h3>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium shrink-0 ${badge.bg} ${badge.text}`}
        >
          {Math.round(insight.confidence * 100)}%
        </span>
      </div>
      <p className="text-sm text-stone-600 mt-2 leading-relaxed">
        {insight.justification}
      </p>
    </div>
  );
}
