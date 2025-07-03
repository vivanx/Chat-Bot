import aiohttp
import os
from pyrogram import Client, filters
from pyrogram.types import Message

# config.py
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7834584002:AAFGQRrqKE3iFek1FPo-e27x59VUU11Bj6g"
TELEGRAPH_API = "https://api.graph.org/upload"  # Replace with working Telegraph alternative

# Initialize Pyrogram client
app = Client("telegraph_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def upload_to_telegraph(file_path: str) -> str:
    """Upload a file to Telegraph alternative."""
    async with aiohttp.ClientSession() as session:
        with open(file_path, "rb") as f:
            async with session.post(TELEGRAPH_API, data={"file": f}) as response:
                if response.status == 200:
                    result = await response.json()
                    return f"https://graph.org{result.get('src', '')}" if result.get("src") else None
                return None

@app.on_message(filters.command("tgm") & filters.reply)
async def handle_tgm(client: Client, message: Message):
    """Handle /tgm command to upload replied media to Telegraph."""
    reply = message.reply_to_message
    media = reply.photo or reply.video or reply.document

    if not media:
        await message.reply("Reply to a photo, video, or document.")
        return

    # Download media
    file = await client.download_media(media)
    if not file:
        await message.reply("Failed to download media.")
        return

    try:
        # Upload and reply with URL
        url = await upload_to_telegraph(file)
        await message.reply(url or "Failed to upload to Telegraph.")
    finally:
        os.remove(file)  # Clean up

if __name__ == "__main__":
    app.run()
