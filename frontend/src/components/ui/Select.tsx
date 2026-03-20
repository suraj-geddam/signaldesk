import type { SelectHTMLAttributes } from "react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export function Select({
  label,
  id,
  options,
  className = "",
  ...props
}: SelectProps) {
  const selectId = id || label?.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={selectId}
          className="text-sm font-medium text-stone-700"
        >
          {label}
        </label>
      )}
      <select
        id={selectId}
        className={`rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900 transition-colors focus:outline-none focus:border-signal-500 focus:ring-1 focus:ring-signal-500 disabled:opacity-50 cursor-pointer ${className}`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
