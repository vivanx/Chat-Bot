import logging
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = 12380656
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"

# Freepik API configuration
FREEPIC_API_KEY = "FPSXa77daa5a26a707a0378902effbd1b594"
FREEPIC_URL = "https://api.freepik.com/v1/ai/mystic"
HEADERS = {
    "x-freepik-api-key": FREEPIC_API_KEY,
    "Content-Type": "application/json"
}

# Initialize Pyrogram client
app = Client("FreepikAIBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Default payload for Freepik API
DEFAULT_PAYLOAD = {
    "prompt": "",
    "webhook_url": "",  # Optional: Add your webhook URL if needed
    "structure_strength": 50,
    "adherence": 50,
    "hdr": 50,
    "resolution": "2k",
    "aspect_ratio": "square_1_1",
    "model": "realism",
    "creative_detailing": 33,
    "engine": "automatic",
    "filter_nsfw": True,
    "styling": {
        "styles": [],
        "characters": [],
        "colors": [{"color": "#FF0000", "weight": 0.5}]
    }
}

async def generate_image(prompt: str) -> dict:
    """Generate image using Freepik API."""
    try:
        payload = DEFAULT_PAYLOAD.copy()
        payload["prompt"] = prompt
        
        response = requests.post(FREEPIC_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        
        logger.info(f"Freepik API response: {response.status_code}")
        return response.json()
    
    except requests.RequestException as e:
        logger.error(f"Error generating image: {str(e)}")
        return {"error": str(e)}

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    await message.reply_text(
        "Welcome to Freepik AI Bot! Use /generate <prompt> to create an AI-generated image."
    )
    logger.info(f"User {message.from_user.id} started the bot")

@app.on_message(filters.command("generate"))
async def generate_command(client: Client, message: Message):
    """Handle /generate command."""
    if len(message.command) < 2:
        await message.reply_text("Please provide a prompt! Usage: /generate <your prompt>")
        return
    
    prompt = " ".join(message.command[1:])
    await message.reply_text("Generating image, please wait...")
    
    logger.info(f"Generating image for user {message.from_user.id} with prompt: {prompt}")
    
    result = await generate_image(prompt)
    
    if "error" in result:
        await message.reply_text(f"Error: {result['error']}")
        return
    
    # Assuming the API returns a URL to the generated image
    if "data" in result and "image_url" in result["data"]:
        await message.reply_photo(result["data"]["image_url"], caption=f"Generated: {prompt}")
    else:
        await message.reply_text("Image generation completed, but no image URL received.")
    
    logger.info(f"Image generation completed for user {message.from_user.id}")

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle /help command."""
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/generate <prompt> - Generate an AI image with the given prompt\n"
        "/help - Show this help message"
    )
    await message.reply_text(help_text)
    logger.info(f"User {message.from_user.id} requested help")

def main():
    """Run the bot."""
    logger.info("Starting Freepik AI Bot...")
    app.run()

if __name__ == "__main__":
    main()
