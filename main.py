import aiohttp
import io
from pyrogram import Client, filters
from pyrogram.types import Message

# Your credentials
API_ID = 12380656
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"
STABILITY_API_KEY = "sk-HTNsjcABp2S1DSl1AaZZI2UqEnJMgBGsOK1BPA8yn1dg4Wyt"

app = Client("image_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def generate_image(prompt: str) -> bytes:
    url = "https://api.stability.ai/v2beta/stable-image/generate/ultra"

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "image/*"
    }

    # Create multipart/form-data with a dummy file field named 'none'
    form = aiohttp.FormData()
    form.add_field("prompt", prompt)
    form.add_field("output_format", "png")

    # Trick: Add a real (but empty) file to satisfy the multipart/form-data requirement
    dummy_file = io.BytesIO(b"")
    form.add_field("none", dummy_file, filename="dummy.txt", content_type="application/octet-stream")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=form) as resp:
            if resp.status != 200:
                try:
                    error = await resp.json()
                except:
                    error = await resp.text()
                raise Exception(f"API error: {resp.status} - {error}")
            return await resp.read()

@app.on_message(filters.command("image") & filters.private)
async def image_handler(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /image your prompt here")
        return

    prompt = message.text.split(" ", 1)[1]
    await message.reply("Generating image... please wait...")

    try:
        image_data = await generate_image(prompt)
        await message.reply_photo(photo=image_data, caption=f"Prompt: {prompt}")
    except Exception as e:
        await message.reply(f"Error: {e}")

app.run()
