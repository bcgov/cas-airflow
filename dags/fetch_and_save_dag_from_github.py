from airflow.sdk import dag, task
from airflow import settings
from dag_configuration import default_dag_args
from datetime import datetime, timedelta
import urllib.request
import logging
import os
import time


START_DATE = datetime.now() - timedelta(days=2)

DAG_DOC = """
DAG to fetch dags and store them to a disk location.

The following parameters are available:

**org**(_str_): Github organization
**repo**(_str_): Github repository
**ref**(_str_): the git ref to use when fetching the dag
**path**(_str_): the path to the dag to fetch, within the github repository
"""

@dag(
    default_args=default_dag_args,
    schedule=None,
    start_date=START_DATE,
    doc_md=DAG_DOC,
)
def fetch_and_save_dag_from_github(
    org: str = "", repo: str = "", ref: str = "", path: str = ""
):
    wait_seconds = settings.MIN_SERIALIZED_DAG_FETCH_INTERVAL + \
        settings.MIN_SERIALIZED_DAG_UPDATE_INTERVAL

    def get_filepath(path):
        file_name = path.split('/')[-1]
        file_path = f'{os.environ["DYNAMIC_DAGS_PATH"]}/{file_name}'
        return file_path

    @task()
    def get_file(org, repo, ref, path):
        url = f'https://raw.githubusercontent.com/{org}/{repo}/{ref}/{path}'
        logging.critical(f'Retrieving remote DAG: {url}')
        file_path = get_filepath(path)
        logging.critical(f'Saving file to disk: {file_path}')
        urllib.request.urlretrieve(url, filename=file_path)

    @task()
    def wait_task(seconds):
        time.sleep(seconds)
        

    get_file(org, repo, ref, path) >> wait_task(wait_seconds*2)


dag = fetch_and_save_dag_from_github()
