# Titan
There was a time when Discord doesn't support embedding the chat on a webpage. But with Titan, you can! It is as simple as 1, 2, 3!
1. Invite the bot to your server (You must have "Manage Server" permissions)
2. Configure the embed to your liking (toggling guest users, etc)
3. Copy the iframe code and paste the line in your webpage!

# Features
- Guest users (a quick way to invite users who do not have a Discord account)
- Moderation Features (Kick & ban users by IP addresses, toggling guest users)
- Discord OAuth support. (Allows those who have a discord account to access the embed)
- Responsive material design! (Thanks materializecss!!)
- All features are done via REST apis (respects discord's rate limiting). Although do not provide consistant connection to Discord, they are easier to maintain and does not often "disconnects" from Discord servers.

# Installation
Would you like to run your own copy of Titan Embeds?
1. Clone the repo
2. Install the pip requirements `pip install -r requirements.txt`
3. Clone `config.example.py` and rename it to `config.py`. Edit the file to your standards
4. Run the development web via `python run.py` -- Though we suggest to use a better server software (look into gunicorn, nginx, etc)


## Join us!
Come and talk with us at our very own [discord server](https://discord.gg/z4pdtuV)! We offer support too!