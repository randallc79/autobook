docker exec -it autobook-web-1 redis-cli -h redis ping

docker exec -it autobook-web-1 python manage.py makemigrations organizer
docker exec -it autobook-web-1 python manage.py migrate

docker compose down
docker compose build
docker compose up -d

apt update && sudo apt install python3 python3-pip -y
apt -y install pipx
git clone https://github.com/patricker/m4binder.git

python3 -m venv /opt/autobook_venv
source /opt/autobook_venv/bin/activate
pip install requests beautifulsoup4 tqdm mutagen

python3 autobook-v2.2.py --m4binder_path /path/to/m4binder.py

deactivate

