FROM python

WORKDIR /app

RUN crontab /app/crontab

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["cron", "-f"]
