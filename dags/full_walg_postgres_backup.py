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
SCHEDULE_INTERVAL = null
make_backup = DAG(DAG_ID, default_args=default_args)
compute_resource = {'request_cpu': '1', 'request_memory': '2Gi', 'limit_cpu': '2', 'limit_memory': '4Gi'}
postgres_image = "docker-registry.default.svc:5000/wksv3k-dev/cas-postgres:latest"

make_backup = KubernetesPodOperator(
    task_id='make_full_postgres_backup',
    name='make_full_postgres_backup',
    namespace=namespace,
    image=postgres_image,
    cmds=["wal-g backup-push"],
    arguments=["$PGDATA"],
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    dag=make_backup)

make_backup
