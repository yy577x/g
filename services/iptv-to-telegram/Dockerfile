FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY iptv_to_telegram ./iptv_to_telegram

ENV TG_SESSION_NAME=userbot
ENV TG_SESSION_WORKDIR=/app/sessions
VOLUME ["/app/sessions"]

CMD ["python", "-m", "iptv_to_telegram"]
