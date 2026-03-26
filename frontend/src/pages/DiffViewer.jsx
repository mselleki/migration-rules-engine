import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { Upload, X, FileSpreadsheet, AlertCircle, GitCompare, Eye, EyeOff } from "lucide-react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import { Tabs, TabsList, TabsTrigger } from "../components/ui/tabs.jsx";

import API from "../api.js";

const DIFF_TYPES = [
  { key: "product",  label: "Product"  },
  { key: "vendor",   label: "Vendor"   },
  { key: "customer", label: "Customer" },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtBytes(b) {
  if (!b) return "";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

function safeStr(v) {
  if (v === null || v === undefined) return "";
  return String(v);
}

// ---------------------------------------------------------------------------
// FileDropZone - same style as Validator.jsx
// ---------------------------------------------------------------------------

function FileDropZone({ label, file, onFile }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.name.endsWith(".xlsx")) onFile(f);
  }, [onFile]);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${label} - drop zone`}
      onClick={() => !file && inputRef.current.click()}
      onKeyDown={e => e.key === "Enter" && inputRef.current.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={[
        "relative flex items-center gap-3 rounded-md border border-dashed p-3.5 transition-colors cursor-pointer",
        dragging ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
                 : file   ? "border-success-500 bg-success-50 dark:bg-green-900/10 cursor-default"
                          : "border-slate-200 dark:border-slate-700 hover:border-brand-400 hover:bg-slate-50 dark:hover:bg-slate-800/40",
      ].join(" ")}
    >
      <FileSpreadsheet className={`h-5 w-5 flex-shrink-0 ${file ? "text-success-500" : "text-slate-400"}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</p>
        {file ? (
          <p className="text-xs text-success-600 dark:text-green-400 mt-0.5 truncate">
            {file.name} · {fmtBytes(file.size)}
          </p>
        ) : (
          <p className="text-xs text-slate-400 mt-0.5">Drop .xlsx or click to browse</p>
        )}
      </div>
      {file ? (
        <button
          onClick={e => { e.stopPropagation(); onFile(null); }}
          className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 transition-colors"
          aria-label="Remove file"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      ) : (
        <Upload className="h-3.5 w-3.5 text-slate-300 flex-shrink-0" />
      )}
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx"
        className="hidden"
        onChange={e => onFile(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Summary bar
// ---------------------------------------------------------------------------

function SummaryBar({ summary }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant="success">+{summary.rows_added} added</Badge>
      <Badge variant="danger">-{summary.rows_deleted} deleted</Badge>
      <Badge variant="warning">~{summary.rows_modified} modified</Badge>
      <Badge variant="secondary">key: {summary.key_column}</Badge>
      {summary.columns_added.length > 0 && (
        <Badge variant="success">cols added: {summary.columns_added.join(", ")}</Badge>
      )}
      {summary.columns_removed.length > 0 && (
        <Badge variant="danger">cols removed: {summary.columns_removed.join(", ")}</Badge>
      )}
      {Object.keys(summary.type_changes).length > 0 && (
        <Badge variant="warning">
          type changes: {Object.keys(summary.type_changes).join(", ")}
        </Badge>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Diff table (virtualised when > 500 rows)
// ---------------------------------------------------------------------------

function DiffTable({ result }) {
  const { summary, rows } = result;
  const [showAll, setShowAll] = useState(false);
  const [colFilter, setColFilter] = useState("");

  // Derive all columns: key first, then union of non-key cols
  const allCols = useMemo(() => {
    const key = summary.key_column;
    const colSet = new Set();
    rows.forEach(r => { Object.keys(r.cells).forEach(c => colSet.add(c)); });
    return [key, ...Array.from(colSet)];
  }, [rows, summary.key_column]);

  // Columns that have at least one change (for filter dropdown)
  const changedCols = useMemo(() => {
    const set = new Set();
    rows.forEach(r => {
      Object.entries(r.cells).forEach(([col, cell]) => {
        if (cell.changed) set.add(col);
      });
    });
    return Array.from(set).sort();
  }, [rows]);

  // Filter rows
  const visibleRows = useMemo(() => {
    let filtered = showAll ? rows : rows.filter(r => r.status !== "unchanged");
    if (colFilter) {
      filtered = filtered.filter(r => r.cells[colFilter]?.changed);
    }
    return filtered;
  }, [rows, showAll, colFilter]);

  const useVirt = visibleRows.length > 500;
  const parentRef = useRef(null);
  const rowVirtualizer = useVirtualizer({
    count: visibleRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
    overscan: 10,
    enabled: useVirt,
  });

  function rowBg(status) {
    if (status === "added")   return "bg-success-50 dark:bg-green-900/10";
    if (status === "deleted") return "bg-danger-50 dark:bg-red-900/10";
    return "";
  }

  function renderCell(row, col) {
    const key = summary.key_column;
    if (col === key) {
      return (
        <span className="font-mono text-xs text-slate-700 dark:text-slate-300">
          {safeStr(row.key)}
        </span>
      );
    }
    const cell = row.cells[col];
    if (!cell) return <span className="text-slate-300 dark:text-slate-700">-</span>;

    if (cell.changed) {
      const oldStr = safeStr(cell.old);
      const newStr = safeStr(cell.new);
      return (
        <span className="inline-block rounded px-1 py-0.5 bg-warning-50 dark:bg-yellow-900/20 text-xs">
          {oldStr && <span className="text-danger-500 line-through mr-1">{oldStr}</span>}
          {newStr && <span className="text-success-600 dark:text-green-400">{newStr}</span>}
          {!oldStr && !newStr && <span className="text-slate-400">-</span>}
        </span>
      );
    }

    const displayVal = row.status === "added"
      ? safeStr(cell.new)
      : row.status === "deleted"
      ? safeStr(cell.old)
      : safeStr(cell.new ?? cell.old);

    return (
      <span className="text-xs text-slate-700 dark:text-slate-300 truncate">
        {displayVal || <span className="text-slate-300 dark:text-slate-700">-</span>}
      </span>
    );
  }

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowAll(v => !v)}
        >
          {showAll ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
          {showAll ? "Hide unchanged" : "Show all rows"}
        </Button>

        <select
          value={colFilter}
          onChange={e => setColFilter(e.target.value)}
          className="text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 focus:outline-none"
          aria-label="Filter by changed column"
        >
          <option value="">All columns</option>
          {changedCols.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <span className="text-xs text-slate-400 ml-auto">
          {visibleRows.length} row{visibleRows.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-800">
        {/* Header */}
        <div
          className="flex border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 sticky top-0 z-10"
          style={{ minWidth: `${allCols.length * 140}px` }}
        >
          {allCols.map(col => (
            <div
              key={col}
              className="flex-shrink-0 px-3 py-2 text-xs font-medium text-slate-500 uppercase tracking-wider"
              style={{ width: col === summary.key_column ? 120 : 180, minWidth: col === summary.key_column ? 120 : 180 }}
            >
              {col}
            </div>
          ))}
        </div>

        {visibleRows.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-400">
            No rows to display.
          </div>
        ) : useVirt ? (
          <div
            ref={parentRef}
            className="overflow-auto bg-white dark:bg-slate-900"
            style={{ height: "min(60vh, 560px)" }}
          >
            <div
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
                width: "100%",
                minWidth: `${allCols.length * 140}px`,
                position: "relative",
              }}
            >
              {rowVirtualizer.getVirtualItems().map(vRow => {
                const row = visibleRows[vRow.index];
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
                      minWidth: `${allCols.length * 140}px`,
                    }}
                    className={`flex border-b border-slate-50 dark:border-slate-800/50 ${rowBg(row.status)}`}
                  >
                    {allCols.map(col => (
                      <div
                        key={col}
                        className="flex-shrink-0 px-3 py-2 flex items-center overflow-hidden"
                        style={{ width: col === summary.key_column ? 120 : 180, minWidth: col === summary.key_column ? 120 : 180 }}
                      >
                        {renderCell(row, col)}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div
            className="overflow-auto bg-white dark:bg-slate-900"
            style={{ maxHeight: "min(60vh, 560px)", minWidth: `${allCols.length * 140}px` }}
          >
            {visibleRows.map((row, idx) => (
              <div
                key={`${row.key}-${idx}`}
                className={`flex border-b border-slate-50 dark:border-slate-800/50 hover:opacity-90 ${rowBg(row.status)}`}
              >
                {allCols.map(col => (
                  <div
                    key={col}
                    className="flex-shrink-0 px-3 py-2 flex items-center overflow-hidden"
                    style={{ width: col === summary.key_column ? 120 : 180, minWidth: col === summary.key_column ? 120 : 180 }}
                  >
                    {renderCell(row, col)}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main DiffViewer page
// ---------------------------------------------------------------------------

export default function DiffViewer() {
  const [diffType, setDiffType] = useState("product");
  const [origFile, setOrigFile] = useState(null);
  const [modFile, setModFile]   = useState(null);
  const [sheets, setSheets]     = useState([]);
  const [sheet, setSheet]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState(null);
  const [activeSheet, setActiveSheet] = useState("");

  // Reset everything when type changes
  const handleTypeChange = useCallback((t) => {
    setDiffType(t);
    setSheets([]);
    setSheet("");
    setResult(null);
    setError(null);
    setActiveSheet("");
  }, []);

  // When both files are ready, fetch sheet list for chosen type
  useEffect(() => {
    if (!origFile || !modFile) {
      setSheets([]);
      setSheet("");
      setResult(null);
      setError(null);
      setActiveSheet("");
      return;
    }
    fetch(`${API}/diff/config?type=${diffType}`)
      .then(r => {
        if (!r.ok) return r.json().then(d => { throw new Error(d.detail || `HTTP ${r.status}`); });
        return r.json();
      })
      .then(data => {
        setSheets(data.sheets);
        setSheet(data.sheets[0] ?? "");
        setResult(null);
        setError(null);
        setActiveSheet(data.sheets[0] ?? "");
      })
      .catch(err => setError(err.message));
  }, [origFile, modFile, diffType]);

  const runDiff = useCallback(async (sheetName) => {
    if (!origFile || !modFile || !sheetName) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("original", origFile);
      fd.append("modified", modFile);
      fd.append("type", diffType);
      fd.append("sheet", sheetName);
      const res = await fetch(`${API}/diff`, { method: "POST", body: fd });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setResult(data);
      setActiveSheet(sheetName);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [origFile, modFile, diffType]);

  const handleSheetTabChange = useCallback((s) => {
    setSheet(s);
    runDiff(s);
  }, [runDiff]);

  const bothUploaded = origFile && modFile;
  const canRun = bothUploaded && sheet && !loading;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Diff</h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Compare two versions of a migration Excel file and inspect what changed
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 items-start">
        {/* Config panel */}
        <Card className="xl:col-span-1">
          <CardHeader>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Configuration</span>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Step 1: type selection */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Type
                </label>
                <div className="flex gap-2 flex-wrap">
                  {DIFF_TYPES.map(({ key, label }) => (
                    <button
                      key={key}
                      onClick={() => handleTypeChange(key)}
                      className={[
                        "px-3 py-1.5 rounded-md text-sm font-medium border transition-colors",
                        diffType === key
                          ? "bg-brand-500 text-white border-brand-500"
                          : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-brand-400 hover:text-brand-500",
                      ].join(" ")}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Step 2: file uploads */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Files
                </label>
                <FileDropZone label="Original file" file={origFile} onFile={setOrigFile} />
                <FileDropZone label="Modified file" file={modFile}  onFile={setModFile}  />
              </div>

              {/* Step 3: sheet + run */}
              {bothUploaded && sheets.length > 0 && (
                <div className="space-y-2">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Sheet
                  </label>
                  <select
                    value={sheet}
                    onChange={e => setSheet(e.target.value)}
                    className="w-full text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                    aria-label="Select sheet"
                  >
                    {sheets.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>

                  <Button
                    onClick={() => runDiff(sheet)}
                    disabled={!canRun}
                    className="w-full"
                    size="md"
                  >
                    {loading ? (
                      <>
                        <span className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Running diff…
                      </>
                    ) : (
                      <>
                        <GitCompare className="h-3.5 w-3.5" />
                        Run diff
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Results panel */}
        <div className="xl:col-span-2 space-y-4">
          {/* Error */}
          {error && (
            <div className="flex items-start gap-2.5 rounded-md border border-danger-100 dark:border-red-800/40 bg-danger-50 dark:bg-red-900/20 px-4 py-3 text-sm text-danger-700 dark:text-red-400">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Loading spinner (no result yet) */}
          {loading && !result && (
            <div className="flex items-center justify-center py-16">
              <span className="h-6 w-6 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin" />
              <span className="ml-3 text-sm text-slate-500">Running diff…</span>
            </div>
          )}

          {result && (
            <Card>
              <CardHeader>
                <div className="flex flex-col gap-2 flex-1">
                  {/* Sheet tabs (multi-sheet types) */}
                  {sheets.length > 1 && (
                    <Tabs value={activeSheet} onValueChange={handleSheetTabChange}>
                      <TabsList>
                        {sheets.map(s => (
                          <TabsTrigger key={s} value={s} disabled={loading}>
                            {s}
                            {loading && activeSheet !== s ? null : null}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                    </Tabs>
                  )}
                  {sheets.length === 1 && (
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      {result.summary.sheet}
                    </span>
                  )}
                  <SummaryBar summary={result.summary} />
                </div>
                {loading && (
                  <span className="h-4 w-4 border-2 border-brand-500/30 border-t-brand-500 rounded-full animate-spin flex-shrink-0" />
                )}
              </CardHeader>
              <CardContent>
                <DiffTable result={result} />
              </CardContent>
            </Card>
          )}

          {!result && !error && !loading && (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <GitCompare className="h-10 w-10 mb-3 opacity-30" />
              <p className="text-sm">Upload two files and run a diff to see changes</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
