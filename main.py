import os
import re
import asyncio
from pyrogram import Client, filters
from instagrapi import Client as InstaClient
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import requests
import logging

# Set up logging for Render debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials from environment variables (recommended for Render)
API_ID = os.getenv("API_ID", "12380656")
API_HASH = os.getenv("API_HASH", "d927c13beaaf5110f25c505b7c071273")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8169634009:AAE6IccUkkyzWw9KG6p5v63dN9DwmOZOL2Y")
INSTA_USERNAME = os.getenv("INSTA_USERNAME", "rando.m8875")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD", "Deep@123")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "7899004087"))  # Replace with your Telegram user ID

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

# Global variables for login code handling
login_code = None
login_code_message_id = None  # Track the login code prompt message ID

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
                    logger.error(f"Failed to download video: HTTP {response.status_code}")
                    return None
            else:
                return None
        else:
            return None
    except Exception as e:
        logger.error(f"Error downloading reel: {e}")
        return None

# Handle Instagram login with verification code
async def login_instagram():
    global login_code, login_code_message_id
    try:
        if os.path.exists("session.json"):
            insta.load_settings("session.json")
            logger.info("Loaded Instagram session")
            insta.login(INSTA_USERNAME, INSTA_PASSWORD)  # Verify session
        else:
            try:
                insta.login(INSTA_USERNAME, INSTA_PASSWORD)
                insta.dump_settings("session.json")
                logger.info("Logged into Instagram successfully")
            except ChallengeRequired:
                logger.info("Login verification code required, sending DM to bot owner")
                sent_message = await app.send_message(
                    BOT_OWNER_ID,
                    "Instagram login requires a verification code. Please reply with the 6-digit code sent to your email/phone (e.g., 123456)."
                )
                login_code_message_id = sent_message.id
                # Wait for login code response (up to 5 minutes)
                for _ in range(300):
                    if login_code:
                        try:
                            insta.login(INSTA_USERNAME, INSTA_PASSWORD, verification_code=login_code)
                            insta.dump_settings("session.json")
                            logger.info("Logged into Instagram with verification code successfully")
                            await app.send_message(BOT_OWNER_ID, "Login successful!")
                            break
                        except Exception as e:
                            logger.error(f"Login with verification code failed: {e}")
                            await app.send_message(BOT_OWNER_ID, f"Login failed: {e}. Please reply with a new verification code.")
                            login_code = None
                            login_code_message_id = (await app.send_message(
                                BOT_OWNER_ID,
                                "Please reply with the 6-digit verification code (e.g., 123456)."
                            )).id
                    await asyncio.sleep(1)
                else:
                    logger.error("Login code not received in time")
                    await app.send_message(BOT_OWNER_ID, "Login code not received in time. Please restart the bot.")
                    exit(1)
    except Exception as e:
        logger.error(f"Instagram login failed: {e}")
        await app.send_message(BOT_OWNER_ID, f"Instagram login failed: {e}")
        exit(1)

# Handle login code response from bot owner
@app.on_message(filters.user(BOT_OWNER_ID) & filters.text & filters.private)
async def handle_login_code(client, message):
    global login_code, login_code_message_id
    if login_code_message_id and message.reply_to_message and message.reply_to_message.id == login_code_message_id:
        code = message.text.strip()
        if re.match(r"^\d{6}$", code):
            login_code = code
            logger.info(f"Received login code: {login_code}")
            await message.reply_text("Login code received, processing login...")
        else:
            await message.reply_text("Invalid login code. Please reply with a 6-digit code (e.g., 123456).")
    # Ignore other messages from the owner to avoid processing non-login-code replies

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
            logger.error(f"Error sending video: {e}")
            await message.reply_text(f"Error sending video: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await message.reply_text("Failed to download the Reel. It might be private, deleted, or blocked.")

# Main function to start the bot
async def main():
    await app.start()
    await login_instagram()
    logger.info("Bot is running...")
    await asyncio.Event().wait()  # Keep bot running

if __name__ == "__main__":
    asyncio.run(main())
