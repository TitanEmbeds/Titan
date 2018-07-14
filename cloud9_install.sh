#!/usr/bin/env bash
echo "[C9Setup] Installing postgresql, redis, and creating titan db table"
cd ~/workspace/
sudo service postgresql start
psql -c "CREATE DATABASE titan WITH ENCODING 'UTF8' TEMPLATE template0"
sudo service redis-server start

echo "[C9Setup] Copying config.py for webapp/discordbot and alembic.ini"
cp ~/workspace/webapp/config.example.py ~/workspace/webapp/config.py
cp ~/workspace/discordbot/config.example.py ~/workspace/discordbot/config.py
cp ~/workspace/webapp/alembic.example.ini ~/workspace/webapp/alembic.ini

echo "[C9Setup] Updating Python3.5"
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.5

echo "[C9Setup] Installing Titan dependencies"
cd ~/workspace/
sudo python3.5 -m pip install --upgrade pip
sudo python3.5 -m pip install -U -r requirements.txt
sudo python3.5 -m pip install -U alembic psycopg2 eventlet

echo "[C9Setup] Auto populating alembic.ini database url and titan database table"
cd ~/workspace/webapp
#sqlalchemy.url =  postgresql:///titan
sed -i '32s/.*/sqlalchemy.url =  postgresql:\/\/\/titan/' ~/workspace/webapp/alembic.ini
alembic upgrade head

echo "[C9Setup] Setting database uri for discordbot/config.py"
#'database-uri': "postgresql:///titan",
sed -i "4s/.*/\'database-uri\': \"postgresql:\/\/\/titan\",/" ~/workspace/discordbot/config.py

echo "[C9Setup] Setting database uri and app location for webapp/config.py"
sed -i "23s/.*/\'database-uri\': \"postgresql+psycopg2:\/\/\/titan?client_encoding=utf8\",/" ~/workspace/webapp/config.py
#'app-location': "/home/ubuntu/workspace/webapp/",
sed -i "20s/.*/\'app-location\': \"\/home\/ubuntu\/workspace\/webapp\/\",/" ~/workspace/webapp/config.py
#'webosockets-mode': "eventlet",
sed -i "25s/.*/\'websockets-mode\': \"eventlet\",/" ~/workspace/webapp/config.py

echo "[C9Setup] Making sure everything can be ran"
cd ~/workspace/
sudo chmod -R 777 *

echo "[C9Setup] Creating Cloud9 Python3.5 runner"
mkdir .c9/runners
touch .c9/runners/Python3.5.run
echo '{ "cmd" : ["python3.5", "$file", "$args"], "info" : "Started $project_path$file_name on Python v3.5", "env" : {}, "selector" : "source.py" }' > .c9/runners/Python3.5.run

echo "[C9Setup] Resetting everything to the master branch"
git reset --hard origin/master

echo "------------------------------"
echo "Cloud9 Installation Done!!!!!"
echo "If there are no errors, then you may proceed by editing the config.py files in the webapp and discordbot directories with your discord bot tokens, etc."
echo ""
echo "After you finished editing those files, you may (1)Double click run_c9.py in the webapp folder, (2)At the menu bar: hit Run->Run With->Python3.5, to start the webapp"
echo "Do the same thing with run.py in the discordbot folder"
echo "The console will show: wsgi starting up on http://0.0.0.0:8080. Click on that url and hit Open to view the local webapp."
echo "------------------------------"
