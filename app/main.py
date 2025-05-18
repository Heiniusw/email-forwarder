import os
import sys
from email import message_from_bytes
import json
import logging

from log import configure_logging

from account import Account
from imap_server import ImapServer
from smtp_server import SmtpServer

from globals import shutdown_flag, shutdown_watcher

# Load the configuration
def load_config(path):
    try:
        with open(path, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.error(f"Config file not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing config file: {e}")
        raise

def main():
    config_path = 'config.json'
    config = load_config(config_path)
    configure_logging(config)
    polling_interval = config.get("polling_interval", 60)
    
    shutdown_watcher()

    try:
        logging.info("Starting email forwarder...")

        imap_servers = {}
        for name, server_config in config.get("imap_servers").items():
            imap_servers[name] = ImapServer(
                name,
                server_config.get("host"),
                server_config.get("port")
            )

        smtp_servers = {}
        for name, server_config in config.get("smtp_servers").items():
            smtp_servers[name] = SmtpServer(
                name,
                server_config.get("host"),
                server_config.get("port"),
                server_config.get("username"),
                server_config.get("password"),
                server_config.get("catchall_email")
            )
        
        accounts = {"poll": [], "idle": []}
        for account_config in config.get("accounts"):
            account_name = account_config.get("destination_email") or account_config.get("source_username")
            mode = account_config.get("mode", "idle")

            imap_server = imap_servers.get(account_config.get("imap_server"))
            if not imap_server:
                logging.error(f"IMAP Server for account {account_name} not found, skipping...")
                continue

            smtp_server = smtp_servers.get(account_config.get("smtp_server"))
            if not smtp_server:
                logging.error("SMTP Server for account {account_name} not found, skipping...")
                continue

            account = Account(
                imap_server,
                smtp_server,
                account_config.get("source_username"),
                account_config.get("source_password"),
                account_config.get("destination_email"),
                mode,
                account_config.get("delete", False)
            )
            accounts[mode].append(account)
            logging.debug(f"Account {account} registerd in {mode} mode.")

        idle_threads = []
        if not accounts["idle"]:
            logging.debug("No Accounts found for idle Loop.")
        else:
            logging.debug("Starting IMAP IDLE Accounts...")
            for account in accounts["idle"]:
                logging.debug(f"Starting Account {account}...")
                idle_threads.append(account.imap_server.start_idle(account))

        if not accounts["poll"]:
            logging.debug("No Accounts found for poll Loop.")
        else:
            logging.debug("Starting IMAP POLL Loop...")
            while not shutdown_flag.is_set():
                logging.debug("Starting IMAP POLL...")
                
                for account in accounts["idle"]:
                    logging.debug("Polling Account {account}...")
                    account.imap_server.poll(account)

                logging.debug(f"Sleeping for {polling_interval} seconds...")
                shutdown_flag.wait(timeout=polling_interval)

        if os.name == 'nt':
            while not shutdown_flag.is_set():
                shutdown_flag.wait(timeout=0.5)
        else:
            signal.pause()

        for thread in idle_threads:
            thread.join()
    finally:
        logging.info("Email forwarder shutting down.")


main()