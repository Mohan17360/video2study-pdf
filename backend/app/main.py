from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config import settings
from app.schemas import GenerationRequest, GenerationResponse
from app.services.youtube_service import YouTubeService
from app.services.ai_service import AISummarizationService
from app.services.image_service import VisualSearchService
from app.services.pdf_service import PDFGenerationService
import os, re

app = FastAPI(title="Video2Study")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

yt = YouTubeService()
ai = AISummarizationService()
visuals = VisualSearchService()
pdf = PDFGenerationService()

@app.post("/api/v1/generate-summary", response_model=GenerationResponse)
async def generate_summary(req: GenerationRequest):
    try:
        meta = yt.get_metadata(req.video_id)
        meta["video_id"] = req.video_id
        transcript = yt.get_transcript(req.video_id, preferred_lang=req.options.language)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        doc = ai.generate_study_structure(meta, transcript, req.options)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    v_count = 0
    if req.options.include_images or req.options.include_diagrams:
        for s in doc.sections:
            if s.visual_query:
                # Resolve with concept name + section title + summary context for exact relevance
                s.visual = visuals.resolve_visual(
                    concept_query=s.visual_query,
                    section_title=s.title,
                    section_summary=s.summary_markdown
                )
                v_count += 1

    try:
        token = await pdf.render_pdf(doc, style=req.options.style)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF creation failed: {str(e)}")

    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', doc.video_title.lower())[:30]
    return GenerationResponse(
        file_token=token,
        pdf_url=f"/api/v1/download/{token}",
        title=doc.video_title,
        slug=slug,
        pages=len(doc.sections) + 2,
        visuals_count=v_count
    )

@app.get("/api/v1/download/{file_token}")
async def download_file(file_token: str, preview: bool = False):
    fpath = os.path.join(settings.STORAGE_DIR, f"{file_token}.pdf")
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="File not found.")
    disp = "inline" if preview else "attachment; filename=study_guide.pdf"
    return FileResponse(fpath, media_type="application/pdf", headers={"Content-Disposition": disp})
