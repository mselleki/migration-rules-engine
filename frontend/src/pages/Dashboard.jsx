import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useHistory } from "../context/HistoryContext.jsx";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Button } from "../components/ui/button.jsx";
import { Plus, Trash2, ArrowRight } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
} from "@tanstack/react-table";

const DOMAINS = ["Product", "Vendor", "Customer"];

function fmt(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short" }) +
    "  " + d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}
function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
}

// ── KPI strip ────────────────────────────────────────────────────────────────
function KpiStrip({ runs }) {
  const total  = runs.length;
  const clean  = runs.filter(r => r.total_errors === 0).length;
  const errors = runs.reduce((s, r) => s + r.total_errors, 0);
  const rate   = total ? Math.round((clean / total) * 100) : 0;

  const items = [
    { label: "Total runs",   value: total  },
    { label: "Pass rate",    value: `${rate}%`, accent: rate === 100 },
    { label: "Clean",        value: clean,  accent: clean > 0 },
    { label: "Total errors", value: errors, danger: errors > 0 },
  ];

  return (
    <div className="grid grid-cols-4 divide-x divide-slate-200 dark:divide-slate-700 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900">
      {items.map(({ label, value, accent, danger }) => (
        <div key={label} className="px-5 py-3">
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-0.5">{label}</p>
          <p className={
            "text-xl font-semibold " +
            (danger ? "text-danger-500" : accent ? "text-success-500" : "text-slate-800 dark:text-slate-100")
          }>
            {value}
          </p>
        </div>
      ))}
    </div>
  );
}

// ── Status matrix cell ────────────────────────────────────────────────────────
function StatusCell({ run, onClick }) {
  if (!run) return (
    <td onClick={onClick} className="px-4 py-2.5 text-center cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
      <span className="text-slate-300 dark:text-slate-600 text-xs">—</span>
    </td>
  );
  const ok = run.total_errors === 0;
  return (
    <td onClick={onClick} className="px-4 py-2.5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
      <div className="space-y-0.5">
        <Badge variant={ok ? "success" : "danger"}>{ok ? "Clean" : `${run.total_errors} errors`}</Badge>
        <p className="text-[11px] text-slate-400">{fmt(run.timestamp)}</p>
      </div>
    </td>
  );
}

function latestRun(runs, domain, entity) {
  return runs.find(r => r.domain === domain && r.legal_entity === entity) ?? null;
}

// ── TanStack table columns ────────────────────────────────────────────────────
const columns = [
  { accessorKey: "timestamp",    header: "Date",          cell: i => <span className="text-slate-500 tabular-nums">{fmt(i.getValue())}</span> },
  { accessorKey: "domain",       header: "Domain",        cell: i => <Badge variant="secondary">{i.getValue()}</Badge> },
  { accessorKey: "legal_entity", header: "Legal Entity",  cell: i => <span className="font-medium">{i.getValue() || "—"}</span> },
  { accessorKey: "total_rows",   header: "Rows",          cell: i => <span className="tabular-nums">{i.getValue()}</span> },
  {
    accessorKey: "total_errors",
    header: "Errors",
    cell: i => {
      const v = i.getValue();
      return <Badge variant={v === 0 ? "success" : "danger"}>{v === 0 ? "0" : v}</Badge>;
    },
  },
];

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ onNavigate }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
        <BarChart className="h-5 w-5 text-slate-400" />
      </div>
      <p className="text-sm font-medium text-slate-700 dark:text-slate-200 mb-1">No validation runs yet</p>
      <p className="text-xs text-slate-400 max-w-xs mb-5">
        Upload migration files in the Validator and run your first validation.
      </p>
      <Button size="sm" onClick={onNavigate}>
        Go to Validator <ArrowRight className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}

