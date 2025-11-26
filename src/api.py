import src.config

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from src.bot import resolve_bot

from telegram import Update

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

@app.post("/webhook")
async def webhook(webhook_data: TelegramWebhook):
    bot = resolve_bot()

    await bot.initialize()

    update = Update.de_json(webhook_data.__dict__, bot.bot) # convert the Telegram Webhook class to dictionary using __dict__ dunder method

    # handle webhook request
    await bot.process_update(update)

    return {"message": "ok"}

@app.get("/")
async def index():
    return {"message": "Hello World"}
