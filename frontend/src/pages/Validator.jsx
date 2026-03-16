import { useState, useRef, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { Upload, X, FileSpreadsheet, AlertCircle, CheckCircle2, Download } from "lucide-react";
import { useHistory } from "../context/HistoryContext.jsx";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select.jsx";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
} from "@tanstack/react-table";

const API = "/api";
const DOMAINS = ["Products", "Vendors", "Customers"];

const DOMAIN_FILES = {
  Products: [
    { key: "global_file", label: "Global Product Data" },
    { key: "local_file",  label: "Local Product Data"  },
  ],
  Vendors: [
    { key: "invoice",     label: "Invoice"     },
    { key: "lea_invoice", label: "LEA Invoice"  },
    { key: "os",          label: "OS"           },
    { key: "lea_os",      label: "LEA OS"       },
  ],
  Customers: [
    { key: "pt",               label: "PT"               },
    { key: "invoice",          label: "Invoice"          },
    { key: "lea_invoice",      label: "LEA Invoice"      },
    { key: "os",               label: "OS"               },
    { key: "lea_os",           label: "LEA OS"           },
    { key: "employee_invoice", label: "Employee Invoice"  },
    { key: "employee_os",      label: "Employee OS"       },
  ],
};

function fmtBytes(b) {
  if (!b) return "";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

function fmt(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" }) + " " +
    d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

// ─── File drop zone ───────────────────────────────────────────────────────────

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
      aria-label={`${label} — drop zone`}
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
      <input ref={inputRef} type="file" accept=".xlsx" className="hidden" onChange={e => onFile(e.target.files?.[0] ?? null)} />
    </div>
  );
}

// ─── Results table (TanStack) ─────────────────────────────────────────────────

