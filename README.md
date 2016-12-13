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
  
/koffing admin [list] [add @user] [remove @user]
  Provides admin administration. List admins, add a new admin, remove an old admin
```

To run koffing bot locally:

1. Install [**discord.py**](https://github.com/Rapptz/discord.py) with the command:
  * `python3 -m pip install -U discord.py`
2. [Invite koffing-bot to your server.] (https://discordapp.com/oauth2/authorize?client_id=256222258647924737&scope=bot)
3. Modify koffing.cfg to contain the following things:
  * Add an entry in `"admin_users"` for any accounts you want. (`AccountName#1234`)
  * Add an entry in `"authorized_channels"` of the form `"server_id": ['channel_name', 'other_channel']` for each channel and server that you want koffing-bot to pay attention to.
  * Add an entry in `"authorized_servers"` for every server listed in `"authorized_channels"` that you want koffing-bot to pay attention to.
2. Launch koffing-bot:
  * `python koffing-client.py`

***At startup koffing-bot will list the server id of each server the acount is a member of.***

To enable voice support:

1. Install [**discord.py**](https://github.com/Rapptz/discord.py) voice support with the command:
  * `python -m pip -U discord.py[voice]`
2. Install [**ffmpeg**](https://ffmpeg.org/download.html) for your OS
3. Place [**ffmpeg**](https://ffmpeg.org/download.html) on your path

To enable or disable specific features, modify the entries in `feature_toggle.cfg`
