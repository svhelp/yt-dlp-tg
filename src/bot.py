import os
import yt_dlp
import traceback
import src.config

from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, InputMediaVideo, InlineQueryResultCachedVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, filters, MessageHandler, InlineQueryHandler, ChosenInlineResultHandler, ContextTypes, CommandHandler

from src.core.utils import generate_random_string, verify_supported_url

from src.db.engine import engine
from src.db.schema import User, File, Request, Video, RequestStatus, RequestType, VideoAuthor
from sqlalchemy.orm import Session

HOST = os.getenv("HOST")
TOKEN = os.getenv("TELEGRAM_API_KEY")
STORAGE_PATH = os.getenv("STORAGE_PATH")
MAX_FILE_SIZE = 45 * 1024 * 1024

async def process_link(request: Request, link: str):
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

    with Session(engine) as session:
        file = File(
            path = path
        )
        session.add(file)  
        
        platform = info.get("extractor")
        platform_id = info.get("uploader_id")

        author = session.query(VideoAuthor).filter(VideoAuthor.platform == platform and VideoAuthor.platform_id == platform_id).first()
        if not author:
            author = VideoAuthor(
                platform = platform,
                platform_id = platform_id,
                name = info.get("uploader"),
            )
            session.add(author)    
            
        video = Video(
            original_name = info.get("title"),
            author = author,
            file = file,
            request = request
        )

        session.add(video)
        session.commit()

    return {
        'result': path
    }

async def personal_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type

    if chat_type != 'private':
        return
    
    link = update.message.text.strip()

    if not verify_supported_url(link):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid URL")
        return
    
    sender = update.effective_user

    with Session(engine) as session:
        user = session.get(User, sender.id)
        if not user:
            user = User(
                id=sender.id,
                name=sender.full_name,
                username=sender.username
            )
            session.add(user)    
            
        if user.is_banned:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You are banned")
            return        

        msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing...")

        request = Request(
            chat_id = update.effective_chat.id,
            message_id = msg.message_id,
            status = RequestStatus.PENDING,
            type = RequestType.PERSONAL,
            link = link,
            user_account = user,
        )

        session.add(request)
        session.commit()

    download_result = await process_link(request, link)
    file_path = download_result.get("result")

    if not file_path:
        await msg.edit_text("Error happened.")

        with Session(engine) as session:
            request.status = RequestStatus.FAILED
            request.error_message = download_result.get("error_message")
            request.error_details = download_result.get("error_details")

            session.commit()

    await msg.reply_video(open(file_path, 'rb'))
    with Session(engine) as session:
        request.status = RequestStatus.SUCCESSFUL

        session.commit()

async def chosen_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_option = update.chosen_inline_result
    inline_message_id = chosen_option.inline_message_id

    if not inline_message_id:
        return
    
    link = chosen_option.query.strip()
    sender = chosen_option.from_user

    if not verify_supported_url(link):
        return
    
    with Session(engine) as session:
        user = session.get(User, sender.id)
        if not user:
            user = User(
                id=sender.id,
                name=sender.full_name,
                username=sender.username
            )
            session.add(user)

        if user.is_banned:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, text="You are banned")
            return   
        
        request = Request(
            message_id = inline_message_id,
            status = RequestStatus.PENDING,
            type = RequestType.INLINE,
            link = link,
            user_account = user,
        )

        session.add(request)
        session.commit()
    
    download_result = await process_link(request, link)
    file_path = download_result.get("result")

    if not file_path:
        await context.bot.edit_message_text(
            inline_message_id=inline_message_id,
            text="Error happened."
        )

        with Session(engine) as session:
            request.status = RequestStatus.FAILED
            request.error_message = download_result.get("error_message")
            request.error_details = download_result.get("error_details")

            session.commit()

    await context.bot.edit_message_media(
        inline_message_id=inline_message_id,
        media=InputMediaVideo(
            media=f'{HOST}/static/{os.path.basename(file_path)}',
            caption="✅ Готово!"
        )
    )

    with Session(engine) as session:
        request.status = RequestStatus.SUCCESSFUL

        session.commit()

async def inline_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    if not query:
        return
    
    link = query.strip()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Без этой хуйни не работает", callback_data="edit")]])
    results = []

    if verify_supported_url(link):
        results.append(
            # InlineQueryResultCachedVideo(
            #     id=str(uuid4()),
            #     # mime_type="image/jpeg",
            #     title="Title",
            #     caption="Caption",
            #     description="Description",
            #     # photo_file_id='AgACAgIAAxkBAAN6aOVR6zD6oShCP2fdn4sQfr7vtDIAApgEMhtyPClLYR7rqe8PQmQBAAMCAANtAAM2BA',
            #     video_file_id='BAACAgIAAxkBAAOAaOVbMgKWXI05DAABDEFp3UrDgrz1AAJ0jQACcjwpSzHyHYcerVVbNgQ',
            #     reply_markup=keyboard
            # ),
            # InlineQueryResultPhoto(
            #     id=str(uuid4()),
            #     # mime_type="image/jpeg",
            #     title="Title",
            #     caption="Caption",
            #     description="Description",
            #     photo_url='https://fastly.picsum.photos/id/31/3264/4912.jpg?hmac=lfmmWE3h_aXmRwDDZ7pZb6p0Foq6u86k_PpaFMnq0r8',
            #     thumbnail_url='https://fastly.picsum.photos/id/31/3264/4912.jpg?hmac=lfmmWE3h_aXmRwDDZ7pZb6p0Foq6u86k_PpaFMnq0r8',
            #     reply_markup=keyboard
            # ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Отправить видео",
                input_message_content=InputTextMessageContent("Загружаю видео..."),
                # description="Нажми, чтобы получить картинку",
                reply_markup=keyboard
            )
        )
    else:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Ссылка не поддерживается",
                input_message_content=InputTextMessageContent("Ссылка не поддерживается"),
                description="Введите корректную ссылку на YT Shorts, Reels или TikTok",
            )
        )

    await context.bot.answer_inline_query(update.inline_query.id, results)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file_id = photo.file_id
    print("Photo file_id:", file_id)
    
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.video[-1]
    file_id = photo.file_id
    print("Video file_id:", file_id)

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def resolve_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    
    # app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), personal_request))

    app.add_handler(InlineQueryHandler(inline_request))
    app.add_handler(ChosenInlineResultHandler(chosen_inline_callback))

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    return app
