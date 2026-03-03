import { useState } from "react";
import { Toaster } from "react-hot-toast";
import Header from "./components/Header";
import UploadZone from "./components/UploadZone";
import ComparisonViewer from "./components/ComparisonViewer";
import TransliterationBox from "./components/TransliterationBox";
import KaithiKeyboard from "./components/KaithiKeyboard";
import ExportPanel from "./components/ExportPanel";
import UserHistory from "./components/UserHistory";
import SearchPanel from "./components/SearchPanel";

export default function App() {
  const [tab, setTab] = useState("ocr");
  const [ocrResult, setOcrResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [keyboardText, setKeyboardText] = useState("");

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-base)" }}>
      <Toaster position="top-right" toastOptions={{
        style: {
          background: "var(--bg-elevated)", color: "var(--text-primary)",
          border: "1px solid var(--border)", fontFamily: "var(--ui-font)",
        },
      }} />
      <Header activeTab={tab} onTabChange={setTab} />
      <main style={{ maxWidth: 1400, margin: "0 auto", padding: "2rem 1.5rem" }}>
        {tab === "ocr" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <UploadZone onResult={setOcrResult} onProcessing={setIsProcessing} />
            {ocrResult && (
              <>
                <ComparisonViewer result={ocrResult} loading={isProcessing} />
                <ExportPanel result={ocrResult} />
              </>
            )}
          </div>
        )}
        {tab === "keyboard" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <KaithiKeyboard value={keyboardText} onChange={setKeyboardText} />
            <TransliterationBox kaithiInput={keyboardText} />
          </div>
        )}
        {tab === "search" && <SearchPanel />}
        {tab === "history" && <UserHistory />}
      </main>
    </div>
  );
}
