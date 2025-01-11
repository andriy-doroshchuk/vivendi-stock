import os
import sys
import datetime
import logging

def enable_logger():

    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)

    current_time = datetime.datetime.now()
    logging.basicConfig(
        filename = os.path.join(log_dir, f'{current_time}.log'.replace(':', '-')),
        level = logging.DEBUG
    )

    logger = logging.getLogger()
    sys.stderr.write = logger.error
    sys.stdout.write = logger.info
