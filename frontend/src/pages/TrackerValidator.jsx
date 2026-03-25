import { useState, useRef, useCallback, useMemo } from "react";
import {
  Upload,
  X,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select.jsx";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
} from "@tanstack/react-table";
import { getPhase, PHASE_STYLE } from "../data/lovPhases.js";
import API from "../api.js";

const DOMAINS = ["Products", "Vendors", "Customers"];

function fmtBytes(b) {
  if (!b) return "";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

// --- File drop zone ---

function FileDropZone({ label, file, onFile }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files?.[0];
      if (f && f.name.endsWith(".xlsx")) onFile(f);
    },
    [onFile],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${label} - drop zone`}
      onClick={() => !file && inputRef.current.click()}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={[
        "relative flex items-center gap-3 rounded-md border border-dashed p-3.5 transition-colors cursor-pointer",
        dragging
          ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
          : file
            ? "border-success-500 bg-success-50 dark:bg-green-900/10 cursor-default"
            : "border-slate-200 dark:border-slate-700 hover:border-brand-400 hover:bg-slate-50 dark:hover:bg-slate-800/40",
      ].join(" ")}
    >
      <FileSpreadsheet
        className={`h-5 w-5 flex-shrink-0 ${file ? "text-success-500" : "text-slate-400"}`}
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
          {label}
        </p>
        {file ? (
          <p className="text-xs text-success-600 dark:text-green-400 mt-0.5 truncate">
            {file.name} - {fmtBytes(file.size)}
          </p>
        ) : (
          <p className="text-xs text-slate-400 mt-0.5">
            Drop .xlsx or click to browse
          </p>
        )}
      </div>
      {file ? (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onFile(null);
          }}
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
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}

// --- Results table ---

const errorColumns = [
  {
    accessorKey: "sheet",
    header: "Sheet",
    size: 130,
    cell: (i) => <Badge variant="secondary">{i.getValue()}</Badge>,
  },
  {
    accessorKey: "row",
    header: "Row",
    size: 60,
    cell: (i) => (
      <span className="tabular-nums text-slate-500">{i.getValue()}</span>
    ),
  },
  {
    accessorKey: "supc",
    header: "ID",
    size: 100,
    cell: (i) => <span className="font-mono text-xs">{i.getValue()}</span>,
  },
  { accessorKey: "rule", header: "Rule", size: 240 },
  { accessorKey: "message", header: "Message", size: undefined },
];

function ErrorTable({ errors }) {
  const [globalFilter, setGlobalFilter] = useState("");
  const table = useReactTable({
    data: errors,
    columns: errorColumns,
    state: { globalFilter },
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 15 } },
  });

  return (
    <div>
      <div className="flex items-center gap-3 mb-3">
        <input
          type="text"
          placeholder="Search errors..."
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          className="flex-1 text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-brand-500 focus:outline-none max-w-xs dark:text-slate-100"
        />
        <span className="text-xs text-slate-400">
          {table.getFilteredRowModel().rows.length} of {errors.length}
        </span>
      </div>
      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
              {table.getHeaderGroups().map((hg) =>
                hg.headers.map((h) => (
                  <th
                    key={h.id}
                    className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider"
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                )),
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50 bg-white dark:bg-slate-900">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="hover:bg-slate-50 dark:hover:bg-slate-800/30"
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-3 py-2.5 text-slate-700 dark:text-slate-300 align-top"
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {table.getPageCount() > 1 && (
        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-slate-400">
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount()}
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Prev
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// --- Completion Panel ---

const PHASE_ORDER = ["MVP", "Phase 1"];
const PHASE_BAR_COLOR = {
  MVP: "bg-amber-400",
  "Phase 1": "bg-blue-400",
  Unclassified: "bg-slate-300 dark:bg-slate-600",
};

function colRateColor(rate) {
  if (rate >= 0.95) return "bg-emerald-500";
  if (rate >= 0.75) return "bg-amber-400";
  if (rate >= 0.5) return "bg-orange-400";
  return "bg-red-500";
}

function CompletionPanel({ completion }) {
  const [selectedSheet, setSelectedSheet] = useState(null);
  const [showAll, setShowAll] = useState(false);

  const stats = useMemo(() => {
    if (!completion?.length) return null;

    const allCols = completion.flatMap((s) =>
      s.columns.map((c) => ({ ...c, totalRows: s.total_rows })),
    );

    const totalCells = allCols.reduce((sum, c) => sum + c.totalRows, 0);
    const filledCells = allCols.reduce((sum, c) => sum + c.filled, 0);
    const overallRate = totalCells > 0 ? filledCells / totalCells : 0;

    const phaseMap = {};
    for (const col of allCols) {
      const key = getPhase(col.attribute) ?? "Unclassified";
      if (!phaseMap[key]) phaseMap[key] = { filled: 0, total: 0 };
      phaseMap[key].filled += col.filled;
      phaseMap[key].total += col.totalRows;
    }

    return { overallRate, totalCells, filledCells, phaseMap };
  }, [completion]);

  if (!stats) return null;

  const currentSheet =
    selectedSheet && completion.find((s) => s.sheet === selectedSheet)
      ? selectedSheet
      : completion[0]?.sheet;

  const sheetData = completion.find((s) => s.sheet === currentSheet);
  const cols = sheetData?.columns ?? [];
  const incomplete = cols
    .filter((c) => c.rate < 1)
    .sort((a, b) => a.rate - b.rate);
  const displayCols = showAll
    ? [...cols].sort((a, b) => a.rate - b.rate)
    : incomplete.slice(0, 25);

  const phaseRows = [
    ...PHASE_ORDER.filter((p) => stats.phaseMap[p]),
    ...(stats.phaseMap["Unclassified"] ? ["Unclassified"] : []),
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
            Completion Analysis
          </span>
          <span className="text-lg font-bold text-brand-500">
            {Math.round(stats.overallRate * 100)}%
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Overall bar */}
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1.5">
            <span>Overall fill rate</span>
            <span className="tabular-nums">
              {stats.filledCells.toLocaleString()} /{" "}
              {stats.totalCells.toLocaleString()} cells
            </span>
          </div>
          <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full transition-all"
              style={{ width: `${stats.overallRate * 100}%` }}
            />
          </div>
        </div>

        {/* Phase breakdown */}
        <div className="space-y-2">
          {phaseRows.map((phase) => {
            const { filled, total } = stats.phaseMap[phase];
            const rate = total > 0 ? filled / total : 0;
            const pStyle = PHASE_STYLE[phase];
            const barColor = PHASE_BAR_COLOR[phase];
            return (
              <div key={phase} className="flex items-center gap-3">
                <div className="w-10 flex-shrink-0">
                  {pStyle ? (
                    <span
                      className={`text-[9px] font-bold px-1 py-px rounded ${pStyle.className}`}
                    >
                      {pStyle.label}
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-400">—</span>
                  )}
                </div>
                <div className="flex-1 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${barColor} rounded-full transition-all`}
                    style={{ width: `${rate * 100}%` }}
                  />
                </div>
                <span className="text-xs tabular-nums text-slate-500 w-8 text-right">
                  {Math.round(rate * 100)}%
                </span>
              </div>
            );
          })}
        </div>

        {/* Divider */}
        <div className="border-t border-slate-100 dark:border-slate-800" />

        {/* Sheet tabs */}
        {completion.length > 1 && (
          <div className="flex gap-1">
            {completion.map((s) => (
              <button
                key={s.sheet}
                onClick={() => {
                  setSelectedSheet(s.sheet);
                  setShowAll(false);
                }}
                className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                  currentSheet === s.sheet
                    ? "bg-brand-500 text-white"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                }`}
              >
                {s.sheet}
                <span className="ml-1.5 opacity-60 tabular-nums">
                  {s.total_rows}r
                </span>
              </button>
            ))}
          </div>
        )}

        {/* Column breakdown */}
        {displayCols.length === 0 ? (
          <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5 flex-shrink-0" />
            All columns are 100% complete.
          </div>
        ) : (
          <div className="space-y-1.5">
            {displayCols.map((col) => {
              const phase = getPhase(col.attribute);
              const pStyle = phase ? PHASE_STYLE[phase] : null;
              return (
                <div key={col.attribute} className="flex items-center gap-2">
                  <span className="text-xs text-slate-600 dark:text-slate-300 truncate w-44 flex-shrink-0">
                    {col.attribute}
                  </span>
                  <div className="w-8 flex-shrink-0 flex justify-start">
                    {pStyle && (
                      <span
                        className={`text-[9px] font-bold px-1 py-px rounded ${pStyle.className}`}
                      >
                        {pStyle.label}
                      </span>
                    )}
                  </div>
                  <div className="flex-1 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${colRateColor(col.rate)} rounded-full transition-all`}
                      style={{ width: `${col.rate * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] tabular-nums text-slate-400 w-24 flex-shrink-0 text-right">
                    {col.filled}/{col.totalRows} · {Math.round(col.rate * 100)}%
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* Show all / incomplete toggle */}
        {(cols.length > 25 || incomplete.length !== cols.length) && (
          <button
            onClick={() => setShowAll((v) => !v)}
            className="text-xs text-brand-500 hover:underline"
          >
            {showAll
              ? `Show incomplete only (${incomplete.length})`
              : `Show all ${cols.length} columns`}
          </button>
        )}
      </CardContent>
    </Card>
  );
}

// --- Main ---

export default function TrackerValidator() {
  const [domain, setDomain] = useState("Products");
  const [mode, setMode] = useState("sharepoint"); // "sharepoint" | "upload"
  const [file, setFile] = useState(null);
  const [sharepointUrl, setSharepointUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const handleDomainChange = useCallback((d) => {
    setDomain(d);
    setFile(null);
    setReport(null);
    setError(null);
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      let res;
      if (mode === "sharepoint") {
        if (!sharepointUrl.trim()) return;
        res = await fetch(`${API}/validate/tracker/sharepoint`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            domain,
            sharepoint_url: sharepointUrl.trim(),
          }),
        });
      } else {
        if (!file) return;
        const fd = new FormData();
        fd.append("domain", domain);
        fd.append("file", file);
        res = await fetch(`${API}/validate/tracker`, {
          method: "POST",
          body: fd,
        });
      }
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || `HTTP ${res.status}`);
      }
      setReport(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const canSubmit =
    mode === "sharepoint" ? sharepointUrl.trim().length > 0 : !!file;
  const totalErrors = report?.summary?.total_errors ?? 0;
  const totalRows = report?.summary?.total_rows ?? 0;
  const errorsByRule = report?.summary?.errors_by_rule ?? {};

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Tracker Validator
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          Validate P1 Data Cleansing tracker files
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 items-start">
        {/* Configuration card */}
        <Card className="xl:col-span-1">
          <CardHeader>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Configuration
            </span>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Domain */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Domain
                </label>
                <Select value={domain} onValueChange={handleDomainChange}>
                  <SelectTrigger aria-label="Select domain">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DOMAINS.map((d) => (
                      <SelectItem key={d} value={d}>
                        {d}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Source mode toggle */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Source
                </label>
                <div className="flex rounded-md border border-slate-200 dark:border-slate-700 overflow-hidden text-xs">
                  {[
                    { id: "sharepoint", label: "SharePoint" },
                    { id: "upload", label: "Upload" },
                  ].map(({ id, label }) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => {
                        setMode(id);
                        setFile(null);
                        setReport(null);
                        setError(null);
                      }}
                      className={`flex-1 py-1.5 font-medium transition-colors ${
                        mode === id
                          ? "bg-brand-500 text-white"
                          : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* SharePoint URL input */}
              {mode === "sharepoint" && (
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    SharePoint URL
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Paste the SharePoint link to the tracker file…"
                    value={sharepointUrl}
                    onChange={(e) => setSharepointUrl(e.target.value)}
                    className="w-full text-xs border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-2 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-brand-500 focus:outline-none resize-none text-slate-700 dark:text-slate-300 placeholder:text-slate-300 dark:placeholder:text-slate-600"
                  />
                </div>
              )}

              {/* File upload */}
              {mode === "upload" && (
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Tracker File
                  </label>
                  <FileDropZone
                    label="Tracker file (.xlsx / .xlsb)"
                    file={file}
                    onFile={setFile}
                  />
                </div>
              )}

              <Button
                type="submit"
                disabled={!canSubmit || loading}
                className="w-full"
                size="md"
              >
                {loading ? (
                  <>
                    <span className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />{" "}
                    {mode === "sharepoint"
                      ? "Fetching from SharePoint…"
                      : "Validating…"}
                  </>
                ) : mode === "sharepoint" ? (
                  "Load & Validate"
                ) : (
                  "Run Validation"
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results area */}
        {(error || report) && (
          <div className="xl:col-span-2 space-y-4">
            {error && (
              <div className="flex items-start gap-2.5 rounded-md border border-danger-100 dark:border-red-800/40 bg-danger-50 dark:bg-red-900/20 px-4 py-3 text-sm text-danger-700 dark:text-red-400">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {report && (
              <div className="space-y-4">
                {/* SharePoint source badge */}
                {report.source?.type === "sharepoint" && (
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <FileSpreadsheet className="h-3.5 w-3.5 flex-shrink-0" />
                    <span className="truncate">{report.source.filename}</span>
                    <span className="text-slate-300 dark:text-slate-600">
                      ·
                    </span>
                    <span className="text-emerald-500">
                      Live from SharePoint
                    </span>
                  </div>
                )}

                {/* Warnings */}
                {report.warnings?.map((w, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 rounded-md border border-warning-100 dark:border-yellow-800/40 bg-warning-50 dark:bg-yellow-900/20 px-4 py-3 text-sm text-warning-500 dark:text-yellow-300"
                  >
                    <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" /> {w}
                  </div>
                ))}

                {/* Metrics strip */}
                <div className="grid grid-cols-2 divide-x divide-slate-200 dark:divide-slate-700 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900">
                  {[
                    { label: "Total rows", value: totalRows },
                    {
                      label: "Total errors",
                      value: totalErrors,
                      danger: totalErrors > 0,
                      accent: totalErrors === 0,
                    },
                  ].map(({ label, value, danger, accent }) => (
                    <div key={label} className="px-5 py-3">
                      <p className="text-xs text-slate-500 dark:text-slate-400 mb-0.5">
                        {label}
                      </p>
                      <p
                        className={
                          "text-xl font-semibold " +
                          (danger
                            ? "text-danger-500"
                            : accent
                              ? "text-success-500"
                              : "text-slate-800 dark:text-slate-100")
                        }
                      >
                        {value}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Completion analysis */}
                {report.completion?.length > 0 && (
                  <CompletionPanel completion={report.completion} />
                )}

                {/* Errors by rule */}
                {Object.keys(errorsByRule).length > 0 && (
                  <Card>
                    <CardHeader>
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                        Errors by Rule
                      </span>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(errorsByRule)
                          .sort((a, b) => b[1] - a[1])
                          .map(([rule, count]) => (
                            <div key={rule} className="flex items-center gap-3">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">
                                  {rule}
                                </p>
                                <div className="mt-1 h-1 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-danger-500 rounded-full transition-all"
                                    style={{
                                      width: `${(count / totalErrors) * 100}%`,
                                    }}
                                  />
                                </div>
                              </div>
                              <Badge
                                variant="danger"
                                className="flex-shrink-0 tabular-nums"
                              >
                                {count}
                              </Badge>
                            </div>
                          ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Error table */}
                <Card>
                  <CardHeader>
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      Detailed Errors
                    </span>
                  </CardHeader>
                  <CardContent>
                    {report.errors?.length === 0 ? (
                      <div className="flex items-center gap-2.5 rounded-md border border-success-100 dark:border-green-800/40 bg-success-50 dark:bg-green-900/20 px-4 py-3 text-sm text-success-500 dark:text-green-400">
                        <CheckCircle2 className="h-4 w-4 flex-shrink-0" /> All
                        rules passed - no errors found.
                      </div>
                    ) : (
                      <ErrorTable errors={report.errors ?? []} />
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
