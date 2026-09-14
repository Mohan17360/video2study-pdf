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
            self.ai_model = genai.GenerativeModel("gemini-3.6-flash")
        else:
            self.ai_model = None

    def resolve_visual(self, concept_query: str, section_title: str, section_summary: str) -> VisualAsset:
        # 1. Try Wikimedia Commons with strict relevance verification
        commons_asset = self._search_wikimedia_verified(concept_query)
        if commons_asset:
            return commons_asset

        # 2. If no verified diagram exists online, generate a concept-specific SVG diagram with Gemini
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
                timeout=4
            ).json()

            pages = resp.get("query", {}).get("pages", {})
            query_keywords = [w.lower() for w in clean_query.split() if len(w) > 3]

            for _, page in pages.items():
                title = page.get("title", "").lower()
                imageinfo = page.get("imageinfo", [{}])[0]
                img_url = imageinfo.get("url", "")
                
                # Verify that key tokens appear in the image title (rejects random photos)
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
        except Exception as e:
            print(f"[Visual Search] Wikimedia error: {e}")
        return None

    def _generate_custom_diagram(self, concept_query: str, section_title: str, section_summary: str) -> VisualAsset:
        """
        Asks Gemini to generate an educational, concept-accurate SVG schematic
        specifically for this section's content.
        """
        if self.ai_model:
            try:
                prompt = f"""You are an educational graphic illustrator and technical diagram designer.
Create a clean, beautiful, visually informative SVG diagram that specifically illustrates this concept:
CONCEPT: {concept_query}
SECTION: {section_title}
CONTEXT: {section_summary[:350]}

REQUIREMENTS:
1. Return ONLY the raw valid <svg viewBox="0 0 650 260" xmlns="http://www.w3.org/2000/svg" width="100%" height="260"> ... </svg> code.
2. Use modern colors: backgrounds #f8fafc, borders #94a3b8, cards #ffffff, primary elements #2563eb, accents #10b981 or #f59e0b, dark text #0f172a.
3. Draw actual components, arrows, labeled boxes, or flow steps matching the concept (e.g. if TCP handshake: show Client/Server SYN->SYN-ACK->ACK; if OSI: show stacked layers; if biology: show inputs/outputs/cycles).
4. Include clear text labels explaining each step or part.
5. Do not wrap in markdown quotes (no ```xml or ```svg). Output only the raw <svg> tag.
"""
                res = self.ai_model.generate_content(prompt)
                svg_code = res.text.strip()
                # Clean any markdown code blocks if the model included them
                if svg_code.startswith("```"):
                    svg_code = re.sub(r"^```[a-zA-Z]*\n", "", svg_code)
                    svg_code = re.sub(r"\n```$", "", svg_code)

                if "<svg" in svg_code and "</svg>" in svg_code:
                    return VisualAsset(
                        target_concept=concept_query,
                        image_url="",
                        source_url="AI Generated Schematic",
                        attribution="Video2Study Educational Diagram Engine",
                        license="Original Educational Diagram",
                        is_generated_svg=True,
                        svg_code=svg_code
                    )
            except Exception as e:
                print(f"[Diagram Engine] AI SVG generation error: {e}")

        # Fallback neatly styled card if AI generation was unreachable
        fallback_svg = f"""<svg viewBox="0 0 600 160" width="100%" height="160" xmlns="[http://www.w3.org/2000/svg](http://www.w3.org/2000/svg)">
          <rect width="600" height="160" fill="#f1f5f9" stroke="#cbd5e1" rx="8"/>
          <text x="300" y="32" font-family="-apple-system, sans-serif" font-size="13" font-weight="bold" text-anchor="middle" fill="#1e293b">CONCEPT: {concept_query.upper()[:45]}</text>
          <rect x="40" y="55" width="150" height="75" fill="#ffffff" stroke="#2563eb" stroke-width="1.5" rx="6"/>
          <text x="115" y="88" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" text-anchor="middle" fill="#1e40af">{section_title[:20]}</text>
          <text x="115" y="106" font-family="-apple-system, sans-serif" font-size="9" text-anchor="middle" fill="#64748b">Primary Input</text>
          <path d="M 195 92 L 235 92" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>
          <rect x="240" y="55" width="150" height="75" fill="#ffffff" stroke="#10b981" stroke-width="1.5" rx="6"/>
          <text x="315" y="88" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" text-anchor="middle" fill="#065f46">Operation / Rules</text>
          <text x="315" y="106" font-family="-apple-system, sans-serif" font-size="9" text-anchor="middle" fill="#64748b">Core Processing</text>
          <path d="M 395 92 L 435 92" stroke="#10b981" stroke-width="2"/>
          <rect x="440" y="55" width="120" height="75" fill="#ffffff" stroke="#6366f1" stroke-width="1.5" rx="6"/>
          <text x="500" y="88" font-family="-apple-system, sans-serif" font-size="11" font-weight="600" text-anchor="middle" fill="#3730a3">Target State</text>
          <text x="500" y="106" font-family="-apple-system, sans-serif" font-size="9" text-anchor="middle" fill="#64748b">Verified Output</text>
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
