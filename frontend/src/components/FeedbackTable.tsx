import type { Feedback } from "../types";
import { Badge } from "./ui/Badge";
import { useAuth } from "../hooks/useAuth";
import { useState, useRef, useEffect } from "react";

interface FeedbackTableProps {
  items: Feedback[];
  onRowClick: (item: Feedback) => void;
  onDelete?: (id: string) => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function ActionsMenu({
  onDelete,
}: {
  onDelete: () => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setOpen(!open);
        }}
        className="p-1 rounded-md text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors cursor-pointer"
        aria-label="Actions"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
        </svg>
      </button>
      {open && (
        <div className="absolute right-0 bottom-full mb-1 w-36 bg-white rounded-lg shadow-lg border border-stone-200 py-1 z-20">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setOpen(false);
              onDelete();
            }}
            className="w-full text-left px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}

export function FeedbackTable({
  items,
  onRowClick,
  onDelete,
}: FeedbackTableProps) {
  const { isAdmin } = useAuth();

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="text-xs font-medium text-stone-500 uppercase tracking-wider border-b border-stone-200">
            <th className="pb-2.5 pl-4">Title</th>
            <th className="pb-2.5 w-24">Status</th>
            <th className="pb-2.5 w-20">Priority</th>
            <th className="pb-2.5 w-17">Source</th>
            <th className="pb-2.5 w-19">Created</th>
            <th className="pb-2.5 w-9 pr-4"></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.id}
              onClick={() => onRowClick(item)}
              className="group border-b border-stone-100 last:border-0 cursor-pointer hover:bg-signal-50/40 transition-colors"
            >
              <td className="py-3 pl-4 pr-4">
                <div className="font-medium text-sm text-stone-900 group-hover:text-signal-700 transition-colors">
                  {item.title}
                </div>
                <div className="text-xs text-stone-400 truncate max-w-md mt-0.5">
                  {item.description}
                </div>
              </td>
              <td className="py-3">
                <Badge type="status" value={item.status} />
              </td>
              <td className="py-3">
                <Badge type="priority" value={item.priority} />
              </td>
              <td className="py-3 text-xs text-stone-500 capitalize">
                {item.source}
              </td>
              <td className="py-3 text-xs text-stone-400 font-mono">
                {formatDate(item.created_at)}
              </td>
              <td className="py-3 pr-4">
                {isAdmin && onDelete && (
                  <ActionsMenu onDelete={() => onDelete(item.id)} />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
