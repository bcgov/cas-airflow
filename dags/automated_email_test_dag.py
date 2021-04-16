
# -*- coding: utf-8 -*-
"""
# DAG triggering the cas-ggircs-acme-renewal cron job
"""
from dag_configuration import default_dag_args
from airflow.operators.python_operator import PythonOperator
from trigger_k8s_cronjob import trigger_k8s_cronjob
from datetime import datetime, timedelta
from airflow import DAG
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


START_DATE = datetime.now() - timedelta(days=2)

namespace = os.getenv('AIRFLOW_NAMESPACE')

default_args = {
    **default_dag_args,
    'start_date': START_DATE,
    'retries': 0
}

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = None  # Never execute

dag_local_error = DAG(f'{DAG_ID}_local_error', schedule_interval=SCHEDULE_INTERVAL,
                      default_args=default_args)

dag_cronjob_error = DAG(f'{DAG_ID}_cronjob_error', schedule_interval=SCHEDULE_INTERVAL,
                        default_args=default_args)


def fail_task():
    raise Exception(
        'This DAG purposely fails, email notification should be sent.')


email_if_error_in_airflow = PythonOperator(
    python_callable=fail_task,
    task_id='email_if_error_in_airflow',
    op_args=[],
    dag=dag_local_error)

email_if_error_in_cronjob = PythonOperator(
    python_callable=trigger_k8s_cronjob,
    task_id='email_if_error_in_cronjob',
    op_args=['cas-airflow-test-email-on-failure', namespace],
    dag=dag_cronjob_error)
