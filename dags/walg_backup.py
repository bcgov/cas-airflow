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

incremental_exec_command = [
    '/bin/sh',
    '-c',
    'lsn_string=$(psql -qtA -c \'select pg_walfile_name(pg_current_wal_lsn())\'); echo "$lsn_string"; lsn_number=$(echo $lsn_string | cut -c 9-); echo $lsn_number; PGPASSWORD=$PGPASSWORD_SUPERUSER envdir $WALE_ENV_DIR wal-g catchup-push $PGDATA --from-lsn 0x$lsn_number'
]

# Work for later: recovery dag

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

ciip_incremental_backup = DAG(
    DAG_ID + '_ciip_incremental', default_args=default_args, schedule_interval='@hourly')
ciip_full_backup = DAG(DAG_ID + '_ciip_full', default_args=default_args,
                       schedule_interval='@daily', start_date=START_DATE)

ggircs_incremental_backup = DAG(
    DAG_ID + '_ggircs_incremental', default_args=default_args, schedule_interval='@daily')
ggircs_full_backup = DAG(DAG_ID + '_ggircs_full', default_args=default_args,
                         schedule_interval='@daily', start_date=START_DATE)

metabase_incremental_backup = DAG(
    DAG_ID + '_metabase_incremental', default_args=default_args, schedule_interval='@hourly')
metabase_full_backup = DAG(DAG_ID + '_metabase_full', default_args=default_args,
                           schedule_interval='@daily', start_date=START_DATE)


def exec_backup_in_pod(dag, namespace, deployment_name):
    exec_command = full_exec_command
    selector = 'spilo-role=master'

    if dag.dag_id.find('incremental') != -1:
        exec_command = incremental_exec_command

    return PythonOperator(
        python_callable=exec_in_pod,
        task_id='make_postgres_backup',
        op_args=[deployment_name, namespace, exec_command, selector],
        dag=dag
    )


exec_backup_in_pod(ciip_incremental_backup, ciip_namespace,
                   'cas-ciip-portal-patroni')
exec_backup_in_pod(ciip_full_backup, ciip_namespace, 'cas-ciip-portal-patroni')
exec_backup_in_pod(ggircs_incremental_backup,
                   ggircs_namespace, 'cas-ggircs-patroni')
exec_backup_in_pod(ggircs_full_backup, ggircs_namespace, 'cas-ggircs-patroni')
exec_backup_in_pod(metabase_incremental_backup,
                   ggircs_namespace, 'cas-metabase-patroni')
exec_backup_in_pod(metabase_full_backup, ggircs_namespace,
                   'cas-metabase-patroni')
