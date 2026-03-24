import { useEffect, useRef, useState, useMemo } from "react";
import { Search, X, ChevronRight, ArrowLeft } from "lucide-react";

import API from "../api.js";

export default function LovSearchModal({ onClose }) {
  const [attributes, setAttributes] = useState([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [values, setValues] = useState([]);
  const [valQuery, setValQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/lovs/attributes`)
      .then((r) => r.json())
      .then(setAttributes)
      .catch(() => {});
  }, []);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") {
        if (selected) {
          setSelected(null);
          setValQuery("");
          setValues([]);
        } else onClose();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose, selected]);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setValues([]);
    setValQuery("");
    fetch(`${API}/lovs?attribute=${encodeURIComponent(selected)}`)
      .then((r) => r.json())
      .then(setValues)
      .catch(() => setValues([]))
      .finally(() => setLoading(false));
  }, [selected]);

  useEffect(() => {
    if (!selected) inputRef.current?.focus();
    else setTimeout(() => inputRef.current?.focus(), 50);
  }, [selected]);

  const filteredAttrs = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q
      ? attributes.filter((a) => a.toLowerCase().includes(q))
      : attributes;
  }, [attributes, query]);

  const filteredValues = useMemo(() => {
    const q = valQuery.trim().toLowerCase();
    return q
      ? values.filter(
          (v) =>
            v.key?.toLowerCase().includes(q) ||
            v.description?.toLowerCase().includes(q),
        )
      : values;
  }, [values, valQuery]);

  const goBack = () => {
    setSelected(null);
    setValQuery("");
    setValues([]);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl mx-4 rounded-2xl overflow-hidden flex flex-col shadow-2xl border border-slate-200 dark:border-slate-700/80"
        style={{
          maxHeight: "min(80vh, 680px)",
          background: "var(--modal-bg, white)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Search bar ──────────────────────────────────────────────── */}
        <div className="bg-white dark:bg-slate-900 flex items-center gap-3 px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
          {selected ? (
            <button
              onClick={goBack}
              className="flex-shrink-0 flex items-center justify-center h-7 w-7 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
          ) : (
            <Search className="h-5 w-5 text-slate-400 flex-shrink-0" />
          )}

          <input
            ref={inputRef}
            value={selected ? valQuery : query}
            onChange={(e) =>
              selected ? setValQuery(e.target.value) : setQuery(e.target.value)
            }
            placeholder={
              selected
                ? `Filter in ${selected}…`
                : "Search for a LOV attribute…"
            }
            className="flex-1 text-base bg-transparent outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500"
          />

          {(selected ? valQuery : query) ? (
            <button
              onClick={() => (selected ? setValQuery("") : setQuery(""))}
              className="flex-shrink-0 flex items-center justify-center h-7 w-7 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 dark:hover:text-slate-300 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          ) : (
            <kbd className="flex-shrink-0 px-2 py-1 text-[11px] font-mono rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 border border-slate-200 dark:border-slate-700">
              Esc
            </kbd>
          )}
        </div>

        {/* ── Breadcrumb when attribute selected ──────────────────────── */}
        {selected && (
          <div className="bg-slate-50 dark:bg-slate-800/50 px-5 py-2 flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 flex-shrink-0">
            <span className="text-xs text-slate-400 dark:text-slate-500">
              Attribute
            </span>
            <ChevronRight className="h-3 w-3 text-slate-300 dark:text-slate-600" />
            <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">
              {selected}
            </span>
            <span className="ml-auto text-xs text-slate-400">
              {loading
                ? "…"
                : `${filteredValues.length} value${filteredValues.length > 1 ? "s" : ""}`}
            </span>
          </div>
        )}

        {/* ── Body ────────────────────────────────────────────────────── */}
        <div className="overflow-y-auto flex-1 bg-white dark:bg-slate-900">
          {/* Attribute list */}
          {!selected &&
            (filteredAttrs.length === 0 ? (
              <div className="py-16 text-center">
                <p className="text-sm text-slate-400">
                  No attribute found for "
                  <span className="text-slate-600 dark:text-slate-300">
                    {query}
                  </span>
                  "
                </p>
              </div>
            ) : (
              <ul className="py-2">
                {filteredAttrs.map((attr) => (
                  <li key={attr}>
                    <button
                      onClick={() => setSelected(attr)}
                      className="w-full text-left px-5 py-2.5 flex items-center justify-between gap-3 hover:bg-slate-50 dark:hover:bg-slate-800/60 group transition-colors"
                    >
                      <span className="text-sm text-slate-700 dark:text-slate-200 group-hover:text-slate-900 dark:group-hover:text-slate-100 transition-colors">
                        {attr}
                      </span>
                      <ChevronRight className="h-4 w-4 text-slate-300 dark:text-slate-600 group-hover:text-brand-400 group-hover:translate-x-0.5 transition-all flex-shrink-0" />
                    </button>
                  </li>
                ))}
              </ul>
            ))}

          {/* Values table */}
          {selected &&
            (loading ? (
              <div className="py-16 text-center text-sm text-slate-400">
                Loading…
              </div>
            ) : filteredValues.length === 0 ? (
              <div className="py-16 text-center text-sm text-slate-400">
                {valQuery ? `No results for "${valQuery}"` : "No values."}
              </div>
            ) : (
              <table className="w-full">
                <thead className="sticky top-0 bg-slate-50/90 dark:bg-slate-800/90 backdrop-blur-sm border-b border-slate-100 dark:border-slate-700/50">
                  <tr>
                    <th className="px-5 py-2.5 text-left text-[10px] font-semibold uppercase tracking-widest text-slate-400 w-44">
                      Key
                    </th>
                    <th className="px-5 py-2.5 text-left text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50">
                  {filteredValues.map((v, i) => (
                    <tr
                      key={i}
                      className="hover:bg-slate-50/80 dark:hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="px-5 py-3">
                        <code className="text-xs font-mono font-semibold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/20 px-2 py-0.5 rounded-md">
                          {v.key}
                        </code>
                      </td>
                      <td className="px-5 py-3 text-sm text-slate-600 dark:text-slate-300">
                        {v.description}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ))}
        </div>

        {/* ── Footer ──────────────────────────────────────────────────── */}
        <div className="bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 px-5 py-2.5 flex-shrink-0 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">
            {selected ? (
              <>
                <span className="text-slate-500 dark:text-slate-400 font-medium">
                  {filteredValues.length}
                </span>{" "}
                value{filteredValues.length > 1 ? "s" : ""}
              </>
            ) : (
              <>
                <span className="text-slate-500 dark:text-slate-400 font-medium">
                  {filteredAttrs.length}
                </span>{" "}
                attribute{filteredAttrs.length > 1 ? "s" : ""}
              </>
            )}
          </span>
          <div className="flex items-center gap-3 text-[11px] text-slate-400">
            {selected ? (
              <span>
                <kbd className="px-1.5 py-px font-mono rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
                  Esc
                </kbd>{" "}
                to go back
              </span>
            ) : (
              <span>
                <kbd className="px-1.5 py-px font-mono rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
                  ↵
                </kbd>{" "}
                to open
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
