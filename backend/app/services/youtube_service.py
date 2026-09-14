from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from app.config import settings

class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_DATA_API_KEY
        self.yt = build("youtube", "v3", developerKey=self.api_key) if self.api_key else None

    def get_metadata(self, video_id: str) -> dict:
        if not self.yt:
            return {"title": f"Educational Lecture ({video_id})", "channel": "YouTube Channel", "description": ""}
        try:
            res = self.yt.videos().list(part="snippet", id=video_id).execute()
            if not res.get("items"):
                raise ValueError("Video not found or is private.")
            item = res["items"][0]["snippet"]
            return {
                "title": item.get("title", ""),
                "channel": item.get("channelTitle", ""),
                "description": item.get("description", "")
            }
        except Exception:
            return {"title": f"Lecture ({video_id})", "channel": "YouTube Channel", "description": ""}

    def get_transcript(self, video_id: str, preferred_lang: str = "en") -> str:
        api = YouTubeTranscriptApi()
        formatted_lines = []

        # 1. Fetch transcript using any available language/format
        try:
            # First attempt: list all transcripts and pick preferred, or any available
            t_list = api.list(video_id)
            selected_transcript = None

            # Try preferred language, then english
            for lang in [preferred_lang, "en"]:
                try:
                    selected_transcript = t_list.find_transcript([lang])
                    break
                except Exception:
                    continue

            # Fallback: grab the very first available transcript (e.g. auto-generated)
            if not selected_transcript:
                for t in t_list:
                    selected_transcript = t
                    break

            if selected_transcript:
                fetched = selected_transcript.fetch()
                for snippet in fetched:
                    sec = int(getattr(snippet, "start", 0) if hasattr(snippet, "start") else snippet.get("start", 0))
                    text = getattr(snippet, "text", "") if hasattr(snippet, "text") else snippet.get("text", "")
                    formatted_lines.append(f"[{sec//60:02d}:{sec%60:02d}] {text}")

        except Exception as e:
            # 2. Alternative direct fetch attempt
            try:
                fetched = api.fetch(video_id)
                for snippet in fetched:
                    sec = int(getattr(snippet, "start", 0) if hasattr(snippet, "start") else snippet.get("start", 0))
                    text = getattr(snippet, "text", "") if hasattr(snippet, "text") else snippet.get("text", "")
                    formatted_lines.append(f"[{sec//60:02d}:{sec%60:02d}] {text}")
            except Exception:
                pass

        # 3. If subtitles exist, return them
        if formatted_lines:
            return "\n".join(formatted_lines)

        # 4. Fallback: If absolutely no subtitles exist on YouTube, summarize from metadata & title
        meta = self.get_metadata(video_id)
        desc = meta.get("description", "").strip()
        title = meta.get("title", "Lecture")
        return f"[NO_CAPTIONS_FALLBACK]\nTitle: {title}\nChannel: {meta.get('channel')}\nOverview & Notes:\n{desc if desc else title}"
