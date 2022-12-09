import time
import logging
import random
import sys

logger = logging.getLogger()

def retry_with_backoff(fn, retries = 10, backoff_in_seconds = 1):
    x = 0
    while True:
        try:
            return fn()
        except Exception as e:
            if x == retries:
                raise
            sleep = (backoff_in_seconds * 2 ** x +
                    random.uniform(0, 1))

            logger.critical("Exception: {} {}\n from function {}"
                .format(sys.exc_info()[0], e, fn))
            logger.critical("Attempt {}, retrying in {} seconds\n".format(x, round(sleep)))
            time.sleep(sleep)
        x += 1
