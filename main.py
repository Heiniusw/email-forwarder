import imaplib
import smtplib
from email import message_from_bytes
import json
import logging
from logging.handlers import RotatingFileHandler

# Configure Logging
def configure_logging(config):
    log_file = config.get('log_file', '/var/log/email-forwarder.log')
    logging_level = config.get('logging_level', 'INFO').upper()
    log_rotation = config.get('log_rotation', False)

    # Set logging level
    level = getattr(logging, logging_level, logging.INFO)

    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s > %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    # Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File Handler
    if log_file:
        if log_rotation:
            file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
        else:
            file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

# Load the configuration
def load_config(path):
    try:
        with open(path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.error(f"Config file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing config file: {e}")
        raise

# Fetch emails from IMAP
def fetch_emails(imap_config):
    try:
        logging.debug(f"Connecting to IMAP server: {imap_config['host']} as {imap_config['email']}")
        mail = imaplib.IMAP4_SSL(imap_config['host'], imap_config['port'])
        mail.login(imap_config['email'], imap_config['password'])
        mail.select("inbox")  # Connect to inbox

        # Search for all messages
        _, data = mail.search(None, 'ALL')

        emails = []
        for num in data[0].split():
            _, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            msg = message_from_bytes(raw_email)
            emails.append((num, msg))  # Store both email ID and message

        return emails, mail

    except Exception as e:
        logging.error(f"Error fetching emails: {e}")
        return [], None

# Send the email via SMTP
def send_email(smtp_config, msg, email_id):
    try:
        email_id_str = int(email_id.decode('utf-8'))
        logging.info(f"Forwarding email #{email_id_str} from {msg['From']} to {smtp_config['to_email']}")
        
        # Connect to SMTP server
        with smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port']) as server:
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            # Forward the email
            server.sendmail(msg['From'], smtp_config['to_email'], msg.as_string())
            logging.info(f"Email #{email_id_str} from {msg['From']} forwarded successfully.")

    except Exception as e:
        logging.error(f"Error sending email #{email_id.decode('utf-8')}: {e}")

# Expunge the email from IMAP after forwarding
def expunge_email(mail, email_id):
    try:
        email_id_str = int(email_id.decode('utf-8'))
        mail.store(email_id, '+FLAGS', '\\Deleted')
        mail.expunge()  # Permanently delete
        logging.info(f"Deleted email #{email_id_str}")
    except Exception as e:
        logging.error(f"Error deleting email #{email_id.decode('utf-8')}: {e}")

def process_accounts(config):
    for account in config['accounts']:
        imap_config = config['imap_server']
        smtp_config = config['smtp_server']
        smtp_config['to_email'] = account['forward_to']
        imap_config['email'] = account['email']
        imap_config['password'] = account['imap_password']

        # Fetch emails from IMAP
        emails, mail = fetch_emails(imap_config)
        if not emails:
            logging.debug("No emails found.")
            continue

        # Process and forward emails
        for email_id, msg in emails:
            send_email(smtp_config, msg, email_id)

            # Expunge the email after sending
            expunge_email(mail, email_id)

        # Close the IMAP connection
        mail.close()
        mail.logout()

def main():
    config_path = '/app/config.json'  # Path to your config file
    config = load_config(config_path)

    # Configure logging
    configure_logging(config)

    logging.debug("Starting email-forwarder...")
    process_accounts(config)
    logging.debug("Exiting email-forwarder...")

if __name__ == '__main__':
    main()
