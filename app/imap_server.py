import email
import logging
import ssl
import threading

from stateful_imap_client import StatefulIMAPClient

from account import Account
from mail import EMail
from globals import active_imap_connections, active_connections_lock, shutdown_flag

RETRY_DELAY = 10

class ImapServer:
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port

    def connect(self, account: Account):
        try:
            logging.debug(f"Connecting to IMAP server {self.name} as {account.source_username}")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connection = StatefulIMAPClient(self.host, self.port, use_uid=True, ssl=True, ssl_context=ssl_context)
            connection.login(account.source_username, account.source_password)
            connection.select_folder('INBOX')
            return connection
        except Exception as e:
            logging.error(f"[{account.source_username}@{self.name}] IMAP connection failed: {e}")
            raise

    def poll(self, account: Account):
        try:
            connection = self.connect(account)
            self.__handle_mails(connection, account)
        except Exception as e:
            logging.error(f"Error polling emails: {e}")
            return [], None
        
    def start_idle(self, account: Account):
        def idle():
            connection = None
            while not shutdown_flag.is_set():
                if connection is None or not connection.is_connection_alive():
                    try:
                        logging.debug(f"[{account.source_username}@{self.name}] Connecting to IMAP server...")
                        connection = self.connect(account)
                        register_connection(connection)
                        logging.info(f"[{account.source_username}@{self.name}] Connected and folder selected.")
                    except Exception as e:
                        logging.error(f"[{account.source_username}@{self.name}] Failed to connect: {e}")
                        shutdown_flag.wait(timeout=RETRY_DELAY)
                        continue
                    
                    try:
                        while not shutdown_flag.is_set() and self.__handle_mails(connection, account) > 0:
                            pass
                    except Exception as e:
                        logging.error(f"[{account.source_username}@{self.name}] IDLE Initial Poll error: {e}")
                
                if not shutdown_flag.is_set():
                    try:
                        connection.idle()
                        logging.info(f"[{account.source_username}@{self.name}] IDLE mode started")
                        responses = connection.idle_check(timeout=300)
                        connection.idle_done()
                        if responses:
                            logging.debug(f"[{account.source_username}@{self.name}] New email event received")
                        while not shutdown_flag.is_set() and self.__handle_mails(connection, account) > 0:
                            pass
                    except Exception as e:
                        logging.error(f"[{account.source_username}@{self.name}] IDLE error: {e}")
                        shutdown_flag.wait(timeout=RETRY_DELAY)
                        unregister_connection(connection)
                        connection = None

            if connection:
                unregister_connection(connection)

            logging.info(f"[{account.source_username}@{self.name}] IDLE Loop Exited")

        thread = threading.Thread(target=idle)
        thread.daemon = True
        thread.start()
        return thread



    def __handle_mails(self, connection, account: Account):
        try:
            messages = connection.search(['ALL'])
        except Exception as e:
            logging.error(f"[{account.source_username}] Failed to search mailbox: {e}")
            raise

        for uid in messages:
            if shutdown_flag.is_set():
                break
            try:
                raw_message = connection.fetch([uid], ['RFC822'])[uid][b'RFC822']
                logging.debug(f"[{account.source_username}] Found email #{uid}.")
                msg = email.message_from_bytes(raw_message)
                success = account.smtp_server.send_email(account, EMail(uid, msg))
                if success:
                    if account.delete:
                        connection.add_flags([uid], [b'\\Deleted'])
                        logging.debug(f"[{account.source_username}] Email #{uid} marked for deletion.")
                    else:
                        connection.add_flags([uid], ['Processed'])
                        logging.debug(f"[{account.source_username}] Email #{uid} marked as processed.")
                else:
                    logging.warning(f"[{account.source_username}] Failed to forward email #{uid}.")

            except Exception as e:
                logging.error(f"[{account.source_username}] Error processing email #{uid}: {e}")
        
        if account.delete:
            try:
                connection.expunge()
                logging.debug(f"[{account.source_username}] Expunged deleted emails.")
            except Exception as e:
                logging.warning(f"[{account.source_username}] Failed to expunge mailbox: {e}")
        
        return len(messages)
    
def register_connection(connection):
    with active_connections_lock:
        if connection not in active_imap_connections:
            active_imap_connections.append(connection)
    
def unregister_connection(connection):
    try:
        connection.idle_done()
    except Exception:
        pass
    try:
        connection.logout()
    except Exception:
        pass
    with active_connections_lock:
        if connection in active_imap_connections:
            active_imap_connections.remove(connection)