FROM python

RUN apt-get update && apt-get install -y cron

WORKDIR /app

COPY . .

RUN crontab crontab

RUN pip install --no-cache-dir -r requirements.txt

CMD ["cron", "-f"]
