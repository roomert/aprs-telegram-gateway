"""Registration: /reg on Telegram -> VERIFY over APRS -> linked in the database."""
import re
import secrets
import time
import sessions
import notify
import registration
import settings

# callsign -> (code, tg_chat_id, expires_at, attempts). In memory on purpose:
# codes only last a few minutes, so losing them on restart is fine.
PENDING = {}
MAX_ATTEMPTS = 3

# NZ amateur calls: ZL or ZM, a digit, then 1-3 letters (ZL2VOID style 4-letter suffixes too)
NZ_CALL = re.compile(r"^Z[LM]\d[A-Z]{1,4}$")


def base_call(call: str) -> str:
    return call.strip().upper().split("-")[0]


def _purge_expired():
    now = time.time()
    for call in [c for c, e in PENDING.items() if e[2] < now]:
        del PENDING[call]


def handle(sender: str, args: str) -> str:
    """/reg ZL2XYZ  (Telegram only)"""
    if not sender.startswith("tg:"):
        return "Use /reg on Telegram, then send VERIFY here"
    if not args:
        return "Usage: /reg <CALLSIGN>  (NZ callsigns only, e.g. /reg ZL2ABC)"

    call = base_call(args.split()[0])
    if not NZ_CALL.match(call):
        return f"'{call}' doesn't look like an NZ amateur callsign."

    owner = registration.chat_for_call(call)
    if owner == sender:
        return f"{call} is already linked to this Telegram account."

    _purge_expired()
    existing = PENDING.get(call)
    if existing and existing[1] == sender:
        code = existing[0]                                   # same person asking again: reuse
    else:
        code = f"{secrets.randbelow(10000):04d}"
        PENDING[call] = (code, sender, time.time() + settings.CODE_MINUTES * 60, 0)

    note = "\n(This will replace its current Telegram link.)" if owner else ""
    return (f"From your radio, send an APRS message to {settings.GATEWAY} containing:\n\n"
            f"VERIFY {code}\n\nfrom {call} (any SSID) within {settings.CODE_MINUTES} minutes.{note}")


def verify(sender: str, args: str) -> str:
    """VERIFY 1234  (APRS only). Replies here go out over RF, so keep them <= 67 chars."""
    if sender.startswith("tg:"):
        return "Send VERIFY from your radio over APRS, not from Telegram."

    call = base_call(sender)
    _purge_expired()
    entry = PENDING.get(call)
    if not entry:
        return "No pending reg or code expired. Use /reg on Telegram"

    code, tg_chat, expires, attempts = entry
    if args.strip() != code:
        attempts += 1
        if attempts >= MAX_ATTEMPTS:
            del PENDING[call]
            notify.telegram(tg_chat, f"Registration for {call} cancelled: too many wrong codes.")
            return "Too many wrong codes. Use /reg on Telegram again"
        PENDING[call] = (code, tg_chat, expires, attempts)
        return f"Wrong code ({MAX_ATTEMPTS - attempts} tries left)"

    del PENDING[call]
    registration.save_link(call, tg_chat)
    notify.telegram(tg_chat, f"✅ {call} verified and linked to this Telegram account.")
    return f"Verified! {call} linked to Telegram"


def unreg(sender: str, args: str) -> str:
    """/unreg ZL2XYZ  (Telegram, only for calls linked to you)"""
    if not sender.startswith("tg:"):
        return "Use /unreg on Telegram"
    mine = registration.calls_for_chat(sender)
    if not args:
        return "Usage: /unreg <CALLSIGN>" + (f"\nLinked: {', '.join(mine)}" if mine else "")
    call = base_call(args.split()[0])
    if call not in mine:
        return f"{call} isn't linked to this Telegram account."
    registration.remove_link(call)
    sessions.close_sessions_for(call)
    return f"{call} unlinked."


def status(sender: str, args: str) -> str:
    """/status  - which callsigns this Telegram account (or APRS call) is linked to"""
    if sender.startswith("tg:"):
        mine = registration.calls_for_chat(sender)
        return ("Linked callsigns: " + ", ".join(mine)) if mine else "No callsigns linked. Use /reg <CALLSIGN>"
    call = base_call(sender)
    return f"{call} is linked to Telegram" if registration.chat_for_call(call) else f"{call} not linked"
