# -*- coding: utf-8 -*-
"""
# DAG to backup the ciip_portal postgres database every hour to a gcs bucket.
"""
from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.python_operator import ShortCircuitOperator
from airflow.contrib.kubernetes.secret import Secret
from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount
from airflow.hooks.base_hook import BaseHook

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
SCHEDULE_INTERVAL = '0 * * * *' # @hourly
make_backup = DAG(DAG_ID, schedule_interval=SCHEDULE_INTERVAL, default_args=default_args)
compute_resource = {'request_cpu': '1', 'request_memory': '2Gi', 'limit_cpu': '2', 'limit_memory': '4Gi'}
postgres_image = "docker-registry.default.svc:5000/wksv3k-dev/cas-postgres:latest"

# can the path to the backup point to google storage or do we have to 'fetch' it first?
# how to get the lsn?
make_backup = KubernetesPodOperator(
    task_id='make_incremental_postgres_backup',
    name='make_incremental_postgres_backup',
    namespace=namespace,
    image=postgres_image,
    cmds=['lsn_string="$(pg_controldata -D $PGDATA | grep "Latest checkpoint\'s REDO location")"; echo "$lsn_string"; lsn_number=$(echo $lsn_string | cut -c 37- | sed "s/\//x/g"); echo $lsn_number'],
    arguments=["$PGDATA", "$lsn_number"],
    # Needs the path to the backup & the LSN of the replica for the backup for incremental
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    dag=make_backup)

make_backup
