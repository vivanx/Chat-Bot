import re, os
from pyrogram import Client, filters
from instagrapi import Client as InstaClient

# Telegram bot credentials
API_ID = "12380656"  # Get from https://my.telegram.org
API_HASH = "d927c13beaaf5110f25c505b7c071273"  # Get from https://my.telegram.org
BOT_TOKEN = "7497440658:AAEpmmyRiihvPgigWVJ2JYDF8VnYhGMFXTM"  # Get from @BotFather

# Instagram credentials
INSTA_USERNAME = "YOUR_INSTAGRAM_USERNAME"
INSTA_PASSWORD = "YOUR_INSTAGRAM_PASSWORD"

# Initialize Pyrogram client
app = Client("insta_reel_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize instagrapi client
insta = InstaClient()

# Login to Instagram
try:
    insta.login(INSTA_USERNAME, INSTA_PASSWORD)
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
                # Download the video
                file_path = f"reel_{media_pk}.mp4"
                insta.download(video_url, file_path)
                return file_path
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
        await message.reply_text("Failed to download the Reel. It might be private or invalid.")

# Run the bot
if __name__ == "__main__":
    print("Bot is starting...")
    app.run()
