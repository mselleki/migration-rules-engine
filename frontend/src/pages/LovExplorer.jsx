import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import {
  Search,
  X,
  Copy,
  CheckCheck,
  Plus,
  Trash2,
  Clock,
  ChevronRight,
} from "lucide-react";
import { Badge } from "../components/ui/badge.jsx";
import { Skeleton } from "../components/ui/skeleton.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { getPhase, PHASE_STYLE, ATTR_GROUP } from "../data/lovPhases.js";
import API from "../api.js";

function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function timeAgo(ts) {
  const diff = Date.now() - ts * 1000;
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return d === 1 ? "1 day ago" : `${d} days ago`;
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
      className="group inline-flex items-center gap-1 font-mono text-xs px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-colors"
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

// ─── Add LOV modal ───────────────────────────────────────────────────────────

const INPUT_CLS =
  "w-full px-3 py-2 text-sm border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500";

function AddLovModal({ attributes, selectedAttr, onAdd, onClose }) {
  // "existing" = add a value to an existing attribute
  // "new"      = create a new attribute with one or more values
  const [mode, setMode] = useState("existing");

  // "existing" mode state
  const [attribute, setAttribute] = useState(selectedAttr || "");
  const [key, setKey] = useState("");
  const [description, setDescription] = useState("");

  // "new" mode state
  const [newAttrName, setNewAttrName] = useState("");
  const [values, setValues] = useState([{ key: "", description: "" }]);

  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const addValueRow = () =>
    setValues((v) => [...v, { key: "", description: "" }]);
  const removeValueRow = (i) =>
    setValues((v) => v.filter((_, idx) => idx !== i));
  const updateValue = (i, field, val) =>
    setValues((v) =>
      v.map((row, idx) => (idx === i ? { ...row, [field]: val } : row)),
    );

  const filledValues = values.filter((v) => v.key.trim());
  const canSubmit =
    mode === "existing"
      ? attribute && key.trim()
      : newAttrName.trim() && filledValues.length > 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    if (mode === "existing") {
      await onAdd([
        { attribute, key: key.trim(), description: description.trim() },
      ]);
    } else {
      await onAdd(
        filledValues.map((v) => ({
          attribute: newAttrName.trim(),
          key: v.key.trim(),
          description: v.description.trim(),
        })),
      );
    }
    setSubmitting(false);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-2xl w-full max-w-md mx-4 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Plus className="h-4 w-4 text-brand-500" />
            Add LOV entry
          </span>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Mode toggle */}
        <div className="flex gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg mb-4">
          {[
            { id: "existing", label: "Add to existing attribute" },
            { id: "new", label: "New attribute" },
          ].map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => setMode(id)}
              className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
                mode === id
                  ? "bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 shadow-sm"
                  : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === "existing" ? (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                  Attribute
                </label>
                <select
                  value={attribute}
                  onChange={(e) => setAttribute(e.target.value)}
                  autoFocus
                  required
                  className={INPUT_CLS}
                >
                  <option value="">Select an attribute…</option>
                  {attributes.map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                  Key
                </label>
                <input
                  value={key}
                  onChange={(e) => setKey(e.target.value)}
                  placeholder="e.g. ACTIVE"
                  required
                  className={INPUT_CLS}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                  Description{" "}
                  <span className="font-normal text-slate-400">(optional)</span>
                </label>
                <input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Active status"
                  className={INPUT_CLS}
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                  Attribute name
                </label>
                <input
                  value={newAttrName}
                  onChange={(e) => setNewAttrName(e.target.value)}
                  placeholder="e.g. Storage Temperature"
                  autoFocus
                  required
                  className={INPUT_CLS}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">
                  Values
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-0.5">
                  {values.map((v, i) => (
                    <div key={i} className="flex gap-2 items-center">
                      <input
                        value={v.key}
                        onChange={(e) => updateValue(i, "key", e.target.value)}
                        placeholder="Key"
                        className="w-28 flex-shrink-0 px-2.5 py-1.5 text-sm border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      />
                      <input
                        value={v.description}
                        onChange={(e) =>
                          updateValue(i, "description", e.target.value)
                        }
                        placeholder="Description (optional)"
                        className="flex-1 px-2.5 py-1.5 text-sm border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      />
                      {values.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeValueRow(i)}
                          className="flex-shrink-0 text-slate-300 hover:text-red-500 dark:text-slate-600 dark:hover:text-red-400 transition-colors"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={addValueRow}
                  className="mt-2 text-xs text-brand-500 hover:text-brand-600 flex items-center gap-1 transition-colors"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Add another value
                </button>
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={!canSubmit || submitting}
            className="w-full py-2 rounded-lg bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors mt-1"
          >
            {submitting
              ? "Saving…"
              : mode === "new"
                ? `Add attribute${filledValues.length > 0 ? ` (${filledValues.length} value${filledValues.length > 1 ? "s" : ""})` : ""}`
                : "Add value"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─── History modal ───────────────────────────────────────────────────────────

function HistoryModal({ history, loading, onClose }) {
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
        className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-2xl w-full max-w-lg mx-4 flex flex-col"
        style={{ maxHeight: "80vh" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Clock className="h-4 w-4 text-slate-400" />
            LOV Change History
          </span>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-4">
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          ) : history.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-10">
              No changes recorded yet.
            </p>
          ) : (
            <ul className="space-y-1">
              {history.map((entry) => (
                <li
                  key={entry.id}
                  className="flex items-start gap-3 py-2.5 border-b border-slate-50 dark:border-slate-800/60 last:border-0"
                >
                  <span
                    className={`mt-0.5 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold flex-shrink-0 ${
                      entry.action === "add"
                        ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                        : "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400"
                    }`}
                  >
                    {entry.action === "add" ? "ADD" : "DEL"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">
                      <span className="font-medium">{entry.attribute}</span>
                      {" — "}
                      <span className="font-mono">{entry.key}</span>
                      {entry.description && (
                        <span className="text-slate-400">
                          {" "}
                          ({entry.description})
                        </span>
                      )}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      {entry.user} · {timeAgo(entry.ts)}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function LovExplorer() {
  const { role, name } = useAuth();
  const isDet = role === "det";

  const [previews, setPreviews] = useState([]);
  const [selectedAttr, setSelectedAttr] = useState("");
  const [attrFilter, setAttrFilter] = useState("");
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // DET-only state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const debouncedSearch = useDebounce(search);

  // Load attribute previews
  useEffect(() => {
    fetch(`${API}/lovs/preview`)
      .then((r) => r.json())
      .then(setPreviews)
      .catch(() => setError("Could not load LOV attributes."));
  }, [refreshKey]);

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
  }, [selectedAttr, debouncedSearch, refreshKey]);

  // Clear table search when switching attribute
  const selectAttr = useCallback((attr) => {
    setSelectedAttr((prev) => (prev === attr ? "" : attr));
    setSearch("");
  }, []);

  const handleAddLov = async (entries) => {
    for (const entry of entries) {
      await fetch(`${API}/lovs/custom`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...entry, user: name }),
      });
    }
    setRefreshKey((k) => k + 1);
  };

  const handleDeleteLov = async (entryId) => {
    await fetch(
      `${API}/lovs/custom/${entryId}?user=${encodeURIComponent(name)}`,
      { method: "DELETE" },
    );
    setRefreshKey((k) => k + 1);
  };

  const openHistory = () => {
    setShowHistory(true);
    setHistoryLoading(true);
    fetch(`${API}/lovs/history`)
      .then((r) => r.json())
      .then(setHistory)
      .finally(() => setHistoryLoading(false));
  };

  const [expandedGroups, setExpandedGroups] = useState(new Set());
  const toggleGroup = useCallback((name) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  }, []);

  // Build sidebar items: group allergens/certifications, flat list when filtering
  const sidebarItems = useMemo(() => {
    const source = attrFilter
      ? previews.filter((p) =>
          p.attribute.toLowerCase().includes(attrFilter.toLowerCase()),
        )
      : previews;

    if (attrFilter) {
      return source.map((p) => ({ type: "item", ...p }));
    }

    const groupedMembers = {};
    const regularItems = [];
    for (const preview of source) {
      const groupName = ATTR_GROUP[preview.attribute];
      if (groupName) {
        if (!groupedMembers[groupName]) groupedMembers[groupName] = [];
        groupedMembers[groupName].push(preview);
      } else {
        regularItems.push({ type: "item", ...preview });
      }
    }

    const result = [...regularItems];
    for (const [name, members] of Object.entries(groupedMembers)) {
      result.push({
        type: "group",
        name,
        members,
        totalCount: members.reduce((s, m) => s + m.count, 0),
      });
    }
    result.sort((a, b) =>
      (a.type === "group" ? a.name : a.attribute).localeCompare(
        b.type === "group" ? b.name : b.attribute,
      ),
    );
    return result;
  }, [previews, attrFilter]);

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

  // List of unique attribute names for the Add modal datalist
  const attributeNames = previews.map((p) => p.attribute);

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
            ) : sidebarItems.length === 0 ? (
              <p className="px-3 py-4 text-xs text-slate-400 text-center">
                No match
              </p>
            ) : (
              sidebarItems.map((item) =>
                item.type === "group" ? (
                  <div key={item.name}>
                    {/* Group header */}
                    <button
                      onClick={() => toggleGroup(item.name)}
                      className="w-full text-left px-3 py-2 border-b border-slate-50 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      <div className="flex items-center gap-1.5">
                        <ChevronRight
                          className={`h-3 w-3 flex-shrink-0 text-slate-400 transition-transform duration-150 ${
                            expandedGroups.has(item.name) ? "rotate-90" : ""
                          }`}
                        />
                        <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 flex-1 truncate">
                          {item.name}
                        </span>
                        <span className="text-[9px] font-bold px-1 py-px rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 flex-shrink-0">
                          P1
                        </span>
                        <span className="text-[10px] text-slate-400 flex-shrink-0">
                          {item.totalCount}
                        </span>
                      </div>
                    </button>
                    {/* Group members */}
                    {expandedGroups.has(item.name) &&
                      item.members.map(({ attribute, count, examples }) => (
                        <button
                          key={attribute}
                          onClick={() => selectAttr(attribute)}
                          className={`w-full text-left pl-6 pr-3 py-2 border-b border-slate-50 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                            selectedAttr === attribute
                              ? "bg-brand-50 dark:bg-brand-900/20 border-l-2 border-l-brand-500"
                              : ""
                          }`}
                        >
                          <div className="flex items-center justify-between gap-1">
                            <span className="text-xs text-slate-600 dark:text-slate-300 truncate">
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
                      ))}
                  </div>
                ) : (
                  <button
                    key={item.attribute}
                    onClick={() => selectAttr(item.attribute)}
                    className={`w-full text-left px-3 py-2.5 border-b border-slate-50 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors ${
                      selectedAttr === item.attribute
                        ? "bg-brand-50 dark:bg-brand-900/20 border-l-2 border-l-brand-500"
                        : ""
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-200 truncate">
                        {item.attribute}
                      </span>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {(() => {
                          const phase = getPhase(item.attribute);
                          const s = PHASE_STYLE[phase];
                          return (
                            <span
                              title={phase}
                              className={`text-[9px] font-bold px-1 py-px rounded ${s.className}`}
                            >
                              {s.label}
                            </span>
                          );
                        })()}
                        <span className="text-[10px] text-slate-400">
                          {item.count}
                        </span>
                      </div>
                    </div>
                    {item.examples.length > 0 && (
                      <p className="text-[10px] text-slate-400 mt-0.5 truncate">
                        {item.examples.join(" · ")}
                      </p>
                    )}
                  </button>
                ),
              )
            )}
          </div>
        </div>

        {/* ── Right panel: LOV table ── */}
        <div className="flex-1 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden flex flex-col bg-white dark:bg-slate-900">
          {/* Header */}
          <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-100 dark:border-slate-800">
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
              className="flex-shrink-0 tabular-nums"
            >
              {loading
                ? "Loading…"
                : rows.length > 0
                  ? `${rows.length} rows`
                  : ""}
            </Badge>

            {/* DET-only actions */}
            {isDet && (
              <>
                <button
                  onClick={openHistory}
                  title="LOV Change History"
                  className="ml-auto h-7 w-7 flex items-center justify-center rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <Clock className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setShowAddModal(true)}
                  title="Add LOV entry"
                  className="h-7 flex items-center gap-1.5 px-2.5 rounded bg-brand-500 hover:bg-brand-600 text-white text-xs font-medium transition-colors"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Add
                </button>
              </>
            )}
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
                  const isCustom = row.source === "custom";
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
                      className={`group grid ${gridCols} border-b border-slate-50 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/30 ${
                        vRow.index % 2 === 1
                          ? "bg-slate-50/40 dark:bg-slate-800/10"
                          : "bg-white dark:bg-slate-900"
                      }`}
                    >
                      {showAttrCol && (
                        <div className="px-4 py-2.5 text-xs text-slate-500 dark:text-slate-400 font-medium truncate">
                          {row.attribute}
                        </div>
                      )}
                      <div className="px-4 py-2.5 flex items-center gap-1.5 flex-wrap">
                        <KeyBadge value={row.key} />
                        {isCustom && (
                          <span className="text-[9px] px-1.5 py-px rounded-full bg-brand-100 dark:bg-brand-900/40 text-brand-600 dark:text-brand-400 font-semibold tracking-wide">
                            custom
                          </span>
                        )}
                      </div>
                      <div className="px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 flex items-center justify-between gap-2">
                        <span className="truncate">{row.description}</span>
                        {isDet && isCustom && (
                          <button
                            onClick={() => handleDeleteLov(row.id)}
                            title={`Delete (added by ${row.added_by})`}
                            className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-0.5 rounded text-slate-300 hover:text-red-500 dark:text-slate-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {showAddModal && (
        <AddLovModal
          attributes={attributeNames}
          selectedAttr={selectedAttr}
          onAdd={handleAddLov}
          onClose={() => setShowAddModal(false)}
        />
      )}
      {showHistory && (
        <HistoryModal
          history={history}
          loading={historyLoading}
          onClose={() => setShowHistory(false)}
        />
      )}
    </div>
  );
}
