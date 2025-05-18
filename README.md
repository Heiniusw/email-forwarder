## Overview
<img src="https://m.it-thaler.de/images/projekte/email-forwarder/email-forwarder-diagramm.png" width="500px"/>

### NEW: IDLE Support
Emails can be polled in a fixed intervall or the idle function can be used to detect new emails instantly.

## Config Example
```json
{
    "logging_level": "DEBUG",
    "polling_interval": 60,
    "imap_servers": {
      "greenmail": {
        "host": "docker-1.usw.lan",
        "port": 3994
      }
    },
    "smtp_servers": {
      "greenmail": {
        "host": "docker-1.usw.lan",
        "port": 3465,
        "username": "test",
        "password": "password",
        "catchall_email": "info@it-thaler.de"
      }
    },
    "accounts": [
      {
        "imap_server": "greenmail",
        "smtp_server": "greenmail",
        "source_username": "test@localhost",
        "source_password": "password",
        "mode": "idle",
        "delete": false
      }
    ]
  }
```
