import requests
import time
import os
import json
from datetime import datetime

AZURACAST_API = os.getenv("AZURACAST_API", "https://www.mawalkingradio.app/api/nowplaying/mawalking_radio")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN", "")
POST_INTERVAL = 7200  # every 2 hours

LAST_TRACK_FILE = "/tmp/last_track.txt"


# ----------------------------------------
# UTIL: SEND ERROR ALERT (email or WhatsApp)
# ----------------------------------------
def send_alert(message):
    """
    Add your Twilio or SendGrid credentials here.
    This function is optional and safe if empty.
    """
    print("⚠️ ALERT:", message)
    # Example Twilio WhatsApp hook (uncomment to enable):
    #
    # from twilio.rest import Client
    # client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_TOKEN"))
    # client.messages.create(
    #     body=message,
    #     from_="whatsapp:+14155238886",
    #     to="whatsapp:+1XXXXXXXXXX"
    # )


# ----------------------------------------
# TRACK PARSING
# ----------------------------------------
def parse_song_info(song):
    raw_title = song.get("title", "") or ""
    raw_artist = song.get("artist", "") or ""
    raw_text = song.get("text", "") or ""

    # Fallback to "text" if title/artist is empty
    if not raw_title or not raw_artist:
        parts = raw_text.split(" - ")
        if len(parts) >= 2:
            raw_artist = raw_artist or parts[0].strip()
            raw_title = raw_title or " - ".join(parts[1:]).strip()

    # Final fallback
    if not raw_title:
        raw_title = raw_text

    if not raw_artist:
        raw_artist = "Mawalking Radio Mix"

    return raw_title.strip(), raw_artist.strip()


# ----------------------------------------
# FETCH NOW PLAYING
# ----------------------------------------
def get_now_playing():
    try:
        r = requests.get(AZURACAST_API, timeout=12)
        r.raise_for_status()

        data = r.json()[0] if isinstance(r.json(), list) else r.json()
        now = data.get("now_playing", {})
        song = now.get("song", {})

        title, artist = parse_song_info(song)

        album_art = (
            song.get("art")
            or now.get("art")
        )

        stream_url = "https://forwardmystream.com/station/mawalkingradiostation"

        return title, artist, album_art, stream_url

    except Exception as e:
        send_alert(f"API ERROR: {e}")
        return None, None, None, None


# ----------------------------------------
# DUPLICATE PROTECTION (PERSISTENT)
# ----------------------------------------
def last_track_posted():
    if os.path.exists(LAST_TRACK_FILE):
        with open(LAST_TRACK_FILE, "r") as f:
            return f.read().strip()
    return None


def save_last_track(track_id):
    with open(LAST_TRACK_FILE, "w") as f:
        f.write(track_id)


# ----------------------------------------
# FACEBOOK POST WITH RETRY
# ----------------------------------------
def post_to_facebook(message, album_art, stream_url, retries=3):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"

    payload = {
        "caption": f"{message}\n\n🎧 Listen live: {stream_url}",
        "url": album_art,
        "access_token": FB_ACCESS_TOKEN
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, data=payload)
            print(f"FB Response {attempt}: {response.status_code} {response.text}")

            if response.status_code == 200:
                return True

            # Rate limiting or auth errors should trigger alert
            if response.status_code in [400, 403, 429]:
                send_alert(f"Facebook Error: {response.text}")

        except Exception as e:
            send_alert(f"Facebook POST EXCEPTION: {e}")

        time.sleep(attempt * 3)

    return False


# ----------------------------------------
# MAIN LOOP
# ----------------------------------------
def main():
    print("🚀 Mawalking Radio Facebook Bot Started")
    
    while True:
        title, artist, album_art, stream_url = get_now_playing()

        if not title:
            print("⚠ No song detected, retrying later.")
            time.sleep(POST_INTERVAL)
            continue

        # Create unique ID for dedupe
        track_id = f"{artist}|{title}"

        if track_id == last_track_posted():
            print(f"⏳ Already posted this track: {track_id}")
        else:
            message = f'🎵 Now playing: "{title}" by {artist}'

            posted = post_to_facebook(message, album_art, stream_url)

            if posted:
                print("✅ Successfully posted to Facebook!")
                save_last_track(track_id)
            else:
                print("❌ Failed to post to Facebook.")

        print(f"😴 Sleeping for {POST_INTERVAL / 3600} hours...\n")
        time.sleep(POST_INTERVAL)


if __name__ == "__main__":
    main()
