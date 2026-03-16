import { cn } from "../../lib/utils";

const variants = {
  primary:   "bg-brand-500 text-white hover:bg-brand-600 active:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed",
  secondary: "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700",
  ghost:     "text-slate-600 hover:bg-slate-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200",
  danger:    "bg-danger-500 text-white hover:bg-danger-600",
  outline:   "border border-slate-300 dark:border-slate-600 bg-transparent hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300",
};

const sizes = {
  sm:   "h-7 px-2.5 text-xs gap-1.5",
  md:   "h-8 px-3 text-sm",
  lg:   "h-9 px-4 text-sm",
  icon: "h-8 w-8 p-0",
};

export function Button({ children, variant = "primary", size = "md", className, disabled, ...props }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded font-medium transition-colors duration-100 cursor-pointer",
        "focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-1 focus-visible:outline-none",
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
