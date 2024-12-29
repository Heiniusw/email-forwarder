## Config Example
```json
[
  {
    "imap_server": {
      "host": "imap.test.de",
      "port": 993
    },
    "smtp_server": {
      "host": "smtp.localmail.com",
      "port": 587,
      "username": "smtp_user",
      "password": "smtp_password"
    },
    "accounts": [
      {
        "email": "user1@test.de",
        "imap_password": "imap_password1"
      },
      {
        "email": "user2@test.de",
        "imap_password": "imap_password2"
      }
    ]
  }
]
```

imap_server: Where emails are fetched from.
smtp_server: Where emails are sent to.
accounts: Accounts to fetch and send.