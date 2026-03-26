import { useState, useRef, useCallback, useMemo, useEffect } from "react";
import {
  Upload,
  X,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
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

/** Primary identifier column per Tracker domain (Data Overview sticky column). */
const DOMAIN_ID_COLUMN = {
  Products: "SUPC",
  Vendors: "SUVC",
  Customers: "SUCC",
};

function resolveIdColumn(domain, allCols) {
  const preferred = DOMAIN_ID_COLUMN[domain];
  if (preferred && allCols.includes(preferred)) return preferred;
  for (const c of ["SUPC", "SUVC", "SUCC"]) {
    if (allCols.includes(c)) return c;
  }
  return allCols[0] ?? "SUPC";
}

// ---------------------------------------------------------------------------
// Mock data - preview only, never sent to the API
// ---------------------------------------------------------------------------
const MOCK_REPORT = {
  summary: {
    total_rows: 847,
    total_errors: 18,
    errors_by_rule: {
      "LOV - invalid value": 9,
      "Required field missing": 6,
      "Format error": 3,
    },
  },
  warnings: [],
  errors: [
    {
      sheet: "Global Product Data",
      row: 12,
      supc: "7821043",
      rule: "LOV - invalid value",
      message: "Brand 'MONOPRIX' is not a recognised value.",
    },
    {
      sheet: "Global Product Data",
      row: 34,
      supc: "7834201",
      rule: "Required field missing",
      message: "OSD Hierarchy is required but empty.",
    },
    {
      sheet: "Global Product Data",
      row: 67,
      supc: "7867554",
      rule: "LOV - invalid value",
      message: "Case UOM 'BOITE' is not a recognised value.",
    },
    {
      sheet: "Global Product Data",
      row: 89,
      supc: "7889012",
      rule: "Required field missing",
      message: "Case Pack is required but empty.",
    },
    {
      sheet: "Global Product Data",
      row: 102,
      supc: "7802341",
      rule: "Format error",
      message: "Case Gross Weight (kg) must be a positive number.",
    },
    {
      sheet: "Global Product Data",
      row: 145,
      supc: "7845678",
      rule: "LOV - invalid value",
      message: "Product Status 'OBSOLETE' is not a recognised value.",
    },
    {
      sheet: "Global Product Data",
      row: 178,
      supc: "7878901",
      rule: "Required field missing",
      message: "Global Product Description is required but empty.",
    },
    {
      sheet: "Global Product Data",
      row: 203,
      supc: "7803456",
      rule: "LOV - invalid value",
      message: "Sysco Brand 'YES' is not a recognised value. Expected Y or N.",
    },
    {
      sheet: "Global Product Data",
      row: 221,
      supc: "7821987",
      rule: "Format error",
      message: "GTIN Outer must be exactly 14 digits.",
    },
    {
      sheet: "Global Product Data",
      row: 256,
      supc: "7856123",
      rule: "LOV - invalid value",
      message: "Catch Weight 'OUI' is not a recognised value. Expected Y or N.",
    },
    {
      sheet: "Global Product Data",
      row: 312,
      supc: "7812654",
      rule: "Required field missing",
      message: "Legal Entity is required but empty.",
    },
    {
      sheet: "Global Product Data",
      row: 378,
      supc: "7878432",
      rule: "LOV - invalid value",
      message: "Storage Area 'SURGELE' is not a recognised value.",
    },
    {
      sheet: "Global Product Data",
      row: 401,
      supc: "7801234",
      rule: "Format error",
      message: "Case Net Weight (kg) must be a positive number.",
    },
    {
      sheet: "Global Product Data",
      row: 445,
      supc: "7845901",
      rule: "LOV - invalid value",
      message:
        "Biodegradable or Compostable 'MAYBE' is not a recognised value.",
    },
    {
      sheet: "Global Product Data",
      row: 501,
      supc: "7801567",
      rule: "Required field missing",
      message: "Default Vendor is required but empty.",
    },
    {
      sheet: "Global Product Data",
      row: 534,
      supc: "7834890",
      rule: "LOV - invalid value",
      message: "Recyclable 'OUI' is not a recognised value. Expected Y or N.",
    },
    {
      sheet: "Global Product Data",
      row: 612,
      supc: "7812345",
      rule: "LOV - invalid value",
      message:
        "Split Product 'MAYBE' is not a recognised value. Expected Y or N.",
    },
    {
      sheet: "Global Product Data",
      row: 789,
      supc: "7889765",
      rule: "Required field missing",
      message: "Vendor Product Code is required but empty.",
    },
  ],
  completion: [
    {
      sheet: "Global Product Data",
      total_rows: 847,
      columns: [
        { attribute: "SUPC", filled: 847, rate: 1.0 },
        { attribute: "Global Product Description", filled: 840, rate: 0.992 },
        { attribute: "Legal Entity", filled: 846, rate: 0.999 },
        { attribute: "OSD Hierarchy", filled: 841, rate: 0.993 },
        { attribute: "Sysco Brand", filled: 847, rate: 1.0 },
        { attribute: "Brand", filled: 823, rate: 0.972 },
        { attribute: "GTIN Outer", filled: 756, rate: 0.893 },
        { attribute: "GTIN Inner", filled: 612, rate: 0.723 },
        { attribute: "Vendor Product Code", filled: 839, rate: 0.991 },
        { attribute: "Default Vendor", filled: 843, rate: 0.995 },
        { attribute: "Case Pack", filled: 847, rate: 1.0 },
        { attribute: "Case Size", filled: 847, rate: 1.0 },
        { attribute: "Case UOM", filled: 847, rate: 1.0 },
        { attribute: "Product Status", filled: 844, rate: 0.997 },
        { attribute: "Proprietary Product", filled: 731, rate: 0.863 },
        { attribute: "Split Product", filled: 698, rate: 0.824 },
        { attribute: "Case Length (cm)", filled: 634, rate: 0.749 },
        { attribute: "Case Width (cm)", filled: 631, rate: 0.745 },
        { attribute: "Case Height (cm)", filled: 628, rate: 0.741 },
        { attribute: "Case Gross Weight (kg)", filled: 521, rate: 0.615 },
        { attribute: "Case Net Weight (kg)", filled: 498, rate: 0.588 },
        { attribute: "Catch Weight", filled: 612, rate: 0.723 },
        { attribute: "Almonds", filled: 423, rate: 0.499 },
        { attribute: "Milk and products thereof", filled: 418, rate: 0.494 },
        { attribute: "Gluten at > 20 ppm", filled: 415, rate: 0.49 },
        { attribute: "Dairy Free", filled: 389, rate: 0.459 },
        { attribute: "Halal", filled: 401, rate: 0.474 },
        { attribute: "Marketing Description", filled: 312, rate: 0.368 },
        { attribute: "Invoice Description", filled: 345, rate: 0.407 },
        { attribute: "Ecom Description", filled: 198, rate: 0.234 },
        { attribute: "Commodity Code", filled: 287, rate: 0.339 },
        { attribute: "Storage Guidelines", filled: 142, rate: 0.168 },
        { attribute: "Cooking Instructions", filled: 87, rate: 0.103 },
        {
          attribute: "Product Country of Origin - Manufactured",
          filled: 412,
          rate: 0.487,
        },
        {
          attribute: "Shelf Life Period in days (Customer)",
          filled: 356,
          rate: 0.42,
        },
        { attribute: "Ecom Category Hierarchy", filled: 134, rate: 0.158 },
        { attribute: "Latin Fish Name", filled: 34, rate: 0.04 },
        { attribute: "MSC Chain of Custody Number", filled: 21, rate: 0.025 },
      ],
    },
    {
      sheet: "Local Product Data",
      total_rows: 847,
      columns: [
        { attribute: "SUPC", filled: 847, rate: 1.0 },
        { attribute: "Description", filled: 843, rate: 0.995 },
        { attribute: "Case Pack", filled: 847, rate: 1.0 },
        { attribute: "Case UOM", filled: 847, rate: 1.0 },
        { attribute: "Split Pack", filled: 523, rate: 0.618 },
        { attribute: "Split UOM", filled: 519, rate: 0.613 },
        { attribute: "Nominal Quantity", filled: 412, rate: 0.487 },
        { attribute: "Item Group", filled: 387, rate: 0.457 },
        { attribute: "Cost Centre", filled: 201, rate: 0.237 },
        { attribute: "Item Vat - Selling", filled: 634, rate: 0.749 },
      ],
    },
  ],
  rows: [
    {
      sheet: "Global Product Data",
      data: [
        {
          SUPC: "7821043",
          "Global Product Description": "FROMAGE BLANC NATURE 3KG",
          Brand: "MONOPRIX",
          "Case Pack": "6",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "DAIRY|FRESH CHEESE",
          "Case Gross Weight (kg)": "3.25",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "",
          "Marketing Description": "",
        },
        {
          SUPC: "7834201",
          "Global Product Description": "",
          Brand: "BRAKES",
          "Case Pack": "12",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "",
          "Case Gross Weight (kg)": "5.10",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "Premium chicken breast fillets",
        },
        {
          SUPC: "7867554",
          "Global Product Description": "HUILE OLIVE 5L",
          Brand: "SYSCO",
          "Case Pack": "4",
          "Case UOM": "BOITE",
          "Product Status": "Active",
          "OSD Hierarchy": "GROCERY|OILS",
          "Case Gross Weight (kg)": "5.80",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "Y",
          "Marketing Description": "Extra virgin olive oil",
        },
        {
          SUPC: "7889012",
          "Global Product Description": "POULET ROTI 1.2KG",
          Brand: "BRAKES",
          "Case Pack": "",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "POULTRY|COOKED",
          "Case Gross Weight (kg)": "7.20",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "",
        },
        {
          SUPC: "7802341",
          "Global Product Description": "SAUMON FUME TRANCHE 200G",
          Brand: "SYSCO",
          "Case Pack": "10",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "FISH|SMOKED",
          "Case Gross Weight (kg)": "abc",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "Smoked Atlantic salmon",
        },
        {
          SUPC: "7845678",
          "Global Product Description": "TOMATES CERISES 500G",
          Brand: "BRAKES",
          "Case Pack": "20",
          "Case UOM": "EA",
          "Product Status": "OBSOLETE",
          "OSD Hierarchy": "PRODUCE|TOMATOES",
          "Case Gross Weight (kg)": "11.0",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "",
        },
        {
          SUPC: "7878901",
          "Global Product Description": "",
          Brand: "SYSCO",
          "Case Pack": "6",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "DAIRY|BUTTER",
          "Case Gross Weight (kg)": "3.00",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "",
          "Marketing Description": "",
        },
        {
          SUPC: "7803456",
          "Global Product Description": "BEURRE DOUX 500G",
          Brand: "YES",
          "Case Pack": "20",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "DAIRY|BUTTER",
          "Case Gross Weight (kg)": "10.5",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "N",
          "Marketing Description": "Fine French butter",
        },
        {
          SUPC: "7821987",
          "Global Product Description": "PAIN DE MIE BLANC 500G",
          Brand: "BRAKES",
          "Case Pack": "12",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "BAKERY|BREAD",
          "Case Gross Weight (kg)": "6.50",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "N",
          "Marketing Description": "",
        },
        {
          SUPC: "7856123",
          "Global Product Description": "ESCALOPE POULET 150G",
          Brand: "SYSCO",
          "Case Pack": "8",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "POULTRY|RAW",
          "Case Gross Weight (kg)": "1.20",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "OUI",
          "Marketing Description": "",
        },
        {
          SUPC: "7812654",
          "Global Product Description": "COMTÉ AOP 200G",
          Brand: "SYSCO",
          "Case Pack": "24",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "DAIRY|CHEESE",
          "Case Gross Weight (kg)": "5.00",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "N",
          "Marketing Description": "Aged Comté AOP 18 months",
        },
        {
          SUPC: "7878432",
          "Global Product Description": "POISSON PANÉ 100G",
          Brand: "BRAKES",
          "Case Pack": "20",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "FISH|BREADED",
          "Case Gross Weight (kg)": "2.10",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "SURGELE",
          "Marketing Description": "",
        },
        {
          SUPC: "7801234",
          "Global Product Description": "CRÈME FRAÎCHE 200ML",
          Brand: "SYSCO",
          "Case Pack": "6",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "DAIRY|CREAM",
          "Case Gross Weight (kg)": "-0.5",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "N",
          "Marketing Description": "",
        },
        {
          SUPC: "7845901",
          "Global Product Description": "FRITES SURGELÉES 2.5KG",
          Brand: "BRAKES",
          "Case Pack": "4",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "POTATO|FROZEN",
          "Case Gross Weight (kg)": "10.2",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "Classic straight-cut fries",
          "Biodegradable or Compostable": "MAYBE",
        },
        {
          SUPC: "7801567",
          "Global Product Description": "RISOTTO MILANAIS 2KG",
          Brand: "SYSCO",
          "Case Pack": "6",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "GROCERY|RICE",
          "Case Gross Weight (kg)": "12.5",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "N",
          "Marketing Description": "Traditional Milanese risotto",
        },
        {
          SUPC: "7834890",
          "Global Product Description": "HARICOTS VERTS EXTRA FIN 1KG",
          Brand: "BRAKES",
          "Case Pack": "10",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "VEGETABLE|BEANS",
          "Case Gross Weight (kg)": "10.3",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "",
          Recyclable: "OUI",
        },
        {
          SUPC: "7812345",
          "Global Product Description": "SAUCE BÉCHAMEL 1L",
          Brand: "SYSCO",
          "Case Pack": "12",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "GROCERY|SAUCES",
          "Case Gross Weight (kg)": "13.2",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "N",
          "Marketing Description": "Classic béchamel",
          "Split Product": "MAYBE",
        },
        {
          SUPC: "7889765",
          "Global Product Description": "MOZZARELLA DI BUFALA 125G",
          Brand: "SYSCO",
          "Case Pack": "24",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "DAIRY|CHEESE",
          "Case Gross Weight (kg)": "3.10",
          Almonds: "N",
          "Milk and products thereof": "Y",
          Halal: "N",
          "Marketing Description": "Buffalo mozzarella DOP",
        },
        {
          SUPC: "7856789",
          "Global Product Description": "CABILLAUD MSC FILET 180G",
          Brand: "BRAKES",
          "Case Pack": "10",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "FISH|WHITE",
          "Case Gross Weight (kg)": "1.90",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "MSC certified cod fillet",
        },
        {
          SUPC: "7823456",
          "Global Product Description": "JAMBON BLANC SUPÉRIEUR 4KG",
          Brand: "SYSCO",
          "Case Pack": "2",
          "Case UOM": "EA",
          "Product Status": "Active",
          "OSD Hierarchy": "CHARCUTERIE|HAM",
          "Case Gross Weight (kg)": "8.80",
          Almonds: "N",
          "Milk and products thereof": "N",
          Halal: "N",
          "Marketing Description": "Premium cooked ham",
        },
      ],
    },
  ],
};

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
        <div className="flex w-full min-w-0 items-center justify-between gap-3">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
            Completion Analysis
          </span>
          <span className="text-lg font-bold text-brand-500 tabular-nums shrink-0">
            {Math.round(stats.overallRate * 100)}%
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
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
                    <span className="text-[10px] text-slate-400">-</span>
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

// --- Data Grid ---

function DataGridPanel({ rows, errors, domain = "Products" }) {
  const [idFilter, setIdFilter] = useState("");
  const [colFilter, setColFilter] = useState("");
  const [activeSheet, setActiveSheet] = useState(0);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 50;

  const sheetData = rows?.[activeSheet] ?? null;
  const allData = sheetData?.data ?? [];
  const allCols = allData.length > 0 ? Object.keys(allData[0]) : [];
  const idCol = resolveIdColumn(domain, allCols);

  const errorIds = useMemo(
    () => new Set(errors?.map((e) => String(e.supc)) ?? []),
    [errors],
  );

  const visibleCols = useMemo(() => {
    const q = colFilter.trim().toLowerCase();
    const matched = q
      ? allCols.filter((c) => c.toLowerCase().includes(q))
      : [...allCols];
    if (!allCols.includes(idCol)) return matched;
    const rest = matched.filter((c) => c !== idCol);
    if (!matched.includes(idCol)) {
      return [idCol, ...rest];
    }
    return [idCol, ...rest];
  }, [allCols, colFilter, idCol]);

  const filteredRows = useMemo(() => {
    const q = idFilter.trim().toLowerCase();
    return q
      ? allData.filter((r) =>
          String(r[idCol] ?? "")
            .toLowerCase()
            .includes(q),
        )
      : allData;
  }, [allData, idFilter, idCol]);

  const pageCount = Math.ceil(filteredRows.length / PAGE_SIZE);
  const pageRows = filteredRows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  if (!rows?.length) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
            Data Overview
          </span>
          <span className="text-xs text-slate-400 tabular-nums">
            {filteredRows.length} rows · {visibleCols.length} columns
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Sheet tabs */}
        {rows.length > 1 && (
          <div className="flex gap-1 flex-wrap">
            {rows.map((s, i) => (
              <button
                key={s.sheet}
                onClick={() => {
                  setActiveSheet(i);
                  setPage(0);
                }}
                className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                  activeSheet === i
                    ? "bg-brand-500 text-white"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                }`}
              >
                {s.sheet}
              </button>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          <input
            type="text"
            placeholder={`Filter by ${idCol}…`}
            value={idFilter}
            onChange={(e) => {
              setIdFilter(e.target.value);
              setPage(0);
            }}
            className="text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-brand-500 focus:outline-none w-44 dark:text-slate-100"
          />
          <input
            type="text"
            placeholder="Filter columns…"
            value={colFilter}
            onChange={(e) => setColFilter(e.target.value)}
            className="text-sm border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 bg-white dark:bg-slate-900 focus:ring-2 focus:ring-brand-500 focus:outline-none w-44 dark:text-slate-100"
          />
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-800">
          <table
            className="text-xs border-collapse"
            style={{ minWidth: "max-content" }}
          >
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-800/60">
                {visibleCols.map((col) => (
                  <th
                    key={col}
                    className={`px-3 py-2 text-left font-medium text-slate-500 whitespace-nowrap border-b border-slate-200 dark:border-slate-700 ${
                      col === idCol
                        ? "sticky left-0 z-20 bg-slate-50 dark:bg-slate-800 shadow-[1px_0_0_0_rgba(0,0,0,0.08)]"
                        : ""
                    }`}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, ri) => {
                const hasError = errorIds.has(String(row[idCol]));
                const rowBg = hasError
                  ? "bg-red-50 dark:bg-red-900/10"
                  : ri % 2 === 0
                    ? "bg-white dark:bg-slate-900"
                    : "bg-slate-50/50 dark:bg-slate-800/20";
                return (
                  <tr key={ri} className={rowBg}>
                    {visibleCols.map((col) => {
                      const val = row[col];
                      const isEmpty = val === "" || val == null;
                      const isStickyCol = col === idCol;
                      return (
                        <td
                          key={col}
                          title={String(val ?? "")}
                          className={[
                            "px-3 py-1.5 border-b border-slate-100 dark:border-slate-800 whitespace-nowrap max-w-[200px] truncate",
                            isStickyCol
                              ? `sticky left-0 z-20 font-mono font-medium shadow-[1px_0_0_0_rgba(0,0,0,0.08)] ${rowBg}`
                              : "",
                            isEmpty
                              ? "text-slate-300 dark:text-slate-600"
                              : "text-slate-700 dark:text-slate-300",
                          ].join(" ")}
                        >
                          {isEmpty ? "-" : String(val)}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {pageCount > 1 && (
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">
              Page {page + 1} / {pageCount}
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPage((p) => p - 1)}
                disabled={page === 0}
              >
                Prev
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= pageCount - 1}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// --- Helpers ---

function timeAgo(ts) {
  if (!ts) return null;
  const diff = Date.now() - ts * 1000;
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// --- Results block (shared between live and cached) ---

function ResultsBlock({ report, error, domain = "Products" }) {
  const totalErrors = report?.summary?.total_errors ?? 0;
  const totalRows = report?.summary?.total_rows ?? 0;
  const errorsByRule = report?.summary?.errors_by_rule ?? {};

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-start gap-2.5 rounded-md border border-danger-100 dark:border-red-800/40 bg-danger-50 dark:bg-red-900/20 px-4 py-3 text-sm text-danger-700 dark:text-red-400">
          <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {report && (
        <>
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

          {/* Data overview grid */}
          {report.rows?.length > 0 && (
            <DataGridPanel
              rows={report.rows}
              errors={report.errors}
              domain={domain}
            />
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
                  <CheckCircle2 className="h-4 w-4 flex-shrink-0" /> All rules
                  passed - no errors found.
                </div>
              ) : (
                <ErrorTable errors={report.errors ?? []} />
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

// --- Main ---

export default function TrackerValidator() {
  const [domain, setDomain] = useState("Products");
  const [dashboard, setDashboard] = useState(null); // { Products: {configured, cached}, ... }
  const [refreshing, setRefreshing] = useState(false);
  const [mockMode, setMockMode] = useState(false);
  // Upload fallback
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadReport, setUploadReport] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Load cached dashboard on mount
  useEffect(() => {
    fetch(`${API}/tracker/dashboard`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setDashboard(data))
      .catch(() => {});
  }, []);

  const domainInfo = dashboard?.[domain];
  const isConfigured = domainInfo?.configured ?? false;
  const cached = domainInfo?.cached ?? null;
  const report = cached?.report ?? null;
  const cacheError = cached?.error ?? null;
  const updatedAt = cached?.updated_at ?? null;

  async function handleRefresh() {
    setRefreshing(true);
    try {
      const res = await fetch(
        `${API}/tracker/refresh?domain=${encodeURIComponent(domain)}`,
        { method: "POST" },
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      // Merge updated domain into dashboard
      setDashboard((prev) => ({ ...prev, [domain]: data }));
    } catch (err) {
      // Error is stored in cache by backend; re-fetch dashboard to show it
      fetch(`${API}/tracker/dashboard`)
        .then((r) => r.json())
        .then(setDashboard)
        .catch(() => {});
    } finally {
      setRefreshing(false);
    }
  }

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadReport(null);
    try {
      const fd = new FormData();
      fd.append("domain", domain);
      fd.append("file", file);
      const res = await fetch(`${API}/validate/tracker`, {
        method: "POST",
        body: fd,
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || `HTTP ${res.status}`);
      }
      setUploadReport(await res.json());
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Compact top bar */}
      <div className="flex items-center gap-3 flex-wrap border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-2.5 bg-white dark:bg-slate-900">
        <h1 className="text-sm font-semibold text-slate-800 dark:text-slate-100 mr-1">
          Tracker Dashboard
        </h1>
        <div className="h-4 w-px bg-slate-200 dark:bg-slate-700" />
        <Select
          value={domain}
          onValueChange={(d) => {
            setDomain(d);
            setFile(null);
            setUploadReport(null);
            setUploadError(null);
          }}
        >
          <SelectTrigger
            aria-label="Select domain"
            className="h-7 text-xs w-32"
          >
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
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <span
            className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${isConfigured ? "bg-emerald-500" : "bg-slate-300 dark:bg-slate-600"}`}
          />
          {isConfigured
            ? updatedAt
              ? `Updated ${timeAgo(updatedAt)}`
              : "Connected"
            : "Not configured"}
        </div>
        <div className="flex-1" />
        <button
          onClick={() => setMockMode((v) => !v)}
          className={`text-xs px-2.5 py-1 rounded-md border transition-colors ${
            mockMode
              ? "border-amber-300 bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:border-amber-700 dark:text-amber-400"
              : "border-slate-200 dark:border-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          {mockMode ? "✕ Mock" : "Preview mock"}
        </button>
        {isConfigured && (
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
            className="h-7 text-xs flex items-center gap-1.5 flex-shrink-0"
          >
            <RefreshCw
              className={`h-3 w-3 ${refreshing ? "animate-spin" : ""}`}
            />
            {refreshing ? "Updating…" : "Update"}
          </Button>
        )}
      </div>

      {/* Upload fallback - shown inline when domain not configured */}
      {!isConfigured && !mockMode && (
        <div className="flex items-end gap-3 flex-wrap">
          <div className="flex-1 min-w-[240px] max-w-sm">
            <p className="text-xs text-slate-400 mb-2">
              No SharePoint URL configured. Upload a tracker file or set{" "}
              <code className="px-1 py-px rounded bg-slate-100 dark:bg-slate-800 text-[10px]">
                TRACKER_URL_{domain.toUpperCase()}
              </code>{" "}
              in Railway.
            </p>
            <form onSubmit={handleUpload} className="flex gap-2 items-start">
              <div className="flex-1">
                <FileDropZone
                  label="Tracker file (.xlsx / .xlsb)"
                  file={file}
                  onFile={setFile}
                />
              </div>
              <Button
                type="submit"
                disabled={!file || uploading}
                size="sm"
                className="flex-shrink-0 mt-0.5"
              >
                {uploading ? (
                  <>
                    <span className="h-3 w-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />{" "}
                    Validating…
                  </>
                ) : (
                  "Validate"
                )}
              </Button>
            </form>
          </div>
        </div>
      )}

      {/* Results - full width */}
      <div>
        {mockMode && (
          <div>
            <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400 mb-3">
              <span className="px-1.5 py-px rounded bg-amber-100 dark:bg-amber-900/30 font-medium text-[10px] uppercase tracking-wide">
                Mock
              </span>
              <span>Sample data - not connected to SharePoint</span>
            </div>
            <ResultsBlock report={MOCK_REPORT} error={null} domain={domain} />
          </div>
        )}

        {!mockMode && refreshing && !cached && (
          <div className="flex items-center justify-center h-40 text-slate-400 text-sm gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Fetching from SharePoint…
          </div>
        )}

        {!mockMode && (report || cacheError) && (
          <div>
            {cached?.report?.source?.filename && (
              <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
                <FileSpreadsheet className="h-3.5 w-3.5 flex-shrink-0" />
                <span className="truncate">
                  {cached.report.source.filename}
                </span>
                <span className="text-slate-300 dark:text-slate-600">·</span>
                <span className="text-emerald-500">SharePoint</span>
                {updatedAt && (
                  <>
                    <span className="text-slate-300 dark:text-slate-600">
                      ·
                    </span>
                    <span>{timeAgo(updatedAt)}</span>
                  </>
                )}
              </div>
            )}
            <ResultsBlock report={report} error={cacheError} domain={domain} />
          </div>
        )}

        {!mockMode && (uploadReport || uploadError) && !isConfigured && (
          <ResultsBlock
            report={uploadReport}
            error={uploadError}
            domain={domain}
          />
        )}
      </div>
    </div>
  );
}
