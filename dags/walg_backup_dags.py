# -*- coding: utf-8 -*-
"""
# DAG to make a full backup of a postgres database to a gcs bucket.
"""
from walg_backups import create_backup_task
from dag_configuration import default_dag_args
from datetime import datetime, timedelta
from airflow import DAG
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


START_DATE = datetime.now() - timedelta(days=2)

ciip_namespace = os.getenv('CIIP_NAMESPACE')
ggircs_namespace = os.getenv('GGIRCS_NAMESPACE')
in_cluster = os.getenv('LOCAL_AIRFLOW', False) == 'False'

default_args = {
    **default_dag_args,
    'start_date': START_DATE
}

DAG_ID = os.path.basename(__file__).replace(".pyc", "").replace(".py", "")

ciip_full_backup = DAG(DAG_ID + '_ciip_full', default_args=default_args,
                       schedule_interval='0 8 * * *', start_date=START_DATE)

ggircs_full_backup = DAG(DAG_ID + '_ggircs_full', default_args=default_args,
                         schedule_interval='0 8 * * *', start_date=START_DATE)

metabase_full_backup = DAG(DAG_ID + '_metabase_full', default_args=default_args,
                           schedule_interval='0 8 * * *', start_date=START_DATE)


create_backup_task(ciip_full_backup, ciip_namespace, 'cas-ciip-portal-patroni')

create_backup_task(ggircs_full_backup, ggircs_namespace, 'cas-ggircs-patroni')

create_backup_task(metabase_full_backup, ggircs_namespace,
                   'cas-metabase-patroni')
