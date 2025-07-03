import aiohttp
import os
import time
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import Message

# Bot configuration
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7834584002:AAFGQRrqKE3iFek1FPo-e27x59VUU11Bj6g"
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID", "YOUR_IMGUR_CLIENT_ID")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "YOUR_IMGBB_API_KEY")
DEFAULT_SERVICE = "catbox"  # Fastest default service
CATBOX_API = "https://catbox.moe/user/api.php"
SERVICES = {
    "catbox": {"url": "https://catbox.moe/user/api.php", "params": {"reqtype": "fileupload"}},
    "litterbox": {"url": "https://litterbox.catbox.moe/resources/internals/api.php", "params": {"reqtype": "fileupload", "time": "1h"}},
    "imgur": {"url": "https://api.imgur.com/3/image", "headers": {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}},
    "imgbb": {"url": "https://api.imgbb.com/1/upload", "params": {"key": IMGBB_API_KEY}},
    "uguu": {"url": "https://uguu.se/upload", "params": {}},
}

# Initialize Pyrogram client with optimized settings
app = Client(
    "fast_upload_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True  # Avoid disk-based session storage
)

async def upload_to_service(file_data: BytesIO, file_name: str, service: str = DEFAULT_SERVICE) -> tuple[str, float]:
    """Upload a file to the specified service, return URL and upload time."""
    start_time = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        try:
            file_data.seek(0)  # Reset buffer position
            service_info = SERVICES[service]
            data = service_info.get("params", {}).copy()
            data["fileToUpload" if service in ["catbox", "litterbox", "uguu"] else "image"] = (file_data, file_name)
            headers = service_info.get("headers", {})
            async with session.post(service_info["url"], data=data, headers=headers) as response:
                upload_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
                if response.status == 200:
                    result = await response.json() if service in ["imgur", "imgbb"] else await response.text()
                    if service == "catbox" or service == "litterbox":
                        url = result.strip() if result.startswith(("https://files.catbox.moe/", "https://litterbox.catbox.moe/")) else f"API error: {result}"
                    elif service == "imgur":
                        url = result["data"]["link"]
                    elif service == "imgbb":
                        url = result["data"]["url"]
                    elif service == "uguu":
                        url = result.strip() if result.startswith("https://a.uguu.se/") else f"API error: {result}"
                    return url, upload_time
                return f"Upload failed with status {response.status}", upload_time
        except Exception as e:
            return f"Error: {str(e)}", (time.perf_counter() - start_time) * 1000

@app.on_message(filters.command("tgm") & filters.reply)
async def handle_tgm(client: Client, message: Message):
    """Handle /tgm command to upload media to Catbox (fastest)."""
    start_time = time.perf_counter()
    reply = message.reply_to_message
    media = reply.photo or reply.video or reply.document

    if not media:
        await message.reply("Reply to a photo, video, or document.")
        return

    # Minimal file validation
    if media.file_size > 100 * 1024 * 1024:  # 100MB limit
        await message.reply("File too large (max 100MB).")
        return

    # Download media to memory
    file_data = BytesIO()
    file_name = "media.jpg"  # Default name
    if reply.photo:
        file_name = "photo.jpg"
    elif reply.video:
        file_name = f"video.{reply.video.mime_type.split('/')[-1]}" if reply.video.mime_type else "video.mp4"
    elif reply.document:
        file_name = reply.document.file_name or "document"

    try:
        await client.download_media(media, file_obj=file_data)
    except Exception as e:
        await message.reply(f"Download failed: {str(e)}")
        return

    # Upload to Catbox (or other service via env variable)
    service = os.getenv("UPLOAD_SERVICE", DEFAULT_SERVICE)
    url, upload_time = await upload_to_service(file_data, file_name, service)
    total_time = (time.perf_counter() - start_time) * 1000  # Convert to ms

    await message.reply(f"{url}\nUpload time: {upload_time:.3f}ms\nTotal time: {total_time:.3f}ms")

if __name__ == "__main__":
    app.run()