// ── Chart tooltip ─────────────────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-3 py-2 text-xs shadow">
      <p className="font-medium text-slate-700 dark:text-slate-200 mb-1">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.fill }}>{p.name}: {p.value}</p>
      ))}
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { runs, clearHistory } = useHistory();
  const navigate = useNavigate();
  const [extraEntities, setExtraEntities] = useState([]);
  const [newEntity, setNewEntity] = useState("");
  const [addingEntity, setAddingEntity] = useState(false);
  const [sorting, setSorting] = useState([{ id: "timestamp", desc: true }]);

  const historyEntities = useMemo(
    () => [...new Set(runs.map(r => r.legal_entity).filter(Boolean))],
    [runs]
  );
  const entities = useMemo(
    () => [...historyEntities, ...extraEntities.filter(e => !historyEntities.includes(e))],
    [historyEntities, extraEntities]
  );

  const chartData = useMemo(() => {
    const map = {};
    runs.forEach(r => {
      const d = fmtDate(r.timestamp);
      if (!map[d]) map[d] = { date: d, Clean: 0, Errors: 0 };
      r.total_errors === 0 ? map[d].Clean++ : map[d].Errors++;
    });
    return Object.values(map).slice(-14);
  }, [runs]);

  const table = useReactTable({
    data: runs,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 10 } },
  });

  function handleAddEntity() {
    const name = newEntity.trim();
    if (!name || entities.includes(name)) { setAddingEntity(false); return; }
    setExtraEntities(prev => [...prev, name]);
    setNewEntity("");
    setAddingEntity(false);
  }

  if (!runs.length && !entities.length) {
    return <EmptyState onNavigate={() => navigate("/validator")} />;
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Dashboard</h1>
          <p className="text-xs text-slate-400 mt-0.5">Validation status across domains and legal entities</p>
        </div>
        {runs.length > 0 && (
          <Button
            variant="ghost" size="sm"
            className="text-slate-400 hover:text-danger-500"
            onClick={() => { if (window.confirm("Clear all validation history?")) clearHistory(); }}
          >
            <Trash2 className="h-3.5 w-3.5" /> Clear history
          </Button>
        )}
      </div>

      {/* KPI strip */}
      {runs.length > 0 && <KpiStrip runs={runs} />}

      {/* Matrix + chart row */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5">
        {/* Status matrix */}
        {entities.length > 0 && (
          <Card className="xl:col-span-3 overflow-hidden">
            <CardHeader>
              <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Status Matrix</span>
              <Button variant="ghost" size="sm" onClick={() => setAddingEntity(true)}>
                <Plus className="h-3.5 w-3.5" /> Add entity
              </Button>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                    <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider min-w-[140px]">Entity</th>
                    {DOMAINS.map(d => (
                      <th key={d} className="px-4 py-2 text-xs font-medium text-slate-500 uppercase tracking-wider min-w-[160px]">{d}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50">
                  {entities.map(entity => (
                    <tr key={entity}>
                      <td className="px-4 py-2.5 font-medium text-slate-800 dark:text-slate-200 text-sm">{entity}</td>
                      {DOMAINS.map(domain => (
                        <StatusCell
                          key={domain}
                          run={latestRun(runs, domain, entity)}
                          onClick={() => navigate("/validator", { state: { domain, legalEntity: entity } })}
                        />
                      ))}
                    </tr>
                  ))}
                  {addingEntity && (
                    <tr>
                      <td colSpan={4} className="px-4 py-2.5">
                        <div className="flex gap-2">
                          <input
                            autoFocus type="text" placeholder="e.g. FR-SYS"
                            value={newEntity}
                            onChange={e => setNewEntity(e.target.value)}
                            onKeyDown={e => { if (e.key === "Enter") handleAddEntity(); if (e.key === "Escape") setAddingEntity(false); }}
                            className="flex-1 text-sm border border-slate-200 dark:border-slate-700 rounded px-2.5 py-1.5 bg-white dark:bg-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                          />
                          <Button size="sm" onClick={handleAddEntity}>Add</Button>
                          <Button size="sm" variant="outline" onClick={() => setAddingEntity(false)}>Cancel</Button>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Chart */}
        {chartData.length > 0 && (
          <Card className="xl:col-span-2">
            <CardHeader>
              <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Runs by day</span>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} barSize={12} barGap={2}>
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} allowDecimals={false} width={24} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(99,102,241,0.05)" }} />
                  <Bar dataKey="Clean"  stackId="a" fill="#16a34a" radius={[0,0,0,0]} />
                  <Bar dataKey="Errors" stackId="a" fill="#dc2626" radius={[2,2,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Recent runs table */}
      {runs.length > 0 && (
        <Card>
          <CardHeader>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Recent runs</span>
            <span className="text-xs text-slate-400">{runs.length} total</span>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                  {table.getHeaderGroups().map(hg => hg.headers.map(h => (
                    <th
                      key={h.id}
                      className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer select-none hover:text-slate-700 dark:hover:text-slate-300"
                      onClick={h.column.getToggleSortingHandler()}
                    >
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      {{ asc: " ↑", desc: " ↓" }[h.column.getIsSorted()] ?? ""}
                    </th>
                  )))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50">
                {table.getRowModel().rows.map(row => (
                  <tr
                    key={row.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-800/30 cursor-pointer transition-colors"
                    onClick={() => navigate("/validator", { state: { domain: row.original.domain, legalEntity: row.original.legal_entity } })}
                  >
                    {row.getVisibleCells().map(cell => (
                      <td key={cell.id} className="px-4 py-2.5 text-slate-700 dark:text-slate-300">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {table.getPageCount() > 1 && (
            <div className="flex items-center justify-between px-4 py-2.5 border-t border-slate-100 dark:border-slate-800">
              <span className="text-xs text-slate-400">Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}</span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>Prev</Button>
                <Button size="sm" variant="outline" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>Next</Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
