from pyrogram import Client, filters
import requests
import os

# Telegram Bot API token (get this from BotFather)
API_ID = 12380656
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"
STABILITY_API_KEY = "sk-HTNsjcABp2S1DSl1AaZZI2UqEnJMgBGsOK1BPA8yn1dg4Wyt"

# Initialize Pyrogram Client
app = Client("image_gen_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Command handler for /start
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Welcome to the Image Generation Bot! Use /generate <prompt> to create an image.")

# Command handler for /generate
@app.on_message(filters.command("generate"))
async def generate_image(client, message):
    # Extract the prompt from the message
    prompt = " ".join(message.command[1:])
    
    if not prompt:
        await message.reply_text("Please provide a prompt. Usage: /generate <description>")
        return

    await message.reply_text("Generating image, please wait...")

    try:
        # Make request to Stability AI API
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/ultra",
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
                "accept": "image/*"
            },
            files={"none": ''},
            data={
                "prompt": prompt,
                "output_format": "webp",
            },
        )

        # Check if the request was successful
        if response.status_code == 200:
            # Save the image temporarily
            image_path = f"temp_{message.chat.id}.webp"
            with open(image_path, 'wb') as file:
                file.write(response.content)

            # Send the image to the user
            await message.reply_photo(image_path, caption=f"Generated image: {prompt}")

            # Clean up the temporary file
            os.remove(image_path)
        else:
            error_message = response.json().get("message", "Unknown error")
            await message.reply_text(f"Error generating image: {error_message}")

    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

# Run the bot
print("Bot is running...")
app.run()
