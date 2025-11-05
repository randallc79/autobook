FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg git && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone dependencies (m4binder, m4b-merge, beets)
RUN git clone https://github.com/patricker/m4binder /opt/m4binder && \
    cd /opt/m4binder && pip install -r requirements.txt
RUN pip install m4b-merge beets beets-audible

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "autobook.wsgi"]
