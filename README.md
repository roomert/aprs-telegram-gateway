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

All operators are stored on an internal database file so that it can keep track of what operators are registered, as well as their contacts and session time info.

This program aims to bring the same functionality of the APRS SMS gateway (formerly SMSGTE), but it being completely free and the only overhead cost is your own internet connection and power bill (bonus points if you're off-grid, I will be jealous though).

**ISSUES**
If you are having any issues with installation I am more than happy to help, flick me a message on Telegram or Discord and I aim to respond as soon as I can.
For bugs, feel free to make a bug report and I will try and get them fixed ASAP (or as fast as my day job will allow me to lmao x3)

Anywayyy, that's pretty much it tbh, 73's ZL2VOID ^w^
