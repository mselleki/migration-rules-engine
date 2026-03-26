import { useEffect, useRef, useState } from "react";
import {
  Building2,
  ChevronDown,
  GitMerge,
  Lock,
  User,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

// Override via VITE_DET_PASSWORD env var in Vercel to rotate without code change.
const DET_PASSWORD = import.meta.env.VITE_DET_PASSWORD ?? "DataE123";

const LEGAL_ENTITIES = [
  "Brakes",
  "Classic_Drinks",
  "Ekofisk",
  "Fresh_Direct",
  "Fruktservice",
  "KFF",
  "LAG",
  "Medina",
  "Menigo",
  "Ready_Chef",
  "Servicestyckarna",
  "Sysco_France",
  "Sysco_Northern_Ireland",
  "Sysco_ROI",
];

const ROLES = [
  {
    id: "market",
    label: "Market",
    desc: "Access to Tracker, Reconciliations, and LOV Explorer.",
    requiresPassword: false,
  },
  {
    id: "det",
    label: "Data Enablement Team",
    desc: "Full access to all features.",
    requiresPassword: true,
  },
];

function MarketSelect({ selected, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function onOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, [open]);

  function toggle(entity) {
    if (selected.includes(entity))
      onChange(selected.filter((x) => x !== entity));
    else onChange([...selected, entity]);
  }

  const label =
    selected.length === 0
      ? "Select your market(s)…"
      : selected.length === 1
        ? selected[0]
        : `${selected.length} markets selected`;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center pl-9 pr-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        <Building2 className="absolute left-3 h-4 w-4 text-slate-400 pointer-events-none" />
        <span
          className={`flex-1 text-left truncate ${selected.length === 0 ? "text-slate-400" : "text-slate-800 dark:text-slate-100"}`}
        >
          {label}
        </span>
        <ChevronDown
          className={`h-4 w-4 text-slate-400 flex-shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="absolute z-50 w-full mt-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-lg overflow-hidden">
          <div className="max-h-48 overflow-y-auto py-1">
            {LEGAL_ENTITIES.map((entity) => {
              const checked = selected.includes(entity);
              return (
                <label
                  key={entity}
                  className="flex cursor-pointer items-center gap-2.5 px-3 py-1.5 hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggle(entity)}
                    className="h-3.5 w-3.5 accent-brand-500"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {entity}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function LoginScreen() {
  const { login } = useAuth();
  const [selected, setSelected] = useState(null);
  // step: "role" | "market-info" | "name" (DET)
  const [step, setStep] = useState("role");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [markets, setMarkets] = useState([]);
  const [error, setError] = useState("");

  const handleSelect = (role) => {
    setSelected(role.id);
    setError("");
    setPassword("");
    if (!role.requiresPassword) {
      // Market: go to info step instead of logging in directly
      setStep("market-info");
    }
  };

  const handleMarketInfoSubmit = (e) => {
    e.preventDefault();
    if (name.trim() && markets.length > 0) {
      login("market", name.trim(), markets);
    }
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (password === DET_PASSWORD) {
      setStep("name");
      setError("");
    } else {
      setError("Incorrect password.");
    }
  };

  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (name.trim()) {
      login("det", name.trim());
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-950 px-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="h-9 w-9 bg-brand-500 rounded-lg flex items-center justify-center">
            <GitMerge className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-xs text-slate-400 leading-none">Sysco</p>
            <p className="text-base font-semibold text-slate-800 dark:text-slate-100">
              Data Governance Tool <span className="text-brand-500">DGT!</span>
            </p>
          </div>
        </div>

        {step === "role" && (
          <>
            <p className="text-sm text-center text-slate-500 dark:text-slate-400 mb-5">
              Select your profile to continue
            </p>

            <div className="space-y-3">
              {ROLES.map((role) => (
                <button
                  key={role.id}
                  onClick={() => handleSelect(role)}
                  className={`w-full text-left px-4 py-3.5 rounded-xl border transition-all ${
                    selected === role.id
                      ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
                      : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                        {role.label}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {role.desc}
                      </p>
                    </div>
                    <ChevronRight
                      className={`h-4 w-4 flex-shrink-0 transition-colors ${
                        selected === role.id
                          ? "text-brand-500"
                          : "text-slate-300 dark:text-slate-600"
                      }`}
                    />
                  </div>
                </button>
              ))}
            </div>

            {/* Password field - DET only */}
            {selected === "det" && (
              <form onSubmit={handlePasswordSubmit} className="mt-4 space-y-3">
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="password"
                    placeholder="Password"
                    autoFocus
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setError("");
                    }}
                    className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                {error && <p className="text-xs text-red-500">{error}</p>}
                <button
                  type="submit"
                  className="w-full py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-sm font-medium transition-colors"
                >
                  Continue
                </button>
              </form>
            )}
          </>
        )}

        {step === "market-info" && (
          <form onSubmit={handleMarketInfoSubmit} className="space-y-4">
            <div className="text-center mb-2">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                Welcome, Market user
              </p>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Enter your name and select your market(s).
                <br />
                Stored locally - never asked again on this browser.
              </p>
            </div>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="First and last name"
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <MarketSelect selected={markets} onChange={setMarkets} />
            <button
              type="submit"
              disabled={!name.trim() || markets.length === 0}
              className="w-full py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              Enter
            </button>
          </form>
        )}

        {step === "name" && (
          <form onSubmit={handleNameSubmit} className="space-y-4">
            <div className="text-center mb-2">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                What&apos;s your first name?
              </p>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Used only to track LOV edits and migration runs.
                <br />
                Stored locally - never asked again on this browser.
              </p>
            </div>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="First name"
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={!name.trim()}
              className="w-full py-2.5 rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
            >
              Enter
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
