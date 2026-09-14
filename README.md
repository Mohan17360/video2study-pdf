# Video2Study PDF 🎓📄

A professional desktop browser extension and FastAPI backend that converts educational YouTube videos into structured, visually attractive study-summary PDFs.

---

## 🌟 Key Features

* **Automatic YouTube Context Extraction**: Detects video metadata, channel details, and timestamps directly from the active tab.
* **Educational Structuring**: Uses Gemini to synthesize transcripts into structured academic notes (learning objectives, subtopics, definitions, step-by-step formulas, and exam revision points).
* **Concept-Specific Diagrams**:
  * Scrapes verified open-access technical schematics from Wikimedia Commons.
  * Dynamically generates customized, labeled vector SVG diagrams for conceptual sections.
  * Embeds the lecture video thumbnail on the document cover page.
* **Publication-Quality A4 PDFs**: Generates print-ready A4 study guides via headless Chromium, complete with page breaks, highlight cards, and an image attribution index.

---

## 📂 Project Architecture

```text
video2study/
├── extension/             # Chrome/Edge Manifest V3 extension
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.css
│   ├── popup.js
│   ├── content.js
│   └── icons/
├── backend/               # FastAPI microservice
│   ├── app/
│   │   ├── main.py        # API routing
│   │   ├── config.py      # Environment configuration
│   │   ├── schemas.py     # Pydantic data models
│   │   ├── services/      # YouTube, AI, diagram, and PDF services
│   │   └── templates/     # Jinja2 PDF layouts
│   ├── run.py             # Server launcher
│   └── requirements.txt
├── .gitignore
└── README.md