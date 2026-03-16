import { FileSpreadsheet, CheckCircle2, Clock } from "lucide-react";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs.jsx";

// ─── Domain definitions ────────────────────────────────────────────────────────

const DOMAINS = {
  Products: {
    description: "Product master data — global attributes and market-specific local data.",
    templates: [
      {
        name: "Global Product Data",
        key: "global_file",
        status: "rules-defined",
        ruleCount: 23,
        columns: ["SUPC","Attribute Group ID","Brand Key","Customer Branded","Sysco Finance Category","True Vendor Name","First & Second Word","Marketing Description","Warehouse Description","Invoice Description","Search Name","Item Group","Item Model Group Id","Multi Language Packaging","EU Hub","Constellation","Case Pack","Case Size","Case UOM","Legally packaged to be sold as a split?","Case Net Weight","Case Length","Case Width","Case Height","Catch Weight","Cases per Layer (Standard Pallet)","Layers per Pallet (Standard Pallet)","Dairy Free","Gluten Free","Halal","Kosher","Organic","Vegan","Vegetarian","Biodegradable or Compostable","Recyclable","Hazardous Material","Product Warranty","Perishable Product/Date Tracked","Shelf Life Period In Days (Manufacturer)","Shelf Life Period in Days (Sysco)","Does Product Have A Taric Code?","Country Of Origin - Manufactured","Country Of Origin - Packed","Country Of Origin - Sold From","Country Of Origin - Raw Ingredients"],
      },
      {
        name: "Local Product Data",
        key: "local_file",
        status: "pending",
        ruleCount: 0,
        columns: ["SUPC","Shelf Life Period in Days (Customer)"],
      },
    ],
  },
  Vendors: {
    description: "Vendor master data — financial and operational setup per legal entity.",
    templates: [
      {
        name: "Invoice",
        key: "invoice",
        status: "rules-defined",
        ruleCount: 2,
        columns: ["StepID","Master Vendor Code","Vendor Name","Company Registration Number","Trade/Indirect Vendor","VAT Registration Number","Intercompany/Trading Partner","Global Location Number","Hold Harmless","Certificate of Insurance","Search Name","Legal Name","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code"],
        ruledCols: ["Intercompany/Trading Partner","Search Name"],
      },
      {
        name: "LEA Invoice",
        key: "lea_invoice",
        status: "rules-defined",
        ruleCount: 3,
        columns: ["SUVC Invoice","Legal Entity","Cost Centre","Method of Payment","VAT Group","Known As","Status"],
        ruledCols: ["Method of Payment","VAT Group","Status"],
      },
      {
        name: "OS",
        key: "os",
        status: "rules-defined",
        ruleCount: 1,
        columns: ["SUVC Ordering/Shipping","Vendor Name","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code","Search Name","Legal Name"],
        ruledCols: ["Search Name"],
      },
      {
        name: "LEA OS",
        key: "lea_os",
        status: "rules-defined",
        ruleCount: 3,
        columns: ["SUVC Ordering/Shipping","Legal Entity","Delivery Terms","Buyer Group","Mode of Delivery","Known As","Warehouse Code","Vendor Managed Inventory","Nominated Vendor Indicator","Duty Paid/Bond","Status"],
        ruledCols: ["Delivery Terms","Mode of Delivery","Status"],
      },
    ],
  },
  Customers: {
    description: "Customer master data — 7 templates covering financial and delivery setup.",
    templates: [
      {
        name: "PT",
        key: "pt",
        status: "pending",
        ruleCount: 0,
        columns: [],
      },
      {
        name: "Invoice",
        key: "invoice",
        status: "rules-defined",
        ruleCount: 3,
        columns: ["Step ID","EU Master Customer Code","Customer Type","Invoice Customer Name","First Name","Last Name","Employee Number","Is Customer a Registered Company","Company Registration Number","VAT Registration Number","Intercompany/Trading Partner","Customer Group","Legal Name - Invoice","Search Name - Invoice","Limited Address","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code"],
        ruledCols: ["Intercompany/Trading Partner","Customer Group","Search Name - Invoice"],
      },
      {
        name: "LEA Invoice",
        key: "lea_invoice",
        status: "rules-defined",
        ruleCount: 5,
        columns: ["Invoice Customer Code","Legal Entity","Legal Entity Customer Master Code","VAT Group","Method of Payment","Reference Code","Customer Own Account Number","Known As - Invoice","Seasonal","Cost Centre","Division","Sales Group","Status"],
        ruledCols: ["VAT Group","Method of Payment","Seasonal","Division","Status"],
      },
      {
        name: "OS",
        key: "os",
        status: "rules-defined",
        ruleCount: 1,
        columns: ["Company Prefix","Ordering/Shipping Customer Code","Ordering/Shipping Customer Name","First Name","Last Name","Legal Name - Delivery","Search Name  - Delivery","Segment","Subsegment","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code"],
        ruledCols: ["Search Name  - Delivery"],
      },
      {
        name: "LEA OS",
        key: "lea_os",
        status: "rules-defined",
        ruleCount: 4,
        columns: ["Ordering/Shipping Customer Code","Legal Entity","Company Chain Code","Delivery Terms","Mode Of Delivery","Known As - Delivery","Warehouse Code","Reference Code","Customer Own Account Number","Sales Area Manager Code","Seasonal","Status"],
        ruledCols: ["Delivery Terms","Mode Of Delivery","Seasonal","Status"],
      },
      {
        name: "Employee Invoice",
        key: "employee_invoice",
        status: "pending",
        ruleCount: 0,
        columns: ["STEP ID","First Name","Last Name","Employee Number","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/PostalCode"],
      },
      {
        name: "Employee OS",
        key: "employee_os",
        status: "pending",
        ruleCount: 0,
        columns: ["Invoice Company Prefix","Invoice Customer Code","Copy Invoice Code","Copy Invoice Address","First Name","Last Name","Legal Entity","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/PostalCode"],
      },
    ],
  },
};

