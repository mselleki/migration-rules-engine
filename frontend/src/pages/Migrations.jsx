import { useState } from "react";
import { Key, Link2, TableProperties, BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs.jsx";

// ─── Mock Data ────────────────────────────────────────────────────────────────
const TABLES = {
  SOURCE: [
    { id: "src_items",   name: "ITEMS",   system: "Legacy ERP", rowCount: "142,803",
      columns: [
        { name: "SUPC_CODE",    type: "VARCHAR(20)",   pk: true,  nullable: false, mapped: true  },
        { name: "ITEM_DESC",    type: "VARCHAR(255)",  pk: false, nullable: false, mapped: true  },
        { name: "UNIT_PRICE",   type: "DECIMAL(10,2)", pk: false, nullable: true,  mapped: true  },
        { name: "CATEGORY_CD",  type: "CHAR(4)",       pk: false, nullable: true,  mapped: true  },
        { name: "LEGACY_FLAG",  type: "CHAR(1)",       pk: false, nullable: true,  mapped: false },
        { name: "CREATE_DT",    type: "DATE",          pk: false, nullable: true,  mapped: true  },
        { name: "VENDOR_ID",    type: "INT",           pk: false, nullable: true,  mapped: true  },
        { name: "INTERNAL_REF", type: "VARCHAR(50)",   pk: false, nullable: true,  mapped: false },
      ],
    },
    { id: "src_vendors", name: "VENDORS", system: "Legacy ERP", rowCount: "8,471",
      columns: [
        { name: "VENDOR_ID",   type: "INT",          pk: true,  nullable: false, mapped: true  },
        { name: "VENDOR_NAME", type: "VARCHAR(200)", pk: false, nullable: false, mapped: true  },
        { name: "VENDOR_CODE", type: "VARCHAR(10)",  pk: false, nullable: true,  mapped: true  },
        { name: "COUNTRY_CD",  type: "CHAR(2)",      pk: false, nullable: true,  mapped: true  },
        { name: "ACTIVE_IND",  type: "CHAR(1)",      pk: false, nullable: true,  mapped: true  },
        { name: "OLD_SYS_ID",  type: "VARCHAR(30)",  pk: false, nullable: true,  mapped: false },
      ],
    },
    { id: "src_orders",  name: "ORDERS",  system: "Legacy ERP", rowCount: "1,204,556",
      columns: [
        { name: "ORDER_NUM",   type: "VARCHAR(20)", pk: true,  nullable: false, mapped: true  },
        { name: "SUPC_CODE",   type: "VARCHAR(20)", pk: false, nullable: false, mapped: true  },
        { name: "ORDER_DATE",  type: "DATE",        pk: false, nullable: false, mapped: true  },
        { name: "QTY_ORD",    type: "INT",         pk: false, nullable: false, mapped: true  },
        { name: "CUST_NUM",    type: "VARCHAR(20)", pk: false, nullable: true,  mapped: true  },
        { name: "STATUS_CD",   type: "CHAR(2)",     pk: false, nullable: true,  mapped: true  },
        { name: "LEGACY_TYPE", type: "CHAR(3)",     pk: false, nullable: true,  mapped: false },
      ],
    },
  ],
  TARGET: [
    { id: "tgt_products",     name: "PRODUCTS",     system: "New Platform", rowCount: "—",
      columns: [
        { name: "ITEM_NUMBER", type: "VARCHAR(20)",   pk: true,  nullable: false, mapped: true },
        { name: "DESCRIPTION", type: "TEXT",          pk: false, nullable: false, mapped: true },
        { name: "PRICE",       type: "NUMERIC(12,4)", pk: false, nullable: true,  mapped: true },
        { name: "CATEGORY_ID", type: "INT",           pk: false, nullable: true,  mapped: true },
        { name: "CREATED_AT",  type: "TIMESTAMP",     pk: false, nullable: true,  mapped: true },
        { name: "SUPPLIER_ID", type: "INT",           pk: false, nullable: true,  mapped: true },
      ],
    },
    { id: "tgt_suppliers",    name: "SUPPLIERS",    system: "New Platform", rowCount: "—",
      columns: [
        { name: "SUPPLIER_ID",   type: "INT",          pk: true,  nullable: false, mapped: true },
        { name: "NAME",          type: "VARCHAR(200)", pk: false, nullable: false, mapped: true },
        { name: "SUPPLIER_CODE", type: "VARCHAR(10)",  pk: false, nullable: true,  mapped: true },
        { name: "COUNTRY_CODE",  type: "CHAR(2)",      pk: false, nullable: true,  mapped: true },
        { name: "IS_ACTIVE",     type: "BOOLEAN",      pk: false, nullable: true,  mapped: true },
      ],
    },
    { id: "tgt_transactions",  name: "TRANSACTIONS", system: "New Platform", rowCount: "—",
      columns: [
        { name: "TRANSACTION_ID",   type: "UUID",        pk: true,  nullable: false, mapped: true },
        { name: "ITEM_NUMBER",      type: "VARCHAR(20)", pk: false, nullable: false, mapped: true },
        { name: "TRANSACTION_DATE", type: "TIMESTAMP",   pk: false, nullable: false, mapped: true },
        { name: "QUANTITY",         type: "INT",         pk: false, nullable: false, mapped: true },
        { name: "CUSTOMER_ID",      type: "VARCHAR(20)", pk: false, nullable: true,  mapped: true },
        { name: "STATUS",           type: "VARCHAR(20)", pk: false, nullable: true,  mapped: true },
      ],
    },
  ],
};

const MAPPINGS = [
  { id: "map_items_products",      name: "Items → Products",     sourceTable: "src_items",   targetTable: "tgt_products",     status: "active", coverage: 87,
    fieldMaps: [
      { src: "SUPC_CODE",   tgt: "ITEM_NUMBER",   transform: "direct",   rule: "Copy as-is" },
      { src: "ITEM_DESC",   tgt: "DESCRIPTION",   transform: "direct",   rule: "Copy as-is" },
      { src: "UNIT_PRICE",  tgt: "PRICE",         transform: "cast",     rule: "DECIMAL → NUMERIC, scale ×1" },
      { src: "CATEGORY_CD", tgt: "CATEGORY_ID",   transform: "lookup",   rule: "JOIN categories_ref ON code" },
      { src: "CREATE_DT",   tgt: "CREATED_AT",    transform: "cast",     rule: "DATE → TIMESTAMP (00:00:00 UTC)" },
      { src: "VENDOR_ID",   tgt: "SUPPLIER_ID",   transform: "direct",   rule: "Copy as-is" },
    ],
  },
  { id: "map_vendors_suppliers",   name: "Vendors → Suppliers",  sourceTable: "src_vendors", targetTable: "tgt_suppliers",    status: "active", coverage: 100,
    fieldMaps: [
      { src: "VENDOR_ID",   tgt: "SUPPLIER_ID",   transform: "direct",   rule: "Copy as-is" },
      { src: "VENDOR_NAME", tgt: "NAME",           transform: "direct",   rule: "Copy as-is" },
      { src: "VENDOR_CODE", tgt: "SUPPLIER_CODE",  transform: "direct",   rule: "Copy as-is" },
      { src: "COUNTRY_CD",  tgt: "COUNTRY_CODE",   transform: "direct",   rule: "Copy as-is" },
      { src: "ACTIVE_IND",  tgt: "IS_ACTIVE",      transform: "convert",  rule: "'Y'/'N' → true/false" },
    ],
  },
  { id: "map_orders_transactions", name: "Orders → Transactions", sourceTable: "src_orders",  targetTable: "tgt_transactions", status: "draft",  coverage: 71,
    fieldMaps: [
      { src: "ORDER_NUM",  tgt: "TRANSACTION_ID",   transform: "generate", rule: "UUID v5 from ORDER_NUM" },
      { src: "SUPC_CODE",  tgt: "ITEM_NUMBER",      transform: "direct",   rule: "Copy as-is" },
      { src: "ORDER_DATE", tgt: "TRANSACTION_DATE", transform: "cast",     rule: "DATE → TIMESTAMP (00:00:00 UTC)" },
      { src: "QTY_ORD",   tgt: "QUANTITY",          transform: "direct",   rule: "Copy as-is" },
      { src: "CUST_NUM",   tgt: "CUSTOMER_ID",      transform: "direct",   rule: "Copy as-is" },
      { src: "STATUS_CD",  tgt: "STATUS",           transform: "lookup",   rule: "Decode via status_map table" },
    ],
  },
];

const TRANSFORM_BADGE = {
  direct:   "secondary",
  cast:     "warning",
  lookup:   "default",
  convert:  "warning",
  generate: "default",
};

const allTables = [...TABLES.SOURCE, ...TABLES.TARGET];

// ─── Components ───────────────────────────────────────────────────────────────

function TableCard({ table, selected, onClick }) {
  const unmapped = table.columns.filter(c => !c.mapped).length;
  return (
    <button
      onClick={onClick}
      aria-pressed={selected}
      className={[
        "w-full text-left rounded-md px-3 py-2.5 border transition-colors",
        selected
          ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
          : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-600",
      ].join(" ")}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-800 dark:text-slate-200">{table.name}</span>
        <span className="text-xs text-slate-400 tabular-nums">{table.rowCount}</span>
      </div>
      <p className="text-xs text-slate-400 mt-0.5 mb-2">{table.system}</p>
      <div className="flex gap-1.5 flex-wrap">
        <Badge variant="secondary">{table.columns.length} cols</Badge>
        {unmapped > 0 && <Badge variant="warning">{unmapped} unmapped</Badge>}
      </div>
    </button>
  );
}

function ColumnTable({ table }) {
  if (!table) return (
    <div className="flex items-center justify-center h-40 text-slate-400 text-sm">← Select a table</div>
  );
  return (
    <div>
      <div className="px-4 py-2.5 border-b border-slate-100 dark:border-slate-800 flex items-center gap-3 bg-slate-50 dark:bg-slate-800/50">
        <span className="text-sm font-medium text-slate-800 dark:text-slate-200">{table.name}</span>
        <span className="text-xs text-slate-400">{table.system} · {table.rowCount} rows</span>
      </div>
      <div className="grid grid-cols-[2fr_1.5fr_90px_50px] text-xs font-medium uppercase tracking-wider text-slate-500 px-4 py-2 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
        <span>Column</span><span>Type</span><span>Nullable</span><span>Mapped</span>
      </div>
      <div className="overflow-y-auto max-h-[460px]">
        {table.columns.map(col => (
          <div
            key={col.name}
            className={`grid grid-cols-[2fr_1.5fr_90px_50px] px-4 py-2 text-sm border-b border-slate-50 dark:border-slate-800/50 items-center ${!col.mapped ? "bg-warning-50/50 dark:bg-yellow-900/10" : ""}`}
          >
            <div className="flex items-center gap-1.5">
              {col.pk && <Key className="h-3 w-3 text-warning-500 flex-shrink-0" aria-label="Primary key" />}
              <span className="font-mono text-xs text-slate-800 dark:text-slate-200">{col.name}</span>
            </div>
            <span className="font-mono text-xs text-slate-500 dark:text-slate-400">{col.type}</span>
            <span className={`text-xs ${col.nullable ? "text-slate-400" : "text-slate-700 dark:text-slate-300"}`}>
              {col.nullable ? "NULL" : "NOT NULL"}
            </span>
            <span className={`h-1.5 w-1.5 rounded-full ${col.mapped ? "bg-success-500" : "bg-warning-500"}`} aria-label={col.mapped ? "Mapped" : "Unmapped"} />
          </div>
        ))}
      </div>
    </div>
  );
}

function FieldMappingRow({ fm }) {
  return (
    <div className="grid grid-cols-[1fr_32px_1fr_90px] items-center gap-2 px-4 py-2 border-b border-slate-50 dark:border-slate-800/50">
      <span className="font-mono text-xs text-brand-500 dark:text-brand-400 font-medium">{fm.src}</span>
      <span className="text-center text-slate-300 dark:text-slate-600 text-xs">→</span>
      <span className="font-mono text-xs text-success-600 dark:text-success-500 font-medium">{fm.tgt}</span>
      <Badge variant={TRANSFORM_BADGE[fm.transform] || "secondary"} className="text-[10px]">{fm.transform}</Badge>
    </div>
  );
}

function MappingCard({ mapping, selected, onClick }) {
  const src = allTables.find(t => t.id === mapping.sourceTable);
  const tgt = allTables.find(t => t.id === mapping.targetTable);
  return (
    <button
      onClick={onClick}
      aria-pressed={selected}
      className={[
        "w-full text-left rounded-md border p-3.5 transition-colors",
        selected
          ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
          : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-600",
      ].join(" ")}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{mapping.name}</p>
          <p className="text-xs text-slate-400 mt-0.5">{src?.name} → {tgt?.name}</p>
        </div>
        <Badge variant={mapping.status === "active" ? "success" : "warning"}>{mapping.status}</Badge>
      </div>
      <div>
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>Coverage</span>
          <span className="font-medium text-slate-600 dark:text-slate-300 tabular-nums">{mapping.coverage}%</span>
        </div>
        <div className="h-1 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-300"
            style={{
              width: `${mapping.coverage}%`,
              background: mapping.coverage === 100 ? "#16a34a" : mapping.coverage > 70 ? "#4f46e5" : "#d97706",
            }}
          />
        </div>
      </div>
    </button>
  );
}

// ─── Diagram Tab ──────────────────────────────────────────────────────────────

function DiagramTab() {
  return (
    <div className="grid grid-cols-[1fr_80px_1fr] gap-4 items-start">
      <div className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-wider text-slate-400 px-1">Source (Legacy ERP)</p>
        {TABLES.SOURCE.map(t => (
          <div key={t.id} className="rounded-md overflow-hidden border border-slate-200 dark:border-slate-700">
            <div className="px-3 py-2 bg-slate-800 dark:bg-slate-700 flex justify-between items-center">
              <span className="text-white text-sm font-medium">{t.name}</span>
              <span className="text-slate-400 text-xs">{t.rowCount}</span>
            </div>
            <div className="bg-white dark:bg-slate-900 py-1">
              {t.columns.slice(0, 5).map(c => (
                <div key={c.name} className="px-3 py-1 flex justify-between text-xs">
                  <span className={`font-mono ${c.pk ? "text-warning-500 font-semibold" : "text-slate-600 dark:text-slate-400"}`}>
                    {c.pk ? "⬥ " : "  "}{c.name}
                  </span>
                  <span className="text-slate-400">{c.type.split("(")[0]}</span>
                </div>
              ))}
              {t.columns.length > 5 && <p className="px-3 py-1 text-xs text-slate-400">+{t.columns.length - 5} more</p>}
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col items-center gap-8 pt-10">
        {MAPPINGS.map(m => (
          <div key={m.id} className="flex flex-col items-center gap-1 text-center">
            <span className="text-slate-400 text-sm">→</span>
            <Badge variant={m.status === "active" ? "success" : "warning"} className="text-[10px]">{m.coverage}%</Badge>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-wider text-slate-400 px-1">Target (New Platform)</p>
        {TABLES.TARGET.map(t => (
          <div key={t.id} className="rounded-md overflow-hidden border border-slate-200 dark:border-slate-700">
            <div className="px-3 py-2 bg-slate-700 dark:bg-slate-600 flex justify-between items-center">
              <span className="text-white text-sm font-medium">{t.name}</span>
              <span className="text-slate-300 text-xs">target</span>
            </div>
            <div className="bg-white dark:bg-slate-900 py-1">
              {t.columns.slice(0, 5).map(c => (
                <div key={c.name} className="px-3 py-1 flex justify-between text-xs">
                  <span className={`font-mono ${c.pk ? "text-warning-500 font-semibold" : "text-slate-600 dark:text-slate-400"}`}>
                    {c.pk ? "⬥ " : "  "}{c.name}
                  </span>
                  <span className="text-slate-400">{c.type.split("(")[0]}</span>
                </div>
              ))}
              {t.columns.length > 5 && <p className="px-3 py-1 text-xs text-slate-400">+{t.columns.length - 5} more</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Migrations() {
  const [selectedSource, setSelectedSource] = useState(TABLES.SOURCE[0]);
  const [selectedMapping, setSelectedMapping] = useState(MAPPINGS[0]);

  const activeMappings = MAPPINGS.filter(m => m.status === "active").length;
  const draftMappings  = MAPPINGS.filter(m => m.status === "draft").length;
  const mappingForSource = MAPPINGS.filter(m => m.sourceTable === selectedSource?.id);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Schema Mapping</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Legacy ERP → New Platform · {TABLES.SOURCE.length} source · {TABLES.TARGET.length} target · {MAPPINGS.length} mappings
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="success">{activeMappings} Active</Badge>
          {draftMappings > 0 && <Badge variant="warning">{draftMappings} Draft</Badge>}
        </div>
      </div>

      <Tabs defaultValue="tables">
        <TabsList>
          <TabsTrigger value="tables"><TableProperties className="h-3.5 w-3.5" /> Tables</TabsTrigger>
          <TabsTrigger value="mappings"><Link2 className="h-3.5 w-3.5" /> Mappings</TabsTrigger>
          <TabsTrigger value="diagram"><BarChart3 className="h-3.5 w-3.5" /> Diagram</TabsTrigger>
        </TabsList>

        {/* ── Tables ── */}
        <TabsContent value="tables">
          <div className="grid grid-cols-[220px_1fr_1fr] gap-4 min-h-[480px]">
            <div className="space-y-1.5">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-400 px-1 mb-2">Source Tables</p>
              {TABLES.SOURCE.map(t => (
                <TableCard key={t.id} table={t} selected={selectedSource?.id === t.id} onClick={() => setSelectedSource(t)} />
              ))}
            </div>

            <Card className="overflow-hidden">
              <ColumnTable table={selectedSource} />
            </Card>

            <Card>
              <CardHeader>
                <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Field Correspondences</span>
                {selectedSource && <span className="text-xs text-slate-400">{selectedSource.name}</span>}
              </CardHeader>
              {mappingForSource.length === 0 ? (
                <CardContent className="text-sm text-slate-400 text-center py-10">No mappings for this table yet.</CardContent>
              ) : (
                mappingForSource.map(mapping => {
                  const tgt = allTables.find(t => t.id === mapping.targetTable);
                  return (
                    <div key={mapping.id}>
                      <div className="px-4 py-2 flex items-center justify-between border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                        <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                          <span className="font-medium text-slate-800 dark:text-slate-200">{selectedSource?.name}</span>
                          <span>→</span>
                          <span className="font-medium text-slate-800 dark:text-slate-200">{tgt?.name}</span>
                        </div>
                        <Badge variant="default">{mapping.coverage}%</Badge>
                      </div>
                      {mapping.fieldMaps.map(fm => <FieldMappingRow key={fm.src} fm={fm} />)}
                    </div>
                  );
                })
              )}
            </Card>
          </div>
        </TabsContent>

        {/* ── Mappings ── */}
        <TabsContent value="mappings">
          <div className="grid grid-cols-[280px_1fr] gap-4 min-h-[480px]">
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-400 px-1 mb-2">Mapping Rules</p>
              {MAPPINGS.map(m => (
                <MappingCard key={m.id} mapping={m} selected={selectedMapping?.id === m.id} onClick={() => setSelectedMapping(m)} />
              ))}
            </div>

            {selectedMapping && (() => {
              const src = allTables.find(t => t.id === selectedMapping.sourceTable);
              const tgt = allTables.find(t => t.id === selectedMapping.targetTable);
              return (
                <Card className="overflow-hidden">
                  <CardHeader>
                    <div>
                      <h3 className="text-sm font-medium text-slate-800 dark:text-slate-200">{selectedMapping.name}</h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {src?.name} ({src?.system}) → {tgt?.name} ({tgt?.system})
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={selectedMapping.status === "active" ? "success" : "warning"}>{selectedMapping.status}</Badge>
                      <span className="text-sm font-semibold text-brand-500 tabular-nums">{selectedMapping.coverage}%</span>
                    </div>
                  </CardHeader>

                  <div className="grid grid-cols-4 divide-x divide-slate-100 dark:divide-slate-800 border-b border-slate-100 dark:border-slate-800">
                    {[
                      { label: "Fields",     val: selectedMapping.fieldMaps.length },
                      { label: "Direct",     val: selectedMapping.fieldMaps.filter(f => f.transform === "direct").length },
                      { label: "Transforms", val: selectedMapping.fieldMaps.filter(f => f.transform !== "direct").length },
                      { label: "Coverage",   val: selectedMapping.coverage + "%" },
                    ].map(s => (
                      <div key={s.label} className="px-4 py-3 text-center">
                        <p className="text-lg font-semibold text-brand-500 tabular-nums">{s.val}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{s.label}</p>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-[1fr_32px_1fr_90px] px-4 py-2 text-xs font-medium uppercase tracking-wider border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 text-slate-500">
                    <span>Source</span>
                    <span />
                    <span>Target</span>
                    <span>Transform</span>
                  </div>
                  <div className="overflow-y-auto max-h-60">
                    {selectedMapping.fieldMaps.map(fm => <FieldMappingRow key={fm.src} fm={fm} />)}
                  </div>

                  <div className="p-4 border-t border-slate-100 dark:border-slate-800">
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Transform Rules</p>
                    <div className="grid grid-cols-2 gap-2">
                      {selectedMapping.fieldMaps.map(fm => (
                        <div key={fm.src} className="rounded-md border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 p-2.5">
                          <span className="font-mono text-xs font-medium text-brand-500">{fm.src}</span>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{fm.rule}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              );
            })()}
          </div>
        </TabsContent>

        {/* ── Diagram ── */}
        <TabsContent value="diagram">
          <Card>
            <CardHeader>
              <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Schema Overview</span>
            </CardHeader>
            <CardContent>
              <DiagramTab />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
