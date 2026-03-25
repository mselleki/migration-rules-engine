import { useState, useMemo } from "react";
import { FileSpreadsheet, CheckCircle2, Clock, ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader } from "../components/ui/card.jsx";
import { Badge } from "../components/ui/badge.jsx";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs.jsx";

// ─── Rule type pill styles ──────────────────────────────────────────────────

// Rule type → pill style (used in rule rows)
const TYPE_STYLE = {
  LOV:      "bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-700",
  Format:   "bg-sky-50 text-sky-700 border border-sky-200 dark:bg-sky-900/20 dark:text-sky-400 dark:border-sky-700",
  Business: "bg-violet-50 text-violet-700 border border-violet-200 dark:bg-violet-900/20 dark:text-violet-400 dark:border-violet-700",
};

// Rule type → column chip style (lighter, for the column tags)
const CHIP_STYLE = {
  LOV:      "bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-700",
  Format:   "bg-sky-50 dark:bg-sky-900/20 text-sky-700 dark:text-sky-400 border-sky-200 dark:border-sky-700",
  Business: "bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-400 border-violet-200 dark:border-violet-700",
};
const CHIP_DEFAULT = "bg-slate-50 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700";

// ─── Domain definitions ─────────────────────────────────────────────────────
// rules: { id, col, type: "LOV"|"Format"|"Business", desc }

