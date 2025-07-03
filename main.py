from pyrogram import Client, filters, idle
from instagrapi import Client as InstaClient
import aiohttp
import aiofiles
import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Telegram bot credentials
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEpmmyRiihvPgigWVJ2JYDF8VnYhGMFXTM"

# Instagram credentials
INSTA_USERNAME = "rando.m8875"
INSTA_PASSWORD = "Deep@123"
TWO_FACTOR_CODE = None

# Initialize Pyrogram client
app = Client("insta_reel_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize instagrapi client
insta = InstaClient()

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=2)

# Load or perform Instagram login
async def initialize_instagram():
    loop = asyncio.get_event_loop()
    try:
        if os.path.exists("session.json"):
            await loop.run_in_executor(executor, lambda: insta.load_settings("session.json"))
            print("Loaded Instagram session")
        await loop.run_in_executor(executor, lambda: insta.login(INSTA_USERNAME, INSTA_PASSWORD, verification_code=TWO_FACTOR_CODE))
        await loop.run_in_executor(executor, lambda: insta.dump_settings("session.json"))
        print("Logged into Instagram successfully")
    except Exception as e:
        print(f"Instagram login failed: {e}")
        exit(1)

# Function to validate Instagram Reel URL (optimized regex)
def is_valid_reel_url(url):
    return bool(re.match(r"https?://www\.instagram\.com/reel/[\w-]+", url))

# Function to download Instagram Reel (optimized with aiohttp)
async def download_reel(url):
    try:
        # Extract media ID (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        media_pk = await loop.run_in_executor(executor, lambda: insta.media_pk_from_url(url))
        media = await loop.run_in_executor(executor, lambda: insta.media_info(media_pk))
        
        if media.media_type == 2:  # Video (Reel)
            video_url = media.video_url
            if video_url:
                file_path = f"reel_{media_pk}.mp4"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                async with aiohttp.ClientSession() as session:
                    async with session.get(video_url, headers=headers) as response:
                        if response.status == 200:
                            async with aiofiles.open(file_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            return file_path
                        else:
                            print(f"Failed to download video: HTTP {response.status}")
                            return None
            return None
        return None
    except Exception as e:
        print(f"Error downloading reel: {e}")
        return None

# Handle /start command
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Hi! I'm a bot that downloads Instagram Reels. Send me a valid Instagram Reel URL."
    )

# Handle incoming messages with Instagram Reel URLs
@app.on_message(filters.text & filters.private)
async def handle_reel_url(client, message):
    url = message.text.strip()
    
    if not is_valid_reel_url(url):
        await message.reply_text("Please send a valid Instagram Reel URL (e.g., https://www.instagram.com/reel/XXXXX/).")
        return
    
    await message.reply_text("Processing your Reel URL, please wait...")
    
    # Download the reel
    file_path = await download_reel(url)
    
    if file_path and os.path.exists(file_path):
        try:
            # Check file size (Telegram limit: 2 GB)
            file_size = await asyncio.get_event_loop().run_in_executor(executor, lambda: os.path.getsize(file_path))
            if file_size > 2_000_000_000:
                await message.reply_text("Reel is too large for Telegram (>2GB). Try a shorter video.")
                await asyncio.get_event_loop().run_in_executor(executor, lambda: os.remove(file_path))
                return
            # Send the video to the user
            await message.reply_video(
                video=file_path,
                caption="Here is your Instagram Reel!"
            )
            # Clean up the downloaded file
            await asyncio.get_event_loop().run_in_executor(executor, lambda: os.remove(file_path))
        except Exception as e:
            await message.reply_text(f"Error sending video: {e}")
            if os.path.exists(file_path):
                await asyncio.get_event_loop().run_in_executor(executor, lambda: os.remove(file_path))
    else:
        await message.reply_text("Failed to download the Reel. It might be private, deleted, or blocked.")

# Run the bot
async def main():
    await initialize_instagram()
    await app.start()
    print("Bot is running...")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
