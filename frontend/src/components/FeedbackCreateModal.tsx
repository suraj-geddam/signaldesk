import { type FormEvent, useState } from "react";
import toast from "react-hot-toast";
import { createFeedback } from "../api";
import { useAuth } from "../hooks/useAuth";
import type { Source, Priority } from "../types";
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

interface FeedbackCreateModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function FeedbackCreateModal({
  open,
  onClose,
  onCreated,
}: FeedbackCreateModalProps) {
  const { token } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [source, setSource] = useState<Source>("email");
  const [priority, setPriority] = useState<Priority>("medium");
  const [submitting, setSubmitting] = useState(false);

  function reset() {
    setTitle("");
    setDescription("");
    setSource("email");
    setPriority("medium");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;

    setSubmitting(true);
    try {
      const idempotencyKey = crypto.randomUUID();
      await createFeedback(
        token,
        { title, description, source, priority },
        idempotencyKey,
      );
      toast.success("Feedback created");
      reset();
      onCreated();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create feedback");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="New feedback"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            form="create-feedback-form"
            loading={submitting}
          >
            Create
          </Button>
        </>
      }
    >
      <form id="create-feedback-form" onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          placeholder="Brief summary of the feedback"
        />
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="description"
            className="text-sm font-medium text-stone-700"
          >
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            rows={3}
            placeholder="Detailed feedback from the customer"
            className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900 placeholder:text-stone-400 transition-colors focus:outline-none focus:border-signal-500 focus:ring-1 focus:ring-signal-500 resize-y"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
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
        </div>
      </form>
    </Modal>
  );
}
