import os
import src.config

from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, InputMediaVideo, InlineQueryResultCachedVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, filters, MessageHandler, InlineQueryHandler, ChosenInlineResultHandler, ContextTypes, CommandHandler

from src.core.utils import verify_supported_url
from src.db.repository import get_or_create_user, create_request, update_request, get_today_requests_count
from src.core.downloader import process_video

from src.db.schema import RequestStatus, RequestType

HOST = os.getenv("HOST")
TOKEN = os.getenv("TELEGRAM_API_KEY")
MAX_REQUESTS = 100

async def personal_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type

    if chat_type != 'private':
        return
    
    link = update.message.text.strip()
    sender = update.effective_user

    if not verify_supported_url(link):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ссылка не поддерживается")
        return

    user = get_or_create_user(sender.id, sender.full_name, sender.username)

    if user.is_banned:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Вы заблокированы")
        return
    
    requests_today = get_today_requests_count(user.id)

    if requests_today >= MAX_REQUESTS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Количество запросов на день исчерпано, попробуйте завтра")
        return
    
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="Processing...")

    request = create_request(user.id, RequestType.PERSONAL, link, msg.message_id, update.effective_chat.id)

    download_result = await process_video(request, link)
    actual_result = download_result.get("result")

    if not actual_result:
        await msg.edit_text("Произошла ошибка")

        update_request(request.id, RequestStatus.FAILED, download_result.get("error_message"), download_result.get("error_details"))

    await msg.reply_video(
        video=open(actual_result.get('path'), 'rb'),
        caption=f"by {actual_result.get("author")}"
    )

    update_request(request.id, RequestStatus.SUCCESSFUL)

async def chosen_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_option = update.chosen_inline_result
    inline_message_id = chosen_option.inline_message_id

    if not inline_message_id:
        return
    
    link = chosen_option.query.strip()
    sender = chosen_option.from_user

    if not verify_supported_url(link):
        await context.bot.edit_message_text(inline_message_id=inline_message_id, text="Ссылка не поддерживается")
        return
    
    user = get_or_create_user(sender.id, sender.full_name, sender.username)

    if user.is_banned:
        await context.bot.edit_message_text(inline_message_id=inline_message_id, text="Вы заблокированы")
        return  
    
    requests_today = get_today_requests_count(user.id)

    if requests_today >= MAX_REQUESTS:
        await context.bot.edit_message_text(inline_message_id=inline_message_id, text="Количество запросов на день исчерпано, попробуйте завтра")
        return
    
    request = create_request(user.id, RequestType.INLINE, link, inline_message_id)
    
    download_result = await process_video(request, link)
    actual_result = download_result.get("result")

    if not actual_result:
        await context.bot.edit_message_text(
            inline_message_id=inline_message_id,
            text="Произошла ошибка"
        )

        update_request(request.id, RequestStatus.FAILED, download_result.get("error_message"), download_result.get("error_details"))

    await context.bot.edit_message_media(
        inline_message_id=inline_message_id,
        media=InputMediaVideo(
            media=f'{HOST}/static/{os.path.basename(actual_result.get("path"))}',
            caption=f"by {actual_result.get("author")}"
        )
    )

    update_request(request.id, RequestStatus.SUCCESSFUL)

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
