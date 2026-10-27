"""APRS-IS side of the gateway.

Connects to an APRS-IS server, receives messages addressed to the gateway,
acks them, skips duplicates, runs them through dispatch(), and sends replies
with message numbers and retries until the radio acks them.

SAFETY: unless allow_live = yes in config.cfg, it will only connect to this
computer (127.0.0.1 / localhost), e.g. tools/fake_aprsis.py.
"""
import ipaddress
import logging
import socket
import threading
import time

import aprslib

import settings
from commands import dispatch

log = logging.getLogger("aprs")

TOCALL = "APZTGB"          # APZxxx = experimental software
MAX_LEN = 67               # APRS message text limit
MAX_CHUNKS = 2             # never send more than this many parts per reply
RETRY_DELAYS = [30, 60, 120]   # seconds between retries (so 4 sends max)
MIN_SEND_GAP = 1.5         # seconds between any two packets we send
INBOUND_LIMIT = (8, 600)   # max 8 commands per callsign per 10 min, then ignore

# ---- duplicate tracking ------------------------------------------------
SEEN = {}   # (from_call, msgno) -> time seen

def is_duplicate(from_call, msgno):
    now = time.time()
    for k, t in list(SEEN.items()):     # forget entries older than 30 min
        if now - t > 1800:
            del SEEN[k]
    key = (from_call, msgno)
    if key in SEEN:
        return True
    SEEN[key] = now
    return False


# ---- inbound rate limit ------------------------------------------------
_inbound = {}   # call -> [timestamps]

def _rate_limited(call):
    limit, window = INBOUND_LIMIT
    now = time.time()
    times = [t for t in _inbound.get(call, []) if now - t < window]
    times.append(now)
    _inbound[call] = times
    return len(times) > limit


