from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.python_operator import ShortCircuitOperator
from airflow.contrib.kubernetes.secret import Secret
from airflow.contrib.kubernetes.volume import Volume
from airflow.contrib.kubernetes.volume_mount import VolumeMount
from airflow.models import Variable
import os
import json

YESTERDAY = datetime.now() - timedelta(days=1)

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

dag = DAG(DAG_ID, schedule_interval=SCHEDULE_INTERVAL, default_args=default_args)
initial_zip_extract_dag = DAG(DAG_ID+'_init', schedule_interval=None, default_args=default_args)

compute_resource = {'request_cpu': '1', 'request_memory': '2Gi', 'limit_cpu': '2', 'limit_memory': '4Gi'}

env_vars = {
    'DEPTH': os.getenv('SWRS_DEPTH'),
    'WEBSITE': os.getenv('SWRS_WEBSITE'),
    'FILTER': os.getenv('SWRS_FILTER'),
    'USER': os.getenv('SWRS_USER'),
    'PASSWORD': os.getenv('SWRS_PASSWORD'),
    'MINIO_ACCESS_KEY': os.getenv('MINIO_ACCESS_KEY'),
    'MINIO_SECRET_KEY': os.getenv('MINIO_SECRET_KEY'),
    'MINIO_HOST': os.getenv('MINIO_HOST')
}

stream_minio_image = "docker.pkg.github.com/bcgov/cas-airflow-dags/stream-minio:" + os.getenv('STREAM_MINIO_IMAGE_TAG')
extract_zips_image = "docker.pkg.github.com/bcgov/cas-airflow-dags/extract-zips-to-ggircs:" + os.getenv('EXTRACT_ZIPS_IMAGE_TAG')

extract_zips_volume_mount = VolumeMount('extract-zips-to-ggircs',
                                        mount_path='/app/tmp',
                                        sub_path=None,
                                        read_only=False)
volume_config= {
    'persistentVolumeClaim':
      {
        'claimName': 'extract-zips-to-ggircs-tmp'
      }
    }
extract_zips_volume = Volume(name='extract-zips-to-ggircs', configs=volume_config)

namespace = os.getenv('NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == 'False'

def should_extract_zips(**context):
    download_return = context['task_instance'].xcom_pull(task_ids = 'download_eccc_files')
    return len(download_return['uploadedObjects']) > 0

extract_zips_env = {
    'GCS_BUCKET': 'swrs-import',
    'TMP_ZIP_DESTINATION': '/app/tmp/eccc-zip.zip',
    'PGHOST': 'cas-postgres-master',
    'ECCC_ZIP_PASSWORDS': os.getenv('ECCC_ZIP_PASSWORDS', '[]')
}

extract_zips_secrets=[
    Secret('env', 'PGDATABASE', 'cas-ggircs-postgres', 'database-name'),
    Secret('env', 'PGPASSWORD', 'cas-ggircs-postgres', 'database-password'),
    Secret('env', 'PGUSER', 'cas-ggircs-postgres', 'database-user'),
    Secret('env', 'GCS_KEY', 'cas-minio', 'gcs_key.json')
]

initial_zip_extract_dag = DAG(DAG_ID+'_init', schedule_interval=None, default_args=default_args)
initial_extract_zips_to_ggircs = KubernetesPodOperator(
    task_id='extract_zips_to_ggircs',
    name='extract_zips_to_ggircs',
    namespace=namespace,
    image=extract_zips_image,
    env_vars=extract_zips_env,
    secrets=extract_zips_secrets,
    volumes=[extract_zips_volume],
    volume_mounts=[extract_zips_volume_mount],
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    do_xcom_push=False,
    dag=initial_zip_extract_dag)

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
    dag=dag)

should_extract_zips_op = ShortCircuitOperator(
    task_id='should_extract_zips',
    provide_context=True,
    python_callable=should_extract_zips,
    dag=dag)

extract_zips_to_ggircs = KubernetesPodOperator(
    task_id='extract_zips_to_ggircs',
    name='extract_zips_to_ggircs',
    namespace=namespace,
    image=extract_zips_image,
    env_vars=extract_zips_env,
    secrets=extract_zips_secrets,
    volumes=[extract_zips_volume],
    volume_mounts=[extract_zips_volume_mount],
    resources=compute_resource,
    is_delete_operator_pod=True,
    get_logs=True,
    in_cluster=in_cluster,
    do_xcom_push=False,
    dag=dag)

should_extract_zips_op >> extract_zips_to_ggircs
download_eccc_files >> should_extract_zips_op

# load_ggircs_swrs = KubernetesPodOperator( # TODO
#     task_id='load_ggircs_swrs',
#     name='load_ggircs_swrs',
#     namespace=namespace,
#     image=image,
#     env_vars={
#         'DOWNLOAD_ECCC_FILES_XCOM': '{{ task_instance.xcom_pull(task_ids="download_eccc_files", key="return_value") }}'
#     },
#     resources=compute_resource,
#     is_delete_operator_pod=True,
#     get_logs=True,
#     in_cluster=in_cluster,
#     do_xcom_push=True,
#     dag=dag)

# load_portal_swrs = KubernetesPodOperator( # TODO
#     task_id='load_ggircs_swrs',
#     name='load_ggircs_swrs',
#     namespace=namespace,
#     image=image,
#     env_vars={
#         'DOWNLOAD_ECCC_FILES_XCOM': '{{ task_instance.xcom_pull(task_ids="download_eccc_files", key="return_value") }}'
#     },
#     resources=compute_resource,
#     is_delete_operator_pod=True,
#     get_logs=True,
#     in_cluster=in_cluster,
#     do_xcom_push=True,
#     dag=dag)

# update_portal_facilities_operators = KubernetesPodOperator( # TODO
#     task_id='load_ggircs_swrs',
#     name='load_ggircs_swrs',
#     namespace=namespace,
#     image=image,
#     env_vars={
#         'DOWNLOAD_ECCC_FILES_XCOM': '{{ task_instance.xcom_pull(task_ids="download_eccc_files", key="return_value") }}'
#     },
#     resources=compute_resource,
#     is_delete_operator_pod=True,
#     get_logs=True,
#     in_cluster=in_cluster,
#     do_xcom_push=True,
#     dag=dag)
