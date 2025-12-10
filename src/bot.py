import os
import src.config

from uuid import uuid4

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InputMediaVideo, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, filters, MessageHandler, InlineQueryHandler, CallbackQueryHandler, ChosenInlineResultHandler, ContextTypes, CommandHandler

from src.core.utils import verify_supported_url, check_for_a_disabled_url
from src.core.limits import ensure_user_limits
from src.db.repository import get_or_create_user, create_request, set_request_successful, set_request_error
from src.core.downloader import process_video
from src.loc.messages import MESSAGES

from src.db.schema import RequestStatus, RequestType

HOST = os.getenv("HOST")
TOKEN = os.getenv("TELEGRAM_API_KEY")

async def personal_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type

    if chat_type != 'private':
        return
    
    link = update.message.text.strip()
    sender = update.effective_user

    if not verify_supported_url(link):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=MESSAGES["error.unsupported_link"])
        return
    
    if check_for_a_disabled_url(link):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=MESSAGES["error.temp_disabled_service"])
        return

    user = get_or_create_user(sender.id, sender.full_name, sender.username)

    if user.is_banned:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=MESSAGES["error.banned_user"])
        return
    
    request_available = ensure_user_limits(user)

    if not request_available:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=MESSAGES["error.limit_reached"])
        return
    
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=MESSAGES["status.processing"])

    request = create_request(user.id, RequestType.PERSONAL, link, msg.message_id, update.effective_chat.id)
    request_id = request.id

    download_result = await process_video(request, link)
    actual_result = download_result.get("result")

    if not actual_result:
        await msg.edit_text(MESSAGES["error.unknown"])

        set_request_error(request_id, download_result.get("error_message"), download_result.get("error_details"))

        return

    await msg.reply_video(
        video=open(actual_result.get('path'), 'rb'),
        #caption=f"by <a href='{link}'>{actual_result.get('author')}</a>",
        caption=f"by {actual_result.get('author')}",
        parse_mode="HTML"
    )

    set_request_successful(request_id)

async def chosen_inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_option = update.chosen_inline_result
    inline_message_id = chosen_option.inline_message_id

    if not inline_message_id:
        return
    
    link = chosen_option.query.strip()
    sender = chosen_option.from_user

    if not verify_supported_url(link):
        await context.bot.edit_message_text(inline_message_id=inline_message_id, text=MESSAGES["error.unsupported_link"])
        return
    
    if check_for_a_disabled_url(link):
        await context.bot.edit_message_text(inline_message_id=inline_message_id, text=MESSAGES["error.temp_disabled_service"])
        return
    
    user = get_or_create_user(sender.id, sender.full_name, sender.username)

    if user.is_banned:
        await context.bot.edit_message_text(inline_message_id=inline_message_id, text=MESSAGES["error.banned_user"])
        return  
    
    request_available = ensure_user_limits(user)

    if not request_available:
        await context.bot.edit_message_text(inline_message_id=inline_message_id, text=MESSAGES["error.limit_reached"])
        return
    
    request = create_request(user.id, RequestType.INLINE, link, inline_message_id)
    request_id = request.id
    
    download_result = await process_video(request, link)
    actual_result = download_result.get("result")

    if not actual_result:
        await context.bot.edit_message_text(
            inline_message_id=inline_message_id,
            text=MESSAGES["error.unknown"]
        )

        set_request_error(request_id, download_result.get("error_message"), download_result.get("error_details"))
        
        return
    
    await context.bot.edit_message_media(
        inline_message_id=inline_message_id,
        media=InputMediaVideo(
            media=f"{HOST}/static/{os.path.basename(actual_result.get('path'))}",
            #caption=f"by <a href='{link}'>{actual_result.get('author')}</a>",
            caption=f"by {actual_result.get('author')}",
            parse_mode="HTML"
        )
    )

    set_request_successful(request_id)

def prepare_inline_results(link: str):
    results = []

    if not verify_supported_url(link):
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=MESSAGES["error.unsupported_link"],
                input_message_content=InputTextMessageContent(MESSAGES["error.unsupported_link"]),
                description=MESSAGES["error.unsupported_link.hint"],
            )
        )

        return results
    
    if check_for_a_disabled_url(link):
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=MESSAGES["error.unsupported_link"],
                input_message_content=InputTextMessageContent(MESSAGES["error.temp_disabled_service"]),
                description=MESSAGES["error.temp_disabled_service"],
            )
        )

        return results
    
    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=MESSAGES["inline.process_video"],
            input_message_content=InputTextMessageContent(MESSAGES["status.processing"]),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(MESSAGES["keyboard.processing"], callback_data="empty_button")]])
        )
    )

    return results

async def inline_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    if not query:
        return
    
    link = query.strip()
    inline_options = prepare_inline_results(link)

    await context.bot.answer_inline_query(update.inline_query.id, inline_options)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    await query.answer(text = MESSAGES["keyboard.clicked"])

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
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(ChosenInlineResultHandler(chosen_inline_callback))

    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    return app
