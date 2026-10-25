def handle(sender: str, args: str) -> str:
    if sender.startswith("tg:"):
        return ("Commands:\n"
                "/reg <CALLSIGN> - link your callsign (needs an APRS radio)\n"
                "/unreg <CALLSIGN> - remove a link\n"
                "/status - show your linked callsigns\n"
                "/to <CALLSIGN> <msg> - message a station\n"
                "/help - this list\n"
                "/contact add|list|remove <alias> - manage non-HAM contacts")
    # APRS replies must fit in 67 characters
    return "@alias <msg>, VERIFY <code>, TO <call> <msg>, END @alias, HELP"
