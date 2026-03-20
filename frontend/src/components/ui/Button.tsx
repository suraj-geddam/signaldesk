import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md";
  loading?: boolean;
  children: ReactNode;
}

const base =
  "inline-flex items-center justify-center gap-1.5 font-medium rounded-lg transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-signal-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";

const variants: Record<string, string> = {
  primary: "bg-signal-600 text-white hover:bg-signal-700 active:bg-signal-800",
  secondary:
    "bg-white text-stone-700 border border-stone-200 hover:bg-stone-50 active:bg-stone-100",
  danger: "bg-red-600 text-white hover:bg-red-700 active:bg-red-800",
  ghost: "text-stone-600 hover:bg-stone-100 active:bg-stone-200",
};

const sizes: Record<string, string> = {
  sm: "text-xs px-2.5 py-1.5",
  md: "text-sm px-3.5 py-2",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin -ml-0.5 h-3.5 w-3.5"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
