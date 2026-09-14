const API_BASE = "http://127.0.0.1:8000/api/v1";
document.addEventListener("DOMContentLoaded", async () => {
  const views = {
    inactive: document.getElementById("viewInactive"),
    active: document.getElementById("viewActive"),
    processing: document.getElementById("viewProcessing"),
    ready: document.getElementById("viewReady"),
    error: document.getElementById("viewError")
  };
  let activeVideo = null, pdfResult = null;
  function switchView(k) { Object.keys(views).forEach(v => views[v].classList.add("hidden")); views[k].classList.remove("hidden"); }
  function showError(t, m) { document.getElementById("errorHeading").innerText = t; document.getElementById("errorMessage").innerText = m; switchView("error"); }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url || !tab.url.includes("youtube.com/watch")) { switchView("inactive"); return; }
  const videoId = new URLSearchParams(new URL(tab.url).search).get("v");
  if (!videoId) { switchView("inactive"); return; }

  activeVideo = { id: videoId, url: tab.url, title: tab.title.replace("- YouTube", "").trim(), channel: "Detecting..." };
  document.getElementById("videoTitle").innerText = activeVideo.title;
  switchView("active");

  chrome.tabs.sendMessage(tab.id, { action: "EXTRACT_VIDEO_CONTEXT" }, (res) => {
    if (res && res.data) {
      if (res.data.title) document.getElementById("videoTitle").innerText = res.data.title;
      if (res.data.channel) document.getElementById("videoChannel").innerText = res.data.channel;
    }
  });

  let selectedStyle = "academic";
  document.querySelectorAll(".style-card").forEach(b => {
    b.onclick = () => {
      document.querySelectorAll(".style-card").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      selectedStyle = b.dataset.style;
    };
  });

  document.getElementById("btnGenerate").onclick = async () => {
    switchView("processing");
    const payload = {
      video_id: activeVideo.id,
      video_url: activeVideo.url,
      options: {
        include_images: document.getElementById("optImages").checked,
        include_diagrams: document.getElementById("optDiagrams").checked,
        include_sources: document.getElementById("optSources").checked,
        include_timestamps: document.getElementById("optTimestamps").checked,
        depth: "detailed",
        style: selectedStyle,
        language: "en"
      }
    };
    try {
      const res = await fetch(`${API_BASE}/generate-summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Generation failed");
      }
      pdfResult = await res.json();
      document.getElementById("pdfStats").innerText = `${pdfResult.title} (${pdfResult.pages} pages)`;
      switchView("ready");
    } catch (e) {
      showError("Processing Error", e.message);
    }
  };

  document.getElementById("btnPreview").onclick = () => {
    if (pdfResult) chrome.tabs.create({ url: `${API_BASE}/download/${pdfResult.file_token}?preview=true` });
  };
  document.getElementById("btnDownload").onclick = () => {
    if (pdfResult) chrome.downloads.download({ url: `${API_BASE}/download/${pdfResult.file_token}`, filename: `${pdfResult.slug}.pdf` });
  };
  document.getElementById("btnReset").onclick = () => switchView("active");
  document.getElementById("btnRetry").onclick = () => switchView("active");
});