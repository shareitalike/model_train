// SearchPanel.jsx
import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { searchDocuments } from "../utils/api";

export function SearchPanel() {
  const [query,    setQuery]    = useState("");
  const [results,  setResults]  = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [searched, setSearched] = useState(false);

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true); setSearched(true);
    try { const r = await searchDocuments(query); setResults(r.results || []); }
    catch { setResults([]); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "1.5rem" }}>
      <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: "1rem" }}>🔍 Search Inside Handwritten PDFs</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: "1.5rem" }}>
        <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key==="Enter"&&doSearch()}
          placeholder="Search Hindi text inside processed documents..."
          style={{ flex: 1, padding: "10px 14px", background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)", borderRadius: 9, color: "var(--text-primary)", fontFamily: "var(--hindi-font)", fontSize: 16 }} />
        <button onClick={doSearch} disabled={loading} style={{ padding: "10px 20px", borderRadius: 9, background: "linear-gradient(135deg,#f97316,#dc2626)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, color: "white", fontWeight: 700, fontSize: 13 }}>
          {loading ? <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }} /> : <Search size={15} />} खोजें
        </button>
      </div>
      {searched && !loading && (
        results.length === 0
          ? <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>No results for "{query}"</div>
          : <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{results.length} results</p>
              {results.map((r, i) => (
                <div key={i} style={{ padding: "14px 16px", background: "rgba(0,0,0,0.2)", border: "1px solid var(--border)", borderRadius: 10 }}>
                  <div style={{ fontSize: 12, color: "var(--accent-light)", marginBottom: 6 }}>{r.filename} — Page {r.page_number}</div>
                  <div style={{ fontFamily: "var(--hindi-font)", fontSize: 18, color: "var(--text-primary)", lineHeight: 1.8 }}
                    dangerouslySetInnerHTML={{ __html: r.snippet?.replace(new RegExp(query,"gi"), `<mark style="background:rgba(249,115,22,0.3);color:var(--accent-light);padding:0 2px;border-radius:3px">$&</mark>`) }} />
                </div>
              ))}
            </div>
      )}
    </div>
  );
}

export default SearchPanel;