const errorColumns = [
  { accessorKey: "sheet",   header: "Sheet",   size: 130, cell: i => <Badge variant="secondary">{i.getValue()}</Badge> },
  { accessorKey: "row",     header: "Row",     size: 60,  cell: i => <span className="tabular-nums text-slate-500">{i.getValue()}</span> },
  { accessorKey: "supc",    header: "SUPC",    size: 100, cell: i => <span className="font-mono text-xs">{i.getValue()}</span> },
  { accessorKey: "rule",    header: "Rule",    size: 240 },
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
          placeholder="Search errors…"
          value={globalFilter}
          onChange={e => setGlobalFilter(e.target.value)}
          className="flex-1 text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-brand-500 focus:outline-none max-w-xs dark:text-slate-100"
        />
        <span className="text-xs text-slate-400">{table.getFilteredRowModel().rows.length} of {errors.length}</span>
      </div>
      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
              {table.getHeaderGroups().map(hg => hg.headers.map(h => (
                <th key={h.id} className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              )))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50 bg-white dark:bg-slate-900">
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-3 py-2.5 text-slate-700 dark:text-slate-300 align-top">
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
          <span className="text-xs text-slate-400">Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}</span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Prev</Button>
            <Button size="sm" variant="outline" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>Next</Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Validator() {
  const location = useLocation();
  const { runs, addRun } = useHistory();

  const [domain, setDomain]   = useState(location.state?.domain ?? "Products");
  const [files, setFiles]     = useState({});
  const [loading, setLoading] = useState(false);
  const [report, setReport]   = useState(null);
  const [error, setError]     = useState(null);

  // Reset files whenever domain changes
  const handleDomainChange = useCallback((d) => { setDomain(d); setFiles({}); setReport(null); setError(null); }, []);

  const setFile = useCallback((key, file) => setFiles(prev => ({ ...prev, [key]: file })), []);

  const buildFormData = (d, f) => {
    const fd = new FormData();
    fd.append("domain", d);
    DOMAIN_FILES[d].forEach(({ key }) => { if (f[key]) fd.append(key, f[key]); });
    return fd;
  };

  async function handleSubmit(e) {
    e.preventDefault();
    const anyFile = DOMAIN_FILES[domain].some(({ key }) => files[key]);
    if (!anyFile) return;
    setLoading(true); setError(null); setReport(null);
    try {
      const res = await fetch(`${API}/validate`, { method: "POST", body: buildFormData(domain, files) });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || `HTTP ${res.status}`); }
      const data = await res.json();
      setReport(data);
      addRun({ ...data, domain });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExportCsv() {
    const res = await fetch(`${API}/validate/export-csv`, { method: "POST", body: buildFormData(domain, files) });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url;
    a.download = `validation_errors_${domain}.csv`;
    a.click(); URL.revokeObjectURL(url);
  }

  const canSubmit = !loading && DOMAIN_FILES[domain].some(({ key }) => files[key]);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Validator</h1>
        <p className="text-xs text-slate-400 mt-0.5">Upload migration Excel files to validate against all business rules</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 items-start">
        {/* Configuration card */}
        <Card className="xl:col-span-1">
          <CardHeader>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Configuration</span>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Domain */}
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Domain</label>
                <Select value={domain} onValueChange={handleDomainChange}>
                  <SelectTrigger aria-label="Select domain"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {DOMAINS.map(d => <SelectItem key={d} value={d}>{d}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>

              {/* File zones */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Files</label>
                {DOMAIN_FILES[domain].map(({ key, label }) => (
                  <FileDropZone key={key} label={`${label} (.xlsx)`} file={files[key] ?? null} onFile={f => setFile(key, f)} />
                ))}
              </div>

              <Button type="submit" disabled={!canSubmit} className="w-full" size="md">
                {loading ? (
                  <><span className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Validating…</>
                ) : "Run Validation"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Recent runs */}
        <Card className="xl:col-span-1">
          <CardHeader>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Recent Runs</span>
            {runs.length > 0 && <span className="text-xs text-slate-400">{runs.length} total</span>}
          </CardHeader>
          <CardContent className="p-0">
            {runs.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-slate-400">No runs yet.</p>
            ) : (
              <div className="divide-y divide-slate-50 dark:divide-slate-800/50 max-h-72 overflow-y-auto">
                {runs.slice(0, 12).map(run => (
                  <button
                    key={run.id}
                    className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800/30 text-left transition-colors"
                    onClick={() => setDomain(run.domain)}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${run.total_errors === 0 ? "bg-success-500" : "bg-danger-500"}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 dark:text-slate-300 truncate">{run.legal_entity || "—"}</p>
                      <p className="text-xs text-slate-400">{run.domain} · {fmt(run.timestamp)}</p>
                    </div>
                    <Badge variant={run.total_errors === 0 ? "success" : "danger"} className="flex-shrink-0 tabular-nums">
                      {run.total_errors === 0 ? "Clean" : run.total_errors}
                    </Badge>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        {(error || report) && (
          <div className="xl:col-span-3 space-y-4">
            {error && (
              <div className="flex items-start gap-2.5 rounded-md border border-danger-100 dark:border-red-800/40 bg-danger-50 dark:bg-red-900/20 px-4 py-3 text-sm text-danger-700 dark:text-red-400">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {report && (
              <div className="space-y-4">
                {/* Warnings */}
                {report.warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-2.5 rounded-md border border-warning-100 dark:border-yellow-800/40 bg-warning-50 dark:bg-yellow-900/20 px-4 py-3 text-sm text-warning-500 dark:text-yellow-300">
                    <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" /> {w}
                  </div>
                ))}

                {/* Metrics strip */}
                <div className="grid grid-cols-4 divide-x divide-slate-200 dark:divide-slate-700 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900">
                  {[
                    { label: "Total rows",   value: report.total_rows },
                    { label: "Global rows",  value: report.global_row_count },
                    { label: "Local rows",   value: report.local_row_count },
                    { label: "Total errors", value: report.total_errors, danger: report.total_errors > 0, accent: report.total_errors === 0 },
                  ].map(({ label, value, danger, accent }) => (
                    <div key={label} className="px-5 py-3">
                      <p className="text-xs text-slate-500 dark:text-slate-400 mb-0.5">{label}</p>
                      <p className={
                        "text-xl font-semibold " +
                        (danger ? "text-danger-500" : accent ? "text-success-500" : "text-slate-800 dark:text-slate-100")
                      }>{value}</p>
                    </div>
                  ))}
                </div>

                {/* Errors by rule */}
                {Object.keys(report.errors_by_rule).length > 0 && (
                  <Card>
                    <CardHeader>
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Errors by Rule</span>
                      {report.total_errors > 0 && (
                        <Button size="sm" variant="outline" onClick={handleExportCsv}>
                          <Download className="h-3.5 w-3.5" /> Download CSV
                        </Button>
                      )}
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(report.errors_by_rule).sort((a, b) => b[1] - a[1]).map(([rule, count]) => (
                          <div key={rule} className="flex items-center gap-3">
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-slate-700 dark:text-slate-300 truncate">{rule}</p>
                              <div className="mt-1 h-1 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-danger-500 rounded-full transition-all"
                                  style={{ width: `${(count / report.total_errors) * 100}%` }}
                                />
                              </div>
                            </div>
                            <Badge variant="danger" className="flex-shrink-0 tabular-nums">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Error table */}
                <Card>
                  <CardHeader>
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Detailed Errors</span>
                  </CardHeader>
                  <CardContent>
                    {report.errors.length === 0 ? (
                      <div className="flex items-center gap-2.5 rounded-md border border-success-100 dark:border-green-800/40 bg-success-50 dark:bg-green-900/20 px-4 py-3 text-sm text-success-500 dark:text-green-400">
                        <CheckCircle2 className="h-4 w-4 flex-shrink-0" /> All rules passed — no errors found.
                      </div>
                    ) : (
                      <ErrorTable errors={report.errors} />
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
