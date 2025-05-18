class Account:
    def __init__(self, imap_server, smtp_server, source_username, source_password, destination_email, mode, delete):
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self.source_username = source_username
        self.source_password = source_password
        self.destination_email = destination_email
        self.mode = mode
        self.delete = delete
    
    def __str__(self):
        return self.destination_email or self.source_username

    def start_idle(self):
        pass