import {
  BrowserRouter,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  LayoutDashboard,
  CheckSquare,
  List,
  GitMerge,
  GitCompare,
  Scale,
  ClipboardCheck,
  ChevronDown,
  Sun,
  Moon,
  Keyboard,
  Info,
  LogOut,
  X,
} from "lucide-react";
import { HistoryProvider } from "./context/HistoryContext.jsx";
import { ThemeProvider, useTheme } from "./components/ThemeProvider.jsx";
import { AuthProvider, useAuth } from "./context/AuthContext.jsx";
import LoginScreen from "./components/LoginScreen.jsx";
import LovSearchModal from "./components/LovSearchModal.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Validator from "./pages/Validator.jsx";
import LovExplorer from "./pages/LovExplorer.jsx";
import Migrations from "./pages/Migrations.jsx";
import DiffViewer from "./pages/DiffViewer.jsx";
import TrackerValidator from "./pages/TrackerValidator.jsx";

const NAV_BASE = [
  {
    to: "/",
    label: "Dashboard",
    icon: LayoutDashboard,
    desc: "Overview of recent validation runs - stats, error trends, and quick access to last results.",
  },
  {
    to: "/tracker",
    label: "Tracker",
    icon: ClipboardCheck,
    desc: "Validate a P1 Data Cleansing tracker file shared with the business - checks mandatory fields, LOV values, and formats.",
  },
  {
    to: "/lov-explorer",
    label: "LOV Explorer",
    icon: List,
    desc: "Browse and search all List-of-Values from the reference workbook (brands, attribute groups, commodity codes, etc.).",
  },
];

const NAV_MIGRATIONS_MENU = {
  label: "Migrations",
  icon: GitMerge,
  items: [
    {
      to: "/migrations",
      label: "Rules",
      icon: Scale,
      desc: "Validation rules and template coverage by domain — which columns are checked and how.",
    },
    {
      to: "/validator",
      label: "Validator",
      icon: CheckSquare,
      desc: "Upload and validate migration Excel files for Products, Vendors, or Customers against all business rules.",
    },
    {
      to: "/diff",
      label: "Diff",
      icon: GitCompare,
      desc: "Compare two versions of a migration Excel file side-by-side and highlight row-level changes.",
    },
  ],
};

/** Flat list for Pages Guide modal (same pages as before, sensible order). */
const PAGES_GUIDE_ENTRIES = [
  NAV_BASE[0],
  ...NAV_MIGRATIONS_MENU.items,
  NAV_BASE[1],
  NAV_BASE[2],
];

