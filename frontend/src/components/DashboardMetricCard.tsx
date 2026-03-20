interface DashboardMetricCardProps {
  label: string;
  value: number;
  colorClass?: string;
}

export function DashboardMetricCard({
  label,
  value,
  colorClass = "text-stone-900",
}: DashboardMetricCardProps) {
  return (
    <div className="bg-white rounded-lg border border-stone-100 p-4 transition-shadow hover:shadow-sm">
      <div className="text-xs font-medium text-stone-500 uppercase tracking-wider">
        {label}
      </div>
      <div className={`text-2xl font-bold mt-1 ${colorClass}`}>{value}</div>
    </div>
  );
}
