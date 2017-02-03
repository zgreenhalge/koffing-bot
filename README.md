A simple discord bot created using [***discord.py***](https://github.com/Rapptz/discord.py).

Responds emphatically to `koffing` in any channel. 

Commands:
```
/koffing help
  Displays help
  
/koffing features
  Shows a list of completed and planned features
  
/koffing mute
  Mutes koffing bot in the channel where the command was given. Requires user to be on admin list
  
/koffing unmute
  Unmutes koffing bot in the channel where the command was given. Requires user to be on admin list
  
/koffing admin 
  list            -  List all admins of the bot
  add @user       -  Add the tagged user as a bot admin
  remove @user    -  Removes the tagged user as a bot admin
  
  
/vote 
  @user           -   Votes for the tagged user
  history         -   Lists the winners for every recorded vote
  list | leaders  -   Lists the current week's vote leaderboards
```

To run koffing bot locally:

1. Install [**python 3**](https://python.org)
2. Install [**discord.py**](https://github.com/Rapptz/discord.py) with the command:
  * `python3 -m pip install -U discord.py`
3. [Invite koffing-bot to your server.] (https://discordapp.com/oauth2/authorize?client_id=256222258647924737&scope=bot)
4. Modify koffing.cfg to contain the following things:
  * Add an entry in `"admin_users"` for any accounts you want. (`AccountName#1234`)
  * Add an entry in `"authorized_channels"` of the form `"server_id": ['channel_name', 'other_channel']` for each channel and server that you want koffing-bot to pay attention to.
  * Add an entry in `"authorized_servers"` for every server listed in `"authorized_channels"` that you want koffing-bot to pay attention to.
5. Launch koffing-bot:
  * `python koffing-client.py`

***At startup koffing-bot will list the server id of each server the acount is a member of.***

To enable or disable specific features, modify the entries in `feature_toggle.cfg`
