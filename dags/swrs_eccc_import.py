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
from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.python_operator import ShortCircuitOperator, PythonOperator
from airflow.contrib.kubernetes.secret import Secret
from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount
from airflow.hooks.base_hook import BaseHook
from trigger_k8s_job import trigger_k8s_job

import os
import json

YESTERDAY = datetime.now() - timedelta(days=1)

namespace = os.getenv('NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == False

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
SCHEDULE_INTERVAL = '0 0 * * *'

dag_incremental = DAG(DAG_ID + '_incremental', schedule_interval=SCHEDULE_INTERVAL, default_args=default_args)
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

extract_zips_volume_mount = VolumeMount('extract-zips-to-ggircs',
                                        mount_path='/app/tmp',
                                        sub_path=None,
                                        read_only=False)
extract_zips_volume = Volume(name='extract-zips-to-ggircs', configs={ 'persistentVolumeClaim': { 'claimName': 'extract-zips-to-ggircs-tmp' }})

def should_extract_zips(**context):
    download_return = context['task_instance'].xcom_pull(task_ids = 'download_eccc_files')
    return len(download_return['uploadedObjects']) > 0

ggircs_postgres_connection = BaseHook.get_connection('ggircs_postgres')

extract_zips_env = {
    'GCS_BUCKET': 'swrs-import',
    'TMP_ZIP_DESTINATION': '/app/tmp/eccc-zip.zip',
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
    volumes=[extract_zips_volume],
    volume_mounts=[extract_zips_volume_mount],
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    do_xcom_push=False,
    dag=dag_full)

extract_zips_env['DOWNLOAD_ECCC_FILES_XCOM']: '{{task_instance.xcom_pull(task_ids="download_eccc_files", key="return_value")}}'

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
    env_vars=extract_zips_env,
    volumes=[extract_zips_volume],
    volume_mounts=[extract_zips_volume_mount],
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    do_xcom_push=False,
    dag=dag_incremental)

def load_ggircs(dag):
    return KubernetesPodOperator(
        task_id='load_ggircs_swrs',
        name='load_ggircs_swrs',
        namespace=namespace,
        image='docker-registry.default.svc:5000/wksv3k-dev/cas-ggircs-etl:latest',
        env_vars={
            'PGHOST': ggircs_postgres_connection.host,
            'PGPORT': str(ggircs_postgres_connection.port) if ggircs_postgres_connection.port else None,
            'PGUSER': ggircs_postgres_connection.login,
            'PGPASSWORD': ggircs_postgres_connection.password,
            'PGDATABASE' : ggircs_postgres_connection.schema
        },
        cmds=["psql"],
        arguments=["-c", "select swrs_transform.load()"],
        resources=compute_resource,
        is_delete_operator_pod=True,
        get_logs=True,
        in_cluster=in_cluster,
        do_xcom_push=False,
        dag=dag)

def import_swrs_in_ciip(dag):
    return PythonOperator(
        python_callable=trigger_k8s_job,
        task_id='cas_ciip_swrs_import_job',
        op_args=['cas-ciip-swrs-import', namespace],
        dag=dag
    )

def load_ciip_facilities(dag):
    return PythonOperator(
        python_callable=trigger_k8s_job,
        task_id='load_ciip_facilities_job',
        op_args=['cas-ciip-portal-schema-deploy', namespace],
        dag=dag
    )

download_eccc_files >> should_extract_zips_op >> extract_zips_to_ggircs
extract_zips_to_ggircs >> load_ggircs(dag_incremental) >> import_swrs_in_ciip(dag_incremental) >> load_ciip_facilities(dag_incremental)
extract_zips_to_ggircs_full >> load_ggircs(dag_full) >> import_swrs_in_ciip(dag_full) >> load_ciip_facilities(dag_full)
