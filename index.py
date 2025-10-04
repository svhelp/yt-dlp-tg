import os

from uuid import uuid4
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, filters, MessageHandler, InlineQueryHandler, ContextTypes, CommandHandler

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_API_KEY")

app = FastAPI()

class TelegramWebhook(BaseModel):
    '''
    Telegram Webhook Model using Pydantic for request body validation
    '''
    update_id: int
    message: Optional[dict] = None
    edited_message: Optional[dict] = None
    channel_post: Optional[dict] = None
    edited_channel_post: Optional[dict] = None
    inline_query: Optional[dict] = None
    chosen_inline_result: Optional[dict] = None
    callback_query: Optional[dict] = None
    shipping_query: Optional[dict] = None
    pre_checkout_query: Optional[dict] = None
    poll: Optional[dict] = None
    poll_answer: Optional[dict] = None

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)

def register_handlers(dispatcher: Application):
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    dispatcher.add_handler(echo_handler)

    inline_caps_handler = InlineQueryHandler(inline_caps)
    dispatcher.add_handler(inline_caps_handler)
    
    # Other handlers
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    dispatcher.add_handler(unknown_handler)

@app.post("/webhook")
async def webhook(webhook_data: TelegramWebhook):
    app = Application.builder().token(TOKEN).build()

    await app.initialize()

    update = Update.de_json(webhook_data.__dict__, app.bot) # convert the Telegram Webhook class to dictionary using __dict__ dunder method

    register_handlers(app)

    # handle webhook request
    await app.process_update(update)

    return {"message": "ok"}

@app.get("/")
async def index():
    return {"message": "Hello World"}
