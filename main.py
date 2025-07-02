import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Telegram Bot Configuration
API_ID = 12380656
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"

# Freepik API Configuration
FREEMIK_API_URL = "https://api.freepik.com/v1/ai/mystic"
FREEMIK_API_KEY = "FPSXa77daa5a26a707a0378902effbd1b594"  # Your provided API key
HEADERS = {
    "x-freepik-api-key": FREEMIK_API_KEY,
    "Content-Type": "application/json"
}

# Initialize Pyrogram Client
app = Client("FreepikAIBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Command handler for /start
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "Welcome to the Freepik AI Bot! Send me a text prompt, and I'll generate an image for you using Freepik's AI. For example: 'A mystical forest at night'."
    )

# Handler for text messages (prompts)
@app.on_message(filters.text & ~filters.command(["start"]))
async def generate_image(client: Client, message: Message):
    prompt = message.text
    await message.reply_text("Generating image, please wait...")

    # Freepik API payload
    payload = {
        "prompt": prompt,  # User's input as the prompt
        "structure_strength": 50,
        "adherence": 50,
        "hdr": 50,
        "resolution": "4k",
        "aspect_ratio": "square_1_1",
        "model": "realism",
        "creative_detailing": 33,
        "engine": "automatic",
        "fixed_generation": False,
        "filter_nsfw": False
    }

    try:
        # Make request to Freepik API
        response = requests.post(FREEMIK_API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()

        # Assuming the API returns an image URL in the response
        if "image_url" in data:
            image_url = data["image_url"]
            await message.reply_photo(image_url, caption=f"Generated image for: '{prompt}'")
        else:
            await message.reply_text("Sorry, no image URL was returned by the API.")
            
    except requests.exceptions.RequestException as e:
        await message.reply_text(f"Error generating image: {str(e)}")
    except ValueError:
        await message.reply_text("Error: Invalid response from Freepik API.")
    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {str(e)}")

# Start the bot
print("Bot is running...")
app.run()
