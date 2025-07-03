from pyrogram import Client, filters, enums
from instagrapi import Client as InstaClient
import requests
import os
import re
from datetime import timedelta

# Telegram bot credentials
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEpmmyRiihvPgigWVJ2JYDF8VnYhGMFXTM"

# Instagram credentials
INSTA_USERNAME = "rando.m8875"
INSTA_PASSWORD = "Deep@123"

# Initialize clients
app = Client("insta_reel_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
insta = InstaClient()

# Instagram login with session reuse
if os.path.exists("session.json"):
    insta.load_settings("session.json")
else:
    insta.login(INSTA_USERNAME, INSTA_PASSWORD)
    insta.dump_settings("session.json")

# Validate Instagram Reel URL
def is_valid_reel_url(url):
    return bool(re.match(r"https?://www\.instagram\.com/reel/[\w-]+/?", url))

# Download Instagram Reel in high quality
async def download_reel(url):
    try:
        media_pk = insta.media_pk_from_url(url)
        media = insta.media_info(media_pk)
        if media.media_type != 2 or not media.video_url:  # Ensure it's a video
            return None, None, None, None
        
        # Extract metadata
        title = media.caption_text[:100] if media.caption_text else "No title"
        if len(media.caption_text) > 100:
            title += "..."  # Truncate long captions
        duration = str(timedelta(seconds=int(media.duration))) if media.duration else "Unknown"
        quality = f"{media.video_width}x{media.video_height}" if media.video_width and media.video_height else "High"

        # Download highest quality video
        file_path = f"reel_{media_pk}.mp4"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        with requests.get(media.video_url, headers=headers, stream=True, timeout=10) as response:
            if response.status_code != 200:
                return None, None, None, None
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=16384):  # Larger chunks for speed
                    f.write(chunk)
        return file_path, title, duration, quality
    except Exception:
        return None, None, None, None

# Handle /start command
@app.on_message(filters.command("start") & filters.private)
async def start(_, message):
    await message.reply("Send an Instagram Reel URL to download it!")

# Handle Reel URLs
@app.on_message(filters.text & filters.private)
async def handle_reel_url(_, message):
    url = message.text.strip()
    if not is_valid_reel_url(url):
        await message.reply("Invalid Reel URL! Send a valid one (e.g., https://www.instagram.com/reel/XXXXX/).")
        return
    
    await message.reply("Downloading Reel...")
    file_path, title, duration, quality = await download_reel(url)
    
    if file_path and os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) > 2_000_000_000:
                await message.reply("Reel too large (>2GB) for Telegram!")
                os.remove(file_path)
                return
            # Send video with metadata in caption
            caption = f"🎥 *Reel*\n📜 *Title*: {title}\n⏱ *Duration*: {duration}\n📺 *Quality*: {quality}"
            await message.reply_video(file_path, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
            os.remove(file_path)
        except Exception:
            await message.reply("Error sending Reel!")
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await message.reply("Failed to download Reel. It might be private or unavailable.")

# Start the bot
app.run()