// ─── Components ────────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  if (status === "rules-defined")
    return <Badge variant="success"><CheckCircle2 className="h-3 w-3" /> Rules defined</Badge>;
  return <Badge variant="secondary"><Clock className="h-3 w-3" /> Pending</Badge>;
}

function TemplateCard({ tmpl }) {
  const ruledSet = new Set(tmpl.ruledCols ?? []);
  return (
    <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100 dark:border-slate-800">
        <FileSpreadsheet className="h-4 w-4 text-slate-400 flex-shrink-0" />
        <span className="text-sm font-medium text-slate-800 dark:text-slate-200 flex-1">{tmpl.name}</span>
        <StatusBadge status={tmpl.status} />
        {tmpl.ruleCount > 0 && (
          <Badge variant="outline" className="tabular-nums">{tmpl.ruleCount} rules</Badge>
        )}
        {tmpl.columns.length > 0 && (
          <span className="text-xs text-slate-400 tabular-nums">{tmpl.columns.length} cols</span>
        )}
      </div>
      {tmpl.columns.length > 0 && (
        <div className="px-4 py-3 flex flex-wrap gap-1.5">
          {tmpl.columns.map(col => (
            <span
              key={col}
              className={[
                "inline-block text-[11px] px-1.5 py-0.5 rounded font-mono",
                ruledSet.has(col)
                  ? "bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 border border-brand-200 dark:border-brand-700"
                  : "bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700",
              ].join(" ")}
            >
              {col}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function DomainPanel({ domain }) {
  const { description, templates } = DOMAINS[domain];
  const defined = templates.filter(t => t.status === "rules-defined").length;
  const total   = templates.length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>
        <span className="text-xs text-slate-400 tabular-nums flex-shrink-0 ml-4">
          {defined} / {total} templates with rules
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-brand-500 rounded-full transition-all"
          style={{ width: `${(defined / total) * 100}%` }}
        />
      </div>

      <div className="space-y-2">
        {templates.map(t => <TemplateCard key={t.key} tmpl={t} />)}
      </div>
    </div>
  );
}

// ─── Main ──────────────────────────────────────────────────────────────────────

export default function Migrations() {
  const totalRules = Object.values(DOMAINS)
    .flatMap(d => d.templates)
    .reduce((s, t) => s + t.ruleCount, 0);

  const totalTemplates = Object.values(DOMAINS).flatMap(d => d.templates).length;
  const definedTemplates = Object.values(DOMAINS)
    .flatMap(d => d.templates)
    .filter(t => t.status === "rules-defined").length;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Migrations</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Template coverage across all domains
          </p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Badge variant="outline" className="tabular-nums">{totalRules} rules</Badge>
          <Badge variant="outline" className="tabular-nums">{definedTemplates}/{totalTemplates} templates</Badge>
        </div>
      </div>

      <Card>
        <Tabs defaultValue="Products">
          <CardHeader className="pb-0">
            <TabsList>
              {Object.keys(DOMAINS).map(d => (
                <TabsTrigger key={d} value={d}>
                  {d}
                  <Badge variant="secondary" className="ml-1.5 tabular-nums">
                    {DOMAINS[d].templates.length}
                  </Badge>
                </TabsTrigger>
              ))}
            </TabsList>
          </CardHeader>

          {Object.keys(DOMAINS).map(d => (
            <TabsContent key={d} value={d}>
              <CardContent className="pt-4">
                <DomainPanel domain={d} />
              </CardContent>
            </TabsContent>
          ))}
        </Tabs>
      </Card>
    </div>
  );
}