const SHORTCUTS = [
  { keys: ["Ctrl", "K"], mac: ["⌘", "K"], desc: "LOV search (modal)" },
  { keys: ["/"], mac: ["/"], desc: "LOV search (modal)" },
  {
    keys: ["Alt", "1–6"],
    mac: ["⌥", "1–6"],
    desc: "Navigate to page 1–6",
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

// ─── Pages guide modal ───────────────────────────────────────────────────────

function PagesGuideModal({ onClose }) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-2xl w-full max-w-md mx-4 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Info className="h-4 w-4 text-slate-400" />
            Pages Guide
          </span>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <ul className="space-y-3">
          {PAGES_GUIDE_ENTRIES.map(({ to, label, icon: Icon, desc }) => (
            <li key={to} className="flex gap-3">
              <div className="mt-0.5 flex-shrink-0 h-6 w-6 rounded bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                <Icon className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                  {label}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

// ─── Global keyboard shortcuts ───────────────────────────────────────────────

const MARKET_ALLOWED = new Set(["/tracker", "/lov-explorer"]);

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

      // Ctrl+K / ⌘K - always intercept (open LOV search modal)
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

      // Alt+1–6 navigation
      if (e.altKey && !e.ctrlKey && !e.metaKey) {
        const routes = [
          "/",
          "/migrations",
          "/validator",
          "/tracker",
          "/lov-explorer",
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

const MENU_EASE = [0.22, 1, 0.36, 1];

const migrationsMenuPanel = {
  initial: { opacity: 0, y: -8, scale: 0.97 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.34,
      ease: MENU_EASE,
    },
  },
  exit: {
    opacity: 0,
    y: -6,
    scale: 0.97,
    transition: { duration: 0.24, ease: MENU_EASE },
  },
};

const migrationsMenuList = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.055,
      delayChildren: 0.08,
    },
  },
};

const migrationsMenuItem = {
  hidden: { opacity: 0, x: -8 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.28, ease: MENU_EASE },
  },
};

const MENU_OPEN_DELAY_MS = 280;
const MENU_CLOSE_DELAY_MS = 320;

function NavMigrationsDropdown({ items }) {
  const [open, setOpen] = useState(false);
  const closeTimerRef = useRef(null);
  const openTimerRef = useRef(null);
  const location = useLocation();
  const MenuIcon = NAV_MIGRATIONS_MENU.icon;

  const childActive = items.some(
    (item) =>
      item.to === "/"
        ? location.pathname === "/"
        : location.pathname === item.to ||
          location.pathname.startsWith(`${item.to}/`),
  );

  const clearCloseTimer = () => {
    if (closeTimerRef.current != null) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  };

  const clearOpenTimer = () => {
    if (openTimerRef.current != null) {
      window.clearTimeout(openTimerRef.current);
      openTimerRef.current = null;
    }
  };

  const scheduleClose = () => {
    clearCloseTimer();
    closeTimerRef.current = window.setTimeout(() => {
      setOpen(false);
      closeTimerRef.current = null;
    }, MENU_CLOSE_DELAY_MS);
  };

  const scheduleOpen = () => {
    clearOpenTimer();
    openTimerRef.current = window.setTimeout(() => {
      setOpen(true);
      openTimerRef.current = null;
    }, MENU_OPEN_DELAY_MS);
  };

  useEffect(() => {
    return () => {
      clearCloseTimer();
      clearOpenTimer();
    };
  }, []);

  useEffect(() => {
    setOpen(false);
    clearCloseTimer();
    clearOpenTimer();
  }, [location.pathname]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div
      className="relative flex h-16 items-stretch"
      onMouseEnter={() => {
        clearCloseTimer();
        scheduleOpen();
      }}
      onMouseLeave={() => {
        clearOpenTimer();
        scheduleClose();
      }}
    >
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={`${NAV_MIGRATIONS_MENU.label} menu`}
        onClick={() => {
          clearOpenTimer();
          clearCloseTimer();
          setOpen((v) => !v);
        }}
        className={
          "flex items-center gap-2 px-4 py-2 text-base font-medium border-b-2 transition-all duration-200 ease-out " +
          (open || childActive
            ? "border-brand-500 text-brand-500 dark:text-brand-400"
            : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200")
        }
      >
        <MenuIcon className="h-4 w-4 shrink-0" aria-hidden="true" />
        {NAV_MIGRATIONS_MENU.label}
        <ChevronDown
          className={
            "h-4 w-4 shrink-0 opacity-70 transition-transform duration-300 ease-out " +
            (open ? "rotate-180" : "")
          }
          aria-hidden="true"
        />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            key="migrations-menu"
            className="absolute left-0 top-full z-50 min-w-[14rem] pt-1"
            role="presentation"
            initial="initial"
            animate="animate"
            exit="exit"
            variants={migrationsMenuPanel}
          >
            <motion.div
              className="py-1 rounded-md border border-slate-200/90 bg-white/95 shadow-lg shadow-slate-200/40 backdrop-blur-sm dark:border-slate-600/80 dark:bg-slate-900/95 dark:shadow-black/30"
              role="menu"
              variants={migrationsMenuList}
              initial="hidden"
              animate="visible"
            >
              {items.map(({ to, label, icon: Icon }) => (
                <motion.div key={to} variants={migrationsMenuItem}>
                  <NavLink
                    to={to}
                    role="menuitem"
                    className={({ isActive }) =>
                      "group flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-all duration-200 ease-out motion-reduce:transform-none " +
                      (isActive
                        ? "bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-400"
                        : "text-slate-700 hover:bg-slate-50/90 hover:translate-x-0.5 dark:text-slate-200 dark:hover:bg-slate-800/80")
                    }
                    onClick={() => setOpen(false)}
                  >
                    <Icon
                      className="h-4 w-4 shrink-0 opacity-60 transition-all duration-200 ease-out group-hover:opacity-100"
                      aria-hidden="true"
                    />
                    {label}
                  </NavLink>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
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
            <Route path="/tracker" element={<TrackerValidator />} />
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
  const [showGuide, setShowGuide] = useState(false);
  const { role, name, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  useKeyboardShortcuts(setShowLov, setShowHelp);

  // Redirect Market users away from DET-only routes
  useEffect(() => {
    if (role === "market" && !MARKET_ALLOWED.has(location.pathname)) {
      navigate("/tracker", { replace: true });
    }
  }, [role, location.pathname, navigate]);

  if (!role) return <LoginScreen />;

  const marketNavItems = NAV_BASE.filter(({ to }) =>
    MARKET_ALLOWED.has(to),
  );

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      <header className="sticky top-0 z-40 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div className="px-8 w-full flex items-center gap-6 h-16">
          {/* Wordmark */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <img src="/sysco-logo.png" alt="Sysco" className="h-6 w-auto" />
            <div className="h-4 w-px bg-slate-200 dark:bg-slate-700" />
            <div className="h-7 w-7 bg-brand-500 rounded flex items-center justify-center">
              <GitMerge className="h-4 w-4 text-white" />
            </div>
            <span className="text-base font-semibold text-slate-800 dark:text-slate-100 tracking-tight">
              Data Governance Tool -{" "}
              <span className="text-brand-500">DGT!</span>
            </span>
          </div>

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700" />

          <nav
            className="flex items-stretch h-16 gap-0 -mb-px"
            role="navigation"
            aria-label="Main navigation"
          >
            {role === "market" ? (
              marketNavItems.map(({ to, label, icon: Icon }) => (
                <NavItem key={to} to={to} label={label} Icon={Icon} />
              ))
            ) : (
              <>
                <NavItem
                  to={NAV_BASE[0].to}
                  label={NAV_BASE[0].label}
                  Icon={NAV_BASE[0].icon}
                />
                <NavMigrationsDropdown items={NAV_MIGRATIONS_MENU.items} />
                {NAV_BASE.slice(1).map(({ to, label, icon: Icon }) => (
                  <NavItem key={to} to={to} label={label} Icon={Icon} />
                ))}
              </>
            )}
          </nav>

          {/* Right side: LOV search trigger + guide + shortcuts + theme */}
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
              onClick={() => setShowGuide((v) => !v)}
              aria-label="Pages Guide"
              title="Pages Guide"
              className="h-8 w-8 flex items-center justify-center rounded text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 transition-colors"
            >
              <Info className="h-4 w-4" />
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
            <button
              onClick={logout}
              aria-label="Log out"
              title={`Log out (${role === "det" ? `DET - ${name}` : "Market"})`}
              className="h-8 w-8 flex items-center justify-center rounded text-slate-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <AnimatedRoutes />

      {showLov && <LovSearchModal onClose={() => setShowLov(false)} />}
      {showHelp && <ShortcutsModal onClose={() => setShowHelp(false)} />}
      {showGuide && <PagesGuideModal onClose={() => setShowGuide(false)} />}
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <HistoryProvider>
          <BrowserRouter>
            <AppInner />
          </BrowserRouter>
        </HistoryProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
