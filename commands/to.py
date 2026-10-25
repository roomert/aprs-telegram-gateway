import notify
import registration
from commands.reg import base_call, NZ_CALL




def handle(sender: str, args: str) -> str:
    target, _, msg = args.partition(" ")
    msg = msg.strip()
    target = base_call(target)

    if not target or not msg:
        return "Usage: /TO <CALL> <msg>"

    if not NZ_CALL.match(target):
        if not sender.startswith("tg:"):
            return f"'{target}' not a callsign. Use @{target.lower()}"
        return f"'{target}' doesn't look like an NZ amateur callsign."

    chat = registration.chat_for_call(target)

    if not chat:
        return f"{target} is not linked to Telegram. Use /reg on Telegram"

    if sender.startswith("tg:"):
        calls = registration.calls_for_chat(sender)
        if not calls:
            return "Link your callsign first with /reg on Telegram"
        from_label = calls[0]
    else:
        from_label = base_call(sender)

    notify.telegram(chat, f"📻 from {from_label}:\n{msg}")
    return f"Sent to {target}."