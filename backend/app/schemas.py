from pydantic import BaseModel
from typing import List, Optional

class OptionsPayload(BaseModel):
    include_images: bool = True
    include_diagrams: bool = True
    include_sources: bool = True
    include_timestamps: bool = True
    depth: str = "detailed"
    style: str = "academic"
    language: str = "en"

class GenerationRequest(BaseModel):
    video_id: str
    video_url: str
    options: OptionsPayload

class VisualAsset(BaseModel):
    target_concept: str
    image_url: str
    source_url: str
    attribution: str
    license: str
    is_generated_svg: bool = False
    svg_code: Optional[str] = None

class SectionContent(BaseModel):
    section_id: str
    title: str
    summary_markdown: str
    key_points: List[str]
    definitions: List[dict]
    formulas_or_steps: List[str]
    visual: Optional[VisualAsset] = None
    visual_query: Optional[str] = None

class StudySummaryDocument(BaseModel):
    video_id: str
    video_title: str
    channel_name: str
    video_url: str
    introduction: str
    learning_objectives: List[str]
    sections: List[SectionContent]
    quick_revision: List[str]
    key_takeaways: List[str]

class GenerationResponse(BaseModel):
    file_token: str
    pdf_url: str
    title: str
    slug: str
    pages: int
    visuals_count: int