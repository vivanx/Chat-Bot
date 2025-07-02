from pyrogram import Client, filters
from instagrapi import Client as InstaClient
import requests
import os
import re

# Telegram bot credentials
API_ID = ""  # Get from https://my.telegram.org
API_HASH = ""  # Get from https://my.telegram.org
BOT_TOKEN = ""  # Get from @BotFather

# Instagram credentials
INSTA_USERNAME = ""
INSTA_PASSWORD = ""
# Optional: 2FA code (set to None if not needed, or prompt dynamically)
TWO_FACTOR_CODE = None  # Replace with 2FA code if required

# Initialize Pyrogram client
app = Client("insta_reel_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize instagrapi client
insta = InstaClient()

# Load or perform Instagram login
try:
    if os.path.exists("session.json"):
        insta.load_settings("session.json")
        print("Loaded Instagram session")
    insta.login(INSTA_USERNAME, INSTA_PASSWORD, verification_code=TWO_FACTOR_CODE)
    insta.dump_settings("session.json")  # Save session after login
    print("Logged into Instagram successfully")
except Exception as e:
    print(f"Instagram login failed: {e}")
    exit(1)

# Function to validate Instagram Reel URL
def is_valid_reel_url(url):
    return bool(re.match(r"https?://www\.instagram\.com/reel/[\w-]+/?", url))

# Function to download Instagram Reel
async def download_reel(url):
    try:
        # Extract media ID from URL
        media_pk = insta.media_pk_from_url(url)
        media = insta.media_info(media_pk)
        
        if media.media_type == 2:  # Video (Reel)
            video_url = media.video_url
            if video_url:
                # Download the video using requests
                file_path = f"reel_{media_pk}.mp4"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }  # Mimic browser to avoid blocks
                response = requests.get(video_url, headers=headers, stream=True)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return file_path
                else:
                    print(f"Failed to download video: HTTP {response.status_code}")
                    return None
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"Error downloading reel: {e}")
        return None

# Handle /start command
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Hi! I'm a bot that downloads Instagram Reels. Send me a valid Instagram Reel URL to download it."
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
            # Check file size (Telegram limit: 2 GB = 2,000,000,000 bytes)
            if os.path.getsize(file_path) > 2_000_000_000:
                await message.reply_text("Reel is too large for Telegram (>2GB). Try a shorter video.")
                os.remove(file_path)
                return
            # Send the video to the user
            await message.reply_video(
                video=file_path,
                caption="Here is your Instagram Reel!"
            )
            # Clean up the downloaded file
            os.remove(file_path)
        except Exception as e:
            await message.reply_text(f"Error sending video: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await message.reply_text("Failed to download the Reel. It might be private, deleted, or blocked.")

# Run the bot
if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
