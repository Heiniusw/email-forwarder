import logging
import signal
import threading


shutdown_flag = threading.Event()
active_imap_connections = []
active_connections_lock = threading.Lock()

def handle_shutdown(signum, frame):
    logging.debug("Shutdown signal received. Setting Shudown flag...")
    shutdown_flag.set()

# Registrierung der Signale für sauberes Beenden
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def on_shutdown():
    logging.info("Shutdown flag was set. Cleaning up...")
    with active_connections_lock:
        for conn in active_imap_connections:
            try:
                conn.idle_done()
                logging.debug("Stopped IDLE on one connection.")
            except Exception as e:
                logging.warning(f"Error stopping IDLE: {e}")

def shutdown_watcher():
    def monitor():
        shutdown_flag.wait()
        on_shutdown()

    thread = threading.Thread(target=monitor, name="ShutdownWatcher", daemon=True)
    thread.start()