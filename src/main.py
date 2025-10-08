import os
import yt_dlp

import src.api
    
# def download_video(message, url, audio=False, format_id="mp4"):
#     msg = bot.reply_to(message, 'Downloading...')
#     video_title = round(time.time() * 1000)

#     with yt_dlp.YoutubeDL({'format': format_id, 'outtmpl': f'{config.output_folder}/{video_title}.%(ext)s', 'postprocessors': [{  # Extract audio using ffmpeg
#         'key': 'FFmpegExtractAudio',
#         'preferredcodec': 'mp3',
#     }] if audio else [], 'max_filesize': config.max_filesize}) as ydl:
#         info = ydl.extract_info(url, download=True)

#         try:
#             bot.edit_message_text(
#                 chat_id=message.chat.id, message_id=msg.message_id, text='Sending file to Telegram...')
#             try:
#                 width = info['requested_downloads'][0]['width']
#                 height = info['requested_downloads'][0]['height']

#                 bot.send_video(message.chat.id, open(
#                     info['requested_downloads'][0]['filepath'], 'rb'), reply_to_message_id=message.message_id, width=width, height=height)
#                 bot.delete_message(message.chat.id, msg.message_id)
#             except Exception as e:
#                 bot.edit_message_text(
#                     chat_id=message.chat.id, message_id=msg.message_id, text=f"Couldn't send file, make sure it's supported by Telegram and it doesn't exceed *{round(config.max_filesize / 1000000)}MB*", parse_mode="MARKDOWN")

#         except Exception as e:
#             if isinstance(e, yt_dlp.utils.DownloadError):
#                 bot.edit_message_text(
#                     'Invalid URL', message.chat.id, msg.message_id)
#             else:
#                 bot.edit_message_text(
#                     f"There was an error downloading your video, make sure it doesn't exceed *{round(config.max_filesize / 1000000)}MB*", message.chat.id, msg.message_id, parse_mode="MARKDOWN")
#     for file in os.listdir(config.output_folder):
#         if file.startswith(str(video_title)):
#             os.remove(f'{config.output_folder}/{file}')
