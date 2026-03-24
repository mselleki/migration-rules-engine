import { useEffect, useState, useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Search, X } from "lucide-react";
import { Card, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Skeleton } from "../components/ui/skeleton.jsx";

import API from "../api.js";

function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

export default function LovExplorer() {
  const [attributes, setAttributes] = useState([]);
  const [selectedAttr, setSelectedAttr] = useState("");
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const debouncedSearch = useDebounce(search);

  useEffect(() => {
    fetch(`${API}/lovs/attributes`)
      .then(r => r.json())
      .then(setAttributes)
      .catch(() => setError("Could not load LOV attributes."));
  }, []);

  useEffect(() => {
    if (!selectedAttr && !debouncedSearch) { setRows([]); return; }
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (selectedAttr) params.set("attribute", selectedAttr);
    if (debouncedSearch) params.set("q", debouncedSearch);
    fetch(`${API}/lovs?${params}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => setRows(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedAttr, debouncedSearch]);

  const searchRef = useRef(null);
  const parentRef = useRef(null);
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">LOV Explorer</h1>
        <p className="text-xs text-slate-400 mt-0.5">Browse and search all List-of-Values from the reference workbook</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3 flex-wrap flex-1">
            <select
              value={selectedAttr}
              onChange={e => setSelectedAttr(e.target.value)}
              className="text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 focus:outline-none min-w-[180px]"
              aria-label="Filter by attribute"
            >
              <option value="">Select an attribute…</option>
              {attributes.map(a => <option key={a} value={a}>{a}</option>)}
            </select>

            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" aria-hidden />
              <input
                ref={searchRef}
                type="text"
                placeholder="Search key or description…"
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={e => { if (e.key === "Escape") { setSearch(""); e.currentTarget.blur(); } }}
                aria-label="Search LOV values"
                className="w-full pl-8 pr-7 py-1.5 text-sm border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                  aria-label="Clear search"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>

          <Badge variant={loading ? "secondary" : "outline"} className="flex-shrink-0 tabular-nums">
            {loading ? "Loading…" : `${rows.length} rows`}
          </Badge>
        </CardHeader>

        {error && (
          <div className="px-4 py-2.5 text-sm text-danger-600 dark:text-red-400 bg-danger-50 dark:bg-red-900/20 border-b border-danger-100 dark:border-red-800/40">
            {error}
          </div>
        )}

        {/* Column headers */}
        <div className="grid grid-cols-[200px_140px_1fr] border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
          {["Attribute", "Key", "Description"].map(h => (
            <div key={h} className="px-4 py-2 text-xs font-medium text-slate-500 uppercase tracking-wider">{h}</div>
          ))}
        </div>

        {loading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8" />)}
          </div>
        ) : rows.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-400">
            {selectedAttr || debouncedSearch ? "No LOV rows found." : "Select an attribute to browse its values."}
          </div>
        ) : (
          <div ref={parentRef} className="overflow-auto" style={{ height: "min(60vh, 560px)" }}>
            <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, width: "100%", position: "relative" }}>
              {rowVirtualizer.getVirtualItems().map(vRow => {
                const row = rows[vRow.index];
                return (
                  <div
                    key={vRow.key}
                    data-index={vRow.index}
                    ref={rowVirtualizer.measureElement}
                    style={{ position: "absolute", top: 0, left: 0, width: "100%", transform: `translateY(${vRow.start}px)` }}
                    className={`grid grid-cols-[200px_140px_1fr] border-b border-slate-50 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/30 ${vRow.index % 2 === 1 ? "bg-slate-50/40 dark:bg-slate-800/10" : "bg-white dark:bg-slate-900"}`}
                  >
                    <div className="px-4 py-2.5 text-xs text-slate-600 dark:text-slate-400 font-medium truncate">{row.attribute}</div>
                    <div className="px-4 py-2.5">
                      <Badge variant="secondary" className="font-mono text-[11px]">{row.key}</Badge>
                    </div>
                    <div className="px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300">{row.description}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
