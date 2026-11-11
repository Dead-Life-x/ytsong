from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import requests

app = FastAPI(title="AuraMusic Backend API")

# Website / App se connect karne ke liye CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize YouTube Music Client
yt = YTMusic()

# Piped instances for stream extraction (Bypasses YouTube bot block)
STREAM_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api-piped.mha.fi",
    "https://pipedapi.tokhmi.xyz"
]

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

# 2. Extract Direct Audio Stream (Fail-safe via Piped Instances)
@app.get("/stream")
def get_audio_stream(id: str):
    if not id:
        raise HTTPException(status_code=400, detail="Song ID is required")
    
    # Try active nodes one by one
    for base in STREAM_INSTANCES:
        try:
            res = requests.get(f"{base}/streams/{id}", timeout=6)
            if res.status_code == 200:
                data = res.json()
                audio_streams = data.get("audioStreams", [])
                if audio_streams:
                    # Sabse best quality audio URL filter karein
                    best_audio = sorted(audio_streams, key=lambda x: x.get("bitrate", 0), reverse=True)[0]
                    return {
                        "id": id,
                        "audio_url": best_audio.get("url")
                    }
        except Exception:
            continue
            
    raise HTTPException(status_code=500, detail="Stream extraction failed across all nodes.")
