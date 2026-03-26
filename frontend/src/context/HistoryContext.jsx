/**
 * Shared validation run history - persisted in localStorage.
 * Each run stores summary data (not the full errors list, which can be huge).
 */
import { createContext, useCallback, useContext, useState } from "react";

const KEY = "mre_validation_history";
const MAX_RUNS = 200;

const HistoryContext = createContext(null);

export function HistoryProvider({ children }) {
  const [runs, setRuns] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "[]");
    } catch {
      return [];
    }
  });

  /** Save a completed validation run (summary only). */
  const addRun = useCallback((run) => {
    const entry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      domain: run.domain,
      legal_entity: run.legal_entity,
      total_rows: run.total_rows,
      global_row_count: run.global_row_count,
      local_row_count: run.local_row_count,
      total_errors: run.total_errors,
      errors_by_rule: run.errors_by_rule,
      warnings_count: run.warnings?.length ?? 0,
    };
    setRuns((prev) => {
      const next = [entry, ...prev].slice(0, MAX_RUNS);
      try { localStorage.setItem(KEY, JSON.stringify(next)); } catch { /* quota */ }
      return next;
    });
  }, []);

  const clearHistory = useCallback(() => {
    localStorage.removeItem(KEY);
    setRuns([]);
  }, []);

  return (
    <HistoryContext.Provider value={{ runs, addRun, clearHistory }}>
      {children}
    </HistoryContext.Provider>
  );
}

export const useHistory = () => useContext(HistoryContext);
