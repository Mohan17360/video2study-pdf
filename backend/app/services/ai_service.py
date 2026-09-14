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
        # Priority list starting with gemini-3.5-flash
        models_to_try = [
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-3-flash",
            "gemini-1.5-flash"
        ]
        
        for name in models_to_try:
            try:
                self.model = genai.GenerativeModel(name)
                print(f"[AI Service] Initialized active Gemini model: {name}")
                return
            except Exception:
                continue

        # Dynamic fallback if none of the above are matched directly
        try:
            available = [
                m.name.replace("models/", "") for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods and "2.5" not in m.name
            ]
            for m in available:
                if "3.5" in m or "flash" in m:
                    self.model = genai.GenerativeModel(m)
                    print(f"[AI Service] Fallback connected to: {m}")
                    return
            if available:
                self.model = genai.GenerativeModel(available[0])
                print(f"[AI Service] Fallback connected to: {available[0]}")
        except Exception as err:
            print(f"[AI Service] Model detection note: {err}")

    def generate_study_structure(self, metadata: dict, transcript: str, options: OptionsPayload) -> StudySummaryDocument:
        if not self.model:
            self._initialize_model()
            if not self.model:
                raise ValueError("Could not connect to Gemini API. Verify your GEMINI_API_KEY in backend/.env")

        is_fallback = "[NO_CAPTIONS_FALLBACK]" in transcript
        context_label = "VIDEO OUTLINE & TOPICS (Captions disabled)" if is_fallback else "TRANSCRIPT"

        # Cap transcript tokens to keep inference fast
        cleaned_transcript = transcript[:25000]

        prompt = f"""You are an expert academic curriculum designer.
Synthesize this lecture into an original, concise, and structured study guide.
Focus strictly on lecture facts. Keep descriptions informative yet punchy for fast study.
Summary Depth: {options.depth}. Target Language: {options.language}.

TITLE: {metadata['title']}
CHANNEL: {metadata['channel']}

{context_label}:
{cleaned_transcript}

Respond ONLY with valid JSON matching this schema:
{{
  "video_id": "{metadata.get('video_id', '')}",
  "video_title": "{metadata['title']}",
  "channel_name": "{metadata['channel']}",
  "introduction": "Introductory scope and lecture overview",
  "learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
  "sections": [
    {{
      "section_id": "sec_1",
      "title": "Module Title",
      "summary_markdown": "Concise high-yield explanation",
      "key_points": ["Key point 1", "Key point 2"],
      "definitions": [{{"term": "Key Term", "definition": "Direct definition"}}],
      "formulas_or_steps": ["Step 1 or Formula"],
      "requires_visual": true,
      "visual_search_query": "Specific technical diagram query"
    }}
  ],
  "quick_revision": ["Exam revision point 1", "Exam revision point 2"],
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
