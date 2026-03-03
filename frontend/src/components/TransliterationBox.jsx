import { useState, useEffect, useRef } from "react";
import { ArrowRight, RefreshCw, ArrowLeftRight } from "lucide-react";
import { transliterateKaithi, reverseToKaithi } from "../utils/api";

const REGIONS = [
  { value: "standard", label: "Standard" }, { value: "tirhut", label: "Tirhut" },
  { value: "bhojpur",  label: "Bhojpur"  }, { value: "magadh", label: "Magadh" },
  { value: "mithila",  label: "Mithila"  },
];

export default function TransliterationBox({ kaithiInput }) {
  const [input,    setInput]    = useState(kaithiInput || "");
  const [output,   setOutput]   = useState("");
  const [region,   setRegion]   = useState("standard");
  const [conf,     setConf]     = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [reversed, setReversed] = useState(false);
  const timer = useRef(null);

  useEffect(() => { if (kaithiInput !== undefined) setInput(kaithiInput); }, [kaithiInput]);

  useEffect(() => {
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      if (!input.trim()) { setOutput(""); setConf(null); return; }
      setLoading(true);
      try {
        if (!reversed) {
          const r = await transliterateKaithi(input, region);
          setOutput(r.hindi || ""); setConf(r.confidence ?? null);
        } else {
          const r = await reverseToKaithi(input);
          setOutput(r.kaithi || ""); setConf(null);
        }
      } catch { setOutput("त्रुटि"); }
      finally { setLoading(false); }
    }, 350);
    return () => clearTimeout(timer.current);
  }, [input, region, reversed]);

  const confColor = conf >= 0.9 ? "#22c55e" : conf >= 0.7 ? "#eab308" : "#ef4444";

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
        <h2 style={{ fontSize: 17, fontWeight: 700 }}>🔄 Real-time Transliteration</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setReversed(!reversed)} style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 7, background: reversed ? "rgba(249,115,22,0.15)" : "rgba(255,255,255,0.05)", border: `1px solid ${reversed?"rgba(249,115,22,0.4)":"var(--border)"}`, cursor: "pointer", fontSize: 11, fontWeight: 600, color: reversed ? "var(--accent-light)" : "var(--text-secondary)" }}>
            <ArrowLeftRight size={12} /> {reversed ? "Hindi → Kaithi" : "Kaithi → Hindi"}
          </button>
          <select value={region} onChange={e => setRegion(e.target.value)} style={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 7, padding: "4px 8px", color: "var(--text-primary)", fontSize: 11, cursor: "pointer" }}>
            {REGIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <div>
          <label style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 5, display: "block" }}>{reversed ? "Hindi Input" : "Kaithi Input"}</label>
          <textarea value={input} onChange={e => setInput(e.target.value)} placeholder={reversed ? "हिन्दी पाठ यहाँ लिखें..." : "कैथी पाठ यहाँ लिखें..."}
            style={{ width: "100%", height: 120, background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", color: "var(--text-primary)", fontFamily: reversed ? "var(--hindi-font)" : "monospace", fontSize: reversed ? 18 : 16, resize: "none", lineHeight: reversed ? 1.8 : 1.5 }} />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
          <div style={{ color: "var(--accent)", display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}>
            {loading ? <RefreshCw size={14} style={{ animation: "spin 1s linear infinite" }} /> : <ArrowRight size={14} />}
            {conf !== null && <span style={{ color: confColor }}>{(conf*100).toFixed(0)}%</span>}
          </div>
          <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
        </div>

        <div>
          <label style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 5, display: "block" }}>{reversed ? "Kaithi Output" : "Hindi Output"}</label>
          <div style={{ background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", minHeight: 120, fontFamily: reversed ? "monospace" : "var(--hindi-font)", fontSize: reversed ? 16 : 22, lineHeight: reversed ? 1.5 : 1.9, wordBreak: "break-word", color: "var(--text-primary)" }}>
            {output || <span style={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--ui-font)", fontStyle: "italic" }}>Output appears here...</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
