docker exec -it autobook-web-1 redis-cli -h redis ping

docker exec -it autobook-web-1 python manage.py makemigrations organizer
docker exec -it autobook-web-1 python manage.py migrate

docker compose down
docker compose build
docker compose up -d
