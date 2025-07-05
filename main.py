import os
import re
import asyncio
from pyrogram import Client, filters
from instagrapi import Client as InstaClient
from instagrapi.exceptions import TwoFactorRequired
import requests

# Telegram credentials
API_ID = "12380656"  # Get from https://my.telegram.org
API_HASH = "d927c13beaaf5110f25c505b7c071273"  # Get from https://my.telegram.org
BOT_TOKEN = "8169634009:AAE6IccUkkyzWw9KG6p5v63dN9DwmOZOL2Y"  # Get from @BotFather

# Instagram credentials
INSTA_USERNAME = "rando.m8875"
INSTA_PASSWORD = "Deep@123"

# Bot owner Telegram user ID (replace with your Telegram user ID)
BOT_OWNER_ID = 7899004087  # Replace with your Telegram user ID (integer)

# Initialize Pyrogram client
app = Client(
    "fast_upload_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# Initialize instagrapi client
insta = InstaClient()
insta.delay_range = [1, 3]  # Add delay to avoid rate limits

# Global variable to store 2FA code
two_factor_code = None

# Function to validate Instagram Reel URL
def is_valid_reel_url(url):
    return bool(re.match(r"https?://www\.instagram\.com/reel/[\w-]+/?", url))

# Function to download Instagram Reel
async def download_reel(url):
    try:
        media_pk = insta.media_pk_from_url(url)
        media = insta.media_info(media_pk)
        
        if media.media_type == 2:  # Video (Reel)
            video_url = media.video_url
            if video_url:
                file_path = f"reel_{media_pk}.mp4"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
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

# Handle Instagram login with 2FA
async def login_instagram():
    global two_factor_code
    try:
        if os.path.exists("session.json"):
            insta.load_settings("session.json")
            print("Loaded Instagram session")
        else:
            try:
                insta.login(INSTA_USERNAME, INSTA_PASSWORD)
                insta.dump_settings("session.json")
                print("Logged into Instagram successfully")
            except TwoFactorRequired:
                print("2FA required, sending DM to bot owner...")
                await app.send_message(BOT_OWNER_ID, "Instagram login requires 2FA. Please reply with the 2FA code.")
                # Wait for 2FA code response
                two_factor_code = None
                for _ in range(60):  # Wait up to 60 seconds
                    if two_factor_code:
                        try:
                            insta.login(INSTA_USERNAME, INSTA_PASSWORD, verification_code=two_factor_code)
                            insta.dump_settings("session.json")
                            print("Logged into Instagram with 2FA successfully")
                            await app.send_message(BOT_OWNER_ID, "2FA login successful!")
                            break
                        except Exception as e:
                            print(f"2FA login failed: {e}")
                            await app.send_message(BOT_OWNER_ID, f"2FA login failed: {e}. Please try again.")
                            two_factor_code = None
                    await asyncio.sleep(1)
                else:
                    print("2FA code not received in time")
                    await app.send_message(BOT_OWNER_ID, "2FA code not received in time. Please restart the bot.")
                    exit(1)
    except Exception as e:
        print(f"Instagram login failed: {e}")
        await app.send_message(BOT_OWNER_ID, f"Instagram login failed: {e}")
        exit(1)

# Handle 2FA code response from bot owner
@app.on_message(filters.user(BOT_OWNER_ID) & filters.text & filters.private)
async def handle_2fa_code(client, message):
    global two_factor_code
    if two_factor_code is None and re.match(r"^\d{6}$", message.text.strip()):
        two_factor_code = message.text.strip()
        print(f"Received 2FA code: {two_factor_code}")
        await message.reply_text("2FA code received, processing login...")
    else:
        await message.reply_text("Please send a valid 6-digit 2FA code.")

# Handle /start command
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "Hi! I'm a bot that downloads Instagram Reels. Send me a valid Instagram Reel URL to download it."
    )

# Handle incoming messages with Instagram Reel URLs
@app.on_message(filters.text & filters.private & ~filters.user(BOT_OWNER_ID))
async def handle_reel_url(client, message):
    url = message.text.strip()
    
    if not is_valid_reel_url(url):
        await message.reply_text("Please send a valid Instagram Reel URL (e.g., https://www.instagram.com/reel/XXXXX/).")
        return
    
    await message.reply_text("Processing your Reel URL, please wait...")
    
    file_path = await download_reel(url)
    
    if file_path and os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) > 2_000_000_000:
                await message.reply_text("Reel is too large for Telegram (>2GB). Try a shorter video.")
                os.remove(file_path)
                return
            await message.reply_video(
                video=file_path,
                caption="Here is your Instagram Reel!"
            )
            os.remove(file_path)
        except Exception as e:
            await message.reply_text(f"Error sending video: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await message.reply_text("Failed to download the Reel. It might be private, deleted, or blocked.")

# Main function to start the bot
async def main():
    await app.start()
    await login_instagram()
    print("Bot is running...")
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
