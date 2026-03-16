import { cn } from "../../lib/utils";

const variants = {
  default:   "bg-brand-50 text-brand-500 dark:bg-brand-700/20 dark:text-brand-300",
  success:   "bg-success-50 text-success-500 dark:bg-green-900/20 dark:text-green-400",
  danger:    "bg-danger-50 text-danger-500 dark:bg-red-900/20 dark:text-red-400",
  warning:   "bg-warning-50 text-warning-500 dark:bg-yellow-900/20 dark:text-yellow-400",
  secondary: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  outline:   "border border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300 bg-transparent",
};

export function Badge({ children, variant = "default", className, ...props }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
