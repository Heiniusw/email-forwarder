FROM python:3.13-slim

WORKDIR /app

RUN crontab crontab

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["crond", "-f"]
