# download_manager.py

import os
import yt_dlp
import subprocess

# Configuration
from config import download_path

# User settings storage
user_settings = {}
progress_messages = {}

async def progress_hook(d):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 1)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        percent = (downloaded_bytes / total_bytes) * 100
        message_id = d.get('message_id')  # Get the message ID from the download status
        if message_id and message_id in progress_messages:
            try:
                progress_message = progress_messages[message_id]
                await progress_message.edit_text(f"Downloading: {d['filename']}\nProgress: {percent:.2f}%")
            except Exception:
                pass  # Handle exceptions, but ignore for now
    elif d['status'] == 'finished':
        print(f"Done downloading, now converting {d['filename']}")

def generate_thumbnail(video_path, thumbnail_path):
    command = [
        'ffmpeg',
        '-i', video_path,
        '-ss', '00:00:15',  # Take the thumbnail at 1 second into the video
        '-vframes', '1',  # Capture only one frame
        thumbnail_path
    ]
    subprocess.run(command)

def download_content(playlist_url, user_id=None):
    mode = user_settings.get(user_id, 'audio')  # Default mode is audio

    if mode == 'audio':
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
        }
    elif mode == 'video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Ensure we get both audio and video
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'noplaylist': False,  # Ensure the entire playlist is downloaded
            'progress_hooks': [progress_hook],
        }
    elif mode == 'both':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',  # Download audio and video separately
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'noplaylist': False,  # Ensure the entire playlist is downloaded
            'progress_hooks': [progress_hook],
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url]) 
