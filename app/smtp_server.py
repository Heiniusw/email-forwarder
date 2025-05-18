import logging
import smtplib

from mail import EMail

from account import Account

class SmtpServer:
    def __init__(self, name, host, port, username=None, password=None, catchall_email=None):
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.catchall_email = catchall_email

    def send_email(self, account: Account, email: EMail):
        try:
            from_addr = email.get_sender()
            to_addr = email.extract_recipient() or account.destination_email or self.catchall_email
            if not to_addr:
                logging.error(f"Error Forwarding email #{email.uid}: Unknown recipient")
                return False
            logging.debug(f"Forwarding email #{email.uid} from {from_addr} to {to_addr}")
            
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(from_addr, to_addr, email.msg.as_string())
                logging.info(f"Email #{email.uid} from {from_addr} forwarded to {to_addr} via {self.name}")
            
            return True
        except Exception as e:
            logging.error(f"SMTP send failed for email #{email.uid} via {self.name}: {e}")
            return False