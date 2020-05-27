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
# postgres_backup_image = "docker.pkg.github.com/bcgov/cas-airflow-dags/walg:" + os.getenv('AIRFLOW_IMAGE_TAG')

DATABASE_CONNECTION_NAME = 'ciip_postgres'
postgres_connection = BaseHook.get_connection(DATABASE_CONNECTION_NAME)

# these should already exist in the postgres image?
env_vars = {
    'GOOGLE_APPLICATION_CREDENTIALS'=json.loads(BaseHook.get_connection('cas_ggl_storage').extra)["extra__google_cloud_platform__keyfile_dict"]
    'WALG_GS_PREFIX'='gs://walg_test/uploadtest'
    'PGHOST': postgres_connection.host,
    'PGPORT': postgres_connection.port,
    'PGUSER': postgres_connection.login,
    'PGPASSWORD': postgres_connection.password,
    'PGDATABASE' : postgres_connection.schema
}

make_backup = KubernetesPodOperator(
    task_id='make_full_postgres_backup',
    name='make_full_postgres_backup',
    namespace=namespace,
    # image=postgres_backup_image,
    cmds=["wal-g backup-push"],
    arguments=["../var/lib/pgsql/data/userdata/global"],
    # Needs the path to the postgres cluster to retrieve pg_control for a full backup
    env_vars=env_vars,
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    dag=make_backup)

make_backup

## WIP TODOs ##
# Finalize dockerfile & Add docker image job to ci config
# Resolve above comments / add necessary paths
# Create more (similar) dags:
# 1) Full backup dag (unscheduled, trigger by api?)
# 2) Restore dag? (unscheduled, triggered by user?) (would need a restore.sh file with backup-fetch)
# Update cas-postgres repo to:
# 1) Deploy with the necessary configs outlined in docs.md
# 2) Trigger the Full backup dag after deploy (a full backup is needed before incremental backups can happen)
