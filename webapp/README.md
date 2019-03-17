# Titan - WebApp Portion
The webapp portion handles the frontend (it's what the users see). The webapp highly depends on the discordbot to push websockets data to the database.

# Installation
1. Clone the repo (make sure you have **Python 3.6.8** (or above) installed on your system.)
2. Clone `config.example.py` and rename it to `config.py`. Edit the file to your standards
3. Run the development web via `python run.py` -- Though we suggest to use a better server software (look into gunicorn, nginx, uwsgi, etc)