## Overview
<img src="https://m.it-thaler.de/images/projekte/email-forwarder/email-forwarder-diagramm.png" width="500px"/>

## Config Example
```json
{
    "log_file": "/var/log/email-forwarder.log",  // Path to the log file
    "logging_level": "DEBUG",  // Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    "log_rotation": true,  // Whether log file should rotate (True or False)
    
    "imap_server": {
        "host": "imap.example.com",  // IMAP server address
        "port": 993,  // IMAP server port (typically 993 for SSL)
    },
    
    "smtp_server": {
        "host": "smtp.example.com",  // SMTP server address
        "port": 465,  // SMTP server port (typically 465 for SSL)
        "username": "your-smtp-username",  // (optional) SMTP server username (if needed)
        "password": "your-smtp-password",  // (optional) SMTP server password (if needed)
    },

    "accounts": [
        {
            "source_username": "user1@example.com",  // Source email address to fetch emails from
            "source_password": "password1",  // IMAP password for the source email
            "destination_email": "destination-email@example.com"  // Destination email address for forwarding
        },
        {
            "source_username": "user2@example.com",  // Another source email address to fetch emails from
            "source_password": "password2",  // IMAP password for the second source email
            "destination_email": "destination-email2@example.com"  // Destination email address for forwarding
        }
    ]
}

```

imap_server: Where emails are fetched from.
smtp_server: Where emails are sent to.
accounts: Accounts to fetch and send.
