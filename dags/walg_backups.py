from airflow.operators.python_operator import PythonOperator
from exec_in_pod import exec_in_pod
import os

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
