# -*- coding: utf-8 -*-
"""
# DAG to make a full backup of a postgres database to a gcs bucket.
"""
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
from dags.exec_in_pod import exec_in_pod

import os

START_DATE = datetime.now() - timedelta(days=2)

namespace = os.getenv('NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == 'False'

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': START_DATE,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

full_exec_command = [
    '/bin/sh',
    '-c',
      'PGPASSWORD=$PGPASSWORD_SUPERUSER envdir $WALE_ENV_DIR wal-g backup-push $PGDATA'
]

incremental_exec_command = [
    '/bin/sh',
    '-c',
    'lsn_string=$(psql -qtA -c \'select pg_walfile_name(pg_current_wal_lsn())\'); echo "$lsn_string"; lsn_number=$(echo $lsn_string | cut -c 9-); echo $lsn_number; PGPASSWORD=$PGPASSWORD_SUPERUSER envdir $WALE_ENV_DIR wal-g catchup-push $PGDATA --from-lsn 0x$lsn_number'
]

## Work for later: recovery dag

# https://www.postgresql.org/docs/12/runtime-config-wal.html#RUNTIME-CONFIG-WAL-RECOVERY-TARGET
# before doing this, replicas should be lowered to 1
# full_restore_exec_command = [
#     '/bin/sh',
#     '-c',
#     'patronictl pause; \\
#     pg_ctl stop; \\
#     envdir $WALE_ENV_DIR wal-g backup-fetch /tmp/walg LATEST; \\
#     touch /tmp/walg/recovery.signal; \\
#     pg_ctl -D /tmp/walg/ start -o "--restore_command=\'PGPASSWORD=$PGPASSWORD_SUPERUSER envdir $WALE_ENV_DIR wal-g wal-fetch %f %p\' --recovery_target_time=\'2020-06-11 11:09:00-07\' --recovery_target_action=promote"; \\
#     pg_ctl -D /tmp/walg/ stop; \\
#     mv $PGDATA $PGDATA-bak; \\
#     mv /tmp/walg/ $PGDATA; \\
#     pg_ctl start; \\
#     patronictl resume; \\
#     rm -rf $PGDATA-bak'
# ]

# incremental_restore_exec_command = [
#     '/bin/sh',
#     '-c',
#     'patronictl pause; \\
#     pg_ctl stop; \\
#     envdir $WALE_ENV_DIR wal-g catchup-fetch /tmp/walg LATEST; \\
#     touch /tmp/walg/recovery.signal; \\
#     pg_ctl -D /tmp/walg/ start -o "--restore_command=\'PGPASSWORD=$PGPASSWORD_SUPERUSER envdir $WALE_ENV_DIR wal-g wal-fetch %f %p\' --recovery_target_time=\'2020-06-11 11:09:00-07\' --recovery_target_action=promote"; \\
#     pg_ctl -D /tmp/walg/ stop; \\
#     mv $PGDATA $PGDATA-bak; \\
#     mv /tmp/walg/ $PGDATA; \\
#     pg_ctl start; \\
#     patronictl resume; \\
#     rm -rf $PGDATA-bak'
# ]

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")

ciip_incremental_backup = DAG(DAG_ID + '_ciip_incremental', default_args=default_args, schedule_interval='@hourly')
ciip_full_backup = DAG(DAG_ID + '_ciip_full', default_args=default_args, schedule_interval='@daily', start_date=START_DATE)

ggircs_incremental_backup = DAG(DAG_ID + '_ggircs_incremental', default_args=default_args, schedule_interval='@daily')
ggircs_full_backup = DAG(DAG_ID + '_ggircs_full', default_args=default_args, schedule_interval='@daily', start_date=START_DATE)

def exec_backup_in_pod(dag):
    exec_command = full_exec_command
    deployment_name = 'cas-ciip-portal-patroni'

    if dag.dag_id.find('incremental') != -1:
      exec_command = incremental_exec_command

    if dag.dag_id.find('ggircs') != -1:
      deployment_name = 'cas-ggircs-patroni'

    return PythonOperator(
        python_callable=exec_in_pod,
        task_id='make_postgres_backup',
        op_args=[deployment_name, namespace, exec_command],
        dag=dag
    )

exec_backup_in_pod(ciip_incremental_backup)
exec_backup_in_pod(ciip_full_backup)
exec_backup_in_pod(ggircs_incremental_backup)
exec_backup_in_pod(ggircs_full_backup)
