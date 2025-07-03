import re
import aiohttp
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message

# config.py
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7834584002:AAFGQRrqKE3iFek1FPo-e27x59VUU11Bj6g"

app = Client("fast_insta_reel_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

INSTAGRAM_REEL_REGEX = r"(https?://(?:www\.)?instagram\.com/reel/[^\s]+)"

# Optional: Cache dictionary for previously downloaded reels
cache = {}

async def fetch_reel_video(url: str) -> str:
    """
    Fetch direct video URL from Instagram reel (public only).
    """
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()

            video_url_match = re.search(r'"video_url":"([^"]+)"', html)
            if video_url_match:
                video_url = video_url_match.group(1).replace("\\u0026", "&").replace("\\", "")
                return video_url
            else:
                raise ValueError("No video URL found in Instagram HTML.")

@app.on_message(filters.private & filters.regex(INSTAGRAM_REEL_REGEX))
async def reel_handler(client: Client, message: Message):
    insta_url = re.search(INSTAGRAM_REEL_REGEX, message.text).group(1)

    # Cache check
    if insta_url in cache:
        video_path = cache[insta_url]
        await message.reply_video(video_path)
        return

    msg = await message.reply("⏳ Fetching reel...")

    try:
        video_url = await fetch_reel_video(insta_url)

        # Download reel video
        filename = f"reel_{hash(insta_url)}.mp4"
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as video_response:
                with open(filename, "wb") as f:
                    while True:
                        chunk = await video_response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)

        await msg.edit("📤 Sending reel...")
        await message.reply_video(filename)

        cache[insta_url] = filename

    except Exception as e:
        await msg.edit(f"❌ Failed: {str(e)}")
    finally:
        await msg.delete()

if __name__ == "__main__":
    app.run()
