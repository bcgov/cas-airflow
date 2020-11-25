
# -*- coding: utf-8 -*-
"""
# DAG triggering the cas-ciip-portal-acme-renewal cron job
"""
import os
import sys
sys.path.insert(0,os.path.abspath(os.path.dirname(__file__)))

from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python_operator import PythonOperator
from trigger_k8s_cronjob import trigger_k8s_cronjob

START_DATE = datetime.now() - timedelta(days=2)

namespace = os.getenv('NAMESPACE')

default_args = {
  'owner': 'airflow',
  'depends_on_past': False,
  'email_on_failure': False,
  'email_on_retry': False,
  'start_date': START_DATE,
  'retries': 1,
  'retry_delay': timedelta(minutes=5),
}

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")
SCHEDULE_INTERVAL = '0 0 * * *'

dag = DAG(DAG_ID, schedule_interval=SCHEDULE_INTERVAL, default_args=default_args)

cert_renewal_task = PythonOperator(
  python_callable=trigger_k8s_cronjob,
  task_id='cert_renewal',
  op_args=['cas-ciip-portal-acme-renewal', namespace],
  dag=dag)
