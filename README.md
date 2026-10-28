### YOU NEED AN AMATEUR CALLSIGN BEFORE YOU CAN USE THIS PROGRAM!! please don't get in trouble x3
APRS Telegram Gateway links the APRS i-Gate servers to a Telegram chatbot and allows users to send messages to each other over the platform so only one party needs radio equipment.

Installation is simple:

- Download the executable for your system to its own folder
- Use either git clone or copy/paste the contents of config.example.cfg to a fresh config.cfg file and place
  the config file next to the executable. The config MUST be named 'config.cfg'
- Put your data in the config as needed, such as bot token and your LAT, LON, callsign, APRS passcode and custom message
      - NOTE: The bot WILL NOT WORK without those fields being filled with the correct information
- If you want the bot to be live on the APRS network, make sure to edit the config so the built in dummy server never runs


**SAFEGUARDS**
My script has a few safeguards to stop flooding the APRS network with traffic, making sure your network doesn't get hit with too many requests.
It also makes sure operators who wish to register their callsign with the bot, actually have their callsign as registration can only be done over RF to an APRS connected i-Gate. 
Sessions only run for 12 hours, if the bot restarts or the timer elapses then the user on Telegram cannot message that operator, and the operator must message the telegram user first.

This script is never meant to be plugged into a repeater, or interact directly over RF, this is an online only tool, where it takes data from one server and throws it back at another.

**PRIVACY**
All operators are stored on an internal database file so that it can keep track of what operators are registered, as well as their contacts and session time info.
This program does not store any message history, the history will be between the person you are talking to on telegram and the bot, not on any hardware.
DO NOT SHARE SENSITIVE INFO OVER THIS BOT, APRS by definition is public which means any packet sent over RF can be intercepted and decoded. Don't say anything you wouldn't say on the sidewalk.

**USAGE**
NOTE: the bot has a 12 hour session timeout which means that any contact that hasn't been closed by the station will be closed automatically by the server
to ensure that abuse of the RF channel by an unlicensed operator cannot happen.

Before you can use the bot you must first register your callsign to the bot in the first place and add a contact after verification:

1. On Telegram with the bot, do /reg <callsign>, for me that'd be /reg ZL2VOID
2. You need to send the verification code over RF, on your radio do the following:
   - Tune to your local APRS repeater/i-Gate
   - Make sure the path of the packet is set to WIDE1-1,WIDE2-1 to make sure it gets forwarded from the digipeater
   - send via APRSDroid or other equivalent **CALLSIGN** ZL2AXB-TG **MESSAGE** VERIFY <4-digit-code>
   - the i-Gate should respond with an OK message
3. Add a contact via Telegram, /contact add @<alias_name
   - Send the link the bot generates to the person you want to contact
   - The person should hit the START button on Telegram to initiate a chat with the bot
   - You both should receive a message saying the contact was accepted
   - you MUST do this for each contact as each invite link is different
4. After they accept the invite you can send via APRS on your radio: **CALLSIGN** ZL2AXB-TG **MESSAGE** @<alias> Hello from RF
   - They will receive a message from the bot with your message and they will be able to respond to you in the same fashion by simply just typing to the bot
     and it will automatically forward each message to you over RF
5. Want to end the contact early? Say less, via your radio send: **CALLSIGN** ZL2AXB-TG **MESSAGE** END @<alias> to cose the session without waiting for the 12 hour session timer to expire

**GATEWAY to RF**
You can also use my bot to message a station from Telegram too, if you are added as multiple peoples callsign contacts.
All you need to do is while an active session is happening, simply use /TO <callsign> {message} and the bot will forward your text to that person and initiate a contact log

This program aims to bring the same functionality of the APRS SMS gateway (formerly SMSGTE) back to New Zealand, but it being completely free and the only 
overhead cost is your own internet connection and power bill (bonus points if you're off-grid, I will be jealous though).

**ISSUES**
If you are having any issues with installation I am more than happy to help, flick me a message on Telegram or Discord and I aim to respond as soon as I can.
For bugs, feel free to make a bug report and I will try and get them fixed ASAP (or as fast as my day job will allow me to lmao x3)

**FUTURE PLANS**
At the moment I have no future plans for this program, if testing is successful within NZ I might lift the restriction on my end and allow global users to interface with my bot.
I also might be looking into setting up the i-Gate at some repeater sites within NZ if I am allowed to but that's not for wayyy into the future.

Anywayyy, that's pretty much it tbh, 73's ZL2VOID ^w^
