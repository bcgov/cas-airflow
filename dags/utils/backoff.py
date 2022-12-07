import time
import logging
import random

def retry_with_backoff(fn, retries = 6, backoff_in_seconds = 1):
    x = 0
    while True:
        try:
            return fn()
        except:
            if x == retries:
                raise
            sleep = (backoff_in_seconds * 2 ** x +
                    random.uniform(0, 1))
            logging.critical(
                "Retrying in {backoff} seconds".format(backoff=sleep))
            time.sleep(sleep)
        x += 1
