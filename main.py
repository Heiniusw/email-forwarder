import imaplib
import smtplib
from email import message_from_bytes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# Load the configuration
def load_config(path):
    with open(path, 'r') as config_file:
        return json.load(config_file)

# Fetch emails from IMAP
def fetch_emails(imap_config):
    try:
        print(f"Connecting to IMAP server: {imap_config['host']}")
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
        print(f"Error fetching emails: {e}")
        return [], None

# Send the email via SMTP
def send_email(smtp_config, msg):
    try:
        print(f"Forwarding email from {msg['From']} to {msg['To']}")
        
        # Connect to SMTP server
        with smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port']) as server:
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            # Forward the email
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            print(f"Email from {msg['From']} forwarded successfully.")

    except Exception as e:
        print(f"Error sending email: {e}")

# Expunge the email from IMAP after forwarding
def expunge_email(mail, email_id):
    try:
        # Mark the email for deletion using its ID
        mail.store(email_id, '+FLAGS', '\\Deleted')
        mail.expunge()  # Permanently delete
        print(f"Deleted email with ID {email_id}")
    except Exception as e:
        print(f"Error deleting email: {e}")

def process_accounts(config):
    for account in config['accounts']:
        imap_config = config['imap_server']
        smtp_config = config['smtp_server']
        imap_config['email'] = account['email']
        imap_config['password'] = account['imap_password']

        # Fetch emails from IMAP
        emails, mail = fetch_emails(imap_config)
        if not emails:
            print("No emails found.")
            continue

        # Process and forward emails
        for email_id, msg in emails:
            send_email(smtp_config, msg)

            # Expunge the email after sending
            expunge_email(mail, email_id)

        # Close the IMAP connection
        mail.close()
        mail.logout()

def main():
    config_path = '/app/config.json'  # Path to your config file
    config = load_config(config_path)
    
    print("Starting email-forwarder...")
    process_accounts(config)
    print("Exiting email-forwarder...")

if __name__ == '__main__':
    main()
