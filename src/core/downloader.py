import os
import yt_dlp
import traceback
import src.config

from src.core.cookies import get_cookies_path
from src.core.utils import generate_random_string
from src.db.repository import create_file_data

from src.db.schema import Request

DEVELOP_MODE = os.getenv("MODE") == 'develop'
STORAGE_PATH = os.getenv("STORAGE_PATH")
MAX_FILE_SIZE = 45 * 1024 * 1024

class DownloadSizeExceeded(Exception):
    """Ошибка: размер файла превысил допустимый лимит"""
    pass

def progress_filesize_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        if downloaded > MAX_FILE_SIZE:
            raise DownloadSizeExceeded(
                f"Превышен лимит {MAX_FILE_SIZE} МБ (скачано {downloaded / 1024 / 1024:.1f} МБ)"
            )
        
async def process_video(request: Request, link: str):
    hash_name = generate_random_string(16)
    cookies_file = get_cookies_path(link)
    ydl_opts = {
        'outtmpl': f'{STORAGE_PATH}/{hash_name}.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessor_args': {
            'default': ["-c:v", "libx265", "-crf", "28", "-c:a", "aac", "-b:a", "128k"]
        },
        'progress_hooks': [progress_filesize_hook],
        'cookiefile': cookies_file,
    }

    if DEVELOP_MODE:
        ydl_opts.update({'verbose': 'true'})

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(link, download=False)
        except Exception as e:
            return {
                'error_message': str(e),
                'error_details': traceback.format_exc()[:1000],
            }
        
        elements_count = len(info['entries']) if 'entries' in info else 1

        if elements_count != 1:
            return {
                'error_message': f'Videos count: {elements_count}'
            }
        
        filesize = (
            info.get('filesize')
            or info.get('filesize_approx')
            or (info.get('formats')[-1].get('filesize') if info.get('formats') else None)
            or 0
        )

        if filesize > MAX_FILE_SIZE:
            return {
                'error_message': f'File is too big: {filesize}'
            }
        
        try:
            download_result = ydl.extract_info(link, download=True)
            path = download_result['requested_downloads'][0]['filepath']
        except DownloadSizeExceeded as e:
            return {
                'error_message': f'File is too big (caught in progress).'
            }
        except Exception as e:
            return {
                'error_message': str(e),
                'error_details': traceback.format_exc()[:1000],
            }
        
    author = info.get("uploader")
    create_file_data(request, path, info.get("title"), info.get("extractor"), info.get("uploader_id"), author)

    return {
        'result': {
            'path': path,
            'author': author,
        }
    }

INSTAGRAM_EXTRACTOR_NAME = 'Instagram'
YOUTUBE_EXTRACTOR_NAME = 'Youtube'
TIKTOK_EXTRACTOR_NAME = 'TikTok'

def parse_video_info(info: dict[str, any]):
    return {
        'title': info.get("title"),
        'video_id': info.get("id"),
        'video_link': prepare_video_link(info),
        'platform': info.get("extractor"),
        'author_name': info.get("uploader"),
        'author_id': info.get("uploader_id"),
    }

def prepare_video_link(info: dict[str, any]):
    extractor = info.get("extractor")

    if extractor == TIKTOK_EXTRACTOR_NAME:
        return f"https://www.tiktok.com/{info.get('uploader_id')}/video/{info.get('id')}"
    
    if extractor == INSTAGRAM_EXTRACTOR_NAME:
        return f"https://www.instagram.com/reel/{info.get('id')}"
    
    if extractor == YOUTUBE_EXTRACTOR_NAME:
        return f"https://www.youtube.com/shorts/{info.get('id')}" if info.get("media_type") == 'short' else f"https://www.youtube.com/watch?v={info.get('id')}"
    
    return None