const DOMAINS = {
  Products: {
    description: "Product master data — global attributes and market-specific local data.",
    templates: [
      {
        name: "Global Product Data",
        key: "global_file",
        status: "rules-defined",
        ruleCount: 30,
        columns: [
          "SUPC","Attribute Group ID","Brand Key","Customer Branded","Sysco Finance Category",
          "True Vendor Name","First & Second Word","Description Text","Search Name",
          "Marketing Description","Warehouse Description","Invoice Description","Latin Fish Name",
          "Item Group","Item Model Group Id","Multi Language Packaging",
          "Multi Language Packaging - Legally Allowed to be Sold in Country",
          "EU Hub","EU Hub Change Date","Constellation","Generic GTIN","GTIN-Outer",
          "Case Pack","Case Size","Case UOM","Legally packaged to be sold as a split?",
          "GTIN-Inner","Split Pack","Split Size","Split UOM",
          "Case Net Weight","Case Tare Weight","Case True Net Weight (Drained/Glazed)",
          "Catch Weight","Case Catch Weight Range From","Case Catch Weight Range To",
          "Split Net Weight","Split Tare Weight","Split True Net Weight (Drained/Glazed)",
          "Case Length","Case Width","Case Height","Split Length","Split Width","Split Height",
          "Splits Per Case","Portion",
          "Cases per Layer (Standard Pallet)","Layers per Pallet (Standard Pallet)",
          "Cases per Layer (Euro Pallet)","Layers per Pallet (Euro Pallet)",
          "Almonds","Barley","Brazil Nuts","Cashew Nuts","Celery and products thereof",
          "Gluten at > 20 ppm","Crustaceans and products thereof","Eggs and products thereof",
          "Fish and products thereof","Hazelnuts","Kamut","Lupin and products thereof",
          "Macadamia Nuts/Queensland Nuts","Milk and products thereof","Molluscs and products thereof",
          "Mustard and products thereof","Nuts","Oats","Peanuts and products thereof",
          "Pecan Nuts","Pistachio Nuts","Rye","Sesame seeds and products thereof",
          "Soybeans and products thereof","Spelt","Sulphur Dioxide > 10 ppm","Walnuts","Wheat",
          "Nutritional Unit","Energy Kcal","Energy KJ","Fat","Of which Saturates",
          "Of which Mono-Unsaturates","Of which Polyunsaturates","Of which Trans Fats",
          "Carbohydrate","Of which Sugars","Of which Polyols","Of which Starch",
          "Fibre","Protein","Salt","Sodium",
          "Dairy Free","Gluten Free","Halal","Kosher","Organic","Vegan","Vegetarian",
          "Biodegradable or Compostable","Recyclable","Hazardous Material",
          "Product Warranty","Product Warranty Code","Perishable Product/Date Tracked",
          "Shelf Life Period In Days (Manufacturer)","Shelf Life Period in Days (Sysco)",
          "Taric Code/Commodity Code","Does Product Have A Taric Code?","Taric Code",
          "Country Of Origin - Manufactured","Country Of Origin - Packed",
          "Country Of Origin - Sold From","Country Of Origin - Raw Ingredients",
          "Cooking Instructions","Defrosting Guidelines","Handling Instructions",
          "Storage Guidelines","Cooking Warning","Food Safety Tips",
        ],
        ruledCols: {
          // LOV (priority 1)
          "Attribute Group ID": "LOV", "Brand Key": "LOV", "Item Group": "LOV",
          "Almonds": "LOV", "Barley": "LOV", "Brazil Nuts": "LOV", "Cashew Nuts": "LOV",
          "Celery and products thereof": "LOV", "Gluten at > 20 ppm": "LOV",
          "Crustaceans and products thereof": "LOV", "Eggs and products thereof": "LOV",
          "Fish and products thereof": "LOV", "Hazelnuts": "LOV", "Kamut": "LOV",
          "Lupin and products thereof": "LOV", "Macadamia Nuts/Queensland Nuts": "LOV",
          "Milk and products thereof": "LOV", "Molluscs and products thereof": "LOV",
          "Mustard and products thereof": "LOV", "Nuts": "LOV", "Oats": "LOV",
          "Peanuts and products thereof": "LOV", "Pecan Nuts": "LOV", "Pistachio Nuts": "LOV",
          "Rye": "LOV", "Sesame seeds and products thereof": "LOV",
          "Soybeans and products thereof": "LOV", "Spelt": "LOV",
          "Sulphur Dioxide > 10 ppm": "LOV", "Walnuts": "LOV", "Wheat": "LOV",
          // Format (priority 2)
          "SUPC": "Format",
          "True Vendor Name": "Format", "First & Second Word": "LOV",
          "Description Text": "Format", "Search Name": "Format",
          "Marketing Description": "Format", "Warehouse Description": "Format",
          "Invoice Description": "Format", "Latin Fish Name": "Format",
          "Cooking Instructions": "Format", "Defrosting Guidelines": "Format",
          "Handling Instructions": "Format", "Storage Guidelines": "Format",
          "Cooking Warning": "Format", "Food Safety Tips": "Format",
          "GTIN-Outer": "Format", "GTIN-Inner": "Format",
          "Taric Code/Commodity Code": "Format",
          "Case Pack": "Format", "Case Size": "Format",
          "Case Net Weight": "Format", "Case Tare Weight": "Format",
          "Case True Net Weight (Drained/Glazed)": "Format",
          "Case Catch Weight Range From": "Format", "Case Catch Weight Range To": "Format",
          "Case Length": "Format", "Case Width": "Format", "Case Height": "Format",
          "Split Pack": "Format", "Split Size": "Format",
          "Split Net Weight": "Format", "Split Tare Weight": "Format",
          "Split True Net Weight (Drained/Glazed)": "Format",
          "Split Length": "Format", "Split Width": "Format", "Split Height": "Format",
          "Splits Per Case": "Format",
          "Cases per Layer (Standard Pallet)": "Format", "Layers per Pallet (Standard Pallet)": "Format",
          "Cases per Layer (Euro Pallet)": "Format", "Layers per Pallet (Euro Pallet)": "Format",
          "Energy Kcal": "Format", "Energy KJ": "Format", "Fat": "Format",
          "Of which Saturates": "Format", "Of which Mono-Unsaturates": "Format",
          "Of which Polyunsaturates": "Format", "Of which Trans Fats": "Format",
          "Carbohydrate": "Format", "Of which Sugars": "Format",
          "Of which Polyols": "Format", "Of which Starch": "Format",
          "Fibre": "Format", "Protein": "Format", "Salt": "Format", "Sodium": "Format",
          "Shelf Life Period In Days (Manufacturer)": "Format",
          "Shelf Life Period in Days (Sysco)": "Format",
          "Country Of Origin - Manufactured": "Format", "Country Of Origin - Packed": "Format",
          "Country Of Origin - Sold From": "Format", "Country Of Origin - Raw Ingredients": "Format",
          // Business (priority 3)
          "Customer Branded": "Business", "Sysco Finance Category": "Business",
          "Item Model Group Id": "Business", "Multi Language Packaging": "Business",
          "EU Hub": "Business", "Constellation": "Business", "Generic GTIN": "LOV",
          "Case UOM": "Business", "Legally packaged to be sold as a split?": "Business",
          "Split UOM": "Business",
          "Catch Weight": "Business", "Does Product Have A Taric Code?": "Business",
          "Nutritional Unit": "Business", "Product Warranty Code": "Business",
          // LOV — yes/no
          "Dairy Free": "LOV", "Gluten Free": "LOV", "Halal": "LOV", "Kosher": "LOV",
          "Organic": "LOV", "Vegan": "LOV", "Vegetarian": "LOV",
          "Biodegradable or Compostable": "LOV", "Recyclable": "LOV",
          "Hazardous Material": "LOV", "Product Warranty": "LOV",
          "Perishable Product/Date Tracked": "LOV",
        },
        rules: [
          { id: "Rule U1",  type: "Business", desc: "SUPC must be unique within the file",
            cols: ["SUPC"] },
          { id: "Rule 1",   type: "Business", desc: "Split attributes required when 'Sold as split' = Yes",
            cols: ["Legally packaged to be sold as a split?","GTIN-Inner","Split Pack","Split Size","Split UOM","Split Net Weight","Split Tare Weight","Split Length","Split Width","Split Height","Splits Per Case"] },
          { id: "Rule 2",   type: "Business", desc: "Split dimensions must not exceed Case dimensions",
            cols: ["Case Length","Case Width","Case Height","Case Net Weight","Split Length","Split Width","Split Height","Split Net Weight"] },
          { id: "Rule 3",   type: "Format",   desc: "Numeric, 8 / 12 / 13 / 14 digits",
            cols: ["GTIN-Outer"] },
          { id: "Rule 4",   type: "Business", desc: "Manufacturer shelf life must be ≥ Sysco shelf life",
            cols: ["Shelf Life Period In Days (Manufacturer)","Shelf Life Period in Days (Sysco)"] },
          { id: "Rule 5",   type: "Business", desc: "Nutritional data must be empty for non-food products",
            cols: ["Nutritional Unit","Energy Kcal","Energy KJ","Fat","Of which Saturates","Of which Mono-Unsaturates","Of which Polyunsaturates","Of which Trans Fats","Carbohydrate","Of which Sugars","Of which Polyols","Of which Starch","Fibre","Protein","Salt","Sodium"] },
          { id: "Rule 8",   type: "Business", desc: "Catch Weight From ≤ To when catch weight is enabled",
            cols: ["Catch Weight","Case Catch Weight Range From","Case Catch Weight Range To"] },
          { id: "Rule 9",   type: "Business", desc: "If Yes → Taric Code required; if No → must be empty",
            cols: ["Does Product Have A Taric Code?","Taric Code/Commodity Code"] },
          { id: "Rule 10",  type: "Business", desc: "Core mandatory fields must not be empty",
            cols: ["SUPC","Attribute Group ID","Brand Key","Customer Branded","Sysco Finance Category","True Vendor Name","First & Second Word","Marketing Description","Warehouse Description","Invoice Description","Item Group","Item Model Group Id","Multi Language Packaging","EU Hub","Constellation","Case Pack","Case Size","Case UOM","Legally packaged to be sold as a split?","Case Net Weight"] },
          { id: "Rule 11",  type: "Business", desc: "If Yes → Product Warranty Code required; if No → must be empty",
            cols: ["Product Warranty","Product Warranty Code"] },
          { id: "F1",       type: "Format",   desc: "Numeric, 8 / 12 / 13 / 14 digits",
            cols: ["GTIN-Inner"] },
          { id: "F2",       type: "Format",   desc: "8-digit zero-padded ID (e.g. 01010100)",
            cols: ["Attribute Group ID"] },
          { id: "F3",       type: "Format",   desc: "Exactly 8 digits when populated",
            cols: ["Taric Code/Commodity Code"] },
          { id: "F4",       type: "Format",   desc: "Must be a whole number",
            cols: ["SUPC","Case Pack","Split Pack","Splits Per Case","Cases per Layer (Standard Pallet)","Layers per Pallet (Standard Pallet)","Cases per Layer (Euro Pallet)","Layers per Pallet (Euro Pallet)","Shelf Life Period In Days (Manufacturer)","Shelf Life Period in Days (Sysco)"] },
          { id: "F5",       type: "Format",   desc: "Must be a valid number",
            cols: ["Case Size","Case Net Weight","Case Tare Weight","Case True Net Weight (Drained/Glazed)","Case Catch Weight Range From","Case Catch Weight Range To","Case Length","Case Width","Case Height","Split Size","Split Net Weight","Split Tare Weight","Split True Net Weight (Drained/Glazed)","Split Length","Split Width","Split Height","Energy Kcal","Energy KJ","Fat","Of which Saturates","Of which Mono-Unsaturates","Of which Polyunsaturates","Of which Trans Fats","Carbohydrate","Of which Sugars","Of which Polyols","Of which Starch","Fibre","Protein","Salt","Sodium"] },
          { id: "F6",       type: "Format",   desc: "Valid ISO 3166-1 alpha-2 country code",
            cols: ["Country Of Origin - Manufactured","Country Of Origin - Packed","Country Of Origin - Sold From","Country Of Origin - Raw Ingredients"] },
          { id: "F7",       type: "Format",   desc: "No disallowed special characters (approved: % & ( ) * + - . / ™ ® + accents)",
            cols: ["True Vendor Name","First & Second Word","Description Text","Marketing Description","Warehouse Description","Invoice Description","Latin Fish Name","Cooking Instructions","Defrosting Guidelines","Handling Instructions","Storage Guidelines","Cooking Warning","Food Safety Tips"] },
          { id: "F8",       type: "Format",   desc: "≤20 chars, no spaces, approved chars only",
            cols: ["Search Name"] },
          { id: "L0",       type: "LOV",      desc: "Valid OSD Hierarchy ID from Attribute Group.xlsx",
            cols: ["Attribute Group ID"] },
          { id: "L1",       type: "LOV",      desc: "Valid Sysco or Vendor brand code from Brands.xlsx",
            cols: ["Brand Key"] },
          { id: "L4",       type: "LOV",      desc: "Valid item group code (7 codes)",
            cols: ["Item Group"] },
          { id: "L7",       type: "LOV",      desc: "Contains / May Contain / Does Not Contain",
            cols: ["Almonds","Barley","Brazil Nuts","Cashew Nuts","Celery and products thereof","Gluten at > 20 ppm","Crustaceans and products thereof","Eggs and products thereof","Fish and products thereof","Hazelnuts","Kamut","Lupin and products thereof","Macadamia Nuts/Queensland Nuts","Milk and products thereof","Molluscs and products thereof","Mustard and products thereof","Nuts","Oats","Peanuts and products thereof","Pecan Nuts","Pistachio Nuts","Rye","Sesame seeds and products thereof","Soybeans and products thereof","Spelt","Sulphur Dioxide > 10 ppm","Walnuts","Wheat"] },
          { id: "L8",       type: "LOV",      desc: "Yes / No",
            cols: ["Dairy Free","Gluten Free","Halal","Kosher","Organic","Vegan","Vegetarian","Biodegradable or Compostable","Recyclable","Hazardous Material","Product Warranty","Perishable Product/Date Tracked"] },
          { id: "Rule 12",  type: "Business", desc: "'Perishable Product/Date Tracked' = Yes only allowed for food Attribute Group IDs",
            cols: ["Perishable Product/Date Tracked","Attribute Group ID"] },
          { id: "L9",       type: "LOV",      desc: "10000000000009, 20000000000009, 30000000000009, 40000000000009, 50000000000009, 60000000000009, 70000000000009, 80000000000009",
            cols: ["Generic GTIN"] },
          { id: "L10",      type: "LOV",      desc: "Must be an approved 'FIRST SECOND' word pair (800+ valid combinations)",
            cols: ["First & Second Word"] },
        ],
      },
      {
        name: "Local Product Data",
        key: "local_file",
        status: "rules-defined",
        ruleCount: 12,
        columns: [
          "SUPC","Legal Entity","Status","Local Product Description","Proprietary Product?",
          "Customer Product","Split Product","Default Vendor","Vendor Product Code",
          "Ecom Description","Ecom Hierarchy Level 2 ID","Item Buyer Group","Lots",
          "Traffic Lights","Storage Area","Min Temperature","Max Temperature",
          "Item VAT - Purchasing","Item VAT - Selling","MSC Chain of Custody Number",
          "Shelf Life Period in Days (Customer)","Product Source Type","EU Address Labelling",
          "Export Health Certificate (EHC)","Export Health Certificate Number",
          "Certificate Of Inspection (COI)","Private Attestation (PA)",
          "PA Subject to import controls at Border Control Post","Meursing Code",
          "Conventional rate of Duty %","Customs Duty","STEP ID",
        ],
        ruledCols: {
          "SUPC": "Business",
          "STEP ID": "Business",
          "Local Product Description": "Format", "Ecom Description": "Format",
          "Legal Entity": "LOV",
          "Status": "LOV",
          "Proprietary Product?": "LOV", "Split Product": "LOV",
          "Min Temperature": "LOV", "Max Temperature": "LOV",
          "Item VAT - Purchasing": "LOV", "Item VAT - Selling": "LOV",
          "Item Buyer Group": "LOV",
          "Storage Area": "LOV",
          "Product Source Type": "LOV",
          "Ecom Hierarchy Level 2 ID": "LOV",
        },
        rules: [
          { id: "LCL-U0", type: "Business", desc: "SUPC must be unique",
            cols: ["SUPC"] },
          { id: "LCL-U1", type: "Business", desc: "STEP ID must be unique",
            cols: ["STEP ID"] },
          { id: "LCL-F1", type: "Format",   desc: "No disallowed special characters (approved: % & ( ) * + - . / ™ ® + accents)",
            cols: ["Local Product Description","Ecom Description"] },
          { id: "LCL-L1", type: "LOV",      desc: "Brakes, Fresh_Direct, Medina, Classic_Drinks, Sysco_France, LAG, Ekofisk, Sysco_ROI, Sysco_Northern_Ireland, Fruktservice, KFF, Menigo, Ready_Chef",
            cols: ["Legal Entity"] },
          { id: "LCL-L2", type: "LOV",      desc: "Active / Delisted / Archived",
            cols: ["Status"] },
          { id: "LCL-L3", type: "LOV",      desc: "Yes / No",
            cols: ["Proprietary Product?","Split Product"] },
          { id: "LCL-L4", type: "LOV",      desc: "TEMP18 (-18°C) / TEMP0 (0°C) / TEMP5 (5°C) / TEMP8 (8°C)",
            cols: ["Min Temperature","Max Temperature"] },
          { id: "LCL-L5", type: "LOV",      desc: "I-STD / I-ZERO / I-RED",
            cols: ["Item VAT - Purchasing","Item VAT - Selling"] },
          { id: "LCL-L9", type: "LOV",      desc: "Valid Ecom Hierarchy Level 2 ID (e.g. 1000100 = Alcohol, 1100100 = Bakery & Savoury, 2500100 = Meat & Poultry…)",
            cols: ["Ecom Hierarchy Level 2 ID"] },
          { id: "LCL-L8", type: "LOV",      desc: "STOCKED (Stocked) / JUST_IN_TIME (Just In Time) / LEAD_TIME (Lead Time) / MAKE_TO_ORDER (Make to Order)",
            cols: ["Product Source Type"] },
          { id: "LCL-L7", type: "LOV",      desc: "F (Freezer) / C (Cooler) / D (Dry)",
            cols: ["Storage Area"] },
          { id: "LCL-L6", type: "LOV",      desc: "Valid ID from reference/Buyer Group.xlsx",
            cols: ["Item Buyer Group"] },
        ],
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
        ruleCount: 8,
        columns: ["StepID","Master Vendor Code","Vendor Name","Company Registration Number","Trade/Indirect Vendor","VAT Registration Number","Intercompany/Trading Partner","Global Location Number","Hold Harmless","Certificate of Insurance","Search Name","Legal Name","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code"],
        ruledCols: {
          "StepID": "Business",
          "Company Registration Number": "Business",
          "Trade/Indirect Vendor": "LOV",
          "Intercompany/Trading Partner": "LOV",
          "Country": "LOV",
          "Address Line 1": "Business", "Town/City": "Business", "Zip/Postal Code": "Business",
          "Search Name": "Format",
        },
        rules: [
          { id: "V-U1",  type: "Business", desc: "StepID must be unique",                                                                       cols: ["StepID"] },
          { id: "V-B1",  type: "Business", desc: "Address Line 1, Town/City, Zip/Postal Code are mandatory",                                    cols: ["Address Line 1","Town/City","Zip/Postal Code"] },
          { id: "V-B2",  type: "Business", desc: "Company Registration Number is mandatory and must be unique",                                  cols: ["Company Registration Number"] },
          { id: "V-L1",  type: "LOV",      desc: "Valid entity code: GB01, GB57, GB58, GB59, GB80, IE01–IE90, HK91–HK92, SE01–SE05, SE99",     cols: ["Intercompany/Trading Partner"] },
          { id: "V-L9",  type: "LOV",      desc: "Trade / Indirect",                                                                            cols: ["Trade/Indirect Vendor"] },
          { id: "V-L11", type: "LOV",      desc: "ISO 3166-1 alpha-2 country code",                                                             cols: ["Country"] },
          { id: "V-F1",  type: "Format",   desc: "≤20 chars, no spaces, approved chars only",                                                   cols: ["Search Name"] },
        ],
      },
      {
        name: "LEA Invoice",
        key: "lea_invoice",
        status: "rules-defined",
        ruleCount: 6,
        columns: ["SUVC Invoice","Legal Entity","Cost Centre","Method of Payment","VAT Group","Known As","Status"],
        ruledCols: { "SUVC Invoice": "Business", "Legal Entity": "LOV", "Cost Centre": "LOV", "Method of Payment": "LOV", "VAT Group": "LOV", "Status": "LOV" },
        rules: [
          { id: "V-U2",  type: "Business", desc: "SUVC Invoice must be unique within the LEA Invoice sheet",                                                                                                                                                                            cols: ["SUVC Invoice"] },
          { id: "V-L8",  type: "LOV",      desc: "Brakes, Fresh_Direct, Medina, Classic_Drinks, Sysco_France, LAG, Ekofisk, Sysco_ROI, Sysco_Northern_Ireland, Fruktservice, KFF, Menigo, Ready_Chef",                                                                                 cols: ["Legal Entity"] },
          { id: "V-L2",  type: "LOV",      desc: "21 valid codes: C_DD_BASE, C_DD_OTHER, C_CASH, C_CARD, C_STRDCARD, C_BANK, C_SWISH, C_AUTOGIRO, C_CHEQUE, C_CONTRA, V_BACS_BAS, V_BACS_OTH, V_CASH, V_CARD, V_SWISH, V_AUTOGIRO, V_BANK, V_CONTRA, V_DD_BASE, V_DD_OTHER, V_CHEQUE", cols: ["Method of Payment"] },
          { id: "V-L3",  type: "LOV",      desc: "I-STD / I-ZERO / I-RED",                                                                                                                                                                                                             cols: ["VAT Group"] },
          { id: "V-L4",  type: "LOV",      desc: "Active / Delisted / Archived",                                                                                                                                                                                                        cols: ["Status"] },
          { id: "V-L13", type: "LOV",      desc: "28 codes: W10025, W10075, T15005, T15015, N20015, N20005, N20020, N20050, P50890, E55999, E55074, A30899, R45831, F35005, I65005, H40005, C70999, X75005, A30099, S25070, S25845, S25846, S25847, S25849, S25850, S25855, S25999, S25305", cols: ["Cost Centre"] },
        ],
      },
      {
        name: "OS",
        key: "os",
        status: "rules-defined",
        ruleCount: 3,
        columns: ["SUVC Ordering/Shipping","Vendor Name","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code","Search Name","Legal Name"],
        ruledCols: { "SUVC Ordering/Shipping": "Business", "Country": "LOV", "Search Name": "Format" },
        rules: [
          { id: "V-U3",  type: "Business", desc: "SUVC Ordering/Shipping must be unique within the OS sheet", cols: ["SUVC Ordering/Shipping"] },
          { id: "V-L12", type: "LOV",      desc: "ISO 3166-1 alpha-2 country code",                           cols: ["Country"] },
          { id: "V-F2",  type: "Format",   desc: "≤20 chars, no spaces, approved chars only",                 cols: ["Search Name"] },
        ],
      },
      {
        name: "LEA OS",
        key: "lea_os",
        status: "rules-defined",
        ruleCount: 7,
        columns: ["SUVC Ordering/Shipping","Legal Entity","Delivery Terms","Buyer Group","Mode of Delivery","Known As","Warehouse Code","Vendor Managed Inventory","Nominated Vendor Indicator","Duty Paid/Bond","Status"],
        ruledCols: { "SUVC Ordering/Shipping": "Business", "Legal Entity": "LOV", "Delivery Terms": "LOV", "Mode of Delivery": "LOV", "Buyer Group": "LOV", "Warehouse Code": "LOV", "Status": "LOV" },
        rules: [
          { id: "V-U4",  type: "Business", desc: "SUVC Ordering/Shipping must be unique within the LEA OS sheet",                                                                                                                       cols: ["SUVC Ordering/Shipping"] },
          { id: "V-L10", type: "LOV",      desc: "Brakes, Fresh_Direct, Medina, Classic_Drinks, Sysco_France, LAG, Ekofisk, Sysco_ROI, Sysco_Northern_Ireland, Fruktservice, KFF, Menigo, Ready_Chef",                                  cols: ["Legal Entity"] },
          { id: "V-L5",  type: "LOV",      desc: "Incoterms: CFR, CIF, CIP, CPT, DAP, DDP, DPU, EXW, FAS, FCA, FOB",                                                                                                                   cols: ["Delivery Terms"] },
          { id: "V-L6",  type: "LOV",      desc: "23 codes: 3PL, AIR, AMB_TRK, ANY, BACK_HAUL, BICYCLE, BOAT, BULK_CRR, COLD_STRG, CONSOL, CONT_SHIP, COURIER, CROSS_DOCK, CUST_COLL, DIRECT, DRON_DLV, FROZ_TRK, INTERMOD, PICKUP, PIPELINE, REFR_TRK, TRAIN, TRUCK", cols: ["Mode of Delivery"] },
          { id: "V-L7",  type: "LOV",      desc: "Active / Delisted / Archived",                                                                                                                                                        cols: ["Status"] },
          { id: "V-L14", type: "LOV",      desc: "Valid ID from reference/Buyer Group.xlsx (same LOV as Local Product Data — Item Buyer Group)",                                                                                         cols: ["Buyer Group"] },
          { id: "V-L15", type: "LOV",      desc: "IW001 (Local Isle of Wight), MK001 (Millbrook), EK001 (Ekofisk)",                                                                                                                     cols: ["Warehouse Code"] },
        ],
      },
    ],
  },

  Customers: {
    description: "Customer master data — 7 templates covering financial and delivery setup.",
    templates: [
      {
        name: "PT",
        key: "pt",
        status: "rules-defined",
        ruleCount: 1,
        columns: ["Company Prefix","Invoice Customer Code","Payment Terms","Currency Code"],
        ruledCols: { "Company Prefix": "LOV" },
        rules: [
          { id: "C-L16", type: "LOV", desc: "GBBR, GBFD, GBKF, GBMD, SWME, SWEK, SWFS, SWSS, IRRI, IRNI, IRRC, IRCD, FRFR, FRLG",
            cols: ["Company Prefix"] },
        ],
      },
      {
        name: "Invoice",
        key: "invoice",
        status: "rules-defined",
        ruleCount: 9,
        columns: ["Step ID","EU Master Customer Code","Customer Type","Invoice Customer Name","First Name","Last Name","Employee Number","Is Customer a Registered Company","Company Registration Number","VAT Registration Number","Intercompany/Trading Partner","Customer Group","Legal Name - Invoice","Search Name - Invoice","Limited Address","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code"],
        ruledCols: {
          "Step ID": "Business",
          "Customer Type": "LOV", "Intercompany/Trading Partner": "LOV",
          "Customer Group": "LOV", "Country": "LOV",
          "Is Customer a Registered Company": "LOV",
          "Search Name - Invoice": "Format",
          "First Name": "Business", "Last Name": "Business",
          "Employee Number": "Business", "Invoice Customer Name": "Business",
          "Company Registration Number": "Business", "VAT Registration Number": "Business",
          "Legal Name - Invoice": "Business", "Limited Address": "Business",
        },
        rules: [
          { id: "C-U1",  type: "Business", desc: "Step ID must be unique within the Invoice sheet",                                                                                                                                                                                                                                                            cols: ["Step ID"] },
          { id: "C-L1",  type: "LOV",      desc: "Valid entity code: GB01, GB57, GB58, GB59, GB80, IE01–IE90, HK91–HK92, SE01–SE05, SE99",                                                                                                                                                                                                                    cols: ["Intercompany/Trading Partner"] },
          { id: "C-L2",  type: "LOV",      desc: "TRS / TRP / LCC / CMU / OTH / WHL / MIS",                                                                                                                                                                                                                                                                   cols: ["Customer Group"] },
          { id: "C-L14", type: "LOV",      desc: "ISO 3166-1 alpha-2 country code",                                                                                                                                                                                                                                                                            cols: ["Country"] },
          { id: "C-F1",  type: "Format",   desc: "≤20 chars, no spaces, approved chars only",                                                                                                                                                                                                                                                                  cols: ["Search Name - Invoice"] },
          { id: "C-L18", type: "LOV",      desc: "Customer / Employee",                                                                                                                                                                                                                                                                                        cols: ["Customer Type"] },
          { id: "C-L19", type: "LOV",      desc: "Yes / No",                                                                                                                                                                                                                                                                                                   cols: ["Is Customer a Registered Company"] },
          { id: "C-B1",  type: "Business", desc: "If Customer Type = Employee → First Name / Last Name / Employee Number required; Invoice Customer Name, VAT Registration Number, Legal Name - Invoice, Search Name - Invoice, Limited Address, Company Registration Number must be empty; Is Customer a Registered Company must be 'No'",
            cols: ["Customer Type","First Name","Last Name","Employee Number","Invoice Customer Name","VAT Registration Number","Legal Name - Invoice","Search Name - Invoice","Limited Address","Company Registration Number","Is Customer a Registered Company"] },
          { id: "C-B2",  type: "Business", desc: "If Is Customer a Registered Company = Yes → Company Registration Number required",                                                                                                                                                                                                                           cols: ["Is Customer a Registered Company","Company Registration Number"] },
        ],
      },
      {
        name: "LEA Invoice",
        key: "lea_invoice",
        status: "rules-defined",
        ruleCount: 7,
        columns: ["Invoice Customer Code","Legal Entity","Legal Entity Customer Master Code","VAT Group","Method of Payment","Reference Code","Customer Own Account Number","Known As - Invoice","Seasonal","Cost Centre","Division","Sales Group","Status"],
        ruledCols: { "Legal Entity": "LOV", "VAT Group": "LOV", "Method of Payment": "LOV", "Seasonal": "LOV", "Cost Centre": "LOV", "Division": "LOV", "Status": "LOV" },
        rules: [
          { id: "C-L12", type: "LOV", desc: "Brakes, Fresh_Direct, Medina, Classic_Drinks, Sysco_France, LAG, Ekofisk, Sysco_ROI, Sysco_Northern_Ireland, Fruktservice, KFF, Menigo, Ready_Chef", cols: ["Legal Entity"] },
          { id: "C-L3",  type: "LOV", desc: "16 codes: BRAKES, COUNTRY_CHOICE, BCE, KFF, FRESH_DIRECT, MEDINA, SYSCO_ROI, SYSCO_NI, CLASSIC_DRINKS, READY_CHEF, MENIGO, SERVICESTYCKARNA, FRUKTSERVICE, EKOFISK, SYSCO_FRANCE, LAG", cols: ["Division"] },
          { id: "C-L4",  type: "LOV", desc: "21 valid codes: C_DD_BASE, C_DD_OTHER, C_CASH, C_CARD, C_STRDCARD, C_BANK, C_SWISH, C_AUTOGIRO, C_CHEQUE, C_CONTRA, V_BACS_BAS, V_BACS_OTH, V_CASH, V_CARD, V_SWISH, V_AUTOGIRO, V_BANK, V_CONTRA, V_DD_BASE, V_DD_OTHER, V_CHEQUE", cols: ["Method of Payment"] },
          { id: "C-L7",  type: "LOV", desc: "I-STD / I-ZERO / I-RED",         cols: ["VAT Group"] },
          { id: "C-L8",  type: "LOV", desc: "01, 02, 03, 04, 05, 06, 07, 99", cols: ["Seasonal"] },
          { id: "C-L9",  type: "LOV", desc: "Active / Delisted / Archived",    cols: ["Status"] },
          { id: "C-L17", type: "LOV", desc: "28 codes: W10025, W10075, T15005, T15015, N20015, N20005, N20020, N20050, P50890, E55999, E55074, A30899, R45831, F35005, I65005, H40005, C70999, X75005, A30099, S25070, S25845, S25846, S25847, S25849, S25850, S25855, S25999, S25305", cols: ["Cost Centre"] },
        ],
      },
      {
        name: "OS",
        key: "os",
        status: "rules-defined",
        ruleCount: 7,
        columns: ["Company Prefix","Ordering/Shipping Customer Code","Ordering/Shipping Customer Name","First Name","Last Name","Legal Name - Delivery","Search Name  - Delivery","Segment","Subsegment","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/Postal Code"],
        ruledCols: {
          "Company Prefix": "LOV",
          "Ordering/Shipping Customer Code": "Business",
          "Country": "LOV",
          "Search Name  - Delivery": "Format",
          "First Name": "Business", "Last Name": "Business",
          "Ordering/Shipping Customer Name": "Business", "Legal Name - Delivery": "Business",
          "Segment": "LOV", "Subsegment": "LOV",
        },
        rules: [
          { id: "C-L22", type: "LOV",      desc: "GBBR, GBFD, GBKF, GBMD, SWME, SWEK, SWFS, SWSS, IRRI, IRNI, IRRC, IRCD, FRFR, FRLG",                                                                      cols: ["Company Prefix"] },
          { id: "C-U3",  type: "Business", desc: "Ordering/Shipping Customer Code must be unique within the OS sheet",                                                                                         cols: ["Ordering/Shipping Customer Code"] },
          { id: "C-L15", type: "LOV",      desc: "ISO 3166-1 alpha-2 country code",                                                                                                                            cols: ["Country"] },
          { id: "C-F2",  type: "Format",   desc: "≤20 chars, no spaces, approved chars only",                                                                                                                  cols: ["Search Name  - Delivery"] },
          { id: "C-B3",  type: "Business", desc: "If First Name and Last Name are both filled (employee) → Ordering/Shipping Customer Name, Legal Name - Delivery, Search Name - Delivery must be empty",      cols: ["First Name","Last Name","Ordering/Shipping Customer Name","Legal Name - Delivery","Search Name  - Delivery"] },
          { id: "C-L25", type: "LOV",      desc: "EDU (Education), HEA (Healthcare), LOD (Lodging), NTR (Non Trade), OTH (Other Food Locations), REC (Recreation), RES (Restaurant), PUB (Pubs & Bars), RET (Retail Food), MISC (Miscellaneous)", cols: ["Segment"] },
          { id: "C-L26", type: "LOV",      desc: "83 subsegment codes — E10–E24, H10–H40, L10–L50, N10–N50, O10–O65, S05–S65, R05–R25, P30–P31, T05–T50, M0", cols: ["Subsegment"] },
        ],
      },
      {
        name: "LEA OS",
        key: "lea_os",
        status: "rules-defined",
        ruleCount: 8,
        columns: ["Ordering/Shipping Customer Code","Legal Entity","Company Chain Code","Delivery Terms","Mode Of Delivery","Known As - Delivery","Warehouse Code","Reference Code","Customer Own Account Number","Sales Area Manager Code","Seasonal","Status"],
        ruledCols: { "Ordering/Shipping Customer Code": "Business", "Legal Entity": "LOV", "Delivery Terms": "LOV", "Mode Of Delivery": "LOV", "Warehouse Code": "LOV", "Sales Area Manager Code": "LOV", "Seasonal": "LOV", "Status": "LOV" },
        rules: [
          { id: "C-U4",  type: "Business", desc: "Ordering/Shipping Customer Code must be unique within the LEA OS sheet",                                                                                      cols: ["Ordering/Shipping Customer Code"] },
          { id: "C-L13", type: "LOV",      desc: "Brakes, Fresh_Direct, Medina, Classic_Drinks, Sysco_France, LAG, Ekofisk, Sysco_ROI, Sysco_Northern_Ireland, Fruktservice, KFF, Menigo, Ready_Chef",         cols: ["Legal Entity"] },
          { id: "C-L5",  type: "LOV",      desc: "23 codes: 3PL, AIR, AMB_TRK, ANY, BACK_HAUL, BICYCLE, BOAT, BULK_CRR, COLD_STRG, CONSOL, CONT_SHIP, COURIER, CROSS_DOCK, CUST_COLL, DIRECT, DRON_DLV, FROZ_TRK, INTERMOD, PICKUP, PIPELINE, REFR_TRK, TRAIN, TRUCK", cols: ["Mode Of Delivery"] },
          { id: "C-L6",  type: "LOV",      desc: "Incoterms: CFR, CIF, CIP, CPT, DAP, DDP, DPU, EXW, FAS, FCA, FOB",                                                                                          cols: ["Delivery Terms"] },
          { id: "C-L10", type: "LOV",      desc: "01, 02, 03, 04, 05, 06, 07, 99",                                                                                                                             cols: ["Seasonal"] },
          { id: "C-L11", type: "LOV",      desc: "Active / Delisted / Archived",                                                                                                                               cols: ["Status"] },
          { id: "C-L23", type: "LOV",      desc: "IW001 (Local Isle of Wight), MK001 (Millbrook), EK001 (Ekofisk)",                                                                                            cols: ["Warehouse Code"] },
          { id: "C-L24", type: "LOV",      desc: "31 ASM codes: ASM20000–ASM20020 (GB), ASM25000–ASM25008 (SE)",                                                                                               cols: ["Sales Area Manager Code"] },
        ],
      },
      {
        name: "Employee Invoice",
        key: "employee_invoice",
        status: "rules-defined",
        ruleCount: 1,
        columns: ["STEP ID","First Name","Last Name","Employee Number","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/PostalCode"],
        ruledCols: { "STEP ID": "Business" },
        rules: [
          { id: "C-U2", type: "Business", desc: "STEP ID must be unique within the Employee Invoice sheet", cols: ["STEP ID"] },
        ],
      },
      {
        name: "Employee OS",
        key: "employee_os",
        status: "rules-defined",
        ruleCount: 4,
        columns: ["Invoice Company Prefix","Invoice Customer Code","Copy Invoice Code","Copy Invoice Address","First Name","Last Name","Legal Entity","Country","Address Line 1","Address Line 2","Town/City","County/District","Zip/PostalCode"],
        ruledCols: {
          "Invoice Company Prefix": "LOV",
          "Copy Invoice Code": "LOV", "Copy Invoice Address": "LOV",
          "Invoice Customer Code": "Business",
          "Address Line 1": "Business", "Address Line 2": "Business",
          "Town/City": "Business", "County/District": "Business",
          "Zip/PostalCode": "Business", "Country": "Business",
        },
        rules: [
          { id: "C-L27", type: "LOV",      desc: "GBBR, GBFD, GBKF, GBMD, SWME, SWEK, SWFS, SWSS, IRRI, IRNI, IRRC, IRCD, FRFR, FRLG",                                                                                                                                              cols: ["Invoice Company Prefix"] },
          { id: "C-L20", type: "LOV",      desc: "Yes / No",                                                                                                                                                                                                                                    cols: ["Copy Invoice Code"] },
          { id: "C-L21", type: "LOV",      desc: "Yes / No",                                                                                                                                                                                                                                    cols: ["Copy Invoice Address"] },
          { id: "C-B4",  type: "Business", desc: "If Copy Invoice Address = Yes → Address Line 1, Address Line 2, Town/City, County/District, Zip/PostalCode, Country must exactly match the corresponding Invoice row (matched by Invoice Customer Code → EU Master Customer Code)",
            cols: ["Copy Invoice Address","Invoice Customer Code","Address Line 1","Address Line 2","Town/City","County/District","Zip/PostalCode","Country"] },
        ],
      },
    ],
  },
};

