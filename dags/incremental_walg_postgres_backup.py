# -*- coding: utf-8 -*-
"""
# DAG to backup a postgres database every hour to a gcs bucket.
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

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = '@hourly'
make_backup = DAG('incremental_walg_postgres_backup', default_args=default_args, schedule_interval=SCHEDULE_INTERVAL)

exec_command = [
    '/bin/sh',
    '-c',
    'source /usr/share/container-scripts/postgresql/common.sh; generate_passwd_file; lsn_string="$(pg_controldata -D $PGDATA | grep "Latest checkpoint\'s REDO location")"; echo "$lsn_string"; lsn_number=$(echo $lsn_string | cut -c 38- | sed "s/\//x/g"); echo $lsn_number'#;wal-g catchup-push $PGDATA --from-lsn 0x$lsn_number'
]

def exec_backup_in_pod(dag):
    return PythonOperator(
        python_callable=exec_in_pod,
        task_id='make_incremental_postgres_backup',
        op_args=['cas-ciip-postgres-master', namespace, exec_command],
        dag=dag
    )

exec_backup_in_pod(make_backup)
