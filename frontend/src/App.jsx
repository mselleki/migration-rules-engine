import {
  BrowserRouter,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  CheckSquare,
  List,
  GitMerge,
  GitCompare,
  Sun,
  Moon,
  Keyboard,
  X,
} from "lucide-react";
import { HistoryProvider } from "./context/HistoryContext.jsx";
import { ThemeProvider, useTheme } from "./components/ThemeProvider.jsx";
import LovSearchModal from "./components/LovSearchModal.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Validator from "./pages/Validator.jsx";
import LovExplorer from "./pages/LovExplorer.jsx";
import Migrations from "./pages/Migrations.jsx";
import DiffViewer from "./pages/DiffViewer.jsx";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/validator", label: "Validator", icon: CheckSquare },
  { to: "/lov-explorer", label: "LOV Explorer", icon: List },
  { to: "/migrations", label: "Migrations", icon: GitMerge },
  { to: "/diff", label: "Diff", icon: GitCompare },
];

const SHORTCUTS = [
  { keys: ["Ctrl", "K"], mac: ["⌘", "K"], desc: "LOV search (modal)" },
  { keys: ["/"], mac: ["/"], desc: "LOV search (modal)" },
  {
    keys: ["Alt", "1–5"],
    mac: ["⌥", "1–5"],
    desc: "Navigate to page 1–5",
  },
  { keys: ["T"], mac: ["T"], desc: "Toggle dark / light" },
  { keys: ["?"], mac: ["?"], desc: "Show this panel" },
  { keys: ["Esc"], mac: ["Esc"], desc: "Close modal" },
];

// ─── Shortcuts help modal ────────────────────────────────────────────────────

function ShortcutsModal({ onClose }) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const isMac = navigator.userAgent.toUpperCase().includes("MAC");

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-2xl w-full max-w-sm mx-4 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Keyboard className="h-4 w-4 text-slate-400" />
            Keyboard Shortcuts
          </span>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <table className="w-full text-sm">
          <tbody>
            {SHORTCUTS.map((s, i) => (
              <tr
                key={i}
                className="border-t border-slate-100 dark:border-slate-800 first:border-0"
              >
                <td className="py-2 pr-4 text-slate-500 dark:text-slate-400">
                  {s.desc}
                </td>
                <td className="py-2 text-right">
                  <span className="inline-flex items-center gap-1">
                    {(isMac ? s.mac : s.keys).map((k, j) => (
                      <kbd
                        key={j}
                        className="px-1.5 py-0.5 text-[11px] font-mono rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"
                      >
                        {k}
                      </kbd>
                    ))}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Global keyboard shortcuts ───────────────────────────────────────────────

function useKeyboardShortcuts(setShowLov, setShowHelp) {
  const navigate = useNavigate();
  const { toggle: toggleTheme } = useTheme();

  useEffect(() => {
    const onKeyDown = (e) => {
      const tag = document.activeElement?.tagName;
      const isTyping =
        tag === "INPUT" ||
        tag === "TEXTAREA" ||
        tag === "SELECT" ||
        document.activeElement?.isContentEditable;

      // Ctrl+K / ⌘K — always intercept (open LOV search modal)
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setShowLov((v) => !v);
        return;
      }

      if (isTyping) return;

      if (e.key === "/") {
        e.preventDefault();
        setShowLov((v) => !v);
        return;
      }
      if (e.key === "t" || e.key === "T") {
        toggleTheme();
        return;
      }
      if (e.key === "?") {
        setShowHelp((v) => !v);
        return;
      }

      // Alt+1–5 navigation
      if (e.altKey && !e.ctrlKey && !e.metaKey) {
        const routes = [
          "/",
          "/validator",
          "/lov-explorer",
          "/migrations",
          "/diff",
        ];
        const idx = parseInt(e.key, 10) - 1;
        if (idx >= 0 && idx < routes.length) {
          e.preventDefault();
          navigate(routes[idx]);
        }
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [navigate, toggleTheme, setShowLov, setShowHelp]);
}

// ─── Nav / Theme ─────────────────────────────────────────────────────────────

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="h-8 w-8 flex items-center justify-center rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 transition-colors"
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
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
        "flex items-center gap-2 px-4 py-2 text-base font-medium border-b-2 transition-colors " +
        (isActive
          ? "border-brand-500 text-brand-500 dark:text-brand-400"
          : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200")
      }
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
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
        className="flex-1 w-full"
      >
        <div className="px-8 py-6">
          <Routes location={location}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/validator" element={<Validator />} />
            <Route path="/lov-explorer" element={<LovExplorer />} />
            <Route path="/migrations" element={<Migrations />} />
            <Route path="/diff" element={<DiffViewer />} />
          </Routes>
        </div>
      </motion.main>
    </AnimatePresence>
  );
}

// ─── App ─────────────────────────────────────────────────────────────────────

function AppInner() {
  const [showLov, setShowLov] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  useKeyboardShortcuts(setShowLov, setShowHelp);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <header className="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div className="px-8 w-full flex items-center gap-6 h-16">
          {/* Wordmark */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="h-7 w-7 bg-brand-500 rounded flex items-center justify-center">
              <GitMerge className="h-4 w-4 text-white" />
            </div>
            <span className="text-base font-semibold text-slate-800 dark:text-slate-100 tracking-tight">
              Sysco <span className="text-brand-500">MRE</span>
            </span>
          </div>

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700" />

          <nav
            className="flex items-stretch h-16 gap-0 -mb-px"
            role="navigation"
            aria-label="Main navigation"
          >
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavItem key={to} to={to} label={label} Icon={Icon} />
            ))}
          </nav>

          {/* Right side: LOV search trigger + shortcuts + theme */}
          <div className="ml-auto flex items-center gap-1">
            <button
              onClick={() => setShowLov(true)}
              aria-label="LOV Search"
              className="hidden sm:flex items-center gap-2 h-8 px-3 rounded text-xs text-slate-400 border border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            >
              <List className="h-3.5 w-3.5" />
              LOV Search
              <kbd className="px-1 py-px font-mono rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                ⌘K
              </kbd>
            </button>
            <button
              onClick={() => setShowHelp((v) => !v)}
              aria-label="Keyboard Shortcuts"
              title="Keyboard Shortcuts (?)"
              className="h-8 w-8 flex items-center justify-center rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 transition-colors"
            >
              <Keyboard className="h-4 w-4" />
            </button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <AnimatedRoutes />

      {showLov && <LovSearchModal onClose={() => setShowLov(false)} />}
      {showHelp && <ShortcutsModal onClose={() => setShowHelp(false)} />}
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
