import requests
import re
import google.generativeai as genai
from app.config import settings
from app.schemas import VisualAsset

class VisualSearchService:
    def __init__(self):
        self.headers = {"User-Agent": settings.COMMONS_API_USER_AGENT}
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            for m in ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3-flash", "gemini-1.5-flash"]:
                try:
                    self.ai_model = genai.GenerativeModel(m)
                    break
                except Exception:
                    continue
        else:
            self.ai_model = None

    def resolve_visual(self, concept_query: str, section_title: str, section_summary: str) -> VisualAsset:
        commons_asset = self._search_wikimedia_verified(concept_query)
        if commons_asset:
            return commons_asset
        return self._generate_custom_diagram(concept_query, section_title, section_summary)

    def _search_wikimedia_verified(self, concept_query: str) -> VisualAsset:
        try:
            clean_query = re.sub(r'[^a-zA-Z0-9\s]', ' ', concept_query).strip()
            resp = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f'"{clean_query}" (diagram OR scheme OR chart OR model) filetype:bitmap|drawing',
                    "gsrlimit": 3,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata|size"
                },
                headers=self.headers,
                timeout=3
            ).json()

            pages = resp.get("query", {}).get("pages", {})
            query_keywords = [w.lower() for w in clean_query.split() if len(w) > 3]

            for _, page in pages.items():
                title = page.get("title", "").lower()
                imageinfo = page.get("imageinfo", [{}])[0]
                img_url = imageinfo.get("url", "")
                matches = sum(1 for kw in query_keywords if kw in title)
                if matches >= max(1, len(query_keywords) // 2):
                    if img_url.endswith((".png", ".jpg", ".jpeg", ".svg")):
                        meta = imageinfo.get("extmetadata", {})
                        artist = meta.get("Artist", {}).get("value", "Wikimedia Contributor")
                        clean_artist = re.sub('<[^<]+?>', '', artist)[:40]
                        license_name = meta.get("LicenseShortName", {}).get("value", "Creative Commons")
                        return VisualAsset(
                            target_concept=concept_query,
                            image_url=img_url,
                            source_url=imageinfo.get("descriptionurl", "https://commons.wikimedia.org"),
                            attribution=clean_artist,
                            license=license_name,
                            is_generated_svg=False
                        )
        except Exception:
            pass
        return None

    def _generate_custom_diagram(self, concept_query: str, section_title: str, section_summary: str) -> VisualAsset:
        if self.ai_model:
            try:
                prompt = f"""Create a clean, beautiful educational SVG diagram illustrating this concept:
CONCEPT: {concept_query}
SECTION: {section_title}
CONTEXT: {section_summary[:300]}

RULES:
1. Return ONLY the raw <svg viewBox="0 0 650 240" xmlns="http://www.w3.org/2000/svg" width="100%" height="240"> ... </svg>.
2. Clean modern styling: background #f8fafc, primary cards #ffffff, border #94a3b8, highlight #2563eb, dark text #0f172a.
3. Draw actual components, arrows, labeled boxes matching the steps or architecture.
4. No markdown block wraps (no ```xml or ```svg). Output raw <svg> only.
"""
                res = self.ai_model.generate_content(prompt)
                svg_code = res.text.strip()
                if svg_code.startswith("```"):
                    svg_code = re.sub(r"^```[a-zA-Z]*\n", "", svg_code)
                    svg_code = re.sub(r"\n```$", "", svg_code)

                if "<svg" in svg_code and "</svg>" in svg_code:
                    return VisualAsset(
                        target_concept=concept_query,
                        image_url="",
                        source_url="AI Generated Schematic",
                        attribution="Video2Study Engine",
                        license="Original Educational Diagram",
                        is_generated_svg=True,
                        svg_code=svg_code
                    )
            except Exception:
                pass

        fallback_svg = f"""<svg viewBox="0 0 600 150" width="100%" height="150" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)">
          <rect width="600" height="150" fill="#f8fafc" stroke="#cbd5e1" rx="8"/>
          <text x="300" y="30" font-family="-apple-system, sans-serif" font-size="13" font-weight="bold" text-anchor="middle" fill="#1e293b">{concept_query.upper()[:45]}</text>
          <rect x="50" y="55" width="140" height="70" fill="#ffffff" stroke="#2563eb" stroke-width="1.5" rx="6"/>
          <text x="120" y="90" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" text-anchor="middle" fill="#1e40af">{section_title[:18]}</text>
          <path d="M 195 90 L 235 90" stroke="#2563eb" stroke-width="2"/>
          <rect x="240" y="55" width="140" height="70" fill="#ffffff" stroke="#10b981" stroke-width="1.5" rx="6"/>
          <text x="310" y="90" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" text-anchor="middle" fill="#065f46">Operation Rules</text>
          <path d="M 385 90 L 425 90" stroke="#10b981" stroke-width="2"/>
          <rect x="430" y="55" width="120" height="70" fill="#ffffff" stroke="#6366f1" stroke-width="1.5" rx="6"/>
          <text x="490" y="90" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" text-anchor="middle" fill="#3730a3">Target State</text>
        </svg>"""
        return VisualAsset(
            target_concept=concept_query,
            image_url="",
            source_url="Educational Schematic",
            attribution="Video2Study Engine",
            license="Generated Diagram",
            is_generated_svg=True,
            svg_code=fallback_svg
        )
