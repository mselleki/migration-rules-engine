import { useState } from "react";
import { BookOpen, ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";

// ─── Rule data ─────────────────────────────────────────────────────────────────

const RULES = {
  Product: {
    label: "Product — Global",
    totalActive: 23,
    categories: [
      {
        name: "Business Rules",
        rules: [
          { id: "Rule 1",  status: "active",   col: "Legally packaged to be sold as a split?", description: "Si vendu en split → 10 attributs split obligatoires (GTIN-Inner, Split Pack, Split Size, Split UOM, Split Net Weight, Split Tare Weight, Split Length, Split Width, Split Height, Splits Per Case)" },
          { id: "Rule 2",  status: "active",   col: "Split dimensions",                        description: "Split Length ≤ Case Length ; Split Width ≤ Case Width ; Split Height ≤ Case Height ; Split Net Weight ≤ Case Net Weight" },
          { id: "Rule 4",  status: "active",   col: "Shelf Life",                              description: "Shelf Life (Sysco) < Shelf Life (Manufacturer)" },
          { id: "Rule 5",  status: "active",   col: "Attribute Group ID",                      description: "Pas de données nutritionnelles pour les produits non-alimentaires (Attribute Group IDs 01xxxxxx, 10xxxxxx, 18xxxxxx)" },
          { id: "Rule 8",  status: "active",   col: "Catch Weight",                            description: "Si Catch Weight = Yes → Case Catch Weight Range From ≤ Case Catch Weight Range To" },
          { id: "Rule 9",  status: "active",   col: "Does Product Have A Taric Code?",         description: "Si Does Product Have A Taric Code? = Yes → Taric Code/Commodity Code obligatoire" },
          { id: "Rule 10", status: "active",   col: "45 colonnes",                             description: "45 colonnes obligatoires doivent être renseignées sur chaque ligne (SUPC, Brand Key, Marketing Description, etc.)" },
        ],
      },
      {
        name: "Formatting Rules",
        rules: [
          { id: "Rule 3",  status: "active",   col: "GTIN-Outer",                    description: "Doit contenir 8, 12, 13 ou 14 chiffres" },
          { id: "Rule F1", status: "active",   col: "GTIN-Inner",                    description: "Doit contenir 8, 12, 13 ou 14 chiffres (si renseigné)" },
          { id: "Rule F2", status: "active",   col: "Attribute Group ID",            description: "Exactement 8 chiffres, zéro-paddé (ex: 01010100)" },
          { id: "Rule F3", status: "active",   col: "Taric Code/Commodity Code",     description: "Exactement 8 chiffres (si renseigné)" },
          { id: "Rule F4", status: "active",   col: "Champs entiers (11 colonnes)",  description: "SUPC, Case Pack, Split Pack, Splits Per Case, Cases/Layers per Pallet, Shelf Life Sysco & Fabricant — doivent être des entiers (sans décimale)" },
          { id: "Rule F5", status: "active",   col: "Champs numériques (30 colonnes)", description: "Poids, dimensions, valeurs nutritionnelles — doivent être des nombres valides (float)" },
          { id: "Rule F6", status: "active",   col: "Country of Origin (4 colonnes)", description: "Code ISO 3166-1 alpha-2 obligatoire (2 lettres majuscules, ex: FR, GB)" },
          { id: "Rule F7", status: "active",   col: "Descriptions (6 colonnes)",    description: "First & Second Word, Marketing/Warehouse/Invoice Description, Description Text, True Vendor Name — caractères spéciaux autorisés : alphanumériques, accents, espaces, % & ( ) * + - . / ™ ® Ø" },
          { id: "Rule F8", status: "active",   col: "Search Name",                  description: "≤ 20 caractères, sans espaces, caractères autorisés uniquement" },
        ],
      },
      {
        name: "LOV Rules",
        rules: [
          { id: "Rule L0", status: "active",   col: "Attribute Group ID",            description: "Doit appartenir à la liste des 620+ OSD Hierarchy IDs (référence: Attribute Group.xlsx)" },
          { id: "Rule L1", status: "active",   col: "Brand Key",                     description: "Doit appartenir aux 96 codes Sysco Own Brand ou aux 10 335 codes Vendor Brand (référence: Brands.xlsx)" },
          { id: "Rule L2", status: "active",   col: "Status",                        description: "Valeurs autorisées : Active, Delisted, Archived" },
          { id: "Rule L3", status: "active",   col: "Seasonal",                      description: "Valeurs autorisées : 01, 02, 03, 04, 05, 06, 07, 99" },
          { id: "Rule L4", status: "active",   col: "Item Group",                    description: "Valeurs autorisées : RM-DRY, RM-COOLER, RM-FREEZER, FG-DRY, FG-COOLER, FG-FREEZER, NON FOOD" },
          { id: "Rule L5", status: "active",   col: "Item VAT - Purchasing / Selling", description: "Valeurs autorisées : I-STD, I-ZERO, I-RED" },
          { id: "Rule L6", status: "active",   col: "Min Temperature / Max Temperature", description: "Valeurs autorisées : TEMP18, TEMP0, TEMP5, TEMP8" },
          { id: "Rule L7", status: "planned",  col: "Biodegradable or Compostable",  description: "Valeurs prévues : BIODEGRADABLE, COMPOSTABLE, NOT_APPLICABLE" },
          { id: "Rule L8", status: "planned",  col: "Nutritional Unit",              description: "Valeurs prévues : G, ML" },
          { id: "Rule L9", status: "planned",  col: "Generic GTIN",                  description: "9 valeurs prévues (à confirmer)" },
          { id: "Rule L-Allergen", status: "planned", col: "28 colonnes Allergen",   description: "Valeurs prévues : 0, 1, 2" },
          { id: "Rule L-UOM",     status: "planned", col: "Case UOM / Split UOM",    description: "44 codes UOM prévus" },
        ],
      },
    ],
  },

  ProductLocal: {
    label: "Product — Local",
    totalActive: 0,
    categories: [
      {
        name: "En attente",
        rules: [
          { id: "—", status: "planned", col: "—", description: "Framework posé, en attente des spécifications métier." },
        ],
      },
    ],
  },

  Customer: {
    label: "Customer (7 feuilles)",
    totalActive: 11,
    categories: [
      {
        name: "Invoice",
        rules: [
          { id: "C1",   status: "active",  col: "Intercompany/Trading Partner", description: "17 codes : GB01, GB57, GB58, GB59, GB80, IE01, IE02, IE03, IE90, HK91, HK92, SE99, SE01, SE02, SE03, SE04, SE05" },
          { id: "C2",   status: "active",  col: "Customer Group",               description: "16 codes : BRAKES, COUNTRY_CHOICE, BCE, KFF, FRESH_DIRECT, MEDINA, SYSCO_ROI, SYSCO_NI, CLASSIC_DRINKS, READY_CHEF, MENIGO, SERVICESTYCKARNA, FRUKTSERVICE, EKOFISK, SYSCO_FRANCE, LAG" },
          { id: "C-F1", status: "active",  col: "Search Name - Invoice",        description: "≤ 20 caractères, sans espaces, caractères autorisés uniquement" },
        ],
      },
      {
        name: "LEA_Invoice",
        rules: [
          { id: "C3",    status: "active", col: "Division",          description: "7 codes : TRS, TRP, LCC, CMU, OTH, WHL, MIS" },
          { id: "C4",    status: "active", col: "Method of Payment",  description: "21 codes : C_DD_BASE, C_DD_OTHER, C_CASH, C_CARD, C_STRDCARD, C_BANK, C_SWISH, C_AUTOGIRO, C_CHEQUE, C_CONTRA, V_BACS_BAS, V_BACS_OTH, V_CASH, V_CARD, V_SWISH, V_AUTOGIRO, V_BANK, V_CONTRA, V_DD_BASE, V_DD_OTHER, V_CHEQUE" },
          { id: "C-L7",  status: "active", col: "VAT Group",         description: "Valeurs autorisées : I-STD, I-ZERO, I-RED" },
          { id: "C-L8",  status: "active", col: "Seasonal",          description: "Valeurs autorisées : 01, 02, 03, 04, 05, 06, 07, 99" },
          { id: "C-L9",  status: "active", col: "Status",            description: "Valeurs autorisées : Active, Delisted, Archived" },
        ],
      },
      {
        name: "OS",
        rules: [
          { id: "C-F2", status: "active", col: "Search Name - Delivery", description: "≤ 20 caractères, sans espaces, caractères autorisés uniquement" },
        ],
      },
      {
        name: "LEA_OS",
        rules: [
          { id: "C5",    status: "active", col: "Mode of Delivery",      description: "23 codes : 3PL, AIR, AMB_TRK, ANY, BACK_HAUL, BICYCLE, BOAT, BULK_CRR, COLD_STRG, CONSOL, CONT_SHIP, COURIER, CROSS_DOCK, CUST_COLL, DIRECT, DRON_DLV, FROZ_TRK, INTERMOD, PICKUP, PIPELINE, REFR_TRK, TRAIN, TRUCK" },
          { id: "C6",    status: "active", col: "Delivery Terms (Incoterms)", description: "11 codes : CFR, CIF, CIP, CPT, DAP, DDP, DPU, EXW, FAS, FCA, FOB" },
          { id: "C-L10", status: "active", col: "Seasonal",              description: "Valeurs autorisées : 01, 02, 03, 04, 05, 06, 07, 99" },
          { id: "C-L11", status: "active", col: "Status",                description: "Valeurs autorisées : Active, Delisted, Archived" },
        ],
      },
      {
        name: "PT / EmployeeInvoice / EmployeeOS",
        rules: [
          { id: "—", status: "planned", col: "—", description: "Feuilles présentes dans le fichier Customer, aucune règle implémentée pour l'instant." },
        ],
      },
    ],
  },

  Vendor: {
    label: "Vendor (4 feuilles)",
    totalActive: 7,
    categories: [
      {
        name: "Invoice",
        rules: [
          { id: "V-L1", status: "active", col: "Intercompany/Trading Partner", description: "17 codes identiques à Customer C1" },
          { id: "V-F1", status: "active", col: "Search Name",                  description: "≤ 20 caractères, sans espaces, caractères autorisés uniquement" },
        ],
      },
      {
        name: "LEA_Invoice",
        rules: [
          { id: "V-L2", status: "active", col: "Method of Payment", description: "21 codes identiques à Customer C4" },
          { id: "V-L3", status: "active", col: "VAT Group",         description: "Valeurs autorisées : I-STD, I-ZERO, I-RED" },
          { id: "V-L4", status: "active", col: "Status",            description: "Valeurs autorisées : Active, Delisted, Archived" },
        ],
      },
      {
        name: "OS",
        rules: [
          { id: "V-F2", status: "active", col: "Search Name", description: "≤ 20 caractères, sans espaces, caractères autorisés uniquement" },
        ],
      },
      {
        name: "LEA_OS",
        rules: [
          { id: "V-L5", status: "active", col: "Delivery Terms (Incoterms)", description: "11 codes Incoterms : CFR, CIF, CIP, CPT, DAP, DDP, DPU, EXW, FAS, FCA, FOB" },
          { id: "V-L6", status: "active", col: "Mode of Delivery",           description: "23 codes identiques à Customer C5" },
          { id: "V-L7", status: "active", col: "Status",                     description: "Valeurs autorisées : Active, Delisted, Archived" },
        ],
      },
    ],
  },
};

// ─── Badge helpers ──────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  if (status === "active")  return <Badge variant="success">Active</Badge>;
  if (status === "planned") return <Badge variant="secondary">Planned</Badge>;
  return null;
}

