import sys
import re
import os
import urllib.request
import json

from youtube_transcript_api import YouTubeTranscriptApi

sys.stdout.reconfigure(encoding="utf-8")

TRANSCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcripts")


def get_video_title(video_id):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    return data.get("title", video_id)


def safe_filename(title):
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", title)
    cleaned = cleaned.strip()
    return cleaned or "transcript"


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_transcript.py <VIDEO_ID>")
        sys.exit(1)

    video_id = sys.argv[1]
    print(f"Fetching title for {video_id}...")
    title = get_video_title(video_id)
    print(f"Title: {title}")

    api = YouTubeTranscriptApi()
    print("Fetching transcript...")
    transcript_list = api.list(video_id)
    transcript = transcript_list.find_transcript(["hi", "en"]).fetch()
    text = " ".join([s.text for s in transcript])

    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    filename = os.path.join(TRANSCRIPTS_DIR, safe_filename(title) + ".txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved {len(text)} characters to {filename}")


if __name__ == "__main__":
    main()