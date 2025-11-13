import requests
import time
import os

# --- Configuration ---
AZURACAST_API = os.getenv("AZURACAST_API", "https://www.mawalkingradio.app/api/nowplaying")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "182798681767685")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "EAAPzVeBZBgWcBP6mTnZAgtThou1ZBwHAUG590PsaNNHyuS5oyWwrJktnzCyzeKzlJdMtWHzmFCZBOw5eaZA7FKplbVl3S40oyFONmKXHbruNCCejeVBVDsT70sMicrz1hDxegZC9ve4mNVQxTI2W7W1WNoKdYzsIgmiM2DnOGLOpO88Auv8qlz9FFrSlZBor5QSKD8YjhAzIHzUMASLlCJW9V8Y9HwEMU8lnr4ZD")

# Post every 2 hours (7200 seconds)
POST_INTERVAL = 7200  

def get_now_playing():
    try:
        r = requests.get(AZURACAST_API, timeout=10)
        r.raise_for_status()
        data = r.json()[0] if isinstance(r.json(), list) else r.json()

        song = data.get('now_playing', {}).get('song', {})
        title = song.get('title', '')
        artist = song.get('artist', '')
        album_art = song.get('art', '') or data.get('now_playing', {}).get('art', '')
        stream_url = "https://forwardmystream.com/station/mawalkingradiostation"

        if title and artist:
            return title, artist, album_art, stream_url
    except Exception as e:
        print("Error fetching now playing:", e)
    return None, None, None, None

def post_to_facebook(message, album_art, stream_url):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    payload = {
        "caption": f"{message}\n\n🎧 Listen live: {stream_url}",
        "url": album_art,
        "access_token": FB_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    print("Facebook post response:", response.status_code, response.text)
    return response.status_code == 200

def main():
    while True:
        title, artist, album_art, stream_url = get_now_playing()
        if title and artist:
            message = f'🎵 Now playing: "{title}" by {artist}'
            success = post_to_facebook(message, album_art, stream_url)
            print("✅ Posted to Facebook" if success else "❌ Failed to post")
        else:
            print("No song data retrieved.")
        print(f"Sleeping for {POST_INTERVAL/3600} hours...\n")
        time.sleep(POST_INTERVAL)

if __name__ == "__main__":
    main()
