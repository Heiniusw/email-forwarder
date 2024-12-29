FROM python

RUN apt-get update && apt-get install -y cron

RUN touch /var/log/cron.log && chmod 666 /var/log/cron.log

WORKDIR /app

COPY . .

RUN crontab crontab

RUN pip install --no-cache-dir -r requirements.txt

CMD ["cron", "-f"]
