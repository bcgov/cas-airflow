# -*- coding: utf-8 -*-
"""
# DAGs to fetch and extract SWRS data from the ECCC website.
swrs_eccc_import_full will download and extract all zip files in the GCS bucket
swrs_eccc_import_incremental will only download and extract files that were uploaded in the first task of the DAG

Both these DAGs is trigger the `transform_load_ggircs` DAG, which runs the transform/load function in the ggircs database,
thus transforming the XML files into tables

These DAGs the following connections:
 - http connection named `swrs_eccc` with the correct Host, Login, Password,
   and an extra JSON object with a 'zip_passwords' property (an array listing the possible passwords for the zip files).
 - http connection named `cas_minio` with the correct Host (without the https:// at the beginning), Login, and Password (TODO: connect to GCS directly).
 - Google cloud platform connection named `cas_ggl_storage` with the correct Keyfile JSON.
 - Postgres connection named `ggircs_postgres` with the correct host, port, login, password,
   and schema (named "schema" in airflow, but refers to the postgres database)
"""
import os
import sys
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))

from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.python_operator import ShortCircuitOperator, PythonOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.hooks.base_hook import BaseHook
from trigger_k8s_cronjob import trigger_k8s_cronjob

import json

START_DATE = datetime.now() - timedelta(days=2)

namespace = os.getenv('NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == False

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'start_date': START_DATE,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = '0 0 * * *'

dag_incremental = DAG(DAG_ID + '_incremental', schedule_interval=SCHEDULE_INTERVAL, default_args=default_args, user_defined_macros={'json': json}, start_date=START_DATE)
dag_full = DAG(DAG_ID+'_full', schedule_interval=None, default_args=default_args)

compute_resource = {'request_cpu': '1', 'request_memory': '2Gi', 'limit_cpu': '2', 'limit_memory': '4Gi'}

swrs_eccc_connection = BaseHook.get_connection('swrs_eccc')
cas_minio_connection = BaseHook.get_connection('cas_minio')
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

stream_minio_image = "docker.pkg.github.com/bcgov/cas-airflow/stream-minio:" + os.getenv('AIRFLOW_IMAGE_TAG')
extract_zips_image = "docker.pkg.github.com/bcgov/cas-airflow/extract-zips-to-ggircs:" + os.getenv('AIRFLOW_IMAGE_TAG')

def should_extract_zips(**context):
    download_return = context['task_instance'].xcom_pull(task_ids = 'download_eccc_files')
    return len(download_return['uploadedObjects']) > 0

ggircs_postgres_connection = BaseHook.get_connection('ggircs_postgres')

extract_zips_env = {
    'GCS_BUCKET': 'swrs-import',
    'PGHOST': ggircs_postgres_connection.host,
    'PGPORT': str(ggircs_postgres_connection.port) if ggircs_postgres_connection.port else None,
    'PGUSER': ggircs_postgres_connection.login,
    'PGPASSWORD': ggircs_postgres_connection.password,
    'PGDATABASE' : ggircs_postgres_connection.schema,
    'ECCC_ZIP_PASSWORDS': json.dumps(json.loads(swrs_eccc_connection.extra)['zip_passwords']),
    'GCS_KEY': json.loads(BaseHook.get_connection('cas_ggl_storage').extra)["extra__google_cloud_platform__keyfile_dict"]
}

extract_zips_to_ggircs_full = KubernetesPodOperator(
    task_id='extract_zips_to_ggircs_full',
    name='extract_zips_to_ggircs_full',
    namespace=namespace,
    image=extract_zips_image,
    env_vars=extract_zips_env,
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    do_xcom_push=False,
    dag=dag_full)

extract_zips_env_incremental = extract_zips_env.copy()
extract_zips_env_incremental['DOWNLOAD_ECCC_FILES_XCOM'] = '{{ json.dumps(task_instance.xcom_pull(task_ids="download_eccc_files")) }}'

download_eccc_files = KubernetesPodOperator(
    task_id='download_eccc_files',
    name='download_eccc_files',
    namespace=namespace,
    image=stream_minio_image,
    cmds=["./init.sh"],
    arguments=["swrs-import"],
    env_vars=env_vars,
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    do_xcom_push=True,
    dag=dag_incremental)

should_extract_zips_op = ShortCircuitOperator(
    task_id='should_extract_zips',
    provide_context=True,
    python_callable=should_extract_zips,
    dag=dag_incremental)

extract_zips_to_ggircs = KubernetesPodOperator(
    task_id='extract_zips_to_ggircs',
    name='extract_zips_to_ggircs',
    namespace=namespace,
    image=extract_zips_image,
    env_vars=extract_zips_env_incremental,
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    do_xcom_push=False,
    dag=dag_incremental)

def load_ggircs(dag):
    return PythonOperator(
        python_callable=trigger_k8s_cronjob,
        task_id='load_ggircs',
        op_args=['cas-ggircs-etl-deploy', namespace],
        dag=dag)


def ggircs_read_only_user(dag):
    return PythonOperator(
        python_callable=trigger_k8s_cronjob,
        task_id='ggircs_read_only_user',
        op_args=['cas-ggircs-db-create-readonly-user', namespace],
        dag=dag)

def trigger_ciip_deploy_db_dag(dag):
    return TriggerDagRunOperator(
        task_id='trigger_ciip_deploy_db_dag',
        trigger_dag_id="ciip_deploy_db",
        dag=dag)

download_eccc_files >> should_extract_zips_op >> extract_zips_to_ggircs
extract_zips_to_ggircs >> load_ggircs(dag_incremental) >> ggircs_read_only_user(dag_incremental) >> trigger_ciip_deploy_db_dag(dag_incremental)
extract_zips_to_ggircs_full >> load_ggircs(dag_full) >> ggircs_read_only_user(dag_full) >> trigger_ciip_deploy_db_dag(dag_full)
