import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "../../lib/utils";

const Tabs = TabsPrimitive.Root;

const TabsList = ({ className, ...props }) => (
  <TabsPrimitive.List
    className={cn(
      "inline-flex items-center border-b border-slate-200 dark:border-slate-700 w-full gap-0",
      className
    )}
    {...props}
  />
);

const TabsTrigger = ({ className, ...props }) => (
  <TabsPrimitive.Trigger
    className={cn(
      "inline-flex items-center justify-center gap-1.5 px-4 py-2.5 text-sm font-medium transition-colors",
      "border-b-2 border-transparent -mb-px",
      "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200",
      "data-[state=active]:border-brand-500 data-[state=active]:text-brand-500 dark:data-[state=active]:text-brand-400",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500",
      "disabled:pointer-events-none disabled:opacity-50",
      className
    )}
    {...props}
  />
);

const TabsContent = ({ className, ...props }) => (
  <TabsPrimitive.Content
    className={cn("mt-4 focus-visible:outline-none", className)}
    {...props}
  />
);

export { Tabs, TabsContent, TabsList, TabsTrigger };
