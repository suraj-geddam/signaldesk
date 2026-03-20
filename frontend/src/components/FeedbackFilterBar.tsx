import { useSearchParams } from "react-router";
import { useDebounce } from "../hooks/useDebounce";
import { Input } from "./ui/Input";
import { Select } from "./ui/Select";
import { useEffect, useState } from "react";

const statusOptions = [
  { value: "", label: "All statuses" },
  { value: "new", label: "New" },
  { value: "in_progress", label: "In Progress" },
  { value: "done", label: "Done" },
];

const priorityOptions = [
  { value: "", label: "All priorities" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const sourceOptions = [
  { value: "", label: "All sources" },
  { value: "email", label: "Email" },
  { value: "call", label: "Call" },
  { value: "slack", label: "Slack" },
  { value: "chat", label: "Chat" },
  { value: "other", label: "Other" },
];

const sortOptions = [
  { value: "created_at:desc", label: "Newest first" },
  { value: "created_at:asc", label: "Oldest first" },
  { value: "priority:desc", label: "Highest priority" },
  { value: "priority:asc", label: "Lowest priority" },
];

export function FeedbackFilterBar() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(
    searchParams.get("search") || "",
  );
  const debouncedSearch = useDebounce(searchInput);

  // Sync debounced search to URL
  useEffect(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (debouncedSearch) {
        next.set("search", debouncedSearch);
      } else {
        next.delete("search");
      }
      next.set("page", "1");
      return next;
    });
  }, [debouncedSearch, setSearchParams]);

  function setParam(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set(key, value);
      } else {
        next.delete(key);
      }
      next.set("page", "1");
      return next;
    });
  }

  const hasFilters =
    searchParams.get("status") ||
    searchParams.get("priority") ||
    searchParams.get("source") ||
    searchParams.get("search");

  function clearFilters() {
    const sort = searchParams.get("sort");
    const next = new URLSearchParams();
    if (sort) next.set("sort", sort);
    next.set("page", "1");
    setSearchParams(next);
    setSearchInput("");
  }

  return (
    <div className="flex flex-wrap items-end gap-2.5">
      <div className="flex-1 min-w-[200px]">
        <Input
          placeholder="Search feedback..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          aria-label="Search feedback"
        />
      </div>
      <Select
        options={statusOptions}
        value={searchParams.get("status") || ""}
        onChange={(e) => setParam("status", e.target.value)}
        aria-label="Filter by status"
      />
      <Select
        options={priorityOptions}
        value={searchParams.get("priority") || ""}
        onChange={(e) => setParam("priority", e.target.value)}
        aria-label="Filter by priority"
      />
      <Select
        options={sourceOptions}
        value={searchParams.get("source") || ""}
        onChange={(e) => setParam("source", e.target.value)}
        aria-label="Filter by source"
      />
      <Select
        options={sortOptions}
        value={
          searchParams.get("sort") || "created_at:desc"
        }
        onChange={(e) => setParam("sort", e.target.value)}
        aria-label="Sort order"
      />
      {hasFilters && (
        <button
          onClick={clearFilters}
          className="text-sm text-signal-600 hover:text-signal-800 transition-colors whitespace-nowrap pb-2 cursor-pointer"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
