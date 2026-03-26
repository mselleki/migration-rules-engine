import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Layers2,
  Loader2,
  RotateCcw,
  Rows3,
  Settings,
  ShoppingCart,
  User,
  X,
} from "lucide-react";
import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
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

// ─── Constants ────────────────────────────────────────────────────────────────

const LEGAL_ENTITIES = [
  "Brakes",
  "Classic_Drinks",
  "Ekofisk",
  "Fresh_Direct",
  "Fruktservice",
  "KFF",
  "LAG",
  "Medina",
  "Menigo",
  "Ready_Chef",
  "Servicestyckarna",
  "Sysco_France",
  "Sysco_Northern_Ireland",
  "Sysco_ROI",
];

const DOMAINS = ["Product", "Vendor", "Customer"];

const DOMAIN_ICONS = {
  Product: Rows3,
  Vendor: ShoppingCart,
  Customer: User,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt(ts) {
  if (!ts) return "";
  return new Date(ts * 1000).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ─── Market multi-select ─────────────────────────────────────────────────────

function MarketMultiSelect({ selected, onChange }) {
  const [open, setOpen] = useState(false);
  const ref = useRef();

  useEffect(() => {
    function onOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, [open]);

  function toggle(entity) {
    if (selected.includes(entity))
      onChange(selected.filter((e) => e !== entity));
    else onChange([...selected, entity]);
  }

  function selectAll() {
    onChange(LEGAL_ENTITIES);
  }
  function clearAll() {
    onChange([]);
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={[
          "flex h-9 min-w-[220px] items-center justify-between gap-2 rounded-md border px-3 text-sm transition-colors",
          open
            ? "border-brand-400 ring-1 ring-brand-300 dark:ring-brand-700"
            : "border-slate-200 dark:border-slate-700 hover:border-brand-300",
          "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300",
        ].join(" ")}
      >
        <span className="truncate">
          {selected.length === 0
            ? "Select markets…"
            : selected.length === LEGAL_ENTITIES.length
              ? "All markets"
              : selected.length === 1
                ? selected[0]
                : `${selected.length} markets selected`}
        </span>
        <ChevronDown
          className={`h-4 w-4 flex-shrink-0 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-64 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-lg">
          <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100 dark:border-slate-800">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
              {selected.length} / {LEGAL_ENTITIES.length}
            </span>
            <div className="flex gap-2">
              <button
                onClick={selectAll}
                className="text-[11px] text-brand-500 hover:underline"
              >
                All
              </button>
              <button
                onClick={clearAll}
                className="text-[11px] text-slate-400 hover:underline"
              >
                Clear
              </button>
            </div>
          </div>
          <div className="max-h-56 overflow-y-auto py-1">
            {LEGAL_ENTITIES.map((entity) => {
              const checked = selected.includes(entity);
              return (
                <label
                  key={entity}
                  className="flex cursor-pointer items-center gap-2.5 px-3 py-1.5 hover:bg-slate-50 dark:hover:bg-slate-800/60"
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggle(entity)}
                    className="h-3.5 w-3.5 accent-brand-500"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    {entity}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* Selected chips */}
      {selected.length > 0 && selected.length < LEGAL_ENTITIES.length && (
        <div className="mt-2 flex flex-wrap gap-1">
          {selected.map((e) => (
            <span
              key={e}
              className="inline-flex items-center gap-1 rounded bg-brand-50 dark:bg-brand-900/30 px-1.5 py-0.5 text-[11px] font-medium text-brand-700 dark:text-brand-300"
            >
              {e}
              <button
                onClick={() => toggle(e)}
                className="text-brand-400 hover:text-brand-600"
              >
                <X className="h-2.5 w-2.5" />
              </button>
            </span>
          ))}
        </div>
      )}
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
        {typeof value === "number" ? value.toLocaleString() : value}
      </span>
      <span className="text-[11px] text-slate-500 dark:text-slate-400">
        {label}
      </span>
    </div>
  );
}

function MetricsRow({ metrics, erpName }) {
  return (
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
  );
}

// ─── Reconciliation table ─────────────────────────────────────────────────────

function presenceCell(val) {
  return val === "X" ? (
    <span className="text-success-600 dark:text-success-400 font-bold">✓</span>
  ) : (
    <span className="text-slate-300 dark:text-slate-600">—</span>
  );
}

function AbsentBadge({ value }) {
  if (value === "-")
    return (
      <Badge
        variant="secondary"
        className="bg-success-50 text-success-700 border-success-200 dark:bg-green-900/20 dark:text-green-400"
      >
        ✓ In all 3
      </Badge>
    );
  const count = value.split(",").length;
  return (
    <Badge
      variant="secondary"
      className={
        count >= 2
          ? "bg-danger-50 text-danger-700 border-danger-200 dark:bg-red-900/20 dark:text-red-400"
          : "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400"
      }
    >
      {value}
    </Badge>
  );
}

const FILTER_OPTS = [
  { value: "all", label: "All" },
  { value: "in_all", label: "In all 3" },
  { value: "missing_stibo", label: "−STIBO" },
  { value: "missing_ct", label: "−CT" },
  { value: "missing_erp", label: "−ERP" },
];

function ReconcTable({ rows, codeKey, erpName }) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const data = useMemo(() => {
    let d = rows;
    if (filter === "in_all") d = d.filter((r) => r.Absent_from === "-");
    else if (filter === "missing_stibo") d = d.filter((r) => r.STIBO === "");
    else if (filter === "missing_ct") d = d.filter((r) => r.CT === "");
    else if (filter === "missing_erp") d = d.filter((r) => r[erpName] === "");
    if (search.trim()) {
      const q = search.toLowerCase();
      d = d.filter((r) => String(r[codeKey]).toLowerCase().includes(q));
    }
    return d;
  }, [rows, filter, search, codeKey, erpName]);

  const columns = useMemo(
    () => [
      {
        accessorKey: codeKey,
        header: codeKey,
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
        size: 55,
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
        size: 65,
        cell: (i) => presenceCell(i.getValue()),
      },
      {
        accessorKey: "Absent_from",
        header: "Status",
        cell: (i) => <AbsentBadge value={i.getValue()} />,
      },
    ],
    [codeKey, erpName],
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 100 } },
  });

  if (rows.length === 0)
    return (
      <p className="py-6 text-center text-sm text-slate-400">
        No data — check SharePoint configuration or uploaded files.
      </p>
    );

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex gap-1">
          {FILTER_OPTS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={[
                "px-2 py-0.5 rounded text-[11px] font-medium border transition-colors",
                filter === value
                  ? "bg-brand-500 text-white border-brand-500"
                  : "border-slate-200 text-slate-500 hover:border-brand-300 dark:border-slate-700 dark:text-slate-400",
              ].join(" ")}
            >
              {label === "−ERP" ? `−${erpName}` : label}
            </button>
          ))}
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search code…"
          className="h-7 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-xs placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-400 w-36"
        />
      </div>

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
                    style={{ width: h.column.getSize() }}
                    className="px-3 py-2 text-left text-xs font-semibold text-slate-500 dark:text-slate-400"
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
                  <td key={cell.id} className="px-3 py-1.5">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>
          {data.length.toLocaleString()} row{data.length !== 1 ? "s" : ""}
          {data.length !== rows.length &&
            ` (filtered from ${rows.length.toLocaleString()})`}
        </span>
        {table.getPageCount() > 1 && (
          <div className="flex items-center gap-1">
            <button
              disabled={!table.getCanPreviousPage()}
              onClick={() => table.previousPage()}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              ‹
            </button>
            <span>
              {table.getState().pagination.pageIndex + 1}/{table.getPageCount()}
            </span>
            <button
              disabled={!table.getCanNextPage()}
              onClick={() => table.nextPage()}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              ›
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Result views ─────────────────────────────────────────────────────────────

function ProductResult({ result }) {
  const erpName = result.erp_name;
  return (
    <div className="space-y-3">
      <MetricsRow metrics={result.metrics} erpName={erpName} />
      <ReconcTable rows={result.rows} codeKey="ProductCode" erpName={erpName} />
    </div>
  );
}

function InvoiceOsResult({ result }) {
  const erpName = result.erp_name;
  return (
    <Tabs defaultValue="invoice" className="w-full">
      <TabsList className="w-full justify-start rounded-none border-0 bg-transparent p-0 h-auto border-b border-slate-200 dark:border-slate-700 mb-4">
        <TabsTrigger value="invoice" className="rounded-none text-xs">
          Invoice
        </TabsTrigger>
        <TabsTrigger value="os" className="rounded-none text-xs">
          Ordering-Shipping
        </TabsTrigger>
      </TabsList>
      <TabsContent value="invoice" className="mt-0 space-y-3">
        <MetricsRow metrics={result.invoice.metrics} erpName={erpName} />
        <ReconcTable
          rows={result.invoice.rows}
          codeKey="Code"
          erpName={erpName}
        />
      </TabsContent>
      <TabsContent value="os" className="mt-0 space-y-3">
        <MetricsRow
          metrics={result.ordering_shipping.metrics}
          erpName={erpName}
        />
        <ReconcTable
          rows={result.ordering_shipping.rows}
          codeKey="Code"
          erpName={erpName}
        />
      </TabsContent>
    </Tabs>
  );
}

function MarketResult({ market, domain, result, warnings, error }) {
  if (error)
    return (
      <div className="flex items-start gap-2 rounded-md border border-danger-200 bg-danger-50 dark:border-red-800 dark:bg-red-900/20 px-3 py-2.5 text-sm text-danger-700 dark:text-red-400">
        <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
        {error}
      </div>
    );

  return (
    <div className="space-y-3">
      {warnings?.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20 px-3 py-2 space-y-0.5">
          {warnings.map((w, i) => (
            <div
              key={i}
              className="flex items-start gap-1.5 text-xs text-amber-700 dark:text-amber-400"
            >
              <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0" />
              {w}
            </div>
          ))}
        </div>
      )}
      {domain === "Product" ? (
        <ProductResult result={result} />
      ) : (
        <InvoiceOsResult result={result} />
      )}
    </div>
  );
}

function RunResults({ runData }) {
  const { domain, markets, results, warnings, errors } = runData;

  if (markets.length === 1) {
    const m = markets[0];
    return (
      <MarketResult
        market={m}
        domain={domain}
        result={results[m]}
        warnings={warnings[m]}
        error={errors[m]}
      />
    );
  }

  return (
    <Tabs defaultValue={markets[0]} className="w-full">
      <TabsList className="w-full justify-start rounded-none border-0 bg-transparent p-0 h-auto border-b border-slate-200 dark:border-slate-700 mb-4 flex-wrap gap-y-1">
        {markets.map((m) => (
          <TabsTrigger
            key={m}
            value={m}
            className="rounded-none text-xs gap-1.5"
          >
            {m}
            {errors[m] && <AlertCircle className="h-3 w-3 text-danger-500" />}
            {warnings[m]?.length > 0 && !errors[m] && (
              <AlertTriangle className="h-3 w-3 text-amber-500" />
            )}
          </TabsTrigger>
        ))}
      </TabsList>
      {markets.map((m) => (
        <TabsContent key={m} value={m} className="mt-0">
          <MarketResult
            market={m}
            domain={domain}
            result={results[m]}
            warnings={warnings[m]}
            error={errors[m]}
          />
        </TabsContent>
      ))}
    </Tabs>
  );
}

// ─── Config status indicator ──────────────────────────────────────────────────

function ConfigWarnings({ markets, domain }) {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!markets.length) return;
    fetch(`${API}/reconcile/config`)
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => {});
  }, [markets, domain]);

  if (!status || !markets.length) return null;

  const missing = [];
  for (const m of markets) {
    if (!status[m]) continue;
    const d = status[m][domain];
    if (!d) continue;
    for (const src of ["ct", "erp", "stibo"]) {
      if (!d[src]) missing.push(`${m} — ${src.toUpperCase()} ${domain}`);
    }
  }

  if (!missing.length) return null;

  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-900/20 px-3 py-2 space-y-0.5">
      <p className="text-xs font-medium text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
        <AlertTriangle className="h-3.5 w-3.5" />
        SharePoint URLs not yet configured — these sources will return 0 codes:
      </p>
      <ul className="mt-1 space-y-0.5">
        {missing.map((m) => (
          <li
            key={m}
            className="text-[11px] text-amber-600 dark:text-amber-500 pl-5"
          >
            {m}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─── History tab ─────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const cls =
    status === "completed"
      ? "bg-success-50 text-success-700 border-success-200 dark:bg-green-900/20 dark:text-green-400"
      : status === "partial"
        ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400"
        : "bg-danger-50 text-danger-700 border-danger-200 dark:bg-red-900/20 dark:text-red-400";
  return (
    <Badge variant="secondary" className={cls}>
      {status}
    </Badge>
  );
}

function HistoryRow({ run, onReopen }) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  async function expand() {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (!detail) {
      setLoading(true);
      try {
        const res = await fetch(`${API}/reconcile/history/${run.id}`);
        const json = await res.json();
        setDetail(json);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    }
  }

  const DomainIcon = DOMAIN_ICONS[run.domain] ?? Rows3;

  return (
    <div className="border-b border-slate-100 dark:border-slate-800 last:border-0">
      <div
        className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50/60 dark:hover:bg-slate-800/30 cursor-pointer transition-colors"
        onClick={expand}
      >
        <ChevronRight
          className={`h-4 w-4 text-slate-400 flex-shrink-0 transition-transform ${expanded ? "rotate-90" : ""}`}
        />
        <div className="flex items-center gap-2 flex-1 min-w-0 flex-wrap gap-y-1">
          <span className="text-xs font-mono text-slate-400 flex-shrink-0">
            {fmt(run.created_at)}
          </span>
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
            {run.user_name}
          </span>
          <div className="flex items-center gap-1 flex-shrink-0">
            <DomainIcon className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-xs text-slate-500">{run.domain}</span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] px-1.5 py-0.5 flex-shrink-0"
          >
            {run.rec_type}
          </Badge>
          <StatusBadge status={run.status} />
          <div className="flex flex-wrap gap-1">
            {run.markets.map((m) => (
              <span
                key={m}
                className="text-[10px] rounded bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 text-slate-500 dark:text-slate-400"
              >
                {m}
              </span>
            ))}
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onReopen(run);
          }}
          title="Reload in Run tab"
          className="p-1 rounded text-slate-400 hover:text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-900/20 transition-colors flex-shrink-0"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-4">
          {loading ? (
            <div className="flex items-center gap-2 py-4 text-sm text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading results…
            </div>
          ) : detail ? (
            <RunResults runData={detail} />
          ) : (
            <p className="py-4 text-sm text-slate-400">
              Could not load results.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function HistoryTab({ onReopen }) {
  const [runs, setRuns] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/reconcile/history?limit=50`);
      setRuns(await res.json());
    } catch {
      setRuns([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Last 50 reconciliation runs. Click a row to expand results.
        </p>
        <Button
          variant="ghost"
          size="sm"
          onClick={load}
          disabled={loading}
          className="h-7 gap-1.5 text-xs"
        >
          <RotateCcw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {loading && !runs && (
        <div className="flex items-center gap-2 py-8 justify-center text-sm text-slate-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading history…
        </div>
      )}

      {runs !== null &&
        (runs.length === 0 ? (
          <div className="py-10 text-center">
            <Clock className="h-8 w-8 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-400">
              No reconciliation runs yet.
            </p>
          </div>
        ) : (
          <div className="rounded-md border border-slate-200 dark:border-slate-700 overflow-hidden">
            {runs.map((run) => (
              <HistoryRow key={run.id} run={run} onReopen={onReopen} />
            ))}
          </div>
        ))}
    </div>
  );
}

// ─── Run tab ──────────────────────────────────────────────────────────────────

function RunTab({ prefill }) {
  const [name, setName] = useState(prefill?.user_name ?? "");
  const [domain, setDomain] = useState(prefill?.domain ?? "Product");
  const [markets, setMarkets] = useState(prefill?.markets ?? []);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Apply prefill when a run is reopened from history.
  useEffect(() => {
    if (!prefill) return;
    setName(prefill.user_name ?? "");
    setDomain(prefill.domain ?? "Product");
    setMarkets(prefill.markets ?? []);
    setResult(prefill);
  }, [prefill]);

  const canRun = name.trim() && markets.length > 0 && !loading;

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API}/reconcile/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_name: name.trim(),
          markets,
          domain,
          rec_type: "range",
        }),
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

  return (
    <div className="space-y-5">
      {/* Form */}
      <div className="space-y-4">
        {/* Row 1: Name + Domain + Type */}
        <div className="flex flex-wrap items-start gap-4">
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
              Your name
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="First Last"
              className="h-9 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-sm text-slate-700 dark:text-slate-300 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-400 w-40"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
              Domain
            </label>
            <div className="flex gap-1">
              {DOMAINS.map((d) => {
                const Icon = DOMAIN_ICONS[d];
                return (
                  <button
                    key={d}
                    onClick={() => setDomain(d)}
                    className={[
                      "flex items-center gap-1.5 h-9 px-3 rounded-md border text-sm font-medium transition-colors",
                      domain === d
                        ? "bg-brand-500 text-white border-brand-500"
                        : "border-slate-200 text-slate-600 hover:border-brand-300 dark:border-slate-700 dark:text-slate-400",
                    ].join(" ")}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {d}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
              Type
            </label>
            <div className="flex gap-1">
              <button className="flex items-center gap-1.5 h-9 px-3 rounded-md border text-sm font-medium bg-brand-500 text-white border-brand-500">
                Range
              </button>
              <button
                disabled
                title="Coming soon"
                className="flex items-center gap-1.5 h-9 px-3 rounded-md border text-sm font-medium border-slate-200 text-slate-400 dark:border-slate-700 cursor-not-allowed opacity-50"
              >
                <Settings className="h-3.5 w-3.5" />
                Attribute
              </button>
            </div>
          </div>
        </div>

        {/* Row 2: Market multi-select */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-slate-600 dark:text-slate-400">
            Markets
          </label>
          <MarketMultiSelect selected={markets} onChange={setMarkets} />
        </div>

        {/* Config warnings */}
        <ConfigWarnings markets={markets} domain={domain} />

        <Button onClick={run} disabled={!canRun} className="h-9 gap-2">
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Running reconciliation…
            </>
          ) : (
            "Run Reconciliation"
          )}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-md border border-danger-200 bg-danger-50 dark:border-red-800 dark:bg-red-900/20 px-3 py-2.5 text-sm text-danger-700 dark:text-red-400">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-success-500" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Results — {result.domain} Range — {result.markets?.join(", ")}
            </span>
            <StatusBadge status={result.status} />
          </div>
          <RunResults runData={result} />
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Reconciliations() {
  const [tab, setTab] = useState("run");
  const [prefill, setPrefill] = useState(null);

  function reopenRun(run) {
    // Load full run detail, switch to run tab, prefill form + results.
    fetch(`${API}/reconcile/history/${run.id}`)
      .then((r) => r.json())
      .then((detail) => {
        setPrefill(detail);
        setTab("run");
      })
      .catch(() => {});
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-500/10 text-brand-600 dark:text-brand-400">
          <Layers2 className="h-5 w-5" aria-hidden />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Reconciliations
          </h1>
          <p className="mt-0.5 max-w-3xl text-xs text-slate-500 dark:text-slate-400">
            Compare{" "}
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
            </span>{" "}
            across three domains (Product, Vendor, Customer) for one or more
            markets. Source files are fetched directly from SharePoint.
          </p>
        </div>
      </div>

      <Card>
        <Tabs value={tab} onValueChange={setTab} className="w-full">
          <CardHeader className="pb-0">
            <TabsList className="w-full justify-start rounded-none border-0 bg-transparent p-0 h-auto">
              <TabsTrigger value="run" className="gap-2 rounded-none">
                <Rows3 className="h-4 w-4 opacity-70" />
                Run
              </TabsTrigger>
              <TabsTrigger value="history" className="gap-2 rounded-none">
                <Clock className="h-4 w-4 opacity-70" />
                History
              </TabsTrigger>
            </TabsList>
          </CardHeader>
          <CardContent className="pt-5">
            <TabsContent value="run" className="mt-0">
              <RunTab prefill={prefill} />
            </TabsContent>
            <TabsContent value="history" className="mt-0">
              <HistoryTab onReopen={reopenRun} />
            </TabsContent>
          </CardContent>
        </Tabs>
      </Card>
    </div>
  );
}
