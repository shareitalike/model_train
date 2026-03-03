import { useState } from "react";
import { Delete, Copy, RotateCcw } from "lucide-react";
import toast from "react-hot-toast";
import { KEYBOARD_DATA } from "../utils/keyboard_data";

export default function KaithiKeyboard({ value, onChange }) {
  const [group, setGroup] = useState("consonants");
  const append = char => onChange(v => v + char);
  const del    = ()   => onChange(v => [...v].slice(0,-1).join(""));
  const clear  = ()   => onChange("");
  const copy   = ()   => { navigator.clipboard.writeText(value); toast.success("Copied!"); };

  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 16, padding: "1.5rem" }}>
      <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: "1rem" }}>⌨️ Kaithi Virtual Keyboard</h2>

      <div style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)", borderRadius: 10, padding: "1rem", minHeight: 64, fontFamily: "monospace", fontSize: 24, letterSpacing: 3, wordBreak: "break-all", marginBottom: "0.75rem" }}>
        {value || <span style={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--ui-font)" }}>Click characters to compose...</span>}
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: "1rem" }}>
        {[
          { icon: Delete,    fn: del,              label: "Del",   color: "#f87171" },
          { icon: RotateCcw, fn: clear,            label: "Clear", color: "var(--text-muted)" },
          { icon: Copy,      fn: copy,             label: "Copy",  color: "var(--accent-light)" },
        ].map(({ icon: Icon, fn, label, color }) => (
          <button key={label} onClick={fn} style={{ display: "flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 7, background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", cursor: "pointer", color, fontSize: 12 }}>
            <Icon size={13} /> {label}
          </button>
        ))}
        <button onClick={() => append(" ")} style={{ padding: "6px 16px", borderRadius: 7, background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", cursor: "pointer", color: "var(--text-secondary)", fontSize: 12 }}>Space</button>
        <button onClick={() => append("।")} style={{ padding: "6px 12px", borderRadius: 7, background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", cursor: "pointer", color: "var(--text-secondary)", fontFamily: "var(--hindi-font)", fontSize: 16 }}>।</button>
      </div>

      <div style={{ display: "flex", gap: 6, marginBottom: "0.75rem", flexWrap: "wrap" }}>
        {Object.keys(KEYBOARD_DATA).map(g => (
          <button key={g} onClick={() => setGroup(g)} style={{ padding: "5px 12px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 11, fontWeight: 600, background: group === g ? "linear-gradient(135deg,rgba(249,115,22,0.3),rgba(220,38,38,0.2))" : "rgba(255,255,255,0.04)", color: group === g ? "var(--accent-light)" : "var(--text-muted)", border: group === g ? "1px solid rgba(249,115,22,0.35)" : "1px solid var(--border)", textTransform: "capitalize" }}>
            {g.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(64px,1fr))", gap: 6 }}>
        {(KEYBOARD_DATA[group] || []).map(({ k, d, l }) => (
          <button key={k} onClick={() => append(k)} title={`${l}: ${k} → ${d}`}
            style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 4px", cursor: "pointer", textAlign: "center", transition: "all 0.12s" }}
            onMouseEnter={e => { e.currentTarget.style.background="rgba(249,115,22,0.12)"; e.currentTarget.style.borderColor="rgba(249,115,22,0.4)"; }}
            onMouseLeave={e => { e.currentTarget.style.background="rgba(255,255,255,0.03)"; e.currentTarget.style.borderColor="var(--border)"; }}>
            <div style={{ fontSize: 20, color: "var(--text-primary)", marginBottom: 2 }}>{k}</div>
            <div style={{ fontSize: 11, color: "var(--text-secondary)", fontFamily: "var(--hindi-font)" }}>{d}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
