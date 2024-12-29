# Use a base image with Python
FROM python:3.13-slim

# Install cron
RUN apt-get update && apt-get install -y cron

# Set the working directory
WORKDIR /app

# Add the cron job to run the script every hour
RUN echo "0 * * * * root python -u /app/main.py >> /var/log/cron.log 2>&1" > /etc/cron.d/email-forwarder-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/email-forwarder-cron

# Apply cron job
RUN crontab /etc/cron.d/email-forwarder-cron

# Create a log file to store cron logs
RUN touch /var/log/cron.log

# Copy the entire project into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run cron in the background along with the email-forwarder
CMD cron && tail -f /var/log/cron.log
