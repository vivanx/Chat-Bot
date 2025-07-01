import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import os

# Telegram Bot Configuration
API_ID = "12380656"
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"

# starryAI API Configuration
STARRYAI_API_URL = "https://api.starryai.com/creations/"
STARRYAI_API_KEY = "UUAEfTF-AGuNFMpzrj63-QtpQgx8xg"

# Initialize Pyrogram Client
app = Client("StarryAIBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to check task status using creation_id
def check_task_status(creation_id):
    status_url = f"https://api.starryai.com/creations/{creation_id}"
    headers = {
        "accept": "application/json",
        "X-API-Key": STARRYAI_API_KEY
    }
    try:
        response = requests.get(status_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return {"error": f"Status check failed with code {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": f"Status check error: {str(e)}"}

# Download image as .jpg and return local path
def download_image_as_jpg(url, index):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_path = f"image_{index}.jpg"
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return file_path
        else:
            return None
    except Exception as e:
        print(f"Download error: {e}")
        return None

# Command Handler for /generate
@app.on_message(filters.command("generate") & filters.group)
async def generate_image(client: Client, message: Message):
    if len(message.text.split()) < 2:
        await message.reply("Please provide a prompt. Example: `/generate a futuristic city`")
        return

    prompt = " ".join(message.text.split()[1:])

    payload = {
        "model": "lyra",
        "aspectRatio": "square",
        "highResolution": False,
        "images": 4,
        "steps": 20,
        "initialImageMode": "color",
        "prompt": prompt
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": STARRYAI_API_KEY
    }

    try:
        response = requests.post(STARRYAI_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            creation_id = data.get("creation_id") or data.get("id")
            if not creation_id:
                await message.reply(f"No creation_id returned. API response: {data}")
                return

            await message.reply("Image generation started. Checking status every 10 seconds...")

            for attempt in range(10):
                status_data = check_task_status(creation_id)
                status = status_data.get("status")
                image_urls = status_data.get("imageUrls") or status_data.get("images", [])

                if status == "completed" and image_urls:
                    for idx, url in enumerate(image_urls):
                        jpg_path = download_image_as_jpg(url, idx)
                        if jpg_path:
                            await message.reply_photo(photo=jpg_path)
                            os.remove(jpg_path)  # Clean up after sending
                        else:
                            await message.reply(f"Failed to download image from: {url}")
                    return
                elif status == "failed":
                    await message.reply(f"Image generation failed: {status_data.get('error', 'Unknown error')}")
                    return
                elif "error" in status_data:
                    await message.reply(f"Status error: {status_data['error']}")
                    return

                await asyncio.sleep(10)

            await message.reply("Image generation timed out. Please try again later.")
        else:
            await message.reply(f"API Error: {response.status_code} - {response.text}")

    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

# Start the Bot
print("Bot is running...")
app.run()
