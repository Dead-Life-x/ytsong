from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp

app = FastAPI(title="AuraMusic Backend API")

# Website / Frontend se connect karne ke liye CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize YouTube Music Client
yt = YTMusic()

@app.get("/")
def home():
    return {"status": "online", "message": "AuraMusic API is running smoothly!"}

# 1. Search Songs Endpoint
@app.get("/search")
def search_songs(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="Search query is required")
    try:
        results = yt.search(q, filter="songs")
        tracks = []
        for item in results:
            tracks.append({
                "id": item.get("videoId"),
                "title": item.get("title"),
                "artist": ", ".join([a.get("name", "") for a in item.get("artists", [])]),
                "thumbnail": item.get("thumbnails", [{}])[-1].get("url", ""),
                "duration": item.get("duration", "0:00")
            })
        return tracks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# 2. Extract Direct Audio Stream Link Endpoint
@app.get("/stream")
def get_audio_stream(id: str):
    if not id:
        raise HTTPException(status_code=400, detail="Song ID is required")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
        'nocheckcertificate': True,
        # Ye do parameters YouTube block bypass karte hain:
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={id}", download=False)
            stream_url = info.get("url")
            return {
                "id": id,
                "audio_url": stream_url
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream extraction failed: {str(e)}")
