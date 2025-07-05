from pyrogram import Client, filters, enums
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageDeleteForbidden
import re
import time
import sqlite3
import logging
import asyncio
from collections import defaultdict
from Bad import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize SQLite database for filter states
def init_db():
    conn = sqlite3.connect("filter_states.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS filter_states (
            chat_id INTEGER PRIMARY KEY,
            link_filter INTEGER DEFAULT 1,
            file_filter INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_db()

def set_filter_state(chat_id: int, link_filter: bool = None, file_filter: bool = None):
    conn = sqlite3.connect("filter_states.db")
    cursor = conn.cursor()
    if link_filter is not None and file_filter is not None:
        cursor.execute(
            "INSERT OR REPLACE INTO filter_states (chat_id, link_filter, file_filter) VALUES (?, ?, ?)",
            (chat_id, int(link_filter), int(file_filter))
        )
    elif link_filter is not None:
        cursor.execute("UPDATE filter_states SET link_filter = ? WHERE chat_id = ?", (int(link_filter), chat_id))
    elif file_filter is not None:
        cursor.execute("UPDATE filter_states SET file_filter = ? WHERE chat_id = ?", (int(file_filter), chat_id))
    conn.commit()
    conn.close()

def get_filter_state(chat_id: int) -> tuple:
    conn = sqlite3.connect("filter_states.db")
    cursor = conn.cursor()
    cursor.execute("SELECT link_filter, file_filter FROM filter_states WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return (bool(result[0]), bool(result[1])) if result else (True, True)

# Regex for link detection (improved to handle more TLDs and valid URLs)
LINK_REGEX = r"(https?://[^\s/$.?#].[^\s]*|www\.[^\s/$.?#].[^\s]*|\b\S+\.[a-zA-Z]{2,}\b)"

# Spam tracking
SPAM_THRESHOLD = 5  # Max messages per minute
SPAM_INTERVAL = 60  # Seconds
user_message_times = defaultdict(list)

# Allowed file extensions
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4')

# Helper function to check if user is admin using enums
async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
    except Exception as e:
        logger.error(f"Error checking admin status for user {user_id} in chat {chat_id}: {e}")
        return False

# Helper function to check bot permissions
async def can_delete_messages(chat_id: int) -> bool:
    try:
        chat = await app.get_chat(chat_id)
        return chat.permissions.can_delete_messages if chat.permissions else False
    except Exception as e:
        logger.error(f"Error checking bot permissions in chat {chat_id}: {e}")
        return False

# Command to enable filters
@app.on_message(filters.group & filters.command(["enablelink", "enablefile", "enableall"]) & filters.admin)
async def enable_filters(_, message: Message):
    chat_id = message.chat.id
    command = message.command[0].lower()
    link_filter, file_filter = get_filter_state(chat_id)

    if command == "enablelink":
        set_filter_state(chat_id, link_filter=True)
        await message.reply_text("Anti-link filter has been enabled for this chat.")
        logger.info(f"Anti-link filter enabled in chat {chat_id} by {message.from_user.id}")
    elif command == "enablefile":
        set_filter_state(chat_id, file_filter=True)
        await message.reply_text("Anti-file filter has been enabled for this chat.")
        logger.info(f"Anti-file filter enabled in chat {chat_id} by {message.from_user.id}")
    elif command == "enableall":
        set_filter_state(chat_id, link_filter=True, file_filter=True)
        await message.reply_text("Anti-link and anti-file filters have been enabled for this chat.")
        logger.info(f"All filters enabled in chat {chat_id} by {message.from_user.id}")

# Command to disable filters
@app.on_message(filters.group & filters.command(["disablelink", "disablefile", "disableall"]) & filters.admin)
async def disable_filters(_, message: Message):
    chat_id = message.chat.id
    command = message.command[0].lower()
    link_filter, file_filter = get_filter_state(chat_id)

    if command == "disablelink":
        set_filter_state(chat_id, link_filter=False)
        await message.reply_text("Anti-link filter has been disabled for this chat.")
        logger.info(f"Anti-link filter disabled in chat {chat_id} by {message.from_user.id}")
    elif command == "disablefile":
        set_filter_state(chat_id, file_filter=False)
        await message.reply_text("Anti-file filter has been disabled for this chat.")
        logger.info(f"Anti-file filter disabled in chat {chat_id} by {message.from_user.id}")
    elif command == "disableall":
        set_filter_state(chat_id, link_filter=False, file_filter=False)
        await message.reply_text("Anti-link and anti-file filters have been disabled for this chat.")
        logger.info(f"All filters disabled in chat {chat_id} by {message.from_user.id}")

# Command to check filter status
@app.on_message(filters.group & filters.command("filterstatus") & filters.admin)
async def filter_status(_, message: Message):
    chat_id = message.chat.id
    link_filter, file_filter = get_filter_state(chat_id)
    status = f"Anti-link filter: {'enabled' if link_filter else 'disabled'}\n"
    status += f"Anti-file filter: {'enabled' if file_filter else 'disabled'}"
    await message.reply_text(f"Filter status for this chat:\n{status}")
    logger.info(f"Filter status checked in chat {chat_id} by {message.from_user.id}")

# Anti-Link Filter
@app.on_message(filters.group & filters.text & ~filters.private)
async def anti_link(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    link_filter, _ = get_filter_state(chat_id)

    # Skip if filter is disabled or user is admin
    if not link_filter or await is_admin(chat_id, user_id):
        return

    # Rate limiting
    current_time = time.time()
    user_message_times[user_id].append(current_time)
    user_message_times[user_id] = [t for t in user_message_times[user_id] if current_time - t < SPAM_INTERVAL]
    if len(user_message_times[user_id]) > SPAM_THRESHOLD:
        await message.reply_text(f"{message.from_user.mention} You are sending messages too fast!")
        logger.warning(f"User {user_id} in chat {chat_id} is spamming")
        return

    if re.search(LINK_REGEX, message.text.lower()):
        try:
            if await can_delete_messages(chat_id):
                await message.delete()
                warning = f"{message.from_user.mention} Links are not allowed."
                await message.reply_text(warning)
                logger.info(f"Deleted link message from user {user_id} in chat {chat_id}")
            else:
                await message.reply_text("Bot lacks permission to delete messages.")
                logger.warning(f"Bot lacks delete permission in chat {chat_id}")
        except FloodWait as e:
            logger.warning(f"FloodWait error: Sleeping for {e.value} seconds")
            await asyncio.sleep(e.value)
            await message.reply_text(warning)
        except MessageDeleteForbidden:
            await message.reply_text("Bot lacks permission to delete messages.")
            logger.warning(f"Bot lacks delete permission in chat {chat_id}")
        except Exception as e:
            logger.error(f"Link Deletion Error in chat {chat_id}: {e}")

# Anti-File Filter
@app.on_message(filters.group & filters.document)
async def anti_files(_, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    _, file_filter = get_filter_state(chat_id)

    # Skip if filter is disabled or user is admin
    if not file_filter or await is_admin(chat_id, user_id):
        return

    # Rate limiting
    current_time = time.time()
    user_message_times[user_id].append(current_time)
    user_message_times[user_id] = [t for t in user_message_times[user_id] if current_time - t < SPAM_INTERVAL]
    if len(user_message_times[user_id]) > SPAM_THRESHOLD:
        await message.reply_text(f"{message.from_user.mention} You are sending messages too fast!")
        logger.warning(f"User {user_id} in chat chat {chat_id} is spamming")
        return

    try:
        file_name = message.document.file_name.lower() if message.document.file_name else ""
        if not file_name.endswith(ALLOWED_EXTENSIONS):
            if await can_delete_messages(chat_id):
                await message.delete()
                warning = (
                    f"{message.from_user.mention} Only image (.jpg, .jpeg, .png, .gif) "
                    "and media (.mp3, .mp4) files are allowed."
                )
                await message.reply_text(warning)
                logger.info(f"Deleted file message from user {user_id} in chat {chat_id}")
            else:
                await message.reply_text("Bot lacks permission to delete messages.")
                logger.warning(f"Bot lacks delete permission in chat {chat_id}")
        else:
            logger.info(f"Allowed file {file_name} from user {user_id} in chat {chat_id}")
    except FloodWait as e:
        logger.warning(f"FloodWait error: Sleeping for {e.value} seconds")
        await asyncio.sleep(e.value)
        await message.reply_text(warning)
    except MessageDeleteForbidden:
        awaitu message.reply_text("Bot lacks permission to delete messages.")
        logger.warning(f"Bot lacks delete permission in chat {chat_id}")
    except Exception as e:
        logger.error(f"File Deletion Error in chat {chat_id}: {e}")
