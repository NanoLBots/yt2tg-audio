# bot.py

import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import api_id, api_hash, bot_token, download_path
from download_manager import download_content, generate_thumbnail, progress_messages, user_settings

# Initialize the bot
app = Client("yt-dlp-bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# /start command handler to welcome the user
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply("Welcome! Please choose your download mode.", reply_markup=mode_selection_keyboard())

# Function to create inline keyboard for mode selection
def mode_selection_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Audio Only", callback_data="set_mode_audio"),
            InlineKeyboardButton("Video Only", callback_data="set_mode_video"),
            InlineKeyboardButton("Audio&Video", callback_data="set_mode_both"),
        ]
    ])

# Callback query handler for setting download mode
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == "set_mode_audio":
        user_settings[user_id] = 'audio'
        await callback_query.answer("Download mode set to Audio Only.")
        await callback_query.message.reply("Current mode: Audio Only. Choose another mode if you want to change.")
    elif data == "set_mode_video":
        user_settings[user_id] = 'video'
        await callback_query.answer("Download mode set to Video Only.")
        await callback_query.message.reply("Current mode: Video Only. Choose another mode if you want to change.")
    elif data == "set_mode_both":
        user_settings[user_id] = 'both'
        await callback_query.answer("Download mode set to Both Audio and Video.")
        await callback_query.message.reply("Current mode: Both Audio and Video. Choose another mode if you want to change.")

# /download command handler to trigger the download
@app.on_message(filters.command("download") & filters.private)
async def download_playlist(client, message):
    # Get the playlist URL from the message
    if len(message.command) < 2:
        await message.reply("Please provide a YouTube playlist URL after the /download command.")
        return

    playlist_url = message.command[1]

    # Notify the user that the download is starting
    status_message = await message.reply("Starting download...")

    os.makedirs(download_path, exist_ok=True)

    # Store message ID for progress updates
    message_id = status_message.id
    progress_messages[message_id] = status_message

    try:
        # Download the playlist as audio or video based on user preference
        download_content(playlist_url, user_id=message.from_user.id)

        # Send files based on the user's mode
        mode = user_settings.get(message.from_user.id, 'audio')  # Get user's selected mode
        for file in os.listdir(download_path):
            file_path = os.path.join(download_path, file)

            # If the mode is audio, send audio files
            if mode == 'audio' and file.endswith('.mp3'):
                await message.reply_audio(file_path)
            # If the mode is video, send video files
            elif mode == 'video' and file.endswith(('.mp4', '.webm')):
                await message.reply_video(file_path, supports_streaming=True)  # Send video with streaming support
            # If the mode is both, send both audio and video files
            elif mode == 'both':
                if file.endswith('.mp3'):
                    await message.reply_audio(file_path)
                elif file.endswith(('.mp4', '.webm')):
                    await message.reply_video(file_path, supports_streaming=True)  # Send video with streaming support

        # Clean up downloaded files
        for file in os.listdir(download_path):
            os.remove(os.path.join(download_path, file))

    except Exception as e:
        await message.reply(f"An error occurred: {e}")
    finally:
        # Clean up progress message after completion or error
        if message_id in progress_messages:
            await status_message.edit_text("Download process completed!")  # Change the text to indicate completion
            del progress_messages[message_id]  # Remove the message ID from progress messages

# Start the bot
app.run()
