import { useCallback, useRef, useState } from "react";
import toast from "react-hot-toast";
import { refreshInsights } from "../api";
import { useAuth } from "../hooks/useAuth";
import { useApi } from "../hooks/useApi";
import type { InsightsResponse } from "../types";
import { InsightsCard } from "../components/InsightsCard";
import { InsightsSkeleton } from "../components/Skeletons";
import { ErrorBanner } from "../components/ErrorBanner";
import { Button } from "../components/ui/Button";

const POLL_INTERVAL = 3000;
const POLL_TIMEOUT = 60000;

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function InsightsPage() {
  const { token, isAdmin } = useAuth();
  const { data, loading, error, refetch } =
    useApi<InsightsResponse>("/feedback/insights");
  const [refreshing, setRefreshing] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const apiBase =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setRefreshing(false);
  }, []);

  async function handleRefresh() {
    if (!token) return;
    setRefreshing(true);

    try {
      await refreshInsights(token);
      toast("Generating new insights...", { icon: "\u2728" });
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to trigger refresh",
      );
      setRefreshing(false);
      return;
    }

    const capturedGeneratedAt = data?.generated_at || null;
    const started = Date.now();

    pollRef.current = setInterval(async () => {
      if (Date.now() - started > POLL_TIMEOUT) {
        toast("Refresh is taking longer than expected", { icon: "\u23F3" });
        stopPolling();
        return;
      }

      try {
        const res = await fetch(`${apiBase}/feedback/insights`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return; // transient failure, keep polling
        const body = (await res.json()) as InsightsResponse;
        if (
          body.generated_at &&
          body.generated_at !== capturedGeneratedAt
        ) {
          toast.success("Insights updated");
          stopPolling();
          refetch();
        }
      } catch {
        // transient failure, keep polling
      }
    }, POLL_INTERVAL);
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-bold text-stone-900">Insights</h1>
        {isAdmin && (
          <Button
            onClick={handleRefresh}
            loading={refreshing}
            disabled={refreshing}
          >
            Refresh insights
          </Button>
        )}
      </div>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && !data && <InsightsSkeleton />}

      {data && (
        <>
          {/* Metadata */}
          {data.feedback_count != null && data.generated_at && (
            <p className="text-xs text-stone-400 mb-3 font-mono">
              Based on {data.feedback_count} feedback items. Generated{" "}
              {formatTimestamp(data.generated_at)}
              {data.model_used && ` using ${data.model_used}`}.
            </p>
          )}

          {/* Stale warning */}
          {data.stale && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 mb-4 text-sm text-amber-800">
              These insights may be outdated — new feedback has been added since
              they were generated.
            </div>
          )}

          {/* Empty state */}
          {data.insights.length === 0 && (
            <div className="text-center py-16">
              <p className="text-stone-500 text-sm">
                {data.message || "No insights generated yet."}
              </p>
              {isAdmin && (
                <p className="text-xs text-stone-400 mt-2">
                  Click "Refresh insights" to generate them.
                </p>
              )}
            </div>
          )}

          {/* Insight cards */}
          {data.insights.length > 0 && (
            <div className="space-y-3">
              {data.insights.map((insight, i) => (
                <InsightsCard key={i} insight={insight} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
