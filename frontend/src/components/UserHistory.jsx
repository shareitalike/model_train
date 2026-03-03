import { useState, useEffect } from "react";
import { CheckCircle, AlertCircle, Clock, Download, Loader2 } from "lucide-react";
import { getUserHistory } from "../utils/api";

const STATUS_ICON = {
  completed: { icon: CheckCircle, color: "#22c55e" },
  failed:    { icon: AlertCircle, color: "#f87171" },
  processing:{ icon: Loader2,     color: "#facc15" },
  queued:    { icon: Clock,       color: "#94a3b8" },
};

export default function UserHistory() {
  const [docs,    setDocs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [page,    setPage]    = useState(1);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try { const r = await getUserHistory(page, 20); setDocs(r.documents || []); }
      catch { setDocs([]); }
      finally { setLoading(false); }
    })();
  }, [page]);

  const downloadDoc = (docId, format = "pdf") => {
    window.open(`/api/v1/export/document/${docId}/${format}`, "_blank");
  };

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.5rem" }}>
        <h2 style={{ fontSize: 17, fontWeight: 700 }}>📋 Processing History</h2>
        <button onClick={() => { setPage(1); setLoading(true); getUserHistory(1,20).then(r => { setDocs(r.documents||[]); setLoading(false); }); }}
          style={{ padding: "6px 12px", borderRadius: 7, background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", cursor: "pointer", color: "var(--text-secondary)", fontSize: 12 }}>
          Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "3rem", color: "var(--text-muted)" }}>
          <Loader2 size={24} style={{ animation: "spin 1s linear infinite" }} />
        </div>
      ) : docs.length === 0 ? (
        <div style={{ textAlign: "center", padding: "3rem", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📄</div>
          No documents processed yet. Upload a PDF to get started.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {docs.map(doc => {
            const { icon: Icon, color } = STATUS_ICON[doc.status] || STATUS_ICON.queued;
            return (
              <div key={doc.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", background: "rgba(0,0,0,0.2)", border: "1px solid var(--border)", borderRadius: 10, transition: "border-color 0.15s" }}
                onMouseEnter={e => e.currentTarget.style.borderColor = "var(--border-hover)"}
                onMouseLeave={e => e.currentTarget.style.borderColor = "var(--border)"}>
                <Icon size={18} color={color} style={doc.status === "processing" ? { animation: "spin 1s linear infinite" } : undefined} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{doc.filename}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    {doc.region} • {doc.pages || 0} pages • {doc.created ? new Date(doc.created).toLocaleDateString("hi-IN") : "—"}
                  </div>
                </div>
                <div style={{ padding: "3px 10px", borderRadius: 20, background: `${color}18`, border: `1px solid ${color}44`, fontSize: 11, fontWeight: 700, color, textTransform: "capitalize" }}>
                  {doc.status}
                </div>
                {doc.status === "completed" && (
                  <button onClick={() => downloadDoc(doc.id, "pdf")} style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 10px", borderRadius: 7, background: "rgba(249,115,22,0.1)", border: "1px solid rgba(249,115,22,0.3)", cursor: "pointer", color: "var(--accent-light)", fontSize: 11 }}>
                    <Download size={12} /> PDF
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: "1.25rem" }}>
        <button onClick={() => setPage(Math.max(1, page-1))} disabled={page === 1}
          style={{ padding: "6px 14px", borderRadius: 7, background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", cursor: page===1?"not-allowed":"pointer", color: page===1?"var(--text-muted)":"var(--text-primary)", fontSize: 12 }}>
          ← Prev
        </button>
        <span style={{ padding: "6px 14px", fontSize: 12, color: "var(--text-secondary)" }}>Page {page}</span>
        <button onClick={() => setPage(page+1)} disabled={docs.length < 20}
          style={{ padding: "6px 14px", borderRadius: 7, background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", cursor: docs.length<20?"not-allowed":"pointer", color: docs.length<20?"var(--text-muted)":"var(--text-primary)", fontSize: 12 }}>
          Next →
        </button>
      </div>
    </div>
  );
}
