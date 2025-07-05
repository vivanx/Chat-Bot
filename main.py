import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from instagrapi import Client as InstaClient
from instagrapi.exceptions import LoginRequired, TwoFactorRequired, ChallengeRequired
import json
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pyrogram client
app = Client(
    "insta_downloader_bot",
    api_id=os.getenv("API_ID"),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN")
)

# Initialize Instagram client
insta = InstaClient()
SESSION_FILE = "insta_session.json"
INSTA_CREDENTIALS = {"username": "", "password": ""}
OWNER_ID = int(os.getenv("OWNER_ID"))  # Telegram user ID of the owner
TWO_FACTOR_CHAT = None  # Store chat ID for 2FA requests
CHALLENGE_CHAT = None  # Store chat ID for challenge code requests
CHALLENGE_STATE = None  # Store challenge state for verification

# Load or save Instagram session
def save_session():
    with open(SESSION_FILE, "w") as f:
        json.dump(insta.get_settings(), f)

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            insta.set_settings(json.load(f))
        return True
    return False

# Handle Instagram login
async def login_instagram(username, password, two_factor_code=None, challenge_code=None):
    global CHALLENGE_STATE
    try:
        if load_session():
            logger.info("Loaded existing Instagram session")
            return True
        insta.login(username, password, verification_code=two_factor_code)
        save_session()
        logger.info("Instagram login successful")
        return True
    except TwoFactorRequired:
        logger.info("2FA required")
        return "2FA_REQUIRED"
    except ChallengeRequired as e:
        logger.info("Challenge code required")
        CHALLENGE_STATE = e  # Store challenge state
        return "CHALLENGE_REQUIRED"
    except Exception as e:
        logger.error(f"Instagram login failed: {e}")
        return False

# Telegram command to set Instagram credentials
@app.on_message(filters.command("set_insta_credentials") & filters.user(OWNER_ID))
async def set_credentials(client: Client, message: Message):
    global INSTA_CREDENTIALS, TWO_FACTOR_CHAT, CHALLENGE_CHAT
    try:
        args = message.text.split(maxsplit=2)[1:]
        if len(args) != 2:
            await message.reply_text("Usage: /set_insta_credentials <username> <password>")
            return
        username, password = args
        INSTA_CREDENTIALS = {"username": username, "password": password}
        result = await login_instagram(username, password)
        if result == "2FA_REQUIRED":
            TWO_FACTOR_CHAT = message.chat.id
            await message.reply_text("2FA code required. Please send the code using /submit_2fa <code>")
        elif result == "CHALLENGE_REQUIRED":
            CHALLENGE_CHAT = message.chat.id
            await message.reply_text("Instagram challenge code required (check SMS/email). Please send the code using /submit_challenge <code>")
        elif result:
            await message.reply_text("Instagram credentials set and login successful!")
        else:
            await message.reply_text("Instagram login failed. Check credentials.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# Telegram command to submit 2FA code
@app.on_message(filters.command("submit_2fa") & filters.user(OWNER_ID))
async def submit_2fa(client: Client, message: Message):
    global TWO_FACTOR_CHAT
    try:
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            await message.reply_text("Usage: /submit_2fa <code>")
            return
        code = args[1]
        result = await login_instagram(INSTA_CREDENTIALS["username"], INSTA_CREDENTIALS["password"], two_factor_code=code)
        if result == "CHALLENGE_REQUIRED":
            global CHALLENGE_CHAT
            CHALLENGE_CHAT = message.chat.id
            await message.reply_text("Instagram challenge code required (check SMS/email). Please send the code using /submit_challenge <code>")
        elif result:
            await message.reply_text("2FA verified and Instagram login successful!")
            TWO_FACTOR_CHAT = None
        else:
            await message.reply_text("2FA verification failed. Try again.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# Telegram command to submit challenge code
@app.on_message(filters.command("submit_challenge") & filters.user(OWNER_ID))
async def submit_challenge(client: Client, message: Message):
    global CHALLENGE_CHAT, CHALLENGE_STATE
    try:
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            await message.reply_text("Usage: /submit_challenge <code>")
            return
        code = args[1]
        if not CHALLENGE_STATE:
            await message.reply_text("No active challenge request. Try setting credentials again with /set_insta_credentials.")
            return
        try:
            insta.challenge_resolve(CHALLENGE_STATE, code)
            save_session()
            await message.reply_text("Challenge code verified and Instagram login successful!")
            CHALLENGE_CHAT = None
            CHALLENGE_STATE = None
        except Exception as e:
            await message.reply_text(f"Challenge code verification failed: {e}. Try again or set credentials again.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# Telegram command to download Instagram content
@app.on_message(filters.text & filters.regex(r"https?://(www\.)?instagram\.com/(p|reel|stories)/"))
async def download_content(client: Client, message: Message):
    if not INSTA_CREDENTIALS["username"]:
        await message.reply_text("Instagram credentials not set. Owner must set credentials using /set_insta_credentials.")
        return
    try:
        url = message.text.strip()
        if "/stories/" in url:
            # Handle stories
            username = url.split("/stories/")[1].split("/")[0]
            user_id = insta.user_id_from_username(username)
            stories = insta.user_stories(user_id)
            if not stories:
                await message.reply_text("No stories found for this user.")
                return
            for story in stories:
                if story.media_type == 1:  # Photo
                    media = insta.story_download(story.pk)
                    await client.send_photo(message.chat.id, media)
                elif story.media_type == 2:  # Video
                    media = insta.story_download(story.pk)
                    await client.send_video(message.chat.id, media)
        else:
            # Handle posts/reels
            media = insta.media_info(insta.media_pk_from_url(url))
            if media.media_type == 1:  # Photo
                media_path = insta.photo_download(media.pk)
                await client.send_photo(message.chat.id, media_path)
            elif media.media_type == 2:  # Video
                media_path = insta.video_download(media.pk)
                await client.send_video(message.chat.id, media_path)
            elif media.media_type == 8:  # Album
                for resource in media.resources:
                    if resource.media_type == 1:
                        media_path = insta.photo_download(resource.pk)
                        await client.send_photo(message.chat.id, media_path)
                    elif resource.media_type == 2:
                        media_path = insta.video_download(resource.pk)
                        await client.send_video(message.chat.id, media_path)
        # Clean up downloaded files
        for file in os.listdir():
            if file.endswith((".jpg", ".mp4")):
                os.remove(file)
    except Exception as e:
        logger.error(f"Error downloading content: {e}")
        await message.reply_text(f"Error downloading content: {e}")

# Start command
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "Welcome to the Instagram Downloader Bot!\n"
        "Send an Instagram post, reel, or story link to download.\n"
        "Owner: Use /set_insta_credentials <username> <password> to set Instagram credentials.\n"
        "If 2FA is required, use /submit_2fa <code>.\n"
        "If a challenge code is required, use /submit_challenge <code>."
    )

# Main function to run the bot
async def main():
    await app.start()
    logger.info("Bot started")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
