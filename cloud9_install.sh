#!/usr/bin/env bash
echo "[C9Setup] Installing mysql, and creating titan db table"
cd ~/workspace/
mysql-ctl start
mysql -u root -e "CREATE DATABASE titan;"

echo "[C9Setup] Copying config.py for webapp/discordbot and alembic.ini"
cp ~/workspace/webapp/config.example.py ~/workspace/webapp/config.py
cp ~/workspace/discordbot/config.example.py ~/workspace/discordbot/config.py
cp ~/workspace/webapp/alembic.example.ini ~/workspace/webapp/alembic.ini

echo "[C9Setup] Installing Titan dependencies"
cd ~/workspace/
sudo python3.5 -m pip install -r requirements.txt
sudo python3.5 -m pip install alembic pymysql gevent uwsgi

echo "[C9Setup] Auto populating alembic.ini database url and titan database table"
cd ~/workspace/webapp
#sqlalchemy.url =  mysql+pymysql://root@localhost/titan
sed -i '32s/.*/sqlalchemy.url =  mysql+pymysql:\/\/root@localhost\/titan/' ~/workspace/webapp/alembic.ini
alembic upgrade head

echo "[C9Setup] Setting database uri for discordbot/config.py"
#'database-uri': "mysql+pymysql://root@localhost/titan",
sed -i "4s/.*/\'database-uri\': \"mysql+pymysql:\/\/root@localhost\/titan\",/" ~/workspace/discordbot/config.py

echo "[C9Setup] Setting database uri and app location for webapp/config.py"
sed -i "11s/.*/\'database-uri\': \"mysql+pymysql:\/\/root@localhost\/titan\",/" ~/workspace/webapp/config.py
#'app-location': "/home/ubuntu/workspace/webapp/",
sed -i "8s/.*/\'app-location\': \"\/home\/ubuntu\/workspace\/webapp\/\",/" ~/workspace/webapp/config.py

echo "[C9Setup] Making sure everything can be ran"
cd ~/workspace/
sudo chmod -R 777 *

echo "------------------------------"
echo "Cloud9 Installation Done!!!!!"
echo "If there are no errors, then you may proceed by editing the config.py files in the webapp and discordbot directories with your discord bottokens, etc."
echo "Remember that your database uri is: mysql+pymysql://root@localhost/titan"
echo ""
echo "After you finished editing those files, you may right click on run_c9.py and click run in the menu to start the webapp."
echo "To run the discordbot, change your directory to discord bot: cd discordbot/"
echo "and type the following command: python3.5 run.py"
echo "------------------------------"
