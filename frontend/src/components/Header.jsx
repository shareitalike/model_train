import { BookText, Keyboard, Search, History } from "lucide-react";

const TABS = [
  { id: "ocr",      label: "OCR Processing",  icon: BookText },
  { id: "keyboard", label: "Kaithi Keyboard", icon: Keyboard },
  { id: "search",   label: "Search PDFs",     icon: Search   },
  { id: "history",  label: "History",         icon: History  },
];

export default function Header({ activeTab, onTabChange }) {
  return (
    <header style={{
      position: "sticky", top: 0, zIndex: 100,
      background: "rgba(10,14,26,0.95)", backdropFilter: "blur(20px)",
      borderBottom: "1px solid var(--border)",
    }}>
      <div style={{
        maxWidth: 1400, margin: "0 auto", padding: "0 1.5rem",
        display: "flex", alignItems: "center", justifyContent: "space-between", height: 64,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 42, height: 42,
            background: "linear-gradient(135deg, #f97316, #dc2626)",
            borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 22, fontFamily: "var(--hindi-font)",
            boxShadow: "0 0 20px rgba(249,115,22,0.3)",
          }}>𑂍</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>कैथी OCR सिस्टम</div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.05em" }}>
              GOVERNMENT DIGITIZATION PLATFORM
            </div>
          </div>
        </div>

        <nav style={{ display: "flex", gap: 4 }}>
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => onTabChange(id)} style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "8px 16px", borderRadius: 8, cursor: "pointer",
              fontSize: 13, fontWeight: 500, fontFamily: "var(--ui-font)",
              transition: "all 0.15s",
              background: activeTab === id
                ? "linear-gradient(135deg, rgba(249,115,22,0.25), rgba(220,38,38,0.15))"
                : "transparent",
              color: activeTab === id ? "var(--accent-light)" : "var(--text-secondary)",
              border: activeTab === id ? "1px solid rgba(249,115,22,0.35)" : "1px solid transparent",
            }}>
              <Icon size={15} />
              {label}
            </button>
          ))}
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--text-muted)" }}>
          <div style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 6px #22c55e" }} />
          System Online
        </div>
      </div>
    </header>
  );
}
