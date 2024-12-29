import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json


def load_config(file_path):
    """Load configuration from a JSON file."""
    with open(file_path, 'r') as config_file:
        return json.load(config_file)


def fetch_emails(imap_config, account):
    """Fetch emails from the IMAP server for a specific account."""
    print(f"Connecting to IMAP server: {imap_config['host']} for {account['email']}")
    with imaplib.IMAP4_SSL(imap_config['host'], imap_config['port']) as imap:
        imap.login(account['email'], account['imap_password'])
        imap.select("INBOX")

        # Search for all emails in the inbox
        status, messages = imap.search(None, "ALL")
        email_ids = messages[0].split()

        emails = []
        for email_id in email_ids:
            status, msg_data = imap.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    raw_email = response_part[1]
                    msg = email.message_from_bytes(raw_email)
                    emails.append((email_id, msg))

        return imap, emails


def forward_email(smtp_config, raw_email, recipient_email):
    """Forward an email using the SMTP server."""
    print(f"Forwarding email to {recipient_email} via {smtp_config['host']}")

    with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as smtp:
        smtp.starttls()
        smtp.login(smtp_config['username'], smtp_config['password'])
        smtp.sendmail(smtp_config['username'], recipient_email, raw_email.as_bytes())
        print(f"Email forwarded to {recipient_email}")


def process_accounts(config):
    """Process all accounts and forward emails."""
    for server_config in config:
        imap_config = server_config["imap_server"]
        smtp_config = server_config["smtp_server"]

        for account in server_config["accounts"]:
            imap, emails = fetch_emails(imap_config, account)

            for email_id, email_msg in emails:
                try:
                    # Forward the email
                    forward_email(smtp_config, email_msg, account["email"])

                    # Mark email for deletion after successful forwarding
                    imap.store(email_id, '+FLAGS', '\\Deleted')
                except Exception as e:
                    print(f"Error forwarding email {email_id} for {account['email']}: {e}")

            # Permanently delete emails marked as deleted
            imap.expunge()
            imap.logout()
            print(f"Processed and cleaned up emails for {account['email']}.")


if __name__ == "__main__":
    # Load the configuration file
    CONFIG_PATH = "config.json"
    config = load_config(CONFIG_PATH)

    # Process each account as per the configuration
    process_accounts(config)
