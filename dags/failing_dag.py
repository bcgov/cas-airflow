
# -*- coding: utf-8 -*-
"""
# DAG triggering the cas-ggircs-acme-renewal cron job
"""
from dag_configuration import default_dag_args
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow import DAG
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


START_DATE = datetime.now() - timedelta(days=2)

namespace = os.getenv('GGIRCS_NAMESPACE')

default_args = {
    **default_dag_args,
    'start_date': START_DATE
}

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = None  # Never execute

dag = DAG(DAG_ID, schedule_interval=SCHEDULE_INTERVAL,
          default_args=default_args)


def fail_task():
    raise Exception(
        'This DAG purposely fails, email notification should be sent')


failing_dag = PythonOperator(
    python_callable=fail_task,
    task_id='failing_dag',
    op_args=[],
    dag=dag)
