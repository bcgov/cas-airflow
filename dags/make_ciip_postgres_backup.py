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

cas_minio_connection = BaseHook.get_connection('cas_minio') # should I do this via minio?

env_vars = {
    'DEPTH': '2',
    'FILTER': '\.zip|\.pp7m',
    'WEBSITE': swrs_eccc_connection.host,
    'USER': swrs_eccc_connection.login,
    'PASSWORD': swrs_eccc_connection.password,
    'MINIO_ACCESS_KEY': cas_minio_connection.login,
    'MINIO_SECRET_KEY': cas_minio_connection.password,
    'MINIO_HOST': cas_minio_connection.host
}

ciip_postgres_backup_image = "docker.pkg.github.com/bcgov/cas-airflow-dags/ciip_postgres_backup:" + os.getenv('CIIP_POSTGRES_BACKUP_IMAGE_TAG')

ggircs_postgres_connection = BaseHook.get_connection('ggircs_postgres') # what is the ciip-postgres connection?

env_vars = {
    'GOOGLE_APPLICATION_CREDENTIALS'=json.loads(BaseHook.get_connection('cas_ggl_storage').extra)["extra__google_cloud_platform__keyfile_dict"]
    'WALG_GS_PREFIX'='gs://walg_test/uploadtest'
    'PGHOST': ggircs_postgres_connection.host,
    'PGPORT': ggircs_postgres_connection.port,
    'PGUSER': ggircs_postgres_connection.login,
    'PGPASSWORD': ggircs_postgres_connection.password,
    'PGDATABASE' : ggircs_postgres_connection.schema
}

# This does a full backup, incremental backup -> cmds=["./make_incremental_backup.sh"]
# Incremental backups will require a full backup to have been done first. Maybe do this in a different unscheduled dag?
make_backup = KubernetesPodOperator(
    task_id='make_ciip_postgres_backup',
    name='make_ciip_postgres_backup',
    namespace=namespace,
    image=stream_minio_image,
    cmds=["./make_full_backup.sh"],
    arguments=["<PATH TO POSTGRES CLUSTER> || <PATH_TO_BACKUP> && <REPLICA_LSN>"],
    # Needs the path to the postgres cluster to retrieve pg_control for a full backup
    # Needs the path to the backup & the LSN of the replica for the backup for incremental
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
