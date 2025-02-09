import sys
import imaplib
import smtplib
from email import message_from_bytes
import json
import logging
from logging.handlers import RotatingFileHandler
from filelock import FileLock

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

# Validate configuration
def validate_config(config):
    
    # Validate IMAP config
    for field in ['host', 'port']:
        if field not in config.get('imap_server', {}):
            logging.error(f"Missing IMAP configuration: {field}")
            sys.exit(1)
    
    # Validate SMTP config
    for field in ['host', 'port']:
        if field not in config.get('smtp_server', {}):
            logging.error(f"Missing SMTP configuration: {field}")
            sys.exit(1)

    # Validate accounts
    if 'accounts' not in config:
        logging.error("Missing 'accounts' section in config")
        sys.exit(1)

    for account in config['accounts']:
        for field in ['source_username', 'source_password', 'destination_email']:
            if field not in account:
                logging.error(f"Missing required field {field} in account: {account}")
                sys.exit(1)

# Acquire file lock
def acquire_lock():
    lock = FileLock("email-forwarder.lock")
    try:
        lock.acquire(timeout=1)
        return lock
    except Exception as e:
        logging.error(f"Failed to acquire lock: {e}")
        sys.exit(1)

# Release file lock
def release_lock(lock):
    lock.release()

# Helper method to safely convert email ID to string
def get_email_id_str(email_id):
    try:
        return str(int(email_id.decode('utf-8')))
    except (ValueError, TypeError) as e:
        logging.error(f"Error converting email ID {email_id}: {e}")
        return "invalid"

# Fetch emails from IMAP
def fetch_emails_from_imap_server(imap_config):
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
def send_email(smtp_config, msg, email_id, destination_email):
    try:
        email_id_str = get_email_id_str(email_id)
        logging.info(f"Forwarding email #{email_id_str} from {msg['From']} to {destination_email}")
        
        # Connect to SMTP server
        with smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port']) as server:
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            # Forward the email
            server.sendmail(msg['From'], destination_email, msg.as_string())
            logging.info(f"Email #{email_id_str} forwarded successfully.")

    except Exception as e:
        email_id_str = get_email_id_str(email_id)
        logging.error(f"Error sending email #{email_id_str}: {e}")

# Expunge the email from IMAP after forwarding
def expunge_email(mail, email_id):
    try:
        email_id_str = get_email_id_str(email_id)
        # Mark the email for deletion
        mail.store(email_id, '+FLAGS', '\\Deleted')
        logging.info(f"Marked email #{email_id_str} for deletion.")
    except Exception as e:
        email_id_str = get_email_id_str(email_id)
        logging.error(f"Error marking email #{email_id_str} for deletion: {e}")

def process_accounts(config):
    for account in config['accounts']:
        imap_config = config['imap_server']
        smtp_config = config['smtp_server']
        imap_config['email'] = account['source_username']
        imap_config['password'] = account['source_password']

        # Fetch emails from IMAP
        emails, mail = fetch_emails_from_imap_server(imap_config)
        if not emails:
            logging.debug("No emails found.")
            continue

        # Process and forward emails
        for email_id, msg in emails:
            try:
                send_email(smtp_config, msg, email_id, account['destination_email'])
                # Mark the email for deletion after successful forwarding
                expunge_email(mail, email_id)
            except Exception as e:
                email_id_str = get_email_id_str(email_id)
                logging.error(f"Error handling email #{email_id_str} due to error: {e}")

        # Expunge (permanently delete) all emails marked for deletion
        try:
            mail.expunge()
            logging.info("All marked emails deleted successfully.")
        except Exception as e:
            logging.error(f"Error during expunge operation: {e}")

        # Close the IMAP connection
        mail.close()
        mail.logout()


def main():
    config_path = '/app/config.json'  # Path to your config file
    config = load_config(config_path)
    
    # Validate the configuration
    validate_config(config)

    # Configure logging
    configure_logging(config)

    # Acquire Lock
    lock_file = acquire_lock()

    try:
        logging.debug("Starting email-forwarder...")
        process_accounts(config)
        logging.debug("Exiting email-forwarder...")
    finally:
        release_lock(lock_file)  # Ensure the lock is always released

if __name__ == '__main__':
    main()
