import time
import logging
import random

logger = logging.getLogger()

def retry_with_backoff(fn, retries = 10, backoff_in_seconds = 1):
    try:
        return fn()
    except:
        if retries <= 0:
            raise
        sleep = (backoff_in_seconds * 2 ** retries +
                random.uniform(0, 1))
        logger.critical("Retrying in {} seconds".format(round(sleep)))
        time.sleep(sleep)
        retry_with_backoff(fn, retries - 1, backoff_in_seconds)
