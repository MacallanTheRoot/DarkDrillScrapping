import logging
import os

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - [%(levelname)s] - %(module)s - %(message)s')

    # Log dosyasının kaydedileceği yer
    log_file = 'activity.log'

    # Handler 1: Dosyaya yazma
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    # Handler 2: Konsola yazma
    screen_handler = logging.StreamHandler()
    screen_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)

    return logger