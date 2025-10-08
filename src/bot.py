import os
import random
import string
import yt_dlp
import src.config

from uuid import uuid4

from urllib.parse import urlparse

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, InputMediaVideo, InlineQueryResultCachedVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, filters, MessageHandler, InlineQueryHandler, ChosenInlineResultHandler, ContextTypes, CommandHandler

from src.db.engine import engine
from src.db.schema import User, File, Request, RequestStatus, RequestType
from sqlalchemy.orm import Session

TOKEN = os.getenv("TELEGRAM_API_KEY")
MAX_FILE_SIZE = 45 * 1024 * 1024

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def verify_supported_url(url: str) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        social_domains = {
            "youtube.com",
            "youtu.be",
            "instagram.com",
            "tiktok.com",
        }

        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in social_domains)

    except Exception:
        return False

def too_large_file(info, *, incomplete):
    size = info.get('filesize')
    if size and size > MAX_FILE_SIZE:
        return 'The video is too big.'

async def personal_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type

    if chat_type != 'private':
        return
    
    link = update.message.text.strip()

    if not verify_supported_url(link):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid URL")
        return
    
    sender = update.effective_user
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing...")

    with Session(engine) as session:
        user = session.get(User, sender.id)
        if not user:
            user = User(
                id=sender.id,
                name=sender.full_name,
                user_name=sender.username
            )
            session.add(user)

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

    # hash_name = generate_random_string(16)
    ydl_opts = {
        'match_filter': too_large_file,
        # 'outtmpl': f'{hash_name}.%(ext)s'
    }

    # with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #     info = ydl.extract_info(link, download=True)
    #     await msg.reply_video(open(info['requested_downloads'][0]['filepath'], 'rb'))
    
    # try:
    #     video = await download_video_to_memory(link)
    #     await msg.reply_video(video)
    # except Exception as e:
    #     await msg.edit_text("Error during downloading.")

async def chosen_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_option = update.chosen_inline_result
    inline_message_id = chosen_option.inline_message_id

    if not inline_message_id:
        return
    
    link = chosen_option.query.strip()
    sender = chosen_option.from_user

    with Session(engine) as session:
        user = session.get(User, sender.id)
        if not user:
            user = User(
                id=sender.id,
                name=sender.full_name,
                user_name=sender.username
            )
            session.add(user)

        request = Request(
            message_id = inline_message_id,
            status = RequestStatus.PENDING,
            type = RequestType.INLINE,
            link = link,
            user_account = user,
        )

        session.add(request)
        session.commit()

    # await context.bot.edit_message_media(
    #     inline_message_id=inline_message_id,
    #     media=InputMediaVideo(media='https://test-videos.co.uk/vids/bigbuckbunny/mp4/av1/360/Big_Buck_Bunny_360_10s_1MB.mp4', caption="✅ Готово!")
    # )

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
    
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), personal_request))

    app.add_handler(InlineQueryHandler(inline_request))
    app.add_handler(ChosenInlineResultHandler(chosen_inline_callback))

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    return app
