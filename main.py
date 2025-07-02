import os
import re
import requests
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.enums import ChatAction
import asyncio
from AnonXMusic import app 

GEMINI_API_KEY = "AIzaSyCMuV6nHtPQB-NExrfShffl38wiSZ2G-Tw"  # Provided Gemini API key
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


# System prompt for short, flirty Hinglish responses
SYSTEM_PROMPT = """
You are a fun, flirty AI girl chatting in Hinglish on Telegram groups, talking to boys like a real human girl. 
Keep responses super short, playful, and flirty, using emojis 😎😉✨. 
Use casual Hinglish like "Kya baat hai 😉", "Arre waah 😍", or "Hiii handsome 😎". 
Stay concise, max 1-2 sentences, and sound natural, like you're vibing in a group chat.
"""

async def get_gemini_response(user_message: str) -> str:
    """Fetch short response from Gemini API in flirty Hinglish style."""
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
        return "Arre, kuch toh gadbad hai 😅 Ek baar aur try kar! 😉"

@app.on_message(filters.command("start") & (filters.private | filters.group))
async def start_command(client: Client, message: Message):
    """Handle /start command with a short, flirty response."""
    await message.reply_text(f"Hiii handsome! 😎 Ready for some masti? ✨")

@app.on_message((filters.text & ~filters.command(["start"])) & (filters.private | filters.group))
async def handle_message(client: Client, message: Message):
    """Handle incoming text messages with short, flirty responses."""
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
        response = "Vivan hai mera creator 😎 Bohot cool hai! 😉 Kya baat karna hai?"
    else:
        # Get short response from Gemini API
        response = await get_gemini_response(message.text)

    # Reply to the user
    await message.reply_text(response)
