import asyncio
import logging
import os
import sessions
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import settings            # loads config.cfg (exits with a message if missing)
import notify
import registration
from aprs_client import client as aprs
from commands import dispatch
import time


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(),
              logging.FileHandler(os.path.join(settings.BASE_DIR, "gateway.log"), encoding="utf-8")],
)
logging.getLogger("httpx").setLevel(logging.WARNING)   # hide Telegram polling spam
log = logging.getLogger("main")

REPLY_LIMIT = 5
REPLY_WINDOW = 300
_recent = {}

def too_many_replies(chat: str) -> bool:
    now = time.time()
    times = [t for t in _recent.get(chat, []) if now - t < REPLY_WINDOW]
    times.append(now)
    _recent[chat] = times
    return len(times) > REPLY_LIMIT



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    message = update.message.text
    chat_id = update.message.chat_id
    chat = f"tg:{chat_id}"
    log.info("TG %s (%s): %s", update.message.from_user.username, chat_id, message)

    if not message.startswith("/"):
        s = sessions.active_session(chat)
        if s:
            if len(message) > 125:
                await update.message.reply_text("Message too long for APRS (max 125 characters). Your message was not sent. (sorry!)")
                return
            if too_many_replies(chat):
                await update.message.reply_text(f"Slow down, max {REPLY_LIMIT} replies per {REPLY_WINDOW // 60} minutes over APRS")
                return
            await asyncio.to_thread(aprs.send_message, s["owner"], f"{s['alias']}: {message}")
            await update.message.reply_text(f"Sent to {s['owner']} over APRS")
            return

        if not registration.calls_for_chat(chat):
            await update.message.reply_text(f"No active session. The operator needs to message you first")
            return
    response = dispatch(chat, message)
    await update.message.reply_text(response)


async def on_startup(app: Application):
    loop = asyncio.get_running_loop()

    def send_tg(tg_chat_id: str, text: str):
        # Called from the APRS thread: hand the send over to Telegram's event loop
        chat = int(tg_chat_id.removeprefix("tg:"))
        asyncio.run_coroutine_threadsafe(app.bot.send_message(chat_id=chat, text=text), loop)

    notify.set_telegram_sender(send_tg)
    aprs.start()


def main():
    registration.init_db()
    app = Application.builder().token(settings.TOKEN).post_init(on_startup).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    log.info("Gateway %s starting", settings.GATEWAY)
    app.run_polling()


if __name__ == "__main__":
    main()