def _is_local(host):
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class APRSClient:
    def __init__(self):
        self.sock = None
        self.send_lock = threading.Lock()
        self.last_send = 0.0
        self.msgno = int(time.time()) % 900 + 1     # start somewhere random-ish
        self.outbox = {}   # (dest, msgno) -> {"packet", "tries", "next"}
        self.out_lock = threading.Lock()
        self.running = False

    def _beacon_loop(self):
        if not settings.BEACON_LAT or not settings.BEACON_LON:
            log.info("No beacon position set, not beaconing")
            return
        time.sleep(30)
        while self.running:
            if self.sock is not None:
                packet = f"{settings.GATEWAY}>{TOCALL},TCPIP*:!{settings.BEACON_LAT}{settings.BEACON_SYMBOL_TABLE}{settings.BEACON_LON}{settings.BEACON_SYMBOL}{settings.BEACON_COMMENT}"
                self._send(packet)
            time.sleep(settings.BEACON_MINUTES * 60)

    # ---------- public ----------
    def start(self):
        """Start in background threads. Returns immediately."""
        if not settings.APRS_ENABLED:
            log.info("APRS disabled in config.cfg")
            return
        if not _is_local(settings.APRS_SERVER) and not settings.ALLOW_LIVE:
            log.error("Refusing to connect to %s: set allow_live = yes in config.cfg "
                      "when you're ready for the real APRS-IS network.", settings.APRS_SERVER)
            return
        self.running = True
        threading.Thread(target=self._run, name="aprs-rx", daemon=True).start()
        threading.Thread(target=self._retry_loop, name="aprs-retry", daemon=True).start()
        threading.Thread(target=self._beacon_loop, name="aprs-beacon", daemon=True).start()

    def send_message(self, dest: str, text: str):
        """Queue a message to a station. Long text is split, max MAX_CHUNKS parts."""
        dest = dest.upper()
        text = " ".join(text.split())      # APRS messages are single-line
        chunks = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)][:MAX_CHUNKS] or [""]
        for chunk in chunks:
            self.msgno = self.msgno % 99999 + 1
            packet = f"{settings.GATEWAY}>{TOCALL},TCPIP*::{dest:<9}:{chunk}{{{self.msgno}"
            with self.out_lock:
                self.outbox[(dest, str(self.msgno))] = {
                    "packet": packet, "tries": 1, "next": time.time() + RETRY_DELAYS[0]}
            self._send(packet)

    # ---------- internals ----------
    def _send(self, line: str):
        with self.send_lock:
            gap = time.time() - self.last_send
            if gap < MIN_SEND_GAP:
                time.sleep(MIN_SEND_GAP - gap)
            if self.sock is None:
                log.warning("Not connected, dropped: %s", line)
                return
            try:
                self.sock.sendall((line + "\r\n").encode("utf-8", "replace"))
                self.last_send = time.time()
                log.info("TX %s", line)
            except OSError as e:
                log.warning("Send failed (%s): %s", e, line)

    def _send_ack(self, dest, msgno):
        self._send(f"{settings.GATEWAY}>{TOCALL},TCPIP*::{dest:<9}:ack{msgno}")

    def _connect(self):
        log.info("Connecting to %s:%s", settings.APRS_SERVER, settings.APRS_PORT)
        s = socket.create_connection((settings.APRS_SERVER, settings.APRS_PORT), timeout=30)
        s.settimeout(120)   # servers send a keepalive every ~20 s
        login = (f"user {settings.APRS_CALLSIGN} pass {settings.APRS_PASSCODE} "
                 f"vers ZL-TG-Gateway 0.1 filter g/{settings.GATEWAY}\r\n")
        s.sendall(login.encode())
        self.sock = s

    def _run(self):
        delay = 5
        while self.running:
            try:
                self._connect()
                delay = 5
                buf = b""
                while self.running:
                    data = self.sock.recv(4096)
                    if not data:
                        raise ConnectionError("server closed the connection")
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        self._handle_line(line.decode("utf-8", "replace").strip())
            except Exception as e:
                log.warning("APRS-IS connection lost: %s. Reconnecting in %ss", e, delay)
            finally:
                if self.sock:
                    try:
                        self.sock.close()
                    except OSError:
                        pass
                self.sock = None
            time.sleep(delay)
            delay = min(delay * 2, 300)   # back off up to 5 min

    def _handle_line(self, line: str):
        if not line:
            return
        if line.startswith("#"):
            log.info("Server: %s", line)
            return
        try:
            pkt = aprslib.parse(line)
        except Exception:
            return                                   # not something we care about
        if pkt.get("format") != "message" or pkt.get("addresse", "").upper() != settings.GATEWAY:
            return

        sender = pkt["from"].upper()
        if sender == settings.GATEWAY:
            return                                   # never talk to ourselves

        # An ack/rej for something we sent: stop retrying it
        if pkt.get("response") in ("ack", "rej"):
            with self.out_lock:
                if self.outbox.pop((sender, str(pkt.get("msgNo"))), None):
                    log.info("Got %s %s from %s", pkt["response"], pkt.get("msgNo"), sender)
            return

        text = pkt.get("message_text", "")
        msgno = pkt.get("msgNo")
        log.info("RX %s: %s (msg %s)", sender, text, msgno)

        if msgno:
            self._send_ack(sender, msgno)            # ack every copy, even duplicates
            if is_duplicate(sender, msgno):
                log.info("Duplicate %s from %s, skipped", msgno, sender)
                return

        if _rate_limited(sender):
            log.warning("Rate limit hit for %s, ignoring: %s", sender, text)
            return
        
        rf_heard = any(p in ("qAR", "qAr", "qAo") for p in pkt.get("path", []))

        if text.strip().upper().startswith("VERIFY") and not rf_heard:
            log.warning("VERIFY from %s not heard on RF (path %s), refused",
                        sender, pkt.get("path"))
            self.send_message(sender, "Packet not received through RF")
            return
        
        reply = dispatch(sender, text)
        if reply:
            self.send_message(sender, reply)

    def _retry_loop(self):
        while self.running:
            time.sleep(1)
            now = time.time()
            due = []
            with self.out_lock:
                for key, item in list(self.outbox.items()):
                    if item["next"] > now:
                        continue
                    if item["tries"] > len(RETRY_DELAYS):
                        log.warning("No ack from %s for msg %s, giving up", *key)
                        del self.outbox[key]
                        continue
                    item["next"] = now + RETRY_DELAYS[min(item["tries"], len(RETRY_DELAYS) - 1)]
                    item["tries"] += 1
                    due.append(item["packet"])
            for packet in due:
                self._send(packet)


client = APRSClient()
