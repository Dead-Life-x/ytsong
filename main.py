from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
from pytubefix import YouTube

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

# 2. Extract Direct Audio Stream (Deciphers YouTube Cipher without bot block)
@app.get("/stream")
def get_audio_stream(id: str):
    if not id:
        raise HTTPException(status_code=400, detail="Song ID is required")
    
    try:
        # Use pytubefix with Android client to bypass bot block & decipher URL
        yt_obj = YouTube(f"https://www.youtube.com/watch?v={id}", client='ANDROID')
        audio_stream = yt_obj.streams.filter(only_audio=True).order_by('abr').desc().first()
        
        if audio_stream and audio_stream.url:
            return {
                "id": id,
                "audio_url": audio_stream.url
            }
        else:
            raise Exception("No audio stream found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stream extraction error: {str(e)}")
