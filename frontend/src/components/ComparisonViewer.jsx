// ComparisonViewer.jsx
import { useState } from "react";
import { ChevronLeft, ChevronRight, Copy, Eye } from "lucide-react";
import toast from "react-hot-toast";

export default function ComparisonViewer({ result }) {
  const [page, setPage]           = useState(0);
  const [showHeatmap, setHeatmap] = useState(false);
  if (!result?.pages?.length) return null;

  const pages   = result.pages;
  const current = pages[page];
  const conf    = current.confidence || 0;
  const confColor = conf >= 0.9 ? "#22c55e" : conf >= 0.7 ? "#eab308" : "#ef4444";
  const copy = t => { navigator.clipboard.writeText(t || ""); toast.success("Copied!"); };

  const panel = { background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)", borderRadius: 10, padding: "1rem", minHeight: 200 };

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>📖 OCR Results</h2>
          <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>
            Overall confidence: <span style={{ color: confColor, fontWeight: 700 }}>{((result.overall_confidence || 0)*100).toFixed(1)}%</span>
            {" "}• Region: <span style={{ color: "var(--accent-light)" }}>{result.region || "standard"}</span>
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button onClick={() => setHeatmap(!showHeatmap)} style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 7, background: showHeatmap ? "rgba(249,115,22,0.15)" : "rgba(255,255,255,0.05)", border: "1px solid var(--border)", cursor: "pointer", color: showHeatmap ? "var(--accent-light)" : "var(--text-secondary)", fontSize: 12 }}>
            <Eye size={13} /> Heatmap
          </button>
          {pages.length > 1 && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <button onClick={() => setPage(Math.max(0, page-1))} disabled={page === 0} style={{ background: "none", border: "1px solid var(--border)", borderRadius: 7, cursor: page===0?"not-allowed":"pointer", color: page===0?"var(--text-muted)":"var(--text-primary)", padding: 6, display: "flex" }}><ChevronLeft size={16}/></button>
              <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{page+1}/{pages.length}</span>
              <button onClick={() => setPage(Math.min(pages.length-1, page+1))} disabled={page===pages.length-1} style={{ background: "none", border: "1px solid var(--border)", borderRadius: 7, cursor: page===pages.length-1?"not-allowed":"pointer", color: page===pages.length-1?"var(--text-muted)":"var(--text-primary)", padding: 6, display: "flex" }}><ChevronRight size={16}/></button>
            </div>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, color: "var(--text-secondary)" }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent)" }} />
              Kaithi OCR Output
            </div>
            <button onClick={() => copy(current.kaithi_text)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex" }}><Copy size={13}/></button>
          </div>
          <div style={{ ...panel, fontFamily: "monospace", fontSize: 14, color: "var(--text-secondary)", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
            {current.kaithi_text || <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>No OCR output</span>}
          </div>
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, color: "var(--text-secondary)" }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e" }} />
              Hindi (Devanagari)
            </div>
            <button onClick={() => copy(current.corrected_text || current.hindi_text)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex" }}><Copy size={13}/></button>
          </div>
          <div style={{ ...panel, fontFamily: "var(--hindi-font)", fontSize: 20, color: "var(--text-primary)", lineHeight: 1.9, whiteSpace: "pre-wrap" }}>
            {current.corrected_text || current.hindi_text || <span style={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--ui-font)", fontStyle: "italic" }}>No Hindi output</span>}
          </div>
        </div>
      </div>

      {showHeatmap && current.word_boxes?.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 8 }}>Confidence Heatmap (word-level)</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {current.word_boxes.slice(0, 80).map((box, i) => {
              const c = box.confidence;
              const col = c >= 0.9 ? "#86efac" : c >= 0.7 ? "#fde047" : "#fca5a5";
              const bg  = c >= 0.9 ? "rgba(34,197,94,0.2)" : c >= 0.7 ? "rgba(234,179,8,0.2)" : "rgba(239,68,68,0.2)";
              return <div key={i} title={`Confidence: ${c?(c*100).toFixed(1)+"%":"N/A"}`} style={{ padding: "3px 8px", borderRadius: 5, border: `1px solid ${col}80`, background: bg, fontSize: 11, color: col }}>{c ? `${(c*100).toFixed(0)}%` : "?"}</div>;
            })}
          </div>
        </div>
      )}

      <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--border)", display: "grid", gridTemplateColumns: "repeat(4,1fr)", textAlign: "center" }}>
        {[
          { label: "Page",       value: `${current.page_number}/${pages.length}` },
          { label: "Confidence", value: `${(conf*100).toFixed(1)}%`, color: confColor },
          { label: "Lines",      value: current.line_count || 0 },
          { label: "Time",       value: `${((current.processing_time_ms||0)/1000).toFixed(1)}s` },
        ].map(({ label, value, color }) => (
          <div key={label}>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{label}</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: color || "var(--text-primary)", marginTop: 2 }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
