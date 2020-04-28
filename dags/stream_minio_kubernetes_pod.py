from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow import configuration as conf
import os

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

namespace = conf.get('kubernetes', 'NAMESPACE')

env_vars = {
    'DEPTH': os.getenv('SWRS_DEPTH'),
    'WEBSITE': os.getenv('SWRS_WEBSITE'),
    'FILTER': os.getenv('SWRS_FILTER'),
    'MINIO_ACCESS_KEY': os.getenv('MINIO_ACCESS_KEY'),
    'MINIO_SECRET_KEY': os.getenv('MINIO_SECRET_KEY'),
    'MINIO_HOST': os.getenv('MINIO_HOST'),
}

image = "docker.pkg.github.com/bcgov/cas-airflow-dags/stream-minio:" + os.getenv('STREAM_MINIO_IMAGE_TAG')

with dag:
    k =KubernetesPodOperator(
        # The ID specified for the task.
        task_id='pod-ex-minimum',
        # Name of task you want to run, used to generate Pod ID.
        name='pod-ex-minimum',
        # Entrypoint of the container, if not specified the Docker container's
        # entrypoint is used. The cmds parameter is templated.
        cmds=['echo'],
        # The namespace to run within Kubernetes, default namespace is
        # `default`. There is the potential for the resource starvation of
        # Airflow workers and scheduler within the Cloud Composer environment,
        # the recommended solution is to increase the amount of nodes in order
        # to satisfy the computing requirements. Alternatively, launching pods
        # into a custom namespace will stop fighting over resources.
        namespace='wksv3k-tools',
        # Docker image specified. Defaults to hub.docker.com, but any fully
        # qualified URLs will point to a custom repository. Supports private
        # gcr.io images if the Composer Environment is under the same
        # project-id as the gcr.io images and the service account that Composer
        # uses has permission to access the Google Container Registry
        # (the default service account has permission)
        image='gcr.io/gcp-runtimes/ubuntu_18_0_4',
        in_cluster=True, # if set to true, will look in the cluster, if false, looks for file
        is_delete_operator_pod=True,
        get_logs=True))
