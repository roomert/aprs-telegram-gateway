import time
import settings

SESSIONS = {}

def open_session(owner_full_call: str, alias: str, contact_chat: str) -> None:
    SESSIONS[contact_chat] = {
        "owner": owner_full_call.upper(),
        "alias": alias.upper(),
        "expires": time.time() + settings.SESSION_HOURS * 3600,
    }

def active_session(contact_chat: str):
    s = SESSIONS.get(contact_chat)
    if s is None:
        return None
    if s["expires"] < time.time():
        del SESSIONS[contact_chat]
        return None
    else:
        return s

def close_session(contact_chat: str) -> bool:
    return SESSIONS.pop(contact_chat, None) is not None

def close_sessions_for(base_owner: str) -> int:
    closed = 0
    for contact_chat, s in list(SESSIONS.items()):
        if s["owner"].split("-")[0] == base_owner:
            del SESSIONS[contact_chat]
            closed += 1
    return closed