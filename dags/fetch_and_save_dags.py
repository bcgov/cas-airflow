from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from dag_configuration import default_dag_args
import urllib.request
import logging

DAGS_FOLDER = '/opt/airflow/dags/dynamic'


@dag(default_args=default_dag_args, schedule_interval=None, start_date=days_ago(2), tags=[''])
def fetch_and_save_dags(org: str = '', repo: str = '', path: str = '', ref: str = ''):
    """
      DAG to fetch dags and store them to a disk location.

      :param url: URL of the git repository containing the dag to fetch
      :type url: str

      :param path: the path to the dag to fetch, within the github repository
      :type path: str

      :param ref: the git ref to use when fetching the dag
      :type ref: str
    """

    @task()
    def get_file(url, path, ref):
        url = f'https://raw.githubusercontent/{org}/{repo}/{ref}/{path}'
        logging.critical(f'Retrieving remote DAG: {url}')
        with urllib.request.urlopen() as f:
            file = f.read()
            return file

    @task()
    def save_file():
        file_name = path.split('/')[-1]
        file_path = f'/opt/airflow/dags/dynamic/{file_name}'
        logging.critical(f'Saving file to disk: {file_path}')
        with open(file_path, 'w') as desc:
            desc.write(file)

    file = get_file()

    save_file(file)


dag = fetch_and_save_dags()
