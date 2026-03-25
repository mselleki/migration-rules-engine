import { useCallback, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  FileSpreadsheet,
  Layers2,
  Loader2,
  Rows3,
  ShoppingCart,
  Upload,
  X,
} from "lucide-react";
import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select.jsx";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs.jsx";
import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  useReactTable,
} from "@tanstack/react-table";
import API from "../api.js";

const ERP_TYPES = ["Jeeves", "Prophet"];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtBytes(b) {
  if (!b) return "";
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
}

// ─── File drop zone ───────────────────────────────────────────────────────────

function FileZone({ label, sublabel, file, onFile, accept = ".xlsx" }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const f = e.dataTransfer.files?.[0];
      if (f) onFile(f);
    },
    [onFile],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${label} — drop zone`}
      onClick={() => !file && inputRef.current.click()}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={[
        "relative flex items-start gap-2.5 rounded-md border border-dashed p-3 transition-colors",
        dragging
          ? "cursor-copy border-brand-500 bg-brand-50 dark:bg-brand-900/20"
          : file
            ? "cursor-default border-success-500 bg-success-50 dark:bg-green-900/10"
            : "cursor-pointer border-slate-200 hover:border-brand-400 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/40",
      ].join(" ")}
    >
      <FileSpreadsheet
        className={`mt-0.5 h-4 w-4 flex-shrink-0 ${file ? "text-success-500" : "text-slate-400"}`}
      />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-slate-700 dark:text-slate-300 leading-tight">
          {label}
        </p>
        {sublabel && (
          <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">
            {sublabel}
          </p>
        )}
        {file ? (
          <p className="text-[11px] text-success-600 dark:text-green-400 mt-1 truncate">
            {file.name} · {fmtBytes(file.size)}
          </p>
        ) : (
          <p className="text-[11px] text-slate-400 mt-0.5">
            Drop {accept} or click to browse
          </p>
        )}
      </div>
      {file ? (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onFile(null);
          }}
          className="mt-0.5 p-0.5 rounded hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-400 transition-colors flex-shrink-0"
          aria-label="Remove file"
        >
          <X className="h-3 w-3" />
        </button>
      ) : (
        <Upload className="mt-0.5 h-3 w-3 text-slate-300 flex-shrink-0" />
      )}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}

// ─── Metrics strip ────────────────────────────────────────────────────────────

function MetricCard({ label, value, highlight }) {
  return (
    <div className="flex flex-col gap-0.5 px-4 py-3 border-r last:border-0 border-slate-100 dark:border-slate-700/60">
      <span
        className={`text-xl font-bold tabular-nums ${highlight ? "text-danger-500" : "text-slate-800 dark:text-slate-100"}`}
      >
        {value.toLocaleString()}
      </span>
      <span className="text-[11px] text-slate-500 dark:text-slate-400">
        {label}
      </span>
    </div>
  );
}

// ─── Reconciliation table ──────────────────────────────────────────────────────

const STATUS_FILTER_OPTIONS = [
  { value: "all", label: "All" },
  { value: "in_all", label: "In all 3" },
  { value: "missing_stibo", label: "Missing STIBO" },
  { value: "missing_ct", label: "Missing CT" },
  { value: "missing_erp", label: "Missing ERP" },
];

function absenceBadge(absent) {
  if (absent === "-")
    return (
      <Badge
        variant="secondary"
        className="bg-success-50 text-success-700 border-success-200 dark:bg-green-900/20 dark:text-green-400"
      >
        ✓ In all 3
      </Badge>
    );
  const count = absent.split(",").length;
  return (
    <Badge
      variant="secondary"
      className={
        count >= 2
          ? "bg-danger-50 text-danger-700 border-danger-200 dark:bg-red-900/20 dark:text-red-400"
          : "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400"
      }
    >
      {absent}
    </Badge>
  );
}

function presenceCell(val) {
  return val === "X" ? (
    <span className="text-success-600 dark:text-success-400 font-bold text-sm">
      ✓
    </span>
  ) : (
    <span className="text-slate-300 dark:text-slate-600 text-sm">—</span>
  );
}

function ReconcTable({ rows, codeColumn, erpName, filterStatus, searchValue }) {
  const filtered = useMemo(() => {
    let data = rows;
    if (filterStatus === "in_all")
      data = data.filter((r) => r.Absent_from === "-");
    else if (filterStatus === "missing_stibo")
      data = data.filter((r) => r.STIBO === "");
    else if (filterStatus === "missing_ct")
      data = data.filter((r) => r.CT === "");
    else if (filterStatus === "missing_erp")
      data = data.filter((r) => r[erpName] === "");

    if (searchValue.trim()) {
      const q = searchValue.trim().toLowerCase();
      data = data.filter((r) =>
        String(r[codeColumn]).toLowerCase().includes(q),
      );
    }
    return data;
  }, [rows, filterStatus, searchValue, codeColumn, erpName]);

  const columns = useMemo(
    () => [
      {
        accessorKey: codeColumn,
        header: codeColumn,
        size: 160,
        cell: (i) => (
          <span className="font-mono text-xs text-slate-800 dark:text-slate-200">
            {i.getValue()}
          </span>
        ),
      },
      {
        accessorKey: "CT",
        header: "CT",
        size: 60,
        cell: (i) => presenceCell(i.getValue()),
      },
      {
        accessorKey: erpName,
        header: erpName,
        size: 80,
        cell: (i) => presenceCell(i.getValue()),
      },
      {
        accessorKey: "STIBO",
        header: "STIBO",
        size: 70,
        cell: (i) => presenceCell(i.getValue()),
      },
      {
        accessorKey: "Absent_from",
        header: "Status",
        size: undefined,
        cell: (i) => absenceBadge(i.getValue()),
      },
    ],
    [codeColumn, erpName],
  );

  const table = useReactTable({
    data: filtered,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 100 } },
  });

  if (filtered.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-slate-400">
        No rows match the current filter.
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-700">
        <table className="w-full text-sm border-collapse">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr
                key={hg.id}
                className="border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50"
              >
                {hg.headers.map((h) => (
                  <th
                    key={h.id}
                    className="px-3 py-2 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 whitespace-nowrap"
                    style={{
                      width:
                        h.column.getSize() !== undefined
                          ? h.column.getSize()
                          : undefined,
                    }}
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50/60 dark:hover:bg-slate-800/30 transition-colors"
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-2">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
        <span>
          {filtered.length.toLocaleString()} row
          {filtered.length !== 1 ? "s" : ""}
          {filtered.length !== rows.length &&
            ` (filtered from ${rows.length.toLocaleString()})`}
        </span>
        {table.getPageCount() > 1 && (
          <div className="flex items-center gap-1">
            <button
              disabled={!table.getCanPreviousPage()}
              onClick={() => table.previousPage()}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              ‹ Prev
            </button>
            <span>
              Page {table.getState().pagination.pageIndex + 1} /{" "}
              {table.getPageCount()}
            </span>
            <button
              disabled={!table.getCanNextPage()}
              onClick={() => table.nextPage()}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Next ›
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Invoice/OS entity section ────────────────────────────────────────────────

function EntitySection({ title, data, erpName }) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const effectiveFilter = filter;

  const metrics = data.metrics;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          {title}
        </h4>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1">
            {[
              "all",
              "in_all",
              "missing_stibo",
              "missing_ct",
              "missing_erp",
            ].map((v) => (
              <button
                key={v}
                onClick={() => setFilter(v)}
                className={[
                  "px-2 py-0.5 rounded text-[11px] font-medium border transition-colors",
                  filter === v
                    ? "bg-brand-500 text-white border-brand-500"
                    : "border-slate-200 text-slate-500 hover:border-brand-300 dark:border-slate-700 dark:text-slate-400",
                ].join(" ")}
              >
                {v === "all"
                  ? "All"
                  : v === "in_all"
                    ? "In all 3"
                    : v === "missing_stibo"
                      ? "−STIBO"
                      : v === "missing_ct"
                        ? "−CT"
                        : `−${erpName}`}
              </button>
            ))}
          </div>
          <input
            type="text"
            placeholder="Search code…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-7 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-xs text-slate-700 dark:text-slate-300 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-400 w-36"
          />
        </div>
      </div>

      <div className="flex rounded-md border border-slate-100 dark:border-slate-700/60 divide-x divide-slate-100 dark:divide-slate-700/60 overflow-hidden bg-white dark:bg-slate-900">
        <MetricCard label="Total" value={metrics.total} />
        <MetricCard label="In all 3" value={metrics.in_all_3} />
        <MetricCard
          label="Missing STIBO"
          value={metrics.missing_stibo}
          highlight={metrics.missing_stibo > 0}
        />
        <MetricCard
          label="Missing CT"
          value={metrics.missing_ct}
          highlight={metrics.missing_ct > 0}
        />
        <MetricCard
          label={`Missing ${erpName}`}
          value={metrics.missing_erp}
          highlight={metrics.missing_erp > 0}
        />
      </div>

      <ReconcTable
        rows={data.rows}
        codeColumn="Code"
        erpName={erpName}
        filterStatus={effectiveFilter}
        searchValue={search}
      />
    </div>
  );
}

// ─── Product tab ──────────────────────────────────────────────────────────────

function ProductTab() {
  const [erpType, setErpType] = useState("Jeeves");
  const [files, setFiles] = useState({ ct: null, erp: null, stibo: null });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const setFile = (key) => (f) => setFiles((prev) => ({ ...prev, [key]: f }));
  const canRun = files.ct && files.erp && files.stibo;

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("erp_type", erpType);
      fd.append("ct_file", files.ct);
      fd.append("erp_file", files.erp);
      fd.append("stibo_file", files.stibo);
      const res = await fetch(`${API}/reconcile/product`, {
        method: "POST",
        body: fd,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || res.statusText);
      setResult(json);
      setFilter("all");
      setSearch("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const erpName = result?.erp_name ?? erpType;
  const m = result?.metrics;

  return (
    <div className="space-y-5">
      {/* Config */}
      <div className="space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
              ERP
            </span>
            <Select value={erpType} onValueChange={setErpType}>
              <SelectTrigger className="h-8 w-32 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ERP_TYPES.map((t) => (
                  <SelectItem key={t} value={t} className="text-xs">
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <FileZone
            label="CT Product"
            sublabel="Headers row 6, data from B7 (.xlsx or .xlsb)"
            file={files.ct}
            onFile={setFile("ct")}
            accept=".xlsx,.xlsb"
          />
          <FileZone
            label={`${erpType} Product`}
            sublabel={
              erpType === "Jeeves"
                ? "Sheet '2-EXCELMASTER', col A from row 3"
                : "Row 2 headers, 'FD Product Code' column"
            }
            file={files.erp}
            onFile={setFile("erp")}
          />
          <FileZone
            label="STIBO Product"
            sublabel="Headers row 1, SUPC column from row 2"
            file={files.stibo}
            onFile={setFile("stibo")}
          />
        </div>

        <Button
          onClick={run}
          disabled={!canRun || loading}
          className="h-8 text-xs gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Running…
            </>
          ) : (
            "Run Reconciliation"
          )}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-md border border-danger-200 bg-danger-50 dark:bg-red-900/20 dark:border-red-800 px-3 py-2.5 text-sm text-danger-700 dark:text-red-400">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Metrics */}
          <div className="flex rounded-md border border-slate-100 dark:border-slate-700/60 divide-x divide-slate-100 dark:divide-slate-700/60 overflow-hidden bg-white dark:bg-slate-900">
            <MetricCard label="Total unique" value={m.total} />
            <MetricCard label="In all 3" value={m.in_all_3} />
            <MetricCard label="CT" value={m.ct_count} />
            <MetricCard label={erpName} value={m.erp_count} />
            <MetricCard label="STIBO" value={m.stibo_count} />
            <MetricCard
              label="Missing STIBO"
              value={m.missing_stibo}
              highlight={m.missing_stibo > 0}
            />
            <MetricCard
              label={`Missing ${erpName}`}
              value={m.missing_erp}
              highlight={m.missing_erp > 0}
            />
            <MetricCard
              label="Missing CT"
              value={m.missing_ct}
              highlight={m.missing_ct > 0}
            />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1">
              {STATUS_FILTER_OPTIONS.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setFilter(value)}
                  className={[
                    "px-2.5 py-1 rounded text-xs font-medium border transition-colors",
                    filter === value
                      ? "bg-brand-500 text-white border-brand-500"
                      : "border-slate-200 text-slate-500 hover:border-brand-300 dark:border-slate-700 dark:text-slate-400",
                  ].join(" ")}
                >
                  {label === "Missing ERP" ? `Missing ${erpName}` : label}
                </button>
              ))}
            </div>
            <input
              type="text"
              placeholder="Search product code…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-7 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-xs text-slate-700 dark:text-slate-300 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-400 w-44"
            />
          </div>

          <ReconcTable
            rows={result.rows}
            codeColumn="ProductCode"
            erpName={erpName}
            filterStatus={filter}
            searchValue={search}
          />
        </div>
      )}
    </div>
  );
}

// ─── Vendor / Customer tab ────────────────────────────────────────────────────

const INVOICE_OS_FILES = [
  {
    key: "ct_vendor_file",
    label: "CT Vendor",
    sublabel: "Sheet 'Invoice' + 'OrderingShipping', col C/D from row 8",
  },
  {
    key: "ct_customer_file",
    label: "CT Customer",
    sublabel: "Sheet 'Invoice' + 'OrderingShipping', col C/D from row 8",
  },
  {
    key: "erp_vendor_file",
    label: "ERP Vendor",
    sublabel: "Vendor invoice + OS (Jeeves: same file with 2 sheets)",
  },
  {
    key: "erp_customer_file",
    label: "ERP Customer",
    sublabel: "Customer invoice + OS (Jeeves: INVOICECUSTOMER sheet)",
  },
  {
    key: "stibo_vendor_invoice",
    label: "STIBO Vendor Invoice",
    sublabel: "SUVC Invoice column, or 'Invoice' sheet",
  },
  {
    key: "stibo_vendor_os",
    label: "STIBO Vendor OS",
    sublabel: "SUVC Ordering/Shipping col, or 'Ordering-Shipping' sheet",
  },
  {
    key: "stibo_customer_invoice",
    label: "STIBO Customer Invoice",
    sublabel: "Invoice Customer Code column, or 'Invoice' sheet",
  },
  {
    key: "stibo_customer_os",
    label: "STIBO Customer OS",
    sublabel: "OS column, or 'Ordering-Shipping' sheet",
  },
];

function VendorCustomerTab() {
  const [erpType, setErpType] = useState("Jeeves");
  const [files, setFiles] = useState(
    Object.fromEntries(INVOICE_OS_FILES.map((f) => [f.key, null])),
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const setFile = (key) => (f) => setFiles((prev) => ({ ...prev, [key]: f }));
  const hasAny = Object.values(files).some(Boolean);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("erp_type", erpType);
      for (const { key } of INVOICE_OS_FILES) {
        if (files[key]) fd.append(key, files[key]);
      }
      const res = await fetch(`${API}/reconcile/invoice-os`, {
        method: "POST",
        body: fd,
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || res.statusText);
      setResult(json);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const erpName = result?.erp_name ?? erpType;

  return (
    <div className="space-y-5">
      {/* Config */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
            ERP
          </span>
          <Select value={erpType} onValueChange={setErpType}>
            <SelectTrigger className="h-8 w-32 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ERP_TYPES.map((t) => (
                <SelectItem key={t} value={t} className="text-xs">
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {INVOICE_OS_FILES.map(({ key, label, sublabel }) => (
            <FileZone
              key={key}
              label={label.replace("ERP", erpType)}
              sublabel={sublabel}
              file={files[key]}
              onFile={setFile(key)}
            />
          ))}
        </div>

        <Button
          onClick={run}
          disabled={!hasAny || loading}
          className="h-8 text-xs gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Running…
            </>
          ) : (
            "Run Reconciliation"
          )}
        </Button>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-danger-200 bg-danger-50 dark:bg-red-900/20 dark:border-red-800 px-3 py-2.5 text-sm text-danger-700 dark:text-red-400">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {result && (
        <Tabs defaultValue="invoice" className="w-full">
          <TabsList className="w-full justify-start rounded-none border-0 bg-transparent p-0 h-auto border-b border-slate-200 dark:border-slate-700 mb-4">
            <TabsTrigger value="invoice" className="gap-2 rounded-none">
              Invoice
            </TabsTrigger>
            <TabsTrigger value="os" className="gap-2 rounded-none">
              Ordering-Shipping
            </TabsTrigger>
          </TabsList>

          <TabsContent value="invoice" className="mt-0 space-y-6">
            <EntitySection
              title="Vendor Invoice"
              data={result.invoice.vendor}
              erpName={erpName}
            />
            <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
              <EntitySection
                title="Customer Invoice"
                data={result.invoice.customer}
                erpName={erpName}
              />
            </div>
          </TabsContent>

          <TabsContent value="os" className="mt-0 space-y-6">
            <EntitySection
              title="Vendor Ordering-Shipping"
              data={result.ordering_shipping.vendor}
              erpName={erpName}
            />
            <div className="border-t border-slate-200 dark:border-slate-700 pt-6">
              <EntitySection
                title="Customer Ordering-Shipping"
                data={result.ordering_shipping.customer}
                erpName={erpName}
              />
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Reconciliations() {
  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-400">
          <Layers2 className="h-5 w-5" aria-hidden />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Reconciliations
          </h1>
          <p className="mt-0.5 max-w-3xl text-xs text-slate-500 dark:text-slate-400">
            Compare product codes and vendor/customer codes across three
            sources:{" "}
            <span className="font-medium text-slate-600 dark:text-slate-300">
              CT
            </span>
            ,{" "}
            <span className="font-medium text-slate-600 dark:text-slate-300">
              ERP
            </span>
            , and{" "}
            <span className="font-medium text-slate-600 dark:text-slate-300">
              STIBO
            </span>
            . Upload your extract files and run the reconciliation to identify
            gaps.
          </p>
        </div>
      </div>

      <Card>
        <Tabs defaultValue="product" className="w-full">
          <CardHeader className="pb-0">
            <TabsList className="w-full justify-start rounded-none border-0 bg-transparent p-0 h-auto">
              <TabsTrigger value="product" className="gap-2 rounded-none">
                <Rows3 className="h-4 w-4 opacity-70" aria-hidden />
                Product (Range)
              </TabsTrigger>
              <TabsTrigger
                value="vendor-customer"
                className="gap-2 rounded-none"
              >
                <ShoppingCart className="h-4 w-4 opacity-70" aria-hidden />
                Vendor / Customer
              </TabsTrigger>
            </TabsList>
          </CardHeader>
          <CardContent className="pt-5">
            <TabsContent value="product" className="mt-0">
              <ProductTab />
            </TabsContent>
            <TabsContent value="vendor-customer" className="mt-0">
              <VendorCustomerTab />
            </TabsContent>
          </CardContent>
        </Tabs>
      </Card>
    </div>
  );
}
