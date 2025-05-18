import logging
from logging.handlers import RotatingFileHandler


def configure_logging(config):
    log_file = config.get('log_file')
    logging_level = config.get('logging_level', 'INFO').upper()
    log_rotation = config.get('log_rotation', False)

    # Set logging level
    level = getattr(logging, logging_level, logging.INFO)

    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s > %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

    logging.getLogger("imapclient").setLevel(logging.INFO)

    # Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File Handler
    if log_file:
        if log_rotation:
            file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
        else:
            file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)