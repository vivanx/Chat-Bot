import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Telegram Bot Configuration
API_ID = "12380656"  # Get from https://my.telegram.org
API_HASH = "d927c13beaaf5110f25c505b7c071273"  # Get from https://my.telegram.org
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"  # Get from BotFather

# starryAI API Configuration
STARRYAI_API_URL = "https://api.starryai.com/creations/"
STARRYAI_API_KEY = "UUAEfTF-AGuNFMpzrj63-QtpQgx8xg"

# Initialize Pyrogram Client
app = Client("StarryAIBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Command Handler for /generate
@app.on_message(filters.command("generate") & filters.group)
async def generate_image(client: Client, message: Message):
    # Check if the command has a prompt
    if len(message.text.split()) < 2:
        await message.reply("Please provide a prompt. Example: `/generate a futuristic city`")
        return

    # Extract the prompt from the message
    prompt = " ".join(message.text.split()[1:])
    
    # Prepare the payload for starryAI API
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
        # Send request to starryAI API
        response = requests.post(STARRYAI_API_URL, json=payload, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            # Assuming the API returns a URL or a list of image URLs
            # Adjust this based on the actual starryAI API response structure
            image_urls = data.get("image_urls", [])  # Replace with actual key from API response
            if image_urls:
                for url in image_urls:
                    await message.reply_photo(url)
            else:
                await message.reply("No images generated. Please try again.")
        else:
            await message.reply(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

# Start the Bot
print("Bot is running...")
app.run()
