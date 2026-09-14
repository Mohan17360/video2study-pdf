import os
import uuid
from jinja2 import Environment, FileSystemLoader
from pyppeteer import launch
from app.config import settings
from app.schemas import StudySummaryDocument

def get_installed_browser_path():
    candidate_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return None

class PDFGenerationService:
    def __init__(self):
        templates_path = os.path.join(os.path.dirname(__file__), "../templates")
        # Explicitly enforce UTF-8 loading with fallback error handling
        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_path, encoding="utf-8")
        )

    async def render_pdf(self, doc: StudySummaryDocument, style: str = "academic") -> str:
        tpl = self.jinja_env.get_template("base_pdf.html")
        html = tpl.render(doc=doc, style=style)
        token = str(uuid.uuid4())
        pdf_path = os.path.join(settings.STORAGE_DIR, f"{token}.pdf")

        browser_path = get_installed_browser_path()
        launch_kwargs = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox"]
        }
        if browser_path:
            launch_kwargs["executablePath"] = browser_path

        browser = await launch(**launch_kwargs)
        page = await browser.newPage()
        await page.setContent(html)
        await page.pdf({"path": pdf_path, "format": "A4", "printBackground": True})
        await browser.close()
        return token
