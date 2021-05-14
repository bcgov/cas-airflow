# -*- coding: utf-8 -*-
"""
# DAGs triggering cron jobs to setup the ggircs database
"""
import json
from dag_configuration import default_dag_args
from trigger_k8s_cronjob import trigger_k8s_cronjob
from airflow.operators.python_operator import PythonOperator
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from datetime import datetime, timedelta
from airflow import DAG
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


YESTERDAY = datetime.now() - timedelta(days=1)

ggircs_namespace = os.getenv('GGIRCS_NAMESPACE')
ciip_namespace = os.getenv('CIIP_NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == False

default_args = {
    **default_dag_args,
    'start_date': YESTERDAY
}

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = None

dag = DAG(DAG_ID, schedule_interval=SCHEDULE_INTERVAL,
          default_args=default_args)

ggircs_load_testing_data = PythonOperator(
    python_callable=trigger_k8s_cronjob,
    task_id='deploy-ggircs-load-testing-data',
    op_args=['cas-ggircs-deploy-load-testing-data', ggircs_namespace],
    dag=dag)

ciip_init_db = PythonOperator(
    python_callable=trigger_k8s_cronjob,
    task_id='ciip_portal_db_init',
    op_args=['cas-ciip-portal-init-db', ciip_namespace],
    dag=dag)

ciip_swrs_import = PythonOperator(
    python_callable=trigger_k8s_cronjob,
    task_id='ciip_swrs_import',
    op_args=['cas-ciip-portal-swrs-import', ciip_namespace],
    dag=dag)

ciip_load_testing_data = PythonOperator(
    python_callable=trigger_k8s_cronjob,
    task_id='ciip_deploy_load_testing_data',
    op_args=['cas-ciip-portal-load-testing-data', ciip_namespace],
    dag=dag)

ciip_graphile_schema = PythonOperator(
    python_callable=trigger_k8s_cronjob,
    task_id='ciip_portal_graphile_schema',
    op_args=['cas-ciip-portal-init-graphile-schema', ciip_namespace],
    dag=dag)


ciip_app_user = PythonOperator(
    python_callable=trigger_k8s_cronjob,
    task_id='ciip_portal_app_user',
    op_args=['cas-ciip-portal-app-user', ciip_namespace],
    dag=dag)


ggircs_load_testing_data >> ciip_init_db >> ciip_swrs_import >> ciip_load_testing_data >> ciip_graphile_schema >> ciip_app_user
