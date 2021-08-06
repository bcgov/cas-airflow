from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.sensors.base import BaseSensorOperator
from airflow.utils import timezone
from airflow import settings
from dag_configuration import default_dag_args
from datetime import timedelta
import urllib.request
import logging
import os


class WaitSensor(BaseSensorOperator):
    """
    Waits for a timedelta after the task's execution_date + schedule_interval.
    In Airflow, the daily task stamped with ``execution_date``
    2016-01-01 can only start running on 2016-01-02. The timedelta here
    represents the time after the execution period has closed.

    :param delta: time length to wait after execution_date before succeeding
    :type delta: datetime.timedelta
    """

    def __init__(self, *, delta, **kwargs):
        super().__init__(**kwargs)
        self.delta = delta
        self.log.info(f'Waiting {delta.seconds} seconds')

    def poke(self, context):
        target_dttm = context['start_date'] + self.delta
        self.log.info('Checking if the time (%s) has come', target_dttm)
        return timezone.utcnow() > target_dttm


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
        file_path = f'{os.environ["DYNAMIC_DAGS_PATH"]}/{file_name}'
        return file_path

    @task()
    def get_file(org, repo, ref, path):
        url = f'https://raw.githubusercontent.com/{org}/{repo}/{ref}/{path}'
        logging.critical(f'Retrieving remote DAG: {url}')
        file_path = get_filepath(path)
        logging.critical(f'Saving file to disk: {file_path}')
        urllib.request.urlretrieve(url, filename=file_path)

    wait_seconds = settings.MIN_SERIALIZED_DAG_FETCH_INTERVAL + \
        settings.MIN_SERIALIZED_DAG_UPDATE_INTERVAL

    wait_task = WaitSensor(
        task_id="wait_for_refresh",
        delta=timedelta(seconds=wait_seconds*2),
        mode='reschedule'
    )

    get_file(org, repo, ref, path) >> wait_task


dag = fetch_and_save_dag_from_github()
