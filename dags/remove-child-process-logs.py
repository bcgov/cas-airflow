from datetime import datetime
from airflow import DAG
from airflow.operators.bash_operator import BashOperator


dag = DAG('remove_child_process_logs_dag', description='Delete log files',
          schedule_interval='0 0 * * *',
          start_date=datetime(2017, 3, 20), catchup=False)

run_remove_child_process_logs = BashOperator(
    task_id='delete_task',
    bash_command='rm -rf ./logs/scheduler',
    dag=dag)

