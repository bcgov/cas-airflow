# -*- coding: utf-8 -*-
"""
# HTTP operator to fetch data from SWRS

HTTP operator to fetch data from the Single Window Reporting System (SWRS)
which is maintained by Environment and Climate Change Canada.

Based on the [example_http_operator](https://github.com/apache/airflow/blob/1.10.4/airflow/example_dags/example_http_operator.py).

Requires an http connection named `swrs_default` be created with the correct Host, Login, and Password.
"""
import json
from datetime import timedelta
from urllib.parse import urlparse
from lxml import html
import re

import airflow
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import BranchPythonOperator
from airflow.sensors.http_sensor import HttpSensor
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.utils import timezone

from operators.custom_http_operator import ContentTypeHttpOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': airflow.utils.dates.days_ago(1),
    'email': ['cas-airflow@gov.bc.ca'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'provide_context': True,
}

dag = DAG('swrs_operator', default_args=default_args, max_active_runs=5)

dag.doc_md = __doc__

MAX_DEPTH = 4


def parse_task(**kwargs):
    """Try pulling and pushing XComs."""
    ti = kwargs['ti']
    dag_run = kwargs['dag_run']
    html_doc = ti.xcom_pull(key='return_value', task_ids='get_task')
    tree = html.fromstring(html_doc)
    urls = tree.xpath('//a/@href')
    urls = [urlparse(url).path for url in urls]
    if dag_run.conf:
        endpoint = dag_run.conf['endpoint']
        depth = dag_run.conf['depth']
        parent_run_id = dag_run.conf['parent_run_id']
        urls = [url for url in urls if url.startswith(
            endpoint) and len(url) > len(endpoint)]
        depth = depth + 1
    else:
        parent_run_id = dag_run.run_id
        urls = [
            url for url in urls if re.search(
                r"\/\d+\/?$",
                url)]  # /BCGHG/2018/ /BCGHG/2019
        depth = 1
    ti.xcom_push(key='endpoints', value=urls)
    ti.xcom_push(key='depth', value=depth)
    for url in urls:
        run_id = '%s-endpoint-%s' % (parent_run_id, url)
        execution_date = timezone.utcnow()
        run = trigger_dag(
            'swrs_operator',
            run_id=run_id,
            conf={
                'endpoint': url,
                'depth': depth,
                'parent_run_id': parent_run_id,
            },
            execution_date=execution_date,
            replace_microseconds=False
        )


def branch_task(**kwargs):
    """Choose to scrape or download"""
    ti = kwargs['ti']
    content_type = ti.xcom_pull(key='return_value', task_ids='head_task')
    if content_type.startswith('text/html'):
        return 'get_task'
    return 'dummy_task'


head_task = ContentTypeHttpOperator(
    task_id='head_task',
    http_conn_id='swrs_default',
    method='HEAD',
    endpoint="{% if dag_run.conf %}{{ dag_run.conf['endpoint'] }}{% else %}/seas_extracts/BCGHG/{% endif %}",
    data={},
    headers={},
    log_response=True,
    xcom_push=True,
    dag=dag,
)

branch_task = BranchPythonOperator(
    task_id='branch_task',
    python_callable=branch_task,
    dag=dag,
)

get_task = SimpleHttpOperator(
    task_id='get_task',
    http_conn_id='swrs_default',
    method='GET',
    endpoint="{% if dag_run.conf %}{{ dag_run.conf['endpoint'] }}{% else %}/seas_extracts/BCGHG/{% endif %}",
    data={},
    headers={},
    response_check=lambda response: 'BCGHG' in response.text,
    log_response=False,
    xcom_push=True,
    dag=dag,
)

parse_task = PythonOperator(
    task_id='parse_task',
    dag=dag,
    python_callable=parse_task,
)

dummy_task = DummyOperator(
    task_id='dummy_task',
    dag=dag,
)

head_task >> branch_task
branch_task >> get_task >> parse_task
branch_task >> dummy_task

# airflow test swrs_operator index_sensor $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# airflow trigger_dag 'swrs_operator' -r $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# --conf '{"endpoint":"/seas_extracts/BCGHG/2019/PROD/"}'
