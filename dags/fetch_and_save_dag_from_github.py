from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from dag_configuration import default_dag_args
import urllib.request
import logging
import os

DAGS_FOLDER = '/opt/airflow/dags/dynamic'

@dag(default_args=default_dag_args, schedule_interval=None, start_date=days_ago(2))
def fetch_and_save_dag_from_github(org: str = '', repo: str = '', ref: str = '', path: str = ''):
    """
      DAG to fetch dags and store them to a disk location.

      :param org: Github organisation
      :type org: str

      :param repo: Github repository
      :type repo: str

      :param ref: the git ref to use when fetching the dag
      :type ref: str

      :param path: the path to the dag to fetch, within the github repository
      :type path: str
    """

    def get_filepath(path):
        file_name = path.split('/')[-1]
        file_path = f'{os.environ["AIRFLOW_HOME"]}/dags/dynamic/{file_name}'
        return file_path

    @task()
    def get_file(org, repo, ref, path):
        url = f'https://raw.githubusercontent.com/{org}/{repo}/{ref}/{path}'
        logging.critical(f'Retrieving remote DAG: {url}')
        file_path = get_filepath(path)
        logging.critical(f'Saving file to disk: {file_path}')
        urllib.request.urlretrieve(url, filename=file_path)

    get_file(org, repo, ref, path)



dag = fetch_and_save_dag_from_github()
