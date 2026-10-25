"""Fake APRS-IS server for testing. Nothing leaves this computer.

Run it in its own terminal:   python tools/fake_aprsis.py
Then start the bot with server = 127.0.0.1 and port = 14580 in config.cfg.

Type lines to pretend to be a radio:
    ZL2VOID-7 VERIFY 1234     -> sends "VERIFY 1234" to the gateway from ZL2VOID-7
    /noack                    -> stop auto-acking gateway messages (to test retries)
    /ack                      -> turn auto-ack back on
    /quit
    /rf      sets fake modem to RF mode
    /net     sets fake modem to TCPIP mode
"""
import socket
import sys
import threading

HOST, PORT = "127.0.0.1", 14580
GATEWAY = sys.argv[1].upper() if len(sys.argv) > 1 else "ZLTG"

state = {"conn": None, "msgno": 0, "autoack": True, "rf": False}
lock = threading.Lock()
RF_ON = "WIDE1-1,qAr,ZL2IGT-10"
RF_OFF = "TCPIP*,qAC,FAKE-T2"

def send(line):
    with lock:
        conn = state["conn"]
    if conn is None:
        print("  (no gateway connected yet)")
        return
    conn.sendall((line + "\r\n").encode())


def handle_client(conn, addr):
    print(f"\n*** Gateway connected from {addr}")
    with lock:
        state["conn"] = conn
    buf = b""
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode(errors="replace").strip()
                if not line:
                    continue
                if line.startswith("user "):
                    call = line.split()[1]
                    print(f"<<< login: {line}")
                    conn.sendall(f"# logresp {call} verified, server FAKE-T2\r\n".encode())
                    continue
                print(f"<<< {line}")
                # Auto-ack messages the gateway sends to a "radio"
                if "::" in line and state["autoack"]:
                    head, body = line.split("::", 1)
                    dest, text = body[:9].strip(), body[10:]
                    if "{" in text and not text.startswith(("ack", "rej")):
                        msgno = text.rsplit("{", 1)[1]
                        print(f"    (auto-ack {msgno} from {dest})")
                        send(f"{dest}>APDR16,TCPIP*,qAC,FAKE-T2::{GATEWAY:<9}:ack{msgno}")
    except OSError:
        pass
    print("*** Gateway disconnected")
    with lock:
        if state["conn"] is conn:
            state["conn"] = None


def server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen()
    while True:
        conn, addr = srv.accept()
        conn.sendall(b"# FAKE APRS-IS test server\r\n")
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


def main():
    threading.Thread(target=server, daemon=True).start()
    print(f"Fake APRS-IS listening on {HOST}:{PORT}, gateway name {GATEWAY}")
    print("Type: <CALLSIGN-SSID> <message>   e.g.  ZL2VOID-7 VERIFY 1234")
    while True:
        try:
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line == "/quit":
            break
        if line in ("/ack", "/noack"):
            state["autoack"] = line == "/ack"
            print(f"  auto-ack {'on' if state['autoack'] else 'off'}")
            continue
        if line in ("/rf", "/net"):
            state["rf"] = line == "/rf"
            print(f"RF state: {'On' if state['rf'] else 'Off'}")
            continue
        call, _, text = line.partition(" ")
        state["msgno"] += 1
        send(f"{call.upper()}>APDR16,{RF_ON if state['rf'] else RF_OFF}::{GATEWAY:<9}:{text}{{{state['msgno']}")
        print(f">>> {call.upper()}: {text} (msg {state['msgno']})")


if __name__ == "__main__":
    main()
