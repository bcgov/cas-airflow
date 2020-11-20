# -*- coding: utf-8 -*-
"""
# DAGs to fetch and extract SWRS data from the ECCC website.
swrs_eccc_import_full will download and extract all zip files in the GCS bucket
swrs_eccc_import_incremental will only download and extract files that were uploaded in the first task of the DAG
"""
from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.python_operator import PythonOperator
from trigger_k8s_cronjob import trigger_k8s_cronjob

import os
import json
import sys

sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))

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
SCHEDULE_INTERVAL = None

dag = DAG(DAG_ID, schedule_interval=SCHEDULE_INTERVAL, default_args=default_args)

ggircs_db_init = PythonOperator(
        python_callable=trigger_k8s_cronjob,
        task_id='ggircs_db_init',
        op_args=['cas-ggircs-db-init', namespace],
        dag=dag)

ggircs_etl = PythonOperator(
        python_callable=trigger_k8s_cronjob,
        task_id='ggircs_etl',
        op_args=['cas-ggircs-etl-deploy', namespace],
        dag=dag)

ggircs_read_only_user = PythonOperator(
        python_callable=trigger_k8s_cronjob,
        task_id='ggircs_read_only_user',
        op_args=['cas-ggircs-db-create-readonly-user', namespace],
        dag=dag)


ggircs_db_init >> ggircs_etl >> ggircs_read_only_user
