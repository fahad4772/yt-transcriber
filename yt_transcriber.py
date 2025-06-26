from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from youtube_transcript_api import YouTubeTranscriptApi
from jinja2 import Environment, FileSystemLoader
import datetime, re, os

app = FastAPI()

# Jinja2 environment setup to load HTML from 'templates' directory
env = Environment(loader=FileSystemLoader("templates"))

def extract_video_id(url: str):
    patterns = [r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:&|$)", r"youtu\.be\/([0-9A-Za-z_-]{11})"]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.get("/", response_class=HTMLResponse)
async def homepage():
    template = env.get_template("index.html")
    return template.render(year=datetime.datetime.now().year)

@app.post("/transcribe")
async def transcribe(yt_url: str = Form(...)):
    video_id = extract_video_id(yt_url)
    if not video_id:
        return {"error": "❌ Invalid YouTube URL."}
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        available = transcripts._manually_created_transcripts or transcripts._generated_transcripts
        if not available:
            return {"error": "⚠️ No transcript available for this video."}
        fetched = list(available.values())[0].fetch()
        text = "\n".join([t.text for t in fetched])
        os.makedirs("transcripts", exist_ok=True)
        with open(f"transcripts/{video_id}.txt", "w", encoding="utf-8") as f:
            f.write(text)
        return {"video_id": video_id, "transcript": text}
    except Exception as e:
        return {"error": f"❌ {str(e)}"}

@app.get("/download/{video_id}")
async def download(video_id: str):
    path = f"transcripts/{video_id}.txt"
    if os.path.exists(path):
        return FileResponse(path, media_type="text/plain", filename=f"{video_id}_transcript.txt")
    return JSONResponse({"error": "File not found."})
