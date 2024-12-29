import imaplib
import smtplib
import email
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_PATH = "/app/config.json"  # Adjust path as needed

def load_config(config_path):
    """Load configuration from JSON file"""
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

def forward_email(smtp_server, smtp_port, smtp_user, smtp_password, from_addr, to_addr, subject, body):
    """Forward an email to the specified SMTP server"""
    try:
        # Set up SMTP connection
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()  # Secure the connection
                server.login(smtp_user, smtp_password)  # Log in to the SMTP server
            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # Send the email
            server.sendmail(from_addr, to_addr, msg.as_string())
            print(f"Email forwarded from {from_addr} to {to_addr}")
    except Exception as e:
        print(f"Failed to forward email from {from_addr} to {to_addr}: {e}")

def process_accounts(config):
    """Process each account, fetch emails and forward them"""
    for account in config["accounts"]:
        print(f"Connecting to IMAP server: {config['imap_server']['host']} for {account['email']}")
        try:
            with imaplib.IMAP4_SSL(config['imap_server']['host'], config['imap_server']['port']) as imap:
                # Login to the account
                imap.login(account['email'], account['imap_password'])

                # Select the mailbox to operate on
                imap.select('INBOX')

                # Search for all emails in the INBOX
                status, messages = imap.search(None, 'ALL')
                if status != 'OK':
                    print(f"Failed to search inbox for {account['email']}")
                    continue

                # Process each message
                for num in messages[0].split():
                    status, data = imap.fetch(num, '(RFC822)')
                    if status != 'OK':
                        print(f"Failed to fetch email {num}")
                        continue
                    
                    msg = email.message_from_bytes(data[0][1])
                    from_addr = msg['From']
                    subject = msg['Subject']
                    body = ""
                    
                    # Check if the email is multipart
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                    else:
                        body = msg.get_payload(decode=True).decode()

                    # Forward the email
                    forward_email(
                        config['smtp_server']['host'],
                        config['smtp_server']['port'],
                        config['smtp_server'].get('username'),
                        config['smtp_server'].get('password'),
                        from_addr,
                        account['email'],
                        subject,
                        body
                    )

                # Expunge deleted messages (ensure we are in the SELECTED state)
                imap.expunge()

                # Logout from the IMAP session
                imap.logout()
        except Exception as e:
            print(f"Error processing account {account['email']}: {e}")

if __name__ == "__main__":
    # Load config from file
    config = load_config(CONFIG_PATH)
    process_accounts(config)
