from pyrogram import Client, filters
import re
import aiohttp
import asyncio
from urllib.parse import urlparse
import time

# Telegram Bot Configuration
app = Client(
    "InstaReelDownloader",
    api_id=12380656,  # Replace with your API ID
    api_hash="d927c13beaaf5110f25c505b7c071273",  # Replace with your API Hash
    bot_token="7834584002:AAEJF4grVniXFxPO8kM-Gpk3jhX8SFyj3hc"  # Replace with your Bot Token
)

# Regex to extract video URL from Instagram page
VIDEO_URL_PATTERN = r'"video_url":"(https:\/\/[^"]+\.mp4[^"]*)"'

async def fetch_url(url: str) -> str:
    """Fetch the HTML content of the given URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return await response.text()

async def extract_video_url(html: str) -> str:
    """Extract the video URL from Instagram page HTML."""
    match = re.search(VIDEO_URL_PATTERN, html)
    return match.group(1) if match else None

async def is_instagram_reel(url: str) -> bool:
    """Check if the URL is a valid Instagram Reel URL."""
    parsed = urlparse(url)
    return parsed.hostname in ("www.instagram.com", "instagram.com") and "/reel/" in parsed.path

@app.on_message(filters.command(["start"]))
async def start_command(client, message):
    await message.reply_text("Send me an Instagram Reel URL, and I'll download it for you!")

@app.on_message(filters.text & filters.regex(r"https?://(www\.)?instagram\.com/reel/[^ ]+"))
async def download_reel(client, message):
    start_time = time.time()
    reel_url = message.text.strip()

    try:
        # Validate URL
        if not await is_instagram_reel(reel_url):
            await message.reply_text("Please send a valid Instagram Reel URL.")
            return

        # Fetch HTML content
        html = await fetch_url(reel_url)
        
        # Extract video URL
        video_url = await extract_video_url(html)
        if not video_url:
            await message.reply_text("Could not extract video URL. The reel might be private or unavailable.")
            return

        # Send video to user
        await message.reply_video(
            video=video_url,
            caption=f"Downloaded in {((time.time() - start_time) * 1000):.2f} ms"
        )

    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

async def main():
    await app.start()
    print("Bot is running...")
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
