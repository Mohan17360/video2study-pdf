import json
import google.generativeai as genai
from app.config import settings
from app.schemas import StudySummaryDocument, SectionContent, OptionsPayload

class AISummarizationService:
    def __init__(self):
        self.model = None
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._initialize_model()

    def _initialize_model(self):
        # Prefer the latest active models
        preferred_models = [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        
        for name in preferred_models:
            try:
                self.model = genai.GenerativeModel(name)
                # Quick test ping to make sure the model is actually active
                print(f"[AI Service] Connected to model: {name}")
                return
            except Exception:
                continue

        # Dynamic fallback if none of the above succeeded
        try:
            available = [
                m.name.replace("models/", "") for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods and "2.5" not in m.name
            ]
            if available:
                self.model = genai.GenerativeModel(available[0])
                print(f"[AI Service] Fallback connected to: {available[0]}")
        except Exception as err:
            print(f"[AI Service] Model initialization warning: {err}")

    def generate_study_structure(self, metadata: dict, transcript: str, options: OptionsPayload) -> StudySummaryDocument:
        if not self.model:
            self._initialize_model()
            if not self.model:
                raise ValueError("Could not connect to Gemini API. Verify your GEMINI_API_KEY in backend/.env")

        is_fallback = "[NO_CAPTIONS_FALLBACK]" in transcript
        context_label = "VIDEO OUTLINE & TOPICS (Captions disabled)" if is_fallback else "TRANSCRIPT"

        prompt = f"""You are an expert academic curriculum designer.
Convert this lecture information into an original, concise, and structured study guide.
Faithful to lecture facts. Do not invent unverified details.
Summary Depth: {options.depth}. Target Language: {options.language}.

TITLE: {metadata['title']}
CHANNEL: {metadata['channel']}

{context_label}:
{transcript[:30000]}

Respond ONLY with valid JSON conforming to this schema:
{{
  "video_id": "{metadata.get('video_id', '')}",
  "video_title": "{metadata['title']}",
  "channel_name": "{metadata['channel']}",
  "introduction": "Introductory scope and summary",
  "learning_objectives": ["Objective 1", "Objective 2"],
  "sections": [
    {{
      "section_id": "sec_1",
      "title": "Module Title",
      "summary_markdown": "Clear academic explanation",
      "key_points": ["Key Point 1", "Key Point 2"],
      "definitions": [{{"term": "Term", "definition": "Explanation"}}],
      "formulas_or_steps": ["Step 1 or Formula"],
      "requires_visual": true,
      "visual_search_query": "Specific diagram or schematic topic"
    }}
  ],
  "quick_revision": ["Revision check 1", "Revision check 2"],
  "key_takeaways": ["Takeaway 1", "Takeaway 2"]
}}
"""
        response = self.model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        data = json.loads(response.text)
        sections = []
        for s in data.get("sections", []):
            sec = SectionContent(
                section_id=s.get("section_id", ""),
                title=s.get("title", ""),
                summary_markdown=s.get("summary_markdown", ""),
                key_points=s.get("key_points", []),
                definitions=s.get("definitions", []),
                formulas_or_steps=s.get("formulas_or_steps", []),
                visual=None,
                visual_query=s.get("visual_search_query") if s.get("requires_visual") else None
            )
            sections.append(sec)

        return StudySummaryDocument(
            video_id=metadata.get("video_id", ""),
            video_title=data.get("video_title", metadata["title"]),
            channel_name=data.get("channel_name", metadata["channel"]),
            video_url=f"https://www.youtube.com/watch?v={metadata.get('video_id', '')}",
            introduction=data.get("introduction", ""),
            learning_objectives=data.get("learning_objectives", []),
            sections=sections,
            quick_revision=data.get("quick_revision", []),
            key_takeaways=data.get("key_takeaways", [])
        )
