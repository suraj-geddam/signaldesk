import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { DailyTrend } from "../types";

interface DashboardTrendChartProps {
  data: DailyTrend[];
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function isToday(dateStr: string): boolean {
  const today = new Date().toISOString().split("T")[0];
  return dateStr === today;
}

export function DashboardTrendChart({ data }: DashboardTrendChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    label: formatDateLabel(d.date),
    today: isToday(d.date),
  }));

  return (
    <div className="bg-white rounded-lg border border-stone-100 p-4">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart
          data={chartData}
          margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
        >
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12, fill: "#78716c" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 12, fill: "#78716c" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              fontFamily: "Outfit, sans-serif",
              fontSize: 13,
              borderRadius: 8,
              border: "1px solid #e7e5e4",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
            cursor={{ fill: "#f5f5f4" }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={40}>
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.today ? "#93c5fd" : "#3b82f6"}
                opacity={entry.today ? 0.7 : 1}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
