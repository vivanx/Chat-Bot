import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# === Replace with your details ===
API_ID = 12380656  # Your Telegram API ID
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"
GEMINI_API_KEY = "AIzaSyCBO96JCK9wIQ5lMzZbFtLGqOkBCNGqLRI"

# === Pyrogram client ===
app = Client("gemini_image_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# === Generate image with Gemini API ===
async def generate_image(prompt: str) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "parts": [{"text": f"Generate an image for: {prompt}"}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "image/png"
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Error from Gemini API: {resp.status}")
            response_json = await resp.json()
            try:
                image_data_base64 = response_json["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                import base64
                return base64.b64decode(image_data_base64)
            except Exception as e:
                raise Exception("Failed to parse image from response.")

# === Telegram command handler ===
@app.on_message(filters.command("image") & filters.private)
async def image_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /image your prompt here")
        return

    prompt = message.text.split(" ", 1)[1]
    await message.reply("Generating image... please wait...")

    try:
        image_data = await generate_image(prompt)
        await message.reply_photo(photo=image_data, caption=f"Generated for: {prompt}")
    except Exception as e:
        await message.reply(f"Error: {e}")

# === Start the bot ===
app.run()
