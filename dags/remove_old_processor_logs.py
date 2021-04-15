# -*- coding: utf-8 -*-
"""
# DAG to remove dag_processor_log files older than 10 days.
"""
from dag_configuration import default_dag_args
from exec_in_pod import exec_in_pod
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow import DAG
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


START_DATE = datetime.now() - timedelta(weeks=2)

namespace = os.getenv('NAMESPACE')
deployment_name = 'airflow'
selector = 'component=web'
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == 'False'

default_args = {
    **default_dag_args,
    'start_date': START_DATE
}

exec_command = [
    '/bin/sh',
    '-c',
    'find /usr/local/airflow/logs/dag_processor_manager -name "dag_processor_manager.log.*" -type f -mtime +10 -exec rm -f {} \;'
]

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")

remove_logs_dag = DAG(DAG_ID, default_args=default_args,
                      schedule_interval='@weekly')


def remove_logs(dag):
    return PythonOperator(
        python_callable=exec_in_pod,
        task_id='remove_processor_logs',
        op_args=[deployment_name, namespace, exec_command, selector],
        dag=dag
    )


remove_logs(remove_logs_dag)
