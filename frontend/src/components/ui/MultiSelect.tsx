import { useState, useRef, useEffect } from "react";

interface MultiSelectProps {
  options: { value: string; label: string }[];
  value: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
  "aria-label"?: string;
}

export function MultiSelect({
  options,
  value,
  onChange,
  placeholder,
  "aria-label": ariaLabel,
}: MultiSelectProps) {
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

  function toggle(optionValue: string) {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  }

  const selectedLabels = options
    .filter((opt) => value.includes(opt.value))
    .map((opt) => opt.label);

  const displayText =
    selectedLabels.length === 0
      ? placeholder
      : selectedLabels.length <= 2
        ? selectedLabels.join(", ")
        : `${selectedLabels.length} selected`;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm transition-colors focus:outline-none focus:border-signal-500 focus:ring-1 focus:ring-signal-500 cursor-pointer text-left min-w-[140px] flex items-center justify-between gap-2 ${
          value.length > 0 ? "text-stone-900" : "text-stone-500"
        }`}
        aria-label={ariaLabel}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className="truncate">{displayText}</span>
        <svg
          className={`w-3.5 h-3.5 text-stone-400 shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {open && (
        <div
          className="absolute left-0 mt-1 w-full bg-white rounded-lg shadow-lg border border-stone-200 py-1 z-20"
          role="listbox"
          aria-multiselectable="true"
          aria-label={ariaLabel}
        >
          {options.map((opt) => (
            <label
              key={opt.value}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-stone-700 hover:bg-stone-50 cursor-pointer transition-colors"
            >
              <input
                type="checkbox"
                checked={value.includes(opt.value)}
                onChange={() => toggle(opt.value)}
                className="rounded border-stone-300 text-signal-600 focus:ring-signal-500 cursor-pointer"
              />
              {opt.label}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
