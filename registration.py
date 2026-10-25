"""SQLite storage for callsign <-> Telegram links.

Each function opens its own connection, so it is safe to call from both
the Telegram side and the APRS thread at the same time.
"""
import sqlite3
import time
import secrets
import settings


def _connect():
    conn = sqlite3.connect(settings.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                callsign    TEXT PRIMARY KEY,   -- base call, no SSID (ZL2VOID)
                tg_chat_id  TEXT NOT NULL,      -- e.g. 'tg:123456789'
                verified_at INTEGER NOT NULL    -- unix time
            )
        """)
        conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    owner_call  TEXT NOT NULL,      -- base call, no SSID (ZL2VOID)
                    alias       TEXT NOT NULL,      -- base call, no SSID (ZL2VOID)
                    tg_chat_id  TEXT,               -- e.g. 'tg:123456789'
                    invite_code TEXT UNIQUE,        -- random code for accepting invites
                    PRIMARY KEY(owner_call, alias)
                )
            """)

def add_contact(owner_call: str, alias: str) -> str:
    """Add an alias for a callsign. Returns the alias added."""
    code = secrets.token_urlsafe(8)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO contacts (owner_call, alias, tg_chat_id, invite_code) "
            "VALUES (?, ?, NULL, ?) "
            "ON CONFLICT(owner_call, alias) DO UPDATE SET "
            "tg_chat_id = NULL, invite_code = excluded.invite_code",
            (owner_call.upper(), alias.upper(), code)
        )
    return code

def contact_chat(owner_call: str, alias: str):
    with _connect() as conn:
        row = conn.execute(
            "SELECT tg_chat_id FROM contacts WHERE owner_call = ? AND alias = ?",
            (owner_call.upper(), alias.upper())
        ).fetchone()
        return row["tg_chat_id"] if row else None

def accept_invite(code: str, tg_chat_id: str):
    with _connect() as conn:
        row = conn.execute(
            "SELECT owner_call, alias FROM contacts WHERE invite_code = ?",
            (code,)
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE contacts SET tg_chat_id = ?, invite_code = NULL WHERE invite_code = ?",
            (tg_chat_id, code)
        )
        return (row["owner_call"], row["alias"])

def list_contacts(owner_call: str) -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT alias, tg_chat_id FROM contacts WHERE owner_call = ? ORDER BY alias",
            (owner_call.upper(),)
        ).fetchall()
        return [(r["alias"], r["tg_chat_id"] is not None) for r in rows]

def remove_contact(owner_call: str, alias: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM contacts WHERE owner_call = ? AND alias = ?",
            (owner_call.upper(), alias.upper())
        )
        return cur.rowcount > 0 

def save_link(callsign: str, tg_chat_id: str) -> None:
    """Link (or re-link) a callsign to a Telegram chat."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO links (callsign, tg_chat_id, verified_at) VALUES (?, ?, ?) "
            "ON CONFLICT(callsign) DO UPDATE SET tg_chat_id = excluded.tg_chat_id, "
            "verified_at = excluded.verified_at",
            (callsign.upper(), tg_chat_id, int(time.time())),
        )


def remove_link(callsign: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM links WHERE callsign = ?", (callsign.upper(),))
        return cur.rowcount > 0


def chat_for_call(callsign: str):
    """Telegram chat id linked to a callsign, or None."""
    with _connect() as conn:
        row = conn.execute("SELECT tg_chat_id FROM links WHERE callsign = ?",
                           (callsign.upper(),)).fetchone()
        return row["tg_chat_id"] if row else None


def calls_for_chat(tg_chat_id: str) -> list:
    """All callsigns linked to a Telegram chat."""
    with _connect() as conn:
        rows = conn.execute("SELECT callsign FROM links WHERE tg_chat_id = ? ORDER BY callsign",
                            (tg_chat_id,)).fetchall()
        return [r["callsign"] for r in rows]
