from pyrogram import Client, filters
from pyrogram.types import Message
import requests

# config.py
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7834584002:AAFGQRrqKE3iFek1FPo-e27x59VUU11Bj6g"

# Telegraph alternative (graph.org)
UPLOAD_URL = "https://graph.org/upload"

app = Client("tgm-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def is_supported(media: Message) -> bool:
    return media.photo or media.video or media.document


@app.on_message(filters.command("tgm") & filters.reply)
async def upload_to_graph(client, message: Message):
    reply = message.reply_to_message

    if not is_supported(reply):
        await message.reply("❌ Please reply to a photo, video, or document.")
        return

    # Download media to memory
    media_path = await reply.download()
    try:
        with open(media_path, "rb") as media_file:
            response = requests.post(UPLOAD_URL, files={"file": media_file})

        if response.ok:
            result = response.json()[0]
            link = f"https://graph.org{result['src']}"
            await message.reply(f"✅ Uploaded:\n{link}")
        else:
            await message.reply("❌ Upload failed. Try again later.")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")
    finally:
        import os
        os.remove(media_path)


print("Bot running...")
app.run()
