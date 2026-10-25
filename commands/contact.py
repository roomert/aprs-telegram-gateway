import registration
import settings
import notify
import sessions
from commands.reg import base_call

def start(sender: str, args: str) -> str:
    """Starts the registration process with the bot"""
    if not args:
        return "Hi! This bot link APRS radio users to Telegram. Send /help"

    result = registration.accept_invite(args.strip(), sender)
    if result is None:
        return "That link is invalid or has already been used"

    owner, alias = result

    owner_chat = registration.chat_for_call(owner)
    if owner_chat:
        notify.telegram(owner_chat, f"@{alias.lower()} accepted your invite ✅")

    return f"You're now a contact of {owner}. They can message you from their radio"


def handle(sender: str, args: str) -> str:
    """/contact add mum | /contact list | / contact remove mum"""
    if not sender.startswith("tg:"):
        return "Manage contacts on Telegram"

    calls = registration.calls_for_chat(sender)
    if not calls:
        return "Link your callsign first with /reg on Telegram"
    owner = calls[0]

    action, _, alias = args.partition(" ")
    action, alias = action.lower(), alias.strip().lower()

    if action == "add":
        if alias == "" or len(alias) > 10 or not alias.isalnum():
            return "Invalid alias. Max 10 numbers/letters only."
        code = registration.add_contact(owner, alias)
        link = f"https://t.me/{settings.BOT_USERNAME}?start={code}"
        return (f"Send this link to {alias}. When they tap it and press Start, "
                f"you can message them with @{alias} from your radio: \n{link}")

    elif action == "list":
        contacts = registration.list_contacts(owner)
        if not contacts:
            return "No contacts yet. Add one with /contact add <alias>"
        lines = [f"@{a} {'✅' if linked else '❌'}" for a, linked in contacts]
        return "Your contacts:\n" + "\n".join(lines)

    elif action == "remove":
        chat = registration.contact_chat(owner, alias)
        if alias == "":
            return "Usage: /contact remove <alias>"
        if registration.remove_contact(owner, alias):
            sessions.close_session(chat)
            notify.telegram(chat, f"You have been removed from {owner}'s contacts list.\n(they submitted the request on their end)")
            return f"Removed @{alias} from your contacts."
        else:
            return f"@{alias} not found in your contacts."
    return "Usage: /contact add <alias> | remove <alias> | list"

def send_to_alias(sender: str, text: str) -> str:
    if sender.startswith("tg:"):
        return "Use @alias from your radio. On Telegram, contacts message you directly"
    alias, _, msg = text.partition(" ")
    alias, msg = alias.strip().upper(), msg.strip()

    if not alias or not msg:
        return "Usage: @alias <msg>"

    chat = registration.contact_chat(base_call(sender), alias)
    if chat is None:
        return f"No contact @{alias.lower()}"

    sessions.open_session(sender, alias, chat)
    notify.telegram(chat, 
                    f"📻 {base_call(sender)}: {msg}\n\n"
                    f"(Reply here to answer. Open for {settings.SESSION_HOURS} hrs)")
    return f"Sent to @{alias.lower()}"

def end(sender: str, args: str) -> str:
    if sender.startswith("tg:"):
        return "Use END @alias from your radio"

    alias = args.strip().lstrip("@").upper()
    if not alias or alias == "":
        return "Usage: END @alias"

    chat = registration.contact_chat(base_call(sender), alias)
    if chat is None:
        return f"No contact @{alias.lower()}"

    if sessions.close_session(chat) is True:
        notify.telegram(chat, f"{base_call(sender)} has ended the conversation.")
        return f"Session with @{alias.lower()} ended"
    else:
        return f"No open session with @{alias.lower()}"