import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, Loader2, CheckCircle, AlertCircle, X } from "lucide-react";
import toast from "react-hot-toast";
import { uploadPDF, pollStatus } from "../utils/api";

const REGIONS = [
  { value: "standard", label: "Standard Kaithi"    },
  { value: "tirhut",   label: "Tirhut (North Bihar)"},
  { value: "bhojpur",  label: "Bhojpur (West Bihar)"},
  { value: "magadh",   label: "Magadh (Patna/Gaya)"},
  { value: "mithila",  label: "Mithila"             },
];

export default function UploadZone({ onResult, onProcessing }) {
  const [file, setFile]         = useState(null);
  const [region, setRegion]     = useState("standard");
  const [state, setState]       = useState("idle");
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback((accepted, rejected) => {
    if (rejected.length > 0) { toast.error("PDF only, max 50MB"); return; }
    setFile(accepted[0]);
    setState("idle");
    setProgress(0);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "application/pdf": [".pdf"] }, maxFiles: 1, maxSize: 50*1024*1024,
  });

  const handleProcess = async () => {
    if (!file) return;
    setState("uploading"); setProgress(5); onProcessing(true);
    try {
      const { doc_id, estimated_s } = await uploadPDF(file, region);
      setState("processing");
      toast.success(`Processing started — est. ${estimated_s}s`);
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts++;
        setProgress(Math.min(90, 5 + attempts * 3));
        try {
          const status = await pollStatus(doc_id);
          if (status.status === "completed") {
            clearInterval(interval);
            setState("done"); setProgress(100);
            onResult(status); onProcessing(false);
            toast.success(`✓ Complete — ${status.pages?.length || 0} pages`);
          } else if (status.status === "failed") {
            clearInterval(interval); setState("error"); onProcessing(false);
            toast.error(status.error || "Processing failed");
          }
        } catch { if (attempts >= 100) { clearInterval(interval); setState("error"); onProcessing(false); } }
      }, 3000);
    } catch (e) {
      setState("error"); onProcessing(false); toast.error(e.message || "Upload failed");
    }
  };

  const reset = () => { setFile(null); setState("idle"); setProgress(0); };

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "2rem", backdropFilter: "blur(10px)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>📄 PDF Upload & Processing</h2>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>Upload handwritten Kaithi documents for Hindi conversion</p>
        </div>
        {file && (
          <button onClick={reset} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, padding: "6px 12px", cursor: "pointer", color: "#f87171", fontSize: 12, display: "flex", alignItems: "center", gap: 4 }}>
            <X size={14} /> Reset
          </button>
        )}
      </div>

      <div {...getRootProps()} style={{ border: `2px dashed ${isDragActive ? "var(--accent)" : "var(--border-hover)"}`, borderRadius: 12, padding: "3rem 2rem", textAlign: "center", cursor: "pointer", background: isDragActive ? "rgba(249,115,22,0.05)" : "rgba(255,255,255,0.02)", transition: "all 0.2s" }}>
        <input {...getInputProps()} />
        {file ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
            <FileText size={40} color="var(--accent)" />
            <div style={{ fontWeight: 600 }}>{file.name}</div>
            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{(file.size/1024/1024).toFixed(2)} MB</div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
            <Upload size={44} color="var(--accent)" style={{ opacity: 0.7 }} />
            <div style={{ fontWeight: 600, fontSize: 16 }}>{isDragActive ? "Drop PDF here" : "Drag & drop Kaithi PDF"}</div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>or click to browse • max 50MB</div>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "1rem", marginTop: "1.25rem", alignItems: "flex-end" }}>
        <div style={{ flex: 1 }}>
          <label style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 6, display: "block" }}>Regional Script Variant</label>
          <select value={region} onChange={e => setRegion(e.target.value)} disabled={state === "uploading" || state === "processing"}
            style={{ width: "100%", background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", color: "var(--text-primary)", fontSize: 13, cursor: "pointer", fontFamily: "var(--ui-font)" }}>
            {REGIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
        <button onClick={handleProcess} disabled={!file || state === "uploading" || state === "processing"}
          style={{ padding: "10px 28px", borderRadius: 10, border: "none", cursor: !file || (state === "uploading" || state === "processing") ? "not-allowed" : "pointer", fontWeight: 700, fontSize: 14, fontFamily: "var(--ui-font)", background: !file || (state === "uploading" || state === "processing") ? "#334155" : "linear-gradient(135deg, #f97316, #dc2626)", color: "white", display: "flex", alignItems: "center", gap: 8, whiteSpace: "nowrap" }}>
          {state === "uploading" || state === "processing" ? <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> : <span style={{ fontFamily: "var(--hindi-font)" }}>𑂍</span>}
          {state === "uploading" ? "Uploading..." : state === "processing" ? `Processing ${progress}%` : "Process PDF"}
        </button>
      </div>

      {(state === "uploading" || state === "processing") && (
        <div style={{ marginTop: "1rem" }}>
          <div style={{ height: 6, background: "rgba(255,255,255,0.08)", borderRadius: 3, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${progress}%`, background: "linear-gradient(90deg, #f97316, #dc2626)", borderRadius: 3, transition: "width 0.5s ease" }} />
          </div>
          <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>Running OCR pipeline: preprocessing → TrOCR → transliteration → correction...</p>
        </div>
      )}
      {state === "done" && <div style={{ marginTop: "1rem", display: "flex", alignItems: "center", gap: 6, color: "#22c55e", fontSize: 13 }}><CheckCircle size={15} /> Processing complete</div>}
      {state === "error" && <div style={{ marginTop: "1rem", display: "flex", alignItems: "center", gap: 6, color: "#f87171", fontSize: 13 }}><AlertCircle size={15} /> Processing failed. Check file and retry.</div>}
    </div>
  );
}
