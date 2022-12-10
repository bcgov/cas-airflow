import time
import logging
import random
import sys

logger = logging.getLogger()

def retry_with_backoff(fn, retries = 10, backoff_in_seconds = 1):

    try:
        return fn()
    except Exception as e:

        logger.critical("Exception: {} {}\n from function {}"
            .format(sys.exc_info()[0], e, fn))

        if retries <= 0:
            raise
        sleep = (backoff_in_seconds + random.uniform(0, 1))

        logger.critical("Retrying in {} seconds\n".format(round(sleep)))
        time.sleep(sleep)

        retry_with_backoff(fn, retries-1, backoff_in_seconds * 2 )
