docker exec -it autobook-web-1 redis-cli -h redis ping

docker exec -it autobook-web-1 python manage.py makemigrations organizer
docker exec -it autobook-web-1 python manage.py migrate

docker compose down
docker compose build
docker compose up -d

apt update && sudo apt install python3 python3-pip -y
apt -y install pipx
apt -y install ffmpeg
apt -y install ffmpeg fdkaac php-cli php-intl php-json php-dom

git clone https://github.com/patricker/m4binder.git
cd /opt/m4binder && pip install -r requirements.txt

git clone https://github.com/sandreas/mp4v2
cd mp4v2
./configure
make && sudo make install

wget https://github.com/sandreas/m4b-tool/releases/download/v0.5.2/m4b-tool.phar -O /usr/local/bin/m4b-tool && chmod +x /usr/local/bin/m4b-tool

python3 -m venv /opt/autobook_venv
source /opt/autobook_venv/bin/activate
pip install requests beautifulsoup4 tqdm mutagen
pip install m4b-merge
pip install bs4

git -C /opt/autobook pull && cp /opt/autobook/autobook-cli/* .

python3 autobook-v2.5.py --m4binder_path /opt/m4binder/m4binder.py

deactivate

