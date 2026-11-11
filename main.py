from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import requests

app = FastAPI(title="AuraMusic Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yt = YTMusic()

@app.get("/")
def home():
    return {"status": "online", "message": "AuraMusic API running perfectly"}

# 1. Search Songs
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

# 2. Extract Direct Audio Stream (Android InnerTube Client - Zero Block)
@app.get("/stream")
def get_audio_stream(id: str):
    if not id:
        raise HTTPException(status_code=400, detail="Song ID is required")
    
    # 1. Direct YouTube Android Client API Call
    innertube_url = "https://www.youtube.com/youtubei/v1/player"
    payload = {
        "videoId": id,
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "19.09.37",
                "androidSdkVersion": 30,
                "hl": "en",
                "gl": "IN"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip"
    }

    try:
        res = requests.post(innertube_url, json=payload, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            streaming_data = data.get("streamingData", {})
            adaptive_formats = streaming_data.get("adaptiveFormats", [])
            
            # Filter pure audio formats (.m4a / .webm) with direct playable URL
            audio_formats = [
                f for f in adaptive_formats 
                if f.get("mimeType", "").startswith("audio/") and "url" in f
            ]
            
            if audio_formats:
                # Highest bitrate stream
                best_audio = sorted(audio_formats, key=lambda x: x.get("bitrate", 0), reverse=True)[0]
                return {
                    "id": id,
                    "audio_url": best_audio.get("url")
                }
    except Exception:
        pass

    # 2. Fallback to Healthy Invidious instances if InnerTube direct url needs decipher
    invidious_nodes = [
        "https://inv.nadeko.net",
        "https://invidious.nerdvpn.de",
        "https://yt.drgnz.club"
    ]
    
    for node in invidious_nodes:
        try:
            r = requests.get(f"{node}/api/v1/videos/{id}", timeout=6)
            if r.status_code == 200:
                vdata = r.json()
                formats = vdata.get("adaptiveFormats", [])
                audio_streams = [f for f in formats if f.get("type", "").startswith("audio/") and "url" in f]
                if audio_streams:
                    best = sorted(audio_streams, key=lambda x: int(x.get("bitrate", 0)), reverse=True)[0]
                    return {
                        "id": id,
                        "audio_url": best.get("url")
                    }
        except Exception:
            continue

    raise HTTPException(status_code=500, detail="Unable to extract stream URL.")
