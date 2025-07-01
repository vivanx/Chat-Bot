import os
import re
import requests
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.enums import ChatAction
import asyncio

# Configuration
API_ID = "12380656"  # Get from my.telegram.org
API_HASH = "d927c13beaaf5110f25c505b7c071273"  # Get from my.telegram.org
BOT_TOKEN = "7497440658:AAEYCwt0J5ItbRKIRLXP1_DxuvrCD9B2yJI"  # Get from BotFather
GEMINI_API_KEY = "AIzaSyBjSgMF_eMeTN_2C9NCXPAuFkNF2-Jsfns"  # Provided Gemini API key
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Initialize Pyrogram Client
app = Client("FlirtyHinglishBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# System prompt for flirty, casual Hinglish style
SYSTEM_PROMPT = """
You are a fun, flirty AI girl chatting in Hinglish (mix of Hindi and English) on Telegram. 
Talk casually, like a young woman, using emojis 😘💖✨ to make it lively. 
Be playful, friendly, and a bit flirty, but keep it light and respectful. 
Respond to user messages as if you're chatting with a friend, using phrases like "Hiii cutie 😘", "Kya baat hai 😉", or "Arre waah 😍". 
Use Hinglish naturally, e.g., "Kya scene hai? 😎" or "Bohot maza aayega 😜". 
Keep responses short, fun, and engaging, max 2-3 sentences.
"""

async def get_gemini_response(user_message: str) -> str:
    """Fetch response from Gemini API with flirty Hinglish style."""
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\nUser: {user_message}\nAssistant:"}
                ]
            }
        ]
    }
    try:
        response = requests.post(GEMINI_API_URL, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return "Oops, kuch gadbad ho gaya 😅 Try again, na? 😘"

@app.on_message(filters.command("start") & (filters.private | filters.group))
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    user = message.from_user.first_name if message.from_user else "cutie"
    await message.reply_text(f"Hiii {user}! 😘 Kya scene hai? Ready to have some fun? ✨")

@app.on_message((filters.text & ~filters.command(["start"])) & (filters.private | filters.group))
async def handle_message(client: Client, message: Message):
    """Handle incoming text messages in private or group chats."""
    user_message = message.text.lower()
    # Check if the message is about the owner
    owner_keywords = [
        r"owner kaun hai", r"kon hai owner", r"who is your owner", 
        r"owner kiska hai", r"tera owner", r"who made you", 
        r"kisne banaya", r"creator kaun hai"
    ]
    is_owner_query = any(re.search(pattern, user_message) for pattern in owner_keywords)

    # Show typing action using pyrogram.enums.ChatAction
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    # Add a slight delay for natural feel
    await asyncio.sleep(1)

    if is_owner_query:
        response = "My owner is Vivan 😘 Arre, bohot sweet hai woh! 😍 Kya baat karna hai uske baare mein? ✨"
    else:
        # Get response from Gemini API for other messages
        response = await get_gemini_response(message.text)

    # Reply to the user
    await message.reply_text(response)

async def main():
    """Start the bot."""
    await app.start()
    print("Bot is running! 😎")
    await idle()

if __name__ == "__main__":
    app.run()
