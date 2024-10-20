import os
import yt_dlp
from pyrogram import Client, filters

# Bot API configuration
api_id = "YOUR_API_ID"
api_hash = "YOUR_API_HASH"
bot_token = "YOUR_BOT_TOKEN"

# Initialize the bot
app = Client("yt-dlp-bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Download progress hook function
progress_messages = {}

def progress_hook(d):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 1)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        percent = (downloaded_bytes / total_bytes) * 100
        message_id = d.get('message_id')
        if message_id and message_id in progress_messages:
            try:
                progress_message = progress_messages[message_id]
                progress_message.edit_text(f"Downloading: {d['filename']}\nProgress: {percent:.2f}%")
            except Exception:
                pass  # In case of an issue, ignore for now
    elif d['status'] == 'finished':
        print(f"Done downloading, now converting {d['filename']}")

# Download audio from YouTube playlist
def download_playlist_as_audio(playlist_url, download_path="downloads", message_id=None):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'noplaylist': False,  # Ensure the entire playlist is downloaded
        'progress_hooks': [progress_hook],
        'message_id': message_id  # Custom field to track progress by message ID
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])

# /start command handler to welcome the user
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply("Hello! Send a YouTube playlist link with /download to download audio.\nExample: `/download <playlist_url>`")

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

    download_path = "downloads"
    os.makedirs(download_path, exist_ok=True)

    # Store message ID for progress updates
    message_id = status_message.message_id
    progress_messages[message_id] = status_message

    try:
        # Download the playlist as audio and track progress
        download_playlist_as_audio(playlist_url, download_path, message_id=message_id)

        # Send each downloaded audio file to the user
        for audio_file in os.listdir(download_path):
            audio_path = os.path.join(download_path, audio_file)
            await message.reply_audio(audio_path)

        # Clean up downloaded files
        for audio_file in os.listdir(download_path):
            os.remove(os.path.join(download_path, audio_file))

    except Exception as e:
        await message.reply(f"An error occurred: {e}")
    finally:
        # Clean up progress message after completion or error
        if message_id in progress_messages:
            del progress_messages[message_id]

# Start the bot
app.run() 
