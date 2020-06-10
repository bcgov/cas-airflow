# -*- coding: utf-8 -*-
"""
# DAG to make a full backup of a postgres database to a gcs bucket.
"""
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
from dags.exec_in_pod import exec_in_pod

import os
import json

YESTERDAY = datetime.now() - timedelta(days=1)

namespace = os.getenv('NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == 'False'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': YESTERDAY,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

full_exec_command = [
    '/bin/sh',
    '-c',
    'source /usr/share/container-scripts/postgresql/common.sh; generate_passwd_file; wal-g backup-push $PGDATA'
]

incremental_exec_command = [
    '/bin/sh',
    '-c',
    'source /usr/share/container-scripts/postgresql/common.sh; generate_passwd_file; lsn_string="$(pg_controldata -D $PGDATA | grep "Latest checkpoint\'s REDO WAL file")"; echo "$lsn_string"; lsn_number=$(echo $lsn_string | cut -c 44- | sed "s/\///g"); echo $lsn_number; wal-g catchup-push $PGDATA --from-lsn 0x$lsn_number'
]

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = '@hourly'

ciip_incremental_backup = DAG(DAG_ID + '_ciip_incremental', default_args=default_args, schedule_interval=SCHEDULE_INTERVAL, op_args=['cas-ciip-portal-patroni', namespace, incremental_exec_command])
ciip_full_backup = DAG(DAG_ID + '_ciip_full', default_args=default_args, schedule_interval=None, op_args=['cas-ciip-portal-patroni', namespace, full_exec_command])

ggircs_incremental_backup = DAG(DAG_ID + '_ggircs_incremental', default_args=default_args, schedule_interval=SCHEDULE_INTERVAL, op_args=['cas-ggircs-patroni', namespace, incremental_exec_command])
ggircs_full_backup = DAG(DAG_ID + '_ggircs_full', default_args=default_args, schedule_interval=None, op_args=['cas-ggircs-patroni', namespace, full_exec_command])

def exec_backup_in_pod(dag):
    return PythonOperator(
        python_callable=exec_in_pod,
        task_id='make_full_postgres_backup',
        dag=dag
    )

exec_backup_in_pod(ciip_incremental_backup)
exec_backup_in_pod(ciip_full_backup)
exec_backup_in_pod(ggircs_incremental_backup)
exec_backup_in_pod(ggircs_full_backup)
