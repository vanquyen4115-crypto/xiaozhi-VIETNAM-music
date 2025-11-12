from flask import Flask, request, jsonify, send_file
import yt_dlp
import requests
import tempfile
import os

app = Flask(__name__)

# Tùy chỉnh để cho phép Zing / Spotify / YouTube
@app.route("/search")
def search_music():
    query = request.args.get("q")
    source = request.args.get("source", "youtube").lower()

    if not query:
        return jsonify({"error": "missing query"}), 400

    # fallback xử lý từng nguồn
    if source == "zing":
        data = try_zing(query)
        if data:
            return jsonify(data)
        source = "youtube"

    if source == "spotify":
        data = try_spotify(query)
        if data:
            return jsonify(data)
        source = "youtube"

    return jsonify(try_youtube(query))


def try_youtube(query):
    with yt_dlp.YoutubeDL({"format": "bestaudio", "quiet": True}) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        if "entries" in info and len(info["entries"]) > 0:
            video = info["entries"][0]
            return {
                "title": video.get("title"),
                "url": video.get("url"),
                "webpage_url": video.get("webpage_url"),
                "source": "youtube",
            }
    return {"error": "No results from YouTube"}


def try_zing(query):
    # ZingMP3 API (không chính thức)
    api = f"https://zingmp3.vn/api/search/multi?q={query}"
    headers = {"Referer": "https://zingmp3.vn", "User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(api, headers=headers, timeout=5)
        if r.ok and "data" in r.json():
            songs = r.json()["data"].get("song", {}).get("items", [])
            if songs:
                title = songs[0]["title"]
                artist = songs[0]["artistsNames"]
                link = f"https://zingmp3.vn{songs[0]['link']}"
                return {"title": f"{title} - {artist}", "url": link, "source": "zing"}
    except Exception:
        pass
    return None


def try_spotify(query):
    # Spotify thường bảo vệ bản quyền, fallback sang ytsearch
    return None


@app.route("/stream")
def stream_music():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing url"}), 400

    with yt_dlp.YoutubeDL({"format": "bestaudio", "quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        best_audio = info["url"]
        return jsonify({"stream_url": best_audio})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
