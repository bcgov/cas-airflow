from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from dag_configuration import default_dag_args

import os

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
DAGS_FOLDER = '/opt/airflow/dags/dynamic'


class GetDagOperator(BaseOperator):
    """Custom operator to sand GET request to provided url"""

    def __init__(self, *, url: str, path: str, ref: str, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.path = path
        self.ref = ref

    def execute(self, context):
        return httpx.get(self.url).json()


@dag(default_args=default_dag_args, schedule_interval=days_ago(2), tags=[''])
def fetch_and_save_dags(url: str = '', path: str = '', ref: str = ''):
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
    file = http.get(...)

    with open(path, 'w') as file_to_write:
        file_to_write.write(file)


dag = fetch_and_save_dags()