function CategoryBadge({ name }) {
  const map = {
    "Business Rules":   "warning",
    "Formatting Rules": "secondary",
    "LOV Rules":        "default",
  };
  const variant = map[name] ?? "secondary";
  return <Badge variant={variant}>{name}</Badge>;
}

// ─── Rule row ───────────────────────────────────────────────────────────────────

function RuleRow({ rule }) {
  return (
    <tr className="border-b border-slate-50 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors">
      <td className="px-3 py-2.5 align-top w-24">
        <span className="font-mono text-xs font-medium text-slate-600 dark:text-slate-300">{rule.id}</span>
      </td>
      <td className="px-3 py-2.5 align-top w-28">
        <StatusBadge status={rule.status} />
      </td>
      <td className="px-3 py-2.5 align-top w-56">
        <span className="text-xs text-slate-500 dark:text-slate-400 italic">{rule.col}</span>
      </td>
      <td className="px-3 py-2.5 align-top text-sm text-slate-700 dark:text-slate-300">
        {rule.description}
      </td>
    </tr>
  );
}

// ─── Domain section ─────────────────────────────────────────────────────────────

function DomainSection({ domainKey, domain }) {
  const [open, setOpen] = useState(true);
  const activeCount   = domain.categories.flatMap(c => c.rules).filter(r => r.status === "active").length;
  const plannedCount  = domain.categories.flatMap(c => c.rules).filter(r => r.status === "planned").length;

  return (
    <Card>
      <CardHeader>
        <button
          className="flex items-center gap-2 w-full text-left"
          onClick={() => setOpen(o => !o)}
          aria-expanded={open}
        >
          {open
            ? <ChevronDown className="h-4 w-4 text-slate-400 flex-shrink-0" />
            : <ChevronRight className="h-4 w-4 text-slate-400 flex-shrink-0" />}
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">{domain.label}</span>
          <div className="ml-auto flex items-center gap-2">
            <Badge variant="success" className="tabular-nums">{activeCount} actives</Badge>
            {plannedCount > 0 && <Badge variant="secondary" className="tabular-nums">{plannedCount} planned</Badge>}
          </div>
        </button>
      </CardHeader>

      {open && (
        <CardContent className="pt-0">
          <div className="space-y-5">
            {domain.categories.map(cat => (
              <div key={cat.name}>
                <div className="flex items-center gap-2 mb-2">
                  <CategoryBadge name={cat.name} />
                </div>
                <div className="overflow-x-auto rounded-md border border-slate-100 dark:border-slate-800">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-24">ID</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-28">Statut</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-56">Colonne(s)</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Description</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-50 dark:divide-slate-800/30">
                      {cat.rules.map(rule => <RuleRow key={rule.id + cat.name} rule={rule} />)}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// ─── Page ───────────────────────────────────────────────────────────────────────

export default function RulesCatalog() {
  const allRules   = Object.values(RULES).flatMap(d => d.categories.flatMap(c => c.rules));
  const totalActive  = allRules.filter(r => r.status === "active").length;
  const totalPlanned = allRules.filter(r => r.status === "planned").length;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Rules Catalog</h1>
          <p className="text-xs text-slate-400 mt-0.5">Toutes les règles de validation implémentées ou planifiées</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success" className="tabular-nums">{totalActive} actives</Badge>
          <Badge variant="secondary" className="tabular-nums">{totalPlanned} planned</Badge>
        </div>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-4 divide-x divide-slate-200 dark:divide-slate-700 border border-slate-200 dark:border-slate-700 rounded-md bg-white dark:bg-slate-900">
        {[
          { label: "Product Global", value: RULES.Product.totalActive },
          { label: "Product Local",  value: RULES.ProductLocal.totalActive },
          { label: "Customer",       value: RULES.Customer.totalActive },
          { label: "Vendor",         value: RULES.Vendor.totalActive },
        ].map(({ label, value }) => (
          <div key={label} className="px-5 py-3">
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-0.5">{label}</p>
            <p className="text-xl font-semibold text-slate-800 dark:text-slate-100">{value}</p>
            <p className="text-xs text-slate-400">règles actives</p>
          </div>
        ))}
      </div>

      {/* Domain sections */}
      {Object.entries(RULES).map(([key, domain]) => (
        <DomainSection key={key} domainKey={key} domain={domain} />
      ))}
    </div>
  );
}
