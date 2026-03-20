import { useApi } from "../hooks/useApi";
import type { DashboardResponse } from "../types";
import { DashboardMetricCard } from "../components/DashboardMetricCard";
import { DashboardTrendChart } from "../components/DashboardTrendChart";
import { DashboardSkeleton } from "../components/Skeletons";
import { ErrorBanner } from "../components/ErrorBanner";

export function DashboardPage() {
  const { data, loading, error, refetch } = useApi<DashboardResponse>(
    "/dashboard",
  );

  return (
    <div>
      <h1 className="text-xl font-bold text-stone-900 mb-5">Dashboard</h1>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && !data && <DashboardSkeleton />}

      {data && (
        <div className="space-y-6">
          {/* Status counts */}
          <div>
            <h2 className="text-xs font-medium text-stone-500 uppercase tracking-wider mb-3">
              By status
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <DashboardMetricCard
                label="New"
                value={data.status_counts.new ?? 0}
              />
              <DashboardMetricCard
                label="In Progress"
                value={data.status_counts.in_progress ?? 0}
              />
              <DashboardMetricCard
                label="Done"
                value={data.status_counts.done ?? 0}
              />
            </div>
          </div>

          {/* Priority counts */}
          <div>
            <h2 className="text-xs font-medium text-stone-500 uppercase tracking-wider mb-3">
              By priority
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <DashboardMetricCard
                label="High"
                value={data.priority_counts.high ?? 0}
                colorClass="text-priority-high-text"
              />
              <DashboardMetricCard
                label="Medium"
                value={data.priority_counts.medium ?? 0}
                colorClass="text-priority-medium-text"
              />
              <DashboardMetricCard
                label="Low"
                value={data.priority_counts.low ?? 0}
                colorClass="text-priority-low-text"
              />
            </div>
          </div>

          {/* Trend chart */}
          <div>
            <h2 className="text-xs font-medium text-stone-500 uppercase tracking-wider mb-3">
              New feedback per day
            </h2>
            <DashboardTrendChart data={data.daily_trend} />
          </div>
        </div>
      )}
    </div>
  );
}
