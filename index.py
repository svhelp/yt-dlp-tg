import os

from uuid import uuid4
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from telegram import Update, Bot
from telegram.ext import Application, filters, MessageHandler, InlineQueryHandler, InlineQueryResultArticle, InputTextMessageContent, ContextTypes, CommandHandler

TOKEN = os.environ.get("TELEGRAM_API_KEY")

app = FastAPI()

class TelegramWebhook(BaseModel):
    '''
    Telegram Webhook Model using Pydantic for request body validation
    '''
    update_id: int
    message: Optional[dict]
    edited_message: Optional[dict]
    channel_post: Optional[dict]
    edited_channel_post: Optional[dict]
    inline_query: Optional[dict]
    chosen_inline_result: Optional[dict]
    callback_query: Optional[dict]
    shipping_query: Optional[dict]
    pre_checkout_query: Optional[dict]
    poll: Optional[dict]
    poll_answer: Optional[dict]

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
def webhook(webhook_data: TelegramWebhook):
    app = Application.builder().token(TOKEN).build()
    update = Update.de_json(webhook_data.__dict__, app.bot) # convert the Telegram Webhook class to dictionary using __dict__ dunder method

    register_handlers(app)

    # handle webhook request
    app.process_update(update)

    return {"message": "ok"}

@app.get("/")
def index():
    return {"message": "Hello World"}