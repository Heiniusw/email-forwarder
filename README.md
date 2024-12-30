## Config Example
```json
{
    "log_file": "/var/log/email-forwarder.log",
    "logging_level": "DEBUG",
    "log_rotation": true,
    "imap_server": {
        "host": "imap.example.com",
        "port": 993
    },
    "smtp_server": {
        "host": "smtp.example.com",
        "port": 465,
        "username": "your-smtp-username",
        "password": "your-smtp-password"
    },
    "accounts": [
        {
            "email": "user1@example.com",
            "imap_password": "password1"
        },
        {
            "email": "user2@example.com",
            "imap_password": "password2"
        }
    ]
}
```

imap_server: Where emails are fetched from.
smtp_server: Where emails are sent to.
accounts: Accounts to fetch and send.