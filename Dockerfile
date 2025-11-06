FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg git libsndfile1 && apt-get clean
RUN apt-get install -y redis-tools

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone deps
RUN git clone https://github.com/patricker/m4binder /opt/m4binder && cd /opt/m4binder && pip install -r requirements.txt
RUN pip install m4b-merge beets beets-audible channels channels-redis

COPY . .

HEALTHCHECK CMD curl --fail http://localhost:8000 || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "autobook.asgi:application"]
