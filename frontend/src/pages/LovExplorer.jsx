import { useEffect, useState, useRef, useCallback } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Search, X, ChevronDown, Check, Copy, CheckCheck } from "lucide-react";
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

// ─── Searchable attribute combobox ──────────────────────────────────────────

function AttributeCombobox({ attributes, value, onChange }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef(null);
  const containerRef = useRef(null);

  const filtered = query
    ? attributes.filter((a) => a.toLowerCase().includes(query.toLowerCase()))
    : attributes;

  const select = useCallback(
    (attr) => {
      onChange(attr);
      setQuery("");
      setOpen(false);
    },
    [onChange],
  );

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const displayLabel = value || "Select an attribute…";

  return (
    <div ref={containerRef} className="relative min-w-[220px]">
      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          setTimeout(() => inputRef.current?.focus(), 0);
        }}
        className="flex items-center justify-between gap-2 w-full text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 focus:outline-none"
      >
        <span
          className={
            value ? "text-slate-900 dark:text-slate-100" : "text-slate-400"
          }
        >
          {displayLabel}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {value && (
            <span
              role="button"
              tabIndex={0}
              onClick={(e) => {
                e.stopPropagation();
                select("");
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.stopPropagation();
                  select("");
                }
              }}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              aria-label="Clear selection"
            >
              <X className="h-3.5 w-3.5" />
            </span>
          )}
          <ChevronDown
            className={`h-3.5 w-3.5 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
          />
        </div>
      </button>

      {open && (
        <div className="absolute z-20 top-full mt-1 w-full min-w-[260px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg">
          <div className="p-2 border-b border-slate-100 dark:border-slate-800">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Search attributes…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setOpen(false);
                    setQuery("");
                  }
                  if (e.key === "Enter" && filtered.length === 1)
                    select(filtered[0]);
                }}
                className="w-full pl-7 pr-2 py-1 text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded focus:outline-none focus:ring-1 focus:ring-brand-500 dark:text-slate-100"
              />
            </div>
          </div>
          <ul className="max-h-60 overflow-auto py-1" role="listbox">
            {filtered.length === 0 ? (
              <li className="px-3 py-2 text-xs text-slate-400">No match</li>
            ) : (
              filtered.map((attr) => (
                <li
                  key={attr}
                  role="option"
                  aria-selected={attr === value}
                  onClick={() => select(attr)}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                >
                  <Check
                    className={`h-3.5 w-3.5 flex-shrink-0 ${attr === value ? "text-brand-500" : "invisible"}`}
                  />
                  {attr}
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

// ─── Copy-to-clipboard key badge ────────────────────────────────────────────

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
      title="Copy key"
      className="group flex items-center gap-1 font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-colors"
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
  const [attributes, setAttributes] = useState([]);
  const [selectedAttr, setSelectedAttr] = useState("");
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const debouncedSearch = useDebounce(search);

  useEffect(() => {
    fetch(`${API}/lovs/attributes`)
      .then((r) => r.json())
      .then(setAttributes)
      .catch(() => setError("Could not load LOV attributes."));
  }, []);

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
      .then((data) => setRows(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedAttr, debouncedSearch]);

  const searchRef = useRef(null);
  const parentRef = useRef(null);

  // When an attribute is selected, the Attribute column is redundant — use a 2-column layout
  const showAttributeCol = !selectedAttr;
  const gridCols = showAttributeCol
    ? "grid-cols-[200px_140px_1fr]"
    : "grid-cols-[160px_1fr]";
  const headers = showAttributeCol
    ? ["Attribute", "Key", "Description"]
    : ["Key", "Description"];

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          LOV Explorer
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Browse and search all List-of-Values from the reference workbook
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3 flex-wrap flex-1">
            <AttributeCombobox
              attributes={attributes}
              value={selectedAttr}
              onChange={setSelectedAttr}
            />

            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search
                className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none"
                aria-hidden
              />
              <input
                ref={searchRef}
                type="text"
                placeholder="Search key or description…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setSearch("");
                    e.currentTarget.blur();
                  }
                }}
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

          <Badge
            variant={loading ? "secondary" : "outline"}
            className="flex-shrink-0 tabular-nums"
          >
            {loading ? "Loading…" : `${rows.length} rows`}
          </Badge>
        </CardHeader>

        {error && (
          <div className="px-4 py-2.5 text-sm text-danger-600 dark:text-red-400 bg-danger-50 dark:bg-red-900/20 border-b border-danger-100 dark:border-red-800/40">
            {error}
          </div>
        )}

        {/* Column headers */}
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

        {loading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-8" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <div className="py-12 text-center text-sm text-slate-400">
            {selectedAttr || debouncedSearch
              ? "No LOV rows found."
              : "Select an attribute or search to browse values."}
          </div>
        ) : (
          <div
            ref={parentRef}
            className="overflow-auto"
            style={{ height: "min(60vh, 560px)" }}
          >
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
                    {showAttributeCol && (
                      <div className="px-4 py-2.5 text-xs text-slate-600 dark:text-slate-400 font-medium truncate">
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
      </Card>
    </div>
  );
}
