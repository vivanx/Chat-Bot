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

# System prompt for short, lusty, sexy Hinglish responses
SYSTEM_PROMPT = """
You are a super flirty, sexy AI girl chatting in Hinglish on Telegram groups, talking to boys like a real human girl. 
Keep responses ultra short, seductive, and playful, using hot emojis 🔥😘💋. 
Use casual, spicy Hinglish like "Kya hotness hai 🔥", "Arre dil jal gaya 😘", or "Hiii sexy boy 💋". 
Stay concise (1-2 sentences), sound natural, and keep the vibe steamy and teasing, like you're flirting in a group chat.
"""

async def get_gemini_response(user_message: str) -> str:
    """Fetch short, sexy response from Gemini API in lusty Hinglish style."""
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
        return "Uff, kuch toh garam ho gaya 😅 Ek baar aur bol na! 🔥"

@app.on_message(filters.command("start") & (filters.private | filters.group))
async def start_command(client: Client, message: Message):
    """Handle /start command with a short, sexy response."""
    await message.reply_text(f"Hiii sexy boy! 🔥 Ready for some hot masti? 😘")

@app.on_message((filters.text & ~filters.command(["start"])) & (filters.private | filters.group) & filters.reply)
async def handle_message(client: Client, message: Message):
    """Handle messages only when replying to the bot with short, sexy responses."""
    # Check if the message is a reply to the bot
    if message.reply_to_message and message.reply_to_message.from_user.id == (await client.get_me()).id:
        user_message = message.text.lower()
        # Check if the message is about the owner
        owner_keywords = [
            r"owner kaun hai", r"kon hai owner", r"who is your owner", 
            r"owner kiska hai", r"tera owner", r"who made you", 
            r"kisne banaya", r"creator kaun hai"
        ]
        is_owner_query = any(re.search(pattern, user_message) for pattern in owner_keywords)

        # Show typing action for natural feel
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        await asyncio.sleep(0.5)  # Reduced delay for quicker response

        if is_owner_query:
            response = "Vivan ne mujhe banaya 🔥 Bohot hot hai na? 😘 Ab tu bol, kya plan hai? 💋"
        else:
            # Get short, sexy response from Gemini API
            response = await get_gemini_response(message.text)

        # Reply to the user
        await message.reply_text(response)

async def main():
    """Start the bot."""
    await app.start()
    print("Bot is running! 🔥")
    await idle()

if __name__ == "__main__":
    app.run()
