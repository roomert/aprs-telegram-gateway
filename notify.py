"""Lets any module send a Telegram message without importing main.py.

main.py calls set_telegram_sender() at start-up. Safe to call from the APRS thread.
"""
import logging

log = logging.getLogger("notify")
_sender = None


def set_telegram_sender(func):
    global _sender
    _sender = func


def telegram(tg_chat_id: str, text: str) -> None:
    if _sender is None:
        log.info("[no Telegram] would send to %s: %s", tg_chat_id, text)
        return
    _sender(tg_chat_id, text)
