# Titan - DiscordBot Portion
The DiscordBot portion handles the communcation with Discord's websockets to provide real-time updates. The bot's primary role is to push content to the webapp's database to be retrieved at a later time.
It also includes misc. features to moderate guest users, etc. right in your discord server!

# Installation
1. Clone the repo (make sure you have **Python 3.5** installed on your system. This discordbot portion depends on that specifc Python version)
2. Install the pip requirements `pip install -r requirements.txt`
3. Clone `config.example.py` and rename it to `config.py`. Edit the file to your standards
4. Start the bot using `python run.py`
