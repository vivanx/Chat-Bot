import aiohttp
import asyncio
import os
import re
from instagrapi import Client as InstaClient
from instagrapi.exceptions import LoginRequired, TwoFactorRequired
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram bot credentials
BOT_TOKEN = "7834584002:AAEJF4grVniXFxPO8kM-Gpk3jhX8SFyj3hc"  # Get from @BotFather

# Instagram credentials
INSTA_USERNAME = "rando.m8875"
INSTA_PASSWORD = "Deep@123"
TWO_FACTOR_CODE = None  # Replace with 2FA code if required, or prompt dynamically

# Initialize instagrapi client
insta = InstaClient()

# Load or perform Instagram login
async def login_instagram():
    try:
        if os.path.exists("session.json"):
            insta.load_settings("session.json")
            print("Loaded Instagram session")
        else:
            insta.login(INSTA_USERNAME, INSTA_PASSWORD, verification_code=TWO_FACTOR_CODE)
            insta.dump_settings("session.json")  # Save session after login
            print("Logged into Instagram successfully")
    except TwoFactorRequired:
        print("2FA required. Please provide the 2FA code and restart.")
        exit(1)
    except LoginRequired:
        print("Instagram session expired. Attempting re-login...")
        insta.login(INSTA_USERNAME, INSTA_PASSWORD, verification_code=TWO_FACTOR_CODE)
        insta.dump_settings("session.json")
        print("Re-logged into Instagram successfully")
    except Exception as e:
        print(f"Instagram login failed: {e}")
        exit(1)

# Function to validate Instagram Reel URL
def is_valid_reel_url(url):
    if not isinstance(url, str):
        print(f"URL is not a string: {url}")
        return False
    # Normalize URL by removing query parameters and trailing slashes
    url = url.split('?')[0].rstrip('/')
    # Match Instagram Reel URLs (e.g., https://www.instagram.com/reel/XXXXX)
    pattern = r"https?://(www\.)?instagram\.com/reel/[\w-]+/?$"
    valid = bool(re.match(pattern, url))
    if not valid:
        print(f"Invalid Reel URL: {url}")
    return valid

# Function to download Instagram Reel
async def download_reel(url):
    try:
        # Ensure URL is a string and normalize it
        url = str(url).split('?')[0].rstrip('/')
        print(f"Processing URL: {url}")

        # Extract media ID from URL
        media_pk = insta.media_pk_from_url(url)
        media = insta.media_info(media_pk)

        if media.media_type == 2 and media.video_url:  # Ensure it's a Reel
            video_url = media.video_url
            caption = media.caption_text or "No caption available"

            # Download the video using aiohttp for speed
            file_path = f"reel_{media_pk}.mp4"
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        return file_path, caption
                    else:
                        print(f"Failed to download video: HTTP {response.status}")
                        return None, None
        else:
            print("Media is not a valid Reel or has no video URL")
            return None, None
    except Exception as e:
        print(f"Error downloading reel: {e}")
        return None, None

# Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm a bot that downloads Instagram Reels with captions. Send me a valid Instagram Reel URL."
    )

# Handle incoming messages with Instagram Reel URLs
async def handle_reel_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_valid_reel_url(url):
        await update.message.reply_text("Please send a valid Instagram Reel URL (e.g., https://www.instagram.com/reel/XXXXX/).")
        return

    await update.message.reply_text("Processing your Reel URL...")

    # Download the reel
    file_path, caption = await download_reel(url)

    if file_path and os.path.exists(file_path):
        try:
            # Check file size (Telegram limit: 2 GB = 2,000,000,000 bytes)
            file_size = os.path.getsize(file_path)
            if file_size > 2_000_000_000:
                await update.message.reply_text("Reel is too large for Telegram (>2GB). Try a shorter video.")
                os.remove(file_path)
                return

            # Send the video to the user with the caption
            with open(file_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=caption[:1024],  # Telegram caption limit is 1024 characters
                    supports_streaming=True  # Enable streaming for faster playback
                )
            # Clean up the downloaded file
            os.remove(file_path)
        except Exception as e:
            await update.message.reply_text(f"Error sending video: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await update.message.reply_text("Failed to download the Reel. It might be private, deleted, or blocked.")

# Run the bot
async def main():
    # Perform Instagram login
    await login_instagram()

    # Initialize the Telegram bot
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reel_url))

    print("Bot is starting...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()  # Keep the bot running

if __name__ == "__main__":
    asyncio.run(main())
