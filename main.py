import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# Replace with your actual credentials
API_ID = 12380656
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"
STABILITY_API_KEY = "sk-HTNsjcABp2S1DSl1AaZZI2UqEnJMgBGsOK1BPA8yn1dg4Wyt"

app = Client("image_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def generate_image(prompt: str) -> bytes:
    url = "https://api.stability.ai/v1/generation/stable-diffusion-v1-5/text-to-image"

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 7,
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 30
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"API error: {resp.status} - {text}")
            data = await resp.json()
            base64_img = data["artifacts"][0]["base64"]
            import base64
            return base64.b64decode(base64_img)

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
