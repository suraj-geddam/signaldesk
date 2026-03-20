import { useCallback, useEffect, useRef, type ReactNode } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (open) {
      previousFocus.current = document.activeElement as HTMLElement;
      document.addEventListener("keydown", handleKeyDown);
      // Focus first focusable element inside dialog
      requestAnimationFrame(() => {
        const el = dialogRef.current?.querySelector<HTMLElement>(
          "input, select, textarea, button:not([disabled])",
        );
        el?.focus();
      });
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      if (!open) previousFocus.current?.focus();
    };
  }, [open, handleKeyDown]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-stone-900/40 backdrop-blur-xs animate-backdrop-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <dialog
        ref={dialogRef}
        open
        className="relative z-10 w-full max-w-lg bg-white rounded-xl shadow-xl border border-stone-200/60 animate-modal-in p-0"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-stone-100">
          <h2 className="text-lg font-semibold text-stone-900">{title}</h2>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-stone-600 transition-colors p-1 rounded-md hover:bg-stone-100 cursor-pointer"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-2.5 px-6 py-4 border-t border-stone-100 bg-stone-50/50 rounded-b-xl">
            {footer}
          </div>
        )}
      </dialog>
    </div>
  );
}
