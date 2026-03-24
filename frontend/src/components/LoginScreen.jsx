import { useState } from "react";
import { GitMerge, Lock, ChevronRight } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

// Override via VITE_DET_PASSWORD env var in Vercel if you need to rotate the password.
const DET_PASSWORD = import.meta.env.VITE_DET_PASSWORD ?? "DataE123";

const ROLES = [
  {
    id: "market",
    label: "Market",
    desc: "Access to Tracker validation and LOV Explorer.",
    requiresPassword: false,
  },
  {
    id: "det",
    label: "Data Enablement Team",
    desc: "Full access to all features.",
    requiresPassword: true,
  },
];

export default function LoginScreen() {
  const { login } = useAuth();
  const [selected, setSelected] = useState(null);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSelect = (role) => {
    setSelected(role.id);
    setError("");
    setPassword("");
    if (!role.requiresPassword) {
      login(role.id);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password === DET_PASSWORD) {
      login("det");
    } else {
      setError("Incorrect password.");
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
                  <p className="text-xs text-slate-400 mt-0.5">{role.desc}</p>
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

        {/* Password field - only for DET */}
        {selected === "det" && (
          <form onSubmit={handleSubmit} className="mt-4 space-y-3">
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
              Sign in
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
