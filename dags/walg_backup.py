# -*- coding: utf-8 -*-
"""
# DAG to make a full backup of a postgres database to a gcs bucket.
"""
from dag_configuration import default_dag_args
from exec_in_pod import exec_in_pod
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from airflow import DAG
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


START_DATE = datetime.now() - timedelta(days=2)

ciip_namespace = os.getenv('CIIP_NAMESPACE')
ggircs_namespace = os.getenv('GGIRCS_NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == 'False'

default_args = {
    **default_dag_args,
    'start_date': START_DATE
}

full_exec_command = [
    '/bin/sh',
    '-c',
    'PGPASSWORD=$PGPASSWORD_SUPERUSER envdir $WALE_ENV_DIR wal-g backup-push $PGDATA'
]

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")

ciip_full_backup = DAG(DAG_ID + '_ciip_full', default_args=default_args,
                       schedule_interval='0 8 * * *', start_date=START_DATE)

ggircs_full_backup = DAG(DAG_ID + '_ggircs_full', default_args=default_args,
                         schedule_interval='0 8 * * *', start_date=START_DATE)

metabase_full_backup = DAG(DAG_ID + '_metabase_full', default_args=default_args,
                           schedule_interval='0 8 * * *', start_date=START_DATE)


def exec_backup_in_pod(dag, namespace, deployment_name):
    exec_command = full_exec_command
    selector = 'spilo-role=master'

    return PythonOperator(
        python_callable=exec_in_pod,
        task_id='make_postgres_backup',
        op_args=[deployment_name, namespace, exec_command, selector],
        dag=dag
    )


exec_backup_in_pod(ciip_full_backup, ciip_namespace, 'cas-ciip-portal-patroni')

exec_backup_in_pod(ggircs_full_backup, ggircs_namespace, 'cas-ggircs-patroni')

exec_backup_in_pod(metabase_full_backup, ggircs_namespace,
                   'cas-metabase-patroni')
