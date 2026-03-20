import type { Status, Priority } from "../../types";

const statusStyles: Record<Status, string> = {
  new: "bg-status-new-bg text-status-new-text",
  in_progress: "bg-status-progress-bg text-status-progress-text",
  done: "bg-status-done-bg text-status-done-text",
};

const priorityStyles: Record<Priority, string> = {
  high: "bg-priority-high-bg text-priority-high-text",
  medium: "bg-priority-medium-bg text-priority-medium-text",
  low: "bg-priority-low-bg text-priority-low-text",
};

const statusLabels: Record<Status, string> = {
  new: "New",
  in_progress: "In Progress",
  done: "Done",
};

const priorityLabels: Record<Priority, string> = {
  high: "High",
  medium: "Medium",
  low: "Low",
};

interface BadgeProps {
  type: "status" | "priority" | "role";
  value: string;
}

export function Badge({ type, value }: BadgeProps) {
  let className = "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium tracking-wide";

  if (type === "status") {
    className += ` ${statusStyles[value as Status] || "bg-stone-100 text-stone-600"}`;
    return <span className={className}>{statusLabels[value as Status] || value}</span>;
  }

  if (type === "priority") {
    className += ` ${priorityStyles[value as Priority] || "bg-stone-100 text-stone-600"}`;
    return <span className={className}>{priorityLabels[value as Priority] || value}</span>;
  }

  // Role badge
  className += " bg-signal-50 text-signal-700";
  return <span className={className}>{value}</span>;
}
