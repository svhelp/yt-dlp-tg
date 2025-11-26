import os
import yt_dlp
import traceback
import src.config

from src.core.utils import generate_random_string
from src.db.repository import create_file_data

from src.db.schema import Request

STORAGE_PATH = os.getenv("STORAGE_PATH")
MAX_FILE_SIZE = 45 * 1024 * 1024

async def process_video(request: Request, link: str):
    hash_name = generate_random_string(16)
    ydl_opts = {
        'outtmpl': f'{STORAGE_PATH}/{hash_name}.%(ext)s',
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        elements_count = len(info['entries']) if 'entries' in info else 1

        if elements_count != 1:
            return {
                'error_message': f'Videos count: {elements_count}'
            }
        
        filesize = (
            info.get('filesize')
            or info.get('filesize_approx')
            or (info.get('formats')[-1].get('filesize') if info.get('formats') else None)
        )

        if filesize > MAX_FILE_SIZE:
            return {
                'error_message': f'File is too big: {filesize}'
            }
        
        try:
            info = ydl.extract_info(link, download=True)
            path = info['requested_downloads'][0]['filepath']
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