// ─── Components ─────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  if (status === "rules-defined")
    return <Badge variant="success"><CheckCircle2 className="h-3 w-3" /> Rules defined</Badge>;
  return <Badge variant="secondary"><Clock className="h-3 w-3" /> Pending</Badge>;
}

function RuleRow({ rule }) {
  return (
    <tr className="border-t border-slate-100 dark:border-slate-800">
      <td className="py-1.5 pr-3 align-top">
        <span className="font-mono text-[11px] font-semibold text-slate-600 dark:text-slate-400 whitespace-nowrap">
          {rule.id}
        </span>
      </td>
      <td className="py-1.5 pr-3 align-top">
        <span className={`inline-block text-[10px] px-1.5 py-0.5 rounded font-medium whitespace-nowrap ${TYPE_STYLE[rule.type]}`}>
          {rule.type}
        </span>
      </td>
      <td className="py-1.5 pr-3 align-top">
        <span className="text-[11px] font-mono text-brand-600 dark:text-brand-400 whitespace-nowrap">
          {rule.col}
        </span>
      </td>
      <td className="py-1.5 align-top">
        <span className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
          {rule.desc}
        </span>
      </td>
    </tr>
  );
}

function TemplateCard({ tmpl }) {
  const [open, setOpen] = useState(false);
  const ruledMap = tmpl.ruledCols ?? {};   // col → "LOV"|"Format"|"Business"
  const hasRules = tmpl.rules.length > 0;

  // col → ["Rule X: desc", ...] derived from rules[].cols
  const colTooltip = useMemo(() => {
    const map = {};
    (tmpl.rules ?? []).forEach(rule => {
      (rule.cols ?? []).forEach(col => {
        if (!map[col]) map[col] = [];
        map[col].push(`${rule.id}: ${rule.desc}`);
      });
    });
    return map;
  }, [tmpl.rules]);

  return (
    <div className="rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
      {/* Header — clickable when there are rules */}
      <button
        onClick={() => hasRules && setOpen(v => !v)}
        className={[
          "w-full flex items-center gap-3 px-4 py-3 text-left",
          hasRules
            ? "hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer"
            : "cursor-default",
        ].join(" ")}
      >
        {hasRules
          ? (open
              ? <ChevronDown className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
              : <ChevronRight className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />)
          : <FileSpreadsheet className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
        }
        <span className="text-sm font-medium text-slate-800 dark:text-slate-200 flex-1">{tmpl.name}</span>
        <StatusBadge status={tmpl.status} />
        {tmpl.ruleCount > 0 && (
          <Badge variant="outline" className="tabular-nums">{tmpl.ruleCount} rules</Badge>
        )}
        {tmpl.columns.length > 0 && (
          <span className="text-xs text-slate-400 tabular-nums">{tmpl.columns.length} cols</span>
        )}
      </button>

      {/* Column chips */}
      {tmpl.columns.length > 0 && (
        <div className="px-4 pb-3 flex flex-wrap gap-1.5">
          {tmpl.columns.map(col => {
            const ruleType = ruledMap[col];
            const tips = colTooltip[col];
            return (
              <span key={col} className="relative group/chip">
                <span className={`inline-block text-[11px] px-1.5 py-0.5 rounded font-mono border cursor-default ${ruleType ? CHIP_STYLE[ruleType] : CHIP_DEFAULT}`}>
                  {col}
                </span>
                {tips && (
                  <span className="pointer-events-none absolute bottom-full left-0 mb-1.5 z-50 hidden group-hover/chip:block w-max max-w-[280px] rounded-md bg-slate-800 dark:bg-slate-700 px-2.5 py-2 shadow-lg">
                    {tips.map((t, i) => (
                      <span key={i} className="block text-[10px] leading-relaxed text-slate-200 whitespace-normal">{t}</span>
                    ))}
                  </span>
                )}
              </span>
            );
          })}
        </div>
      )}

      {/* Rules panel */}
      {open && hasRules && (
        <div className="border-t border-slate-100 dark:border-slate-800 px-4 py-3 bg-slate-50/60 dark:bg-slate-800/30">
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left text-[10px] font-semibold uppercase tracking-wide text-slate-400 pb-1.5 pr-3">ID</th>
                <th className="text-left text-[10px] font-semibold uppercase tracking-wide text-slate-400 pb-1.5 pr-3">Type</th>
                <th className="text-left text-[10px] font-semibold uppercase tracking-wide text-slate-400 pb-1.5 pr-3">Column</th>
                <th className="text-left text-[10px] font-semibold uppercase tracking-wide text-slate-400 pb-1.5">Description</th>
              </tr>
            </thead>
            <tbody>
              {tmpl.rules.map(r => <RuleRow key={r.id} rule={r} />)}
            </tbody>
          </table>
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

      {/* Legend */}
      <div className="flex items-center gap-4 text-[11px] text-slate-400">
        {["LOV", "Format", "Business"].map(t => (
          <span key={t} className="flex items-center gap-1.5">
            <span className={`inline-block text-[10px] px-1 rounded ${TYPE_STYLE[t]}`}>{t}</span>
          </span>
        ))}
        <span className="ml-auto italic">Click a template to expand its rules</span>
      </div>

      <div className="space-y-2">
        {templates.map(t => <TemplateCard key={t.key} tmpl={t} />)}
      </div>
    </div>
  );
}

// ─── Main ───────────────────────────────────────────────────────────────────

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
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Rules</h1>
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
