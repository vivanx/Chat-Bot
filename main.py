import aiohttp
import os
from pyrogram import Client, filters
from pyrogram.types import Message

# Bot configuration
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7834584002:AAFGQRrqKE3iFek1FPo-e27x59VUU11Bj6g"
CATBOX_API = "https://catbox.moe/user/api.php"

# Initialize Pyrogram client
app = Client("catbox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def upload_to_catbox(file_path: str) -> str:
    """Upload a file to Catbox.moe anonymously."""
    async with aiohttp.ClientSession() as session:
        try:
            with open(file_path, "rb") as f:
                async with session.post(
                    CATBOX_API,
                    data={"reqtype": "fileupload", "fileToUpload": f}
                ) as response:
                    if response.status == 200:
                        url = await response.text()
                        return url.strip() if url.startswith("https://files.catbox.moe/") else f"API error: {url}"
                    return f"Upload failed with status {response.status}: {await response.text()}"
        except aiohttp.ClientError as e:
            return f"Network error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

@app.on_message(filters.command("tgm") & filters.reply)
async def handle_tgm(client: Client, message: Message):
    """Handle /tgm command to upload replied media to Catbox.moe."""
    reply = message.reply_to_message
    media = reply.photo or reply.video or reply.document

    if not media:
        await message.reply("Reply to a photo, video, or document.")
        return

    # Check file type and size (Catbox supports up to 200MB)
    if reply.document and reply.document.mime_type not in [
        "image/jpeg", "image/png", "image/gif", "video/mp4", "video/webm", "audio/mpeg", "audio/ogg"
    ]:
        await message.reply("Only .jpg, .png, .gif, .mp4, .webm, .mp3, and .ogg are supported.")
        return
    if media.file_size > 200 * 1024 * 1024:
        await message.reply("File too large (max 200MB).")
        return

    # Download media
    file = await client.download_media(media)
    if not file:
        await message.reply("Failed to download media.")
        return

    try:
        # Upload and reply with URL
        url = await upload_to_catbox(file)
        await message.reply(url or "Failed to upload to Catbox.moe.")
    finally:
        os.remove(file)  # Clean up

if __name__ == "__main__":
    app.run()
