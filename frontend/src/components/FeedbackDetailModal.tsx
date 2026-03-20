import React, { type FormEvent, useState } from "react";
import toast from "react-hot-toast";
import { updateFeedback } from "../api";
import { useAuth } from "../hooks/useAuth";
import type { Feedback, Priority, Source, Status } from "../types";
import { Badge } from "./ui/Badge";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { Modal } from "./ui/Modal";
import { Select } from "./ui/Select";

const sourceOptions = [
  { value: "email", label: "Email" },
  { value: "call", label: "Call" },
  { value: "slack", label: "Slack" },
  { value: "chat", label: "Chat" },
  { value: "other", label: "Other" },
];

const priorityOptions = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

const statusOptions = [
  { value: "new", label: "New" },
  { value: "in_progress", label: "In Progress" },
  { value: "done", label: "Done" },
];

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

interface FeedbackDetailModalProps {
  feedback: Feedback | null;
  onClose: () => void;
  onUpdated: () => void;
}

export function FeedbackDetailModal({
  feedback,
  onClose,
  onUpdated,
}: FeedbackDetailModalProps) {
  const { token, user, isAdmin } = useAuth();
  const [mode, setMode] = useState<"view" | "edit">("view");

  // Edit form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [source, setSource] = useState<Source>("email");
  const [priority, setPriority] = useState<Priority>("medium");
  const [status, setStatus] = useState<Status>("new");
  const [submitting, setSubmitting] = useState(false);

  const canEdit =
    isAdmin || (user && feedback && feedback.created_by === user.id);

  function enterEdit() {
    if (!feedback) return;
    setTitle(feedback.title);
    setDescription(feedback.description);
    setSource(feedback.source);
    setPriority(feedback.priority);
    setStatus(feedback.status);
    setMode("edit");
  }

  function cancelEdit() {
    setMode("view");
  }

  function handleClose() {
    setMode("view");
    onClose();
  }

  async function handleSave(e?: FormEvent | React.MouseEvent) {
    e?.preventDefault();
    if (!token || !feedback) return;

    setSubmitting(true);
    try {
      await updateFeedback(token, feedback.id, {
        title,
        description,
        source,
        priority,
        status,
      });
      toast.success("Feedback updated");
      setMode("view");
      onUpdated();
      onClose();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to update feedback",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (!feedback) return null;

  const viewFooter = canEdit ? (
    <Button onClick={enterEdit}>Edit</Button>
  ) : null;

  const editFooter = (
    <>
      <Button variant="secondary" onClick={cancelEdit}>
        Cancel
      </Button>
      <Button
        onClick={handleSave}
        loading={submitting}
      >
        Save
      </Button>
    </>
  );

  return (
    <Modal
      open={!!feedback}
      onClose={handleClose}
      title={mode === "view" ? feedback.title : "Edit feedback"}
      footer={mode === "view" ? viewFooter : editFooter}
    >
      {mode === "view" ? (
        <div className="space-y-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-stone-500">Status</span>
              <Badge type="status" value={feedback.status} />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-stone-500">Priority</span>
              <Badge type="priority" value={feedback.priority} />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-stone-500">Source</span>
              <span className="text-xs text-stone-600 capitalize">
                {feedback.source}
              </span>
            </div>
          </div>
          <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">
            {feedback.description}
          </p>
          <div className="text-xs text-stone-400 font-mono space-y-0.5 pt-2 border-t border-stone-100">
            <p>Created: {formatTimestamp(feedback.created_at)}</p>
            <p>Updated: {formatTimestamp(feedback.updated_at)}</p>
          </div>
        </div>
      ) : (
        <form
          id="edit-feedback-form"
          onSubmit={handleSave}
          className="space-y-4"
        >
          <Input
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            maxLength={200}
          />
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="edit-description"
              className="text-sm font-medium text-stone-700"
            >
              Description
            </label>
            <textarea
              id="edit-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={3}
              className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 transition-colors focus:outline-none focus:border-signal-500 focus:ring-1 focus:ring-signal-500 resize-y"
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Select
              label="Source"
              options={sourceOptions}
              value={source}
              onChange={(e) => setSource(e.target.value as Source)}
            />
            <Select
              label="Priority"
              options={priorityOptions}
              value={priority}
              onChange={(e) => setPriority(e.target.value as Priority)}
            />
            <Select
              label="Status"
              options={statusOptions}
              value={status}
              onChange={(e) => setStatus(e.target.value as Status)}
            />
          </div>
        </form>
      )}
    </Modal>
  );
}
