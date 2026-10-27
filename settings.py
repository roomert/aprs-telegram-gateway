"""Loads config.cfg once so every module can share the same settings."""
import configparser
import os
import sys

# Folder holding the exe (when built) or this script (when run with python)
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.cfg")

if not os.path.isfile(CONFIG_PATH):
    sys.exit(f"config.cfg not found in {BASE_DIR}. Copy config.example.cfg to config.cfg and fill it in.")

cfg = configparser.ConfigParser()
cfg.read(CONFIG_PATH, encoding="utf-8")

# --- Telegram ---
TOKEN = cfg.get("telegram", "token", fallback="")

# --- APRS ---
APRS_ENABLED  = cfg.getboolean("aprs", "enabled", fallback=True)
APRS_CALLSIGN = cfg.get("aprs", "callsign", fallback="N0CALL").upper()   # your login callsign
APRS_PASSCODE = cfg.get("aprs", "passcode", fallback="-1")
GATEWAY       = cfg.get("aprs", "gateway_name", fallback="ZLTG").upper()  # name people message
APRS_SERVER   = cfg.get("aprs", "server", fallback="127.0.0.1")
APRS_PORT     = cfg.getint("aprs", "port", fallback=14580)
BEACON_SYMBOL_TABLE = cfg.get("aprs", "beacon_symbol_table", fallback="/")
BEACON_SYMBOL = cfg.get("aprs", "beacon_symbol", fallback="&")
# Safety switch: refuses to connect anywhere except this computer unless set to yes
ALLOW_LIVE    = cfg.getboolean("aprs", "allow_live", fallback=False)
BEACON_LAT     = cfg.get("aprs", "beacon_lat", fallback="")
BEACON_LON     = cfg.get("aprs", "beacon_lon", fallback="")
BEACON_COMMENT = cfg.get("aprs", "beacon_comment", fallback="APRS-Telegram Gateway")
BEACON_MINUTES = cfg.getint("aprs", "beacon_minutes", fallback=120)

# --- Registration ---
DB_PATH        = os.path.join(BASE_DIR, cfg.get("registration", "database", fallback="registrations.db"))
CODE_MINUTES   = cfg.getint("registration", "code_minutes", fallback=5)
BOT_USERNAME   = cfg.get("registration", "bot_username", fallback="ZL2VOID_aprs_bot")
SESSION_HOURS  = cfg.getint("registration", "session_hours", fallback=12)
