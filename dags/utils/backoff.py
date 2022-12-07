import time
import logging
import random

logger = logging.getLogger()

def retry_with_backoff(fn, retries = 10, backoff_in_seconds = 1):
    x = 0
    while True:
        try:
            return fn()
        except:
            if x == retries:
                raise
            sleep = (backoff_in_seconds * 2 ** x +
                    random.uniform(0, 1))
            logger.critical("Attempt {}, retrying in {} seconds".format(x, round(sleep)))
            time.sleep(sleep)
        x += 1
