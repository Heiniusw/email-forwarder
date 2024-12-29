FROM python:3.13-slim

RUN apt-get update && apt-get install -y cron

WORKDIR /app

RUN crontab ./crontab

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["cron", "-f"]
