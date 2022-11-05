import os
import logging
import sys

ROOT_DIR = os.path.abspath(os.curdir)
LOG_NAME = "pump_log"


def create_logger(log_path='./logs'):

    # create logger
    logger = logging.getLogger(LOG_NAME)

    # check if logger already been created
    if logger.hasHandlers():
        return logger

    # Create handlers
    c_handler = logging.StreamHandler(stream=sys.stdout)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    f_handler = logging.FileHandler(f'{log_path}/{LOG_NAME}.log', mode='a+')
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    logger.setLevel(logging.DEBUG)

    return logger
