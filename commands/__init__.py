import logging

from . import reg, to, help, contact

log = logging.getLogger("commands")

COMMANDS = {
    "REG":    reg.handle,
    "START":  contact.start,
    "CONTACT": contact.handle,
    "VERIFY": reg.verify,
    "UNREG":  reg.unreg,
    "STATUS": reg.status,
    "TO":     to.handle,
    "HELP":   help.handle,
    "END":    contact.end
}


def dispatch(sender: str, text: str) -> str:
    text = (text or "").strip().lstrip("/")
    if not text:
        return "Empty message. Send HELP"
    if text.startswith("@"):
        return contact.send_to_alias(sender, text[1:])
    cmd, _, args = text.partition(" ")
    cmd = cmd.split("@")[0]          # Telegram groups send /reg@YourBot
    handler = COMMANDS.get(cmd.upper())
    if handler is None:
        return f"Unknown cmd '{cmd[:20]}'. Send HELP"
    try:
        return handler(sender, args.strip())
    except Exception as e:
        log.exception("Command %s from %s failed", cmd, sender)
        return f"Error: {e}"[:67]
