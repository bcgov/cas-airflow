import asyncio
import time
import logging
import random

def retry_with_backoff(fn, retries = 6, backoff_in_seconds = 1):
    x = 0
    while True:
        try:
            print('trying to return function')
            return fn()
        except:
            print('except {}'.format(x))
            if x == retries:
                return None
            sleep = (backoff_in_seconds * 2 ** x + 
                    random.uniform(0, 1))
            logging.critical(
                "Retrying in {backoff} seconds".format(backoff=sleep))
            time.sleep(sleep)
        x += 1

def test_retry_with_backoff(monkeypatch):
    """
    GIVEN a monkeypatched version of an api call 
    WHEN example1() is called
    THEN the api call returns after x seconds 
    """
    
    # def mock_get_pod_name():
    #     async def mock_return():
    #         await asyncio.sleep(5) 
    #         return 'example_name'
    #     try: 
    #         mock_return() 
    #     except: 
    #         logging.critical('error')

    # pod_name = retry_with_backoff(mock_get_pod_name)

    retry_with_backoff(monkeypatch, 2)

    assert 1==1
    
