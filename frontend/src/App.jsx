import { BrowserRouter, NavLink, Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { LayoutDashboard, CheckSquare, List, GitMerge, BookOpen, Sun, Moon } from "lucide-react";
import { HistoryProvider } from "./context/HistoryContext.jsx";
import { ThemeProvider, useTheme } from "./components/ThemeProvider.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Validator from "./pages/Validator.jsx";
import LovExplorer from "./pages/LovExplorer.jsx";
import Migrations from "./pages/Migrations.jsx";
import RulesCatalog from "./pages/RulesCatalog.jsx";

const NAV = [
  { to: "/",             label: "Dashboard",    icon: LayoutDashboard },
  { to: "/validator",    label: "Validator",    icon: CheckSquare      },
  { to: "/rules",        label: "Rules",        icon: BookOpen         },
  { to: "/lov-explorer", label: "LOV Explorer", icon: List             },
  { to: "/migrations",   label: "Migrations",   icon: GitMerge         },
];

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="h-8 w-8 flex items-center justify-center rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 transition-colors"
    >
      {theme === "dark"
        ? <Sun className="h-4 w-4" />
        : <Moon className="h-4 w-4" />}
    </button>
  );
}

function NavItem({ to, label, Icon }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      aria-label={label}
      className={({ isActive }) =>
        "flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 transition-colors " +
        (isActive
          ? "border-brand-500 text-brand-500 dark:text-brand-400"
          : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200")
      }
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {label}
    </NavLink>
  );
}

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.main
        key={location.pathname}
        id="main-content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.12 }}
        className="flex-1 max-w-screen-xl mx-auto w-full px-6 py-6"
      >
        <Routes location={location}>
          <Route path="/"             element={<Dashboard />}   />
          <Route path="/validator"    element={<Validator />}   />
          <Route path="/lov-explorer" element={<LovExplorer />} />
          <Route path="/rules"        element={<RulesCatalog />} />
          <Route path="/migrations"   element={<Migrations />}  />
        </Routes>
      </motion.main>
    </AnimatePresence>
  );
}

function AppInner() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Nav */}
      <header className="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-screen-xl mx-auto px-6 flex items-center gap-6 h-12">
          {/* Wordmark */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="h-5 w-5 bg-brand-500 rounded flex items-center justify-center">
              <GitMerge className="h-3 w-3 text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 tracking-tight">
              Sysco <span className="text-brand-500">MRE</span>
            </span>
          </div>

          {/* Separator */}
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700" />

          {/* Nav links — bottom-border style */}
          <nav
            className="flex items-stretch h-12 gap-0 -mb-px"
            role="navigation"
            aria-label="Main navigation"
          >
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavItem key={to} to={to} label={label} Icon={Icon} />
            ))}
          </nav>

          {/* Spacer + theme toggle */}
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>
      </header>

      <AnimatedRoutes />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <HistoryProvider>
        <BrowserRouter>
          <AppInner />
        </BrowserRouter>
      </HistoryProvider>
    </ThemeProvider>
  );
}
