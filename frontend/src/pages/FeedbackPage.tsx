import { useState } from "react";
import { useSearchParams } from "react-router";
import toast from "react-hot-toast";
import { deleteFeedback } from "../api";
import { useAuth } from "../hooks/useAuth";
import { useApi } from "../hooks/useApi";
import type { Feedback, FeedbackListResponse } from "../types";
import { FeedbackFilterBar } from "../components/FeedbackFilterBar";
import { FeedbackTable } from "../components/FeedbackTable";
import { FeedbackCreateModal } from "../components/FeedbackCreateModal";
import { FeedbackDetailModal } from "../components/FeedbackDetailModal";
import { FeedbackTableSkeleton } from "../components/Skeletons";
import { ErrorBanner } from "../components/ErrorBanner";
import { Button } from "../components/ui/Button";

function buildApiUrl(params: URLSearchParams): string {
  const query = new URLSearchParams();
  const page = params.get("page") || "1";
  query.set("page", page);
  query.set("per_page", "20");

  if (params.get("status")) query.set("status", params.get("status")!);
  if (params.get("priority")) query.set("priority", params.get("priority")!);
  if (params.get("source")) query.set("source", params.get("source")!);
  if (params.get("search")) query.set("search", params.get("search")!);

  const sort = params.get("sort") || "created_at:desc";
  const [sortBy, sortOrder] = sort.split(":");
  query.set("sort_by", sortBy);
  query.set("sort_order", sortOrder);

  return `/feedback?${query.toString()}`;
}

export function FeedbackPage() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const apiUrl = buildApiUrl(searchParams);
  const { data, loading, error, refetch } = useApi<FeedbackListResponse>(
    apiUrl,
    [apiUrl],
  );

  const page = parseInt(searchParams.get("page") || "1", 10);
  const totalPages = data ? Math.ceil(data.total / data.per_page) : 0;
  const showFrom = data && data.total > 0 ? (page - 1) * data.per_page + 1 : 0;
  const showTo = data ? Math.min(page * data.per_page, data.total) : 0;

  function setPage(p: number) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("page", String(p));
      return next;
    });
  }

  async function handleDelete(id: string) {
    if (!token) return;
    if (deleteConfirm !== id) {
      setDeleteConfirm(id);
      return;
    }
    try {
      await deleteFeedback(token, id);
      toast.success("Feedback deleted");
      setDeleteConfirm(null);
      refetch();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to delete feedback",
      );
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-bold text-stone-900">Feedback</h1>
        <Button onClick={() => setCreateOpen(true)}>+ New feedback</Button>
      </div>

      {/* Filter bar */}
      <FeedbackFilterBar />

      {/* Content */}
      {error && <div className="mt-4"><ErrorBanner message={error} onRetry={refetch} /></div>}

      {loading && !data && <FeedbackTableSkeleton />}

      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          {searchParams.get("search") ||
          searchParams.get("status") ||
          searchParams.get("priority") ||
          searchParams.get("source") ? (
            <>
              <p className="text-stone-500 text-sm">
                No feedback matches your filters.
              </p>
              <button
                onClick={() => {
                  setSearchParams(new URLSearchParams());
                }}
                className="text-sm text-signal-600 hover:text-signal-800 mt-2 cursor-pointer"
              >
                Clear filters
              </button>
            </>
          ) : (
            <>
              <p className="text-stone-500 text-sm mb-3">No feedback yet.</p>
              <Button onClick={() => setCreateOpen(true)}>
                Create your first item
              </Button>
            </>
          )}
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <FeedbackTable
            items={data.items}
            onRowClick={setSelectedFeedback}
            onDelete={handleDelete}
          />

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4 text-sm text-stone-500">
            <span>
              Showing {showFrom}–{showTo} of {data.total}
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                Prev
              </Button>
              {Array.from({ length: totalPages }, (_, i) => i + 1)
                .filter(
                  (p) =>
                    p === 1 ||
                    p === totalPages ||
                    Math.abs(p - page) <= 1,
                )
                .reduce<(number | "...")[]>((acc, p, i, arr) => {
                  if (i > 0 && p - (arr[i - 1] ?? 0) > 1) acc.push("...");
                  acc.push(p);
                  return acc;
                }, [])
                .map((p, i) =>
                  p === "..." ? (
                    <span key={`ellipsis-${i}`} className="px-1">
                      ...
                    </span>
                  ) : (
                    <Button
                      key={p}
                      variant={p === page ? "primary" : "ghost"}
                      size="sm"
                      onClick={() => setPage(p as number)}
                    >
                      {p}
                    </Button>
                  ),
                )}
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}

      {/* Delete confirmation */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-stone-900/40 backdrop-blur-xs animate-backdrop-in"
            onClick={() => setDeleteConfirm(null)}
          />
          <div className="relative z-10 bg-white rounded-xl shadow-xl border border-stone-200/60 p-6 max-w-sm w-full animate-modal-in">
            <h3 className="font-semibold text-stone-900 mb-2">
              Delete this feedback?
            </h3>
            <p className="text-sm text-stone-500 mb-5">
              This cannot be undone.
            </p>
            <div className="flex justify-end gap-2.5">
              <Button
                variant="secondary"
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={() => handleDelete(deleteConfirm)}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      <FeedbackCreateModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={refetch}
      />
      <FeedbackDetailModal
        feedback={selectedFeedback}
        onClose={() => setSelectedFeedback(null)}
        onUpdated={refetch}
      />
    </div>
  );
}
