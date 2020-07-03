# -*- coding: utf-8 -*-
"""
# DAGs to deploy the ciip portal.
ciip_deploy_db will initialize the portal database and import the swrs data
cron_acme_issue will issue a certificate for the CIIP portal
"""
from airflow import DAG
from datetime import datetime, timedelta
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.python_operator import PythonOperator
from dags.trigger_k8s_cronjob import trigger_k8s_cronjob

import os
import json

YESTERDAY = datetime.now() - timedelta(days=1)

namespace = os.getenv('NAMESPACE')

default_args = {
  'owner': 'airflow',
  'depends_on_past': False,
  'start_date': YESTERDAY,
  'email_on_failure': False,
  'email_on_retry': False,
  'retries': 1,
  'retry_delay': timedelta(minutes=5)
}

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = None

dag = DAG(DAG_ID, schedule_interval=SCHEDULE_INTERVAL, default_args=default_args)

ciip_portal_init_db = PythonOperator(
  python_callable=trigger_k8s_cronjob,
  task_id='ciip_portal_db_init',
  op_args=['cas-ciip-portal-init-db', namespace],
  dag=dag)

ciip_portal_swrs_import = PythonOperator(
  python_callable=trigger_k8s_cronjob,
  task_id='ciip_portal_swrs_import',
  op_args=['cas-ciip-portal-swrs-import', namespace],
  dag=dag)

ciip_portal_deploy_data = PythonOperator(
  python_callable=trigger_k8s_cronjob,
  task_id='ciip_portal_deploy_data',
  op_args=['cas-ciip-portal-schema-deploy-data', namespace],
  dag=dag)

ciip_portal_graphile_schema = PythonOperator(
  python_callable=trigger_k8s_cronjob,
  task_id='ciip_portal_graphile_schema',
  op_args=['cas-ciip-portal-init-graphile-schema', namespace],
  dag=dag)

ciip_portal_app_user = PythonOperator(
  python_callable=trigger_k8s_cronjob,
  task_id='ciip_portal_app_user',
  op_args=['cas-ciip-portal-app-user', namespace],
  dag=dag)

ciip_portal_init_db >> ciip_portal_swrs_import >> ciip_portal_deploy_data  >> ciip_portal_graphile_schema >> ciip_portal_app_user

acme_issue_dag = DAG('ciip_portal_acme_issue', schedule_interval=SCHEDULE_INTERVAL, default_args=default_args)

cron_acme_issue_task = PythonOperator(
  python_callable=trigger_k8s_cronjob,
  task_id='ciip_portal_acme_issue',
  op_args=['cas-ciip-portal-acme-issue', namespace],
  dag=acme_issue_dag)
