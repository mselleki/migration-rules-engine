import { useEffect, useState, useRef, useCallback } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Search, X, Copy, CheckCheck } from "lucide-react";
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

// ─── Copy badge ─────────────────────────────────────────────────────────────

function KeyBadge({ value }) {
  const [copied, setCopied] = useState(false);
  const copy = useCallback(() => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }, [value]);

  return (
    <button
      onClick={copy}
      title="Copy"
      className="group inline-flex items-center gap-1 font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-colors"
    >
      {value}
      {copied ? (
        <CheckCheck className="h-3 w-3 text-green-500 flex-shrink-0" />
      ) : (
        <Copy className="h-3 w-3 text-slate-300 dark:text-slate-600 group-hover:text-brand-400 flex-shrink-0" />
      )}
    </button>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function LovExplorer() {
  const [previews, setPreviews] = useState([]); // [{attribute, count, examples}]
  const [selectedAttr, setSelectedAttr] = useState("");
  const [attrFilter, setAttrFilter] = useState(""); // sidebar search
  const [search, setSearch] = useState(""); // table search
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const debouncedSearch = useDebounce(search);

  // Load attribute previews once
  useEffect(() => {
    fetch(`${API}/lovs/preview`)
      .then((r) => r.json())
      .then(setPreviews)
      .catch(() => setError("Could not load LOV attributes."));
  }, []);

  // Load rows when attribute or search changes
  useEffect(() => {
    if (!selectedAttr && !debouncedSearch) {
      setRows([]);
      return;
    }
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (selectedAttr) params.set("attribute", selectedAttr);
    if (debouncedSearch) params.set("q", debouncedSearch);
    fetch(`${API}/lovs?${params}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setRows)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedAttr, debouncedSearch]);

  // Clear table search when switching attribute
  const selectAttr = useCallback((attr) => {
    setSelectedAttr((prev) => (prev === attr ? "" : attr));
    setSearch("");
  }, []);

  const filteredPreviews = attrFilter
    ? previews.filter((p) =>
        p.attribute.toLowerCase().includes(attrFilter.toLowerCase()),
      )
    : previews;

  // Virtual list
  const parentRef = useRef(null);
  const showAttrCol = !selectedAttr;
  const gridCols = showAttrCol
    ? "grid-cols-[180px_140px_1fr]"
    : "grid-cols-[160px_1fr]";
  const headers = showAttrCol
    ? ["Attribute", "Key", "Description"]
    : ["Key", "Description"];

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          LOV Explorer
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Browse and search all List-of-Values from the reference workbook
        </p>
      </div>

      <div
        className="flex gap-3"
        style={{ height: "calc(100vh - 200px)", minHeight: "480px" }}
      >
        {/* ── Sidebar: attribute list ── */}
        <div className="w-56 flex-shrink-0 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden flex flex-col bg-white dark:bg-slate-900">
          <div className="p-2 border-b border-slate-100 dark:border-slate-800">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Filter…"
                value={attrFilter}
                onChange={(e) => setAttrFilter(e.target.value)}
                className="w-full pl-7 pr-2 py-1 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded focus:outline-none focus:ring-1 focus:ring-brand-500 dark:text-slate-100"
              />
            </div>
          </div>

          <div className="overflow-y-auto flex-1">
            {previews.length === 0 ? (
              <div className="p-3 space-y-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-10" />
                ))}
              </div>
            ) : filteredPreviews.length === 0 ? (
              <p className="px-3 py-4 text-xs text-slate-400 text-center">
                No match
              </p>
            ) : (
              filteredPreviews.map(({ attribute, count, examples }) => (
                <button
                  key={attribute}
                  onClick={() => selectAttr(attribute)}
                  className={`w-full text-left px-3 py-2.5 border-b border-slate-50 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                    selectedAttr === attribute
                      ? "bg-brand-50 dark:bg-brand-900/20 border-l-2 border-l-brand-500"
                      : ""
                  }`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs font-medium text-slate-700 dark:text-slate-200 truncate">
                      {attribute}
                    </span>
                    <span className="text-[10px] text-slate-400 flex-shrink-0">
                      {count}
                    </span>
                  </div>
                  {examples.length > 0 && (
                    <p className="text-[10px] text-slate-400 mt-0.5 truncate">
                      {examples.join(" · ")}
                    </p>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* ── Right panel: LOV table ── */}
        <div className="flex-1 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden flex flex-col bg-white dark:bg-slate-900">
          {/* Header */}
          <div className="flex items-center gap-3 px-3 py-2 border-b border-slate-100 dark:border-slate-800">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
              <input
                type="text"
                placeholder={
                  selectedAttr
                    ? `Search in ${selectedAttr}…`
                    : "Search across all LOVs…"
                }
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") setSearch("");
                }}
                className="w-full pl-8 pr-7 py-1.5 text-sm border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
              {search && (
                <button
                  onClick={() => setSearch("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
            <Badge
              variant={loading ? "secondary" : "outline"}
              className="flex-shrink-0 tabular-nums ml-auto"
            >
              {loading
                ? "Loading…"
                : rows.length > 0
                  ? `${rows.length} rows`
                  : ""}
            </Badge>
          </div>

          {error && (
            <div className="px-4 py-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-b border-red-100 dark:border-red-800/40">
              {error}
            </div>
          )}

          {/* Column headers */}
          {(rows.length > 0 || loading) && (
            <div
              className={`grid ${gridCols} border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50`}
            >
              {headers.map((h) => (
                <div
                  key={h}
                  className="px-4 py-2 text-xs font-medium text-slate-500 uppercase tracking-wider"
                >
                  {h}
                </div>
              ))}
            </div>
          )}

          {/* Body */}
          {loading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-8" />
              ))}
            </div>
          ) : rows.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-sm text-slate-400 gap-2">
              {selectedAttr || debouncedSearch ? (
                "No results found."
              ) : (
                <>
                  <span>Select an attribute on the left</span>
                  <span className="text-xs">
                    or type to search across all LOVs
                  </span>
                </>
              )}
            </div>
          ) : (
            <div ref={parentRef} className="overflow-auto flex-1">
              <div
                style={{
                  height: `${rowVirtualizer.getTotalSize()}px`,
                  width: "100%",
                  position: "relative",
                }}
              >
                {rowVirtualizer.getVirtualItems().map((vRow) => {
                  const row = rows[vRow.index];
                  return (
                    <div
                      key={vRow.key}
                      data-index={vRow.index}
                      ref={rowVirtualizer.measureElement}
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        transform: `translateY(${vRow.start}px)`,
                      }}
                      className={`grid ${gridCols} border-b border-slate-50 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/30 ${vRow.index % 2 === 1 ? "bg-slate-50/40 dark:bg-slate-800/10" : "bg-white dark:bg-slate-900"}`}
                    >
                      {showAttrCol && (
                        <div className="px-4 py-2.5 text-xs text-slate-500 dark:text-slate-400 font-medium truncate">
                          {row.attribute}
                        </div>
                      )}
                      <div className="px-4 py-2.5">
                        <KeyBadge value={row.key} />
                      </div>
                      <div className="px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300">
                        {row.description}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
