from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from exec_in_pod import exec_in_pod
import os

START_DATE = datetime.now() - timedelta(days=2)

ciip_namespace = os.getenv('CIIP_NAMESPACE')
ggircs_namespace = os.getenv('GGIRCS_NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == 'False'

PATRONI_SELECTOR = 'spilo-role=master'

full_exec_command = [
    '/bin/sh',
    '-c',
    'PGPASSWORD=$PGPASSWORD_SUPERUSER envdir $WALE_ENV_DIR wal-g backup-push $PGDATA'
]


def create_backup_task(dag, namespace, deployment_name, task_id='make_postgres_backup'):
    return PythonOperator(
        python_callable=exec_in_pod,
        task_id=task_id,
        op_args=[deployment_name, namespace,
                 full_exec_command, PATRONI_SELECTOR],
        dag=dag
    )
