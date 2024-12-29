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
                    emails.append(msg)

        imap.logout()
        print(f"Fetched {len(emails)} emails for {account['email']}.")
        return emails


def forward_email(smtp_config, original_email, recipient_email):
    """Forward an email using the SMTP server."""
    print(f"Forwarding email to {recipient_email} via {smtp_config['host']}")

    # Create a new MIME email message
    forwarded = MIMEMultipart()
    forwarded['From'] = smtp_config['username']
    forwarded['To'] = recipient_email
    forwarded['Subject'] = "FWD: " + original_email['Subject']

    # Include the original email content
    if original_email.is_multipart():
        for part in original_email.get_payload():
            forwarded.attach(part)
    else:
        forwarded.attach(MIMEText(original_email.get_payload(), "plain"))

    # Send the email
    with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as smtp:
        smtp.starttls()
        smtp.login(smtp_config['username'], smtp_config['password'])
        smtp.sendmail(smtp_config['username'], recipient_email, forwarded.as_string())
        print(f"Email forwarded to {recipient_email}")


def process_accounts(config):
    """Process all accounts and forward emails."""
    for server_config in config:
        imap_config = server_config["imap_server"]
        smtp_config = server_config["smtp_server"]

        for account in server_config["accounts"]:
            emails = fetch_emails(imap_config, account)

            for email_msg in emails:
                forward_email(smtp_config, email_msg, account["email"])


if __name__ == "__main__":
    # Load the configuration file
    CONFIG_PATH = "config.json"
    config = load_config(CONFIG_PATH)

    # Process each account as per the configuration
    process_accounts(config)
