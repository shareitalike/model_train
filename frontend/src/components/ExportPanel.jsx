import { useState } from "react";
import { Download, FileText, File, Code, AlignLeft, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { exportResult } from "../utils/api";

const FORMATS = [
  { id: "pdf",  label: "Searchable PDF",  icon: File,      ext: "pdf",  color: "#f87171" },
  { id: "docx", label: "Word Document",   icon: FileText,  ext: "docx", color: "#60a5fa" },
  { id: "json", label: "JSON Data",       icon: Code,      ext: "json", color: "#4ade80" },
  { id: "txt",  label: "Plain Text",      icon: AlignLeft, ext: "txt",  color: "#facc15" },
];

export default function ExportPanel({ result }) {
  const [loading, setLoading] = useState(null);

  const download = async (format, ext) => {
    setLoading(format);
    try {
      const blob = await exportResult(result, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `kaithi_ocr.${ext}`;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(url);
      toast.success(`Downloaded as ${format.toUpperCase()}`);
    } catch { toast.error(`Export failed`); }
    finally { setLoading(null); }
  };

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "1.5rem" }}>
      <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: "1rem" }}>📥 Export Results</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "0.75rem" }}>
        {FORMATS.map(({ id, label, icon: Icon, ext, color }) => (
          <button key={id} onClick={() => download(id, ext)} disabled={loading !== null}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "1.25rem 0.75rem", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 12, cursor: loading ? "not-allowed" : "pointer", opacity: loading && loading !== id ? 0.5 : 1 }}
            onMouseEnter={e => { if(!loading){ e.currentTarget.style.background="rgba(255,255,255,0.07)"; e.currentTarget.style.borderColor="var(--border-hover)"; }}}
            onMouseLeave={e => { e.currentTarget.style.background="rgba(255,255,255,0.03)"; e.currentTarget.style.borderColor="var(--border)"; }}>
            {loading === id ? <Loader2 size={28} color={color} style={{ animation: "spin 1s linear infinite" }} /> : <Icon size={28} color={color} />}
            <div style={{ fontWeight: 600, fontSize: 13 }}>{label}</div>
            <div style={{ padding: "2px 8px", borderRadius: 4, background: `${color}18`, border: `1px solid ${color}44`, fontSize: 10, color, fontWeight: 700 }}>.{ext}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
