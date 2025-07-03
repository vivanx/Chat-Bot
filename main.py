import aiohttp
import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message

# Bot configuration
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7834584002:AAFGQRrqKE3iFek1FPo-e27x59VUU11Bj6g"
TELEGRAPH_API = "https://api.graph.org/upload"

# Initialize Pyrogram client
app = Client("telegraph_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def upload_to_telegraph(file_path: str) -> str:
    """Upload a file to graph.org with retry logic."""
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):  # Retry up to 3 times
            try:
                with open(file_path, "rb") as f:
                    async with session.post(TELEGRAPH_API, data={"file": f}) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("src"):
                                return f"https://graph.org{result['src']}"
                            return f"API error: {result.get('error', 'No src in response')}"
                        return f"Upload failed with status {response.status}: {await response.text()}"
            except aiohttp.ClientError as e:
                return f"Network error: {str(e)}"
            except Exception as e:
                if "FLOOD_WAIT" in str(e):
                    wait_time = int(str(e).split("_")[-1]) if "FLOOD_WAIT" in str(e) else 5
                    await message.reply(f"Rate limit hit, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return f"Unexpected error: {str(e)}"
        return "Failed after retries."

@app.on_message(filters.command("tgm") & filters.reply)
async def handle_tgm(client: Client, message: Message):
    """Handle /tgm command to upload replied media to graph.org."""
    reply = message.reply_to_message
    media = reply.photo or reply.video or reply.document

    if not media:
        await message.reply("Reply to a photo, video, or document.")
        return

    # Check file type
    if reply.document and reply.document.mime_type not in [
        "image/jpeg", "image/png", "image/gif", "video/mp4"
    ]:
        await message.reply("Only .jpg, .png, .gif, and .mp4 are supported.")
        return

    # Download media
    file = await client.download_media(media)
    if not file:
        await message.reply("Failed to download media.")
        return

    try:
        # Upload and reply with result
        url = await upload_to_telegraph(file)
        await message.reply(url or "Failed to upload to graph.org.")
    finally:
        os.remove(file)  # Clean up

if __name__ == "__main__":
    app.run()
