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

compute_resource = {'request_cpu': '800m', 'request_memory': '3Gi', 'limit_cpu': '800m', 'limit_memory': '3Gi'}

with dag:
    k = KubernetesPodOperator(
        task_id=DAG_ID,
        name=DAG_ID,
        namespace=namespace,
        image="docker.pkg.github.com/bcgov/cas-airflow-dags/stream-minio:lasted",
        cmds=["./init.sh"],
        arguments=[],
        env_vars={'MINIO_HOST': 'cas-minio-wksv3k-dev.pathfinder.gov.bc.ca'},
        resources=compute_resource,
        is_delete_operator_pod=True,
        get_logs=True,
        in_cluster=False,
        do_xcom_push=False)
