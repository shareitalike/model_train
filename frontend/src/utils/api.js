const BASE = process.env.REACT_APP_API_URL || "/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: response.statusText }));
    throw new Error(err.detail || err.error || `HTTP ${response.status}`);
  }
  return response;
}

export async function uploadPDF(file, region = "standard") {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/ocr/upload?region=${region}`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function pollStatus(docId) {
  const res = await request(`/ocr/status/${docId}`);
  return res.json();
}

export async function transliterateKaithi(text, region = "standard") {
  const res = await request("/transliterate/kaithi-to-hindi", {
    method: "POST",
    body: JSON.stringify({ text, region }),
  });
  return res.json();
}

export async function reverseToKaithi(hindiText) {
  const res = await request("/transliterate/hindi-to-kaithi", {
    method: "POST",
    body: JSON.stringify({ hindi_text: hindiText }),
  });
  return res.json();
}

export async function exportResult(resultData, format) {
  const res = await fetch(`${BASE}/export/download`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ result_data: resultData, format }),
  });
  if (!res.ok) throw new Error("Export failed");
  return res.blob();
}

export async function searchDocuments(query, page = 1) {
  const res = await request(`/search?q=${encodeURIComponent(query)}&page=${page}`);
  return res.json();
}

export async function getUserHistory(page = 1, limit = 20) {
  const res = await request(`/users/history?page=${page}&limit=${limit}`);
  return res.json();
}
