# airflow DAG
from datetime import datetime
from airflow.decorators import dag, task
import os
import sys

# Maintain the path manipulation pattern you are testing
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Environment configuration check
BCIERS_NAMESPACE = os.getenv("BCIERS_NAMESPACE")

# Define which environments this Dag loads in to
CURRENT_ENV = os.environ.get("ENVIRONMENT", "dev")
ALLOWED_ENVIRONMENTS = ["dev", "test"]
FAKE_NOT_ALLOWED_ENV = "prod"

# Mock the default arguments to avoid importing 'dag_configuration'
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2026, 7, 1),
    'retries': 1,
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
}

@dag(
    dag_id="variable_load_dag_DEVELOP",
    schedule=None,
    default_args=default_args,
    is_paused_upon_creation=False,
    tags=['bciers'],
    doc_md="Dag to test if dags load or stay unloaded in the right or wrong namespaces."
)
def variable_load_dag_dev():

    @task
    def test_task():
        print(f"BCIERS_NAMESPACE: {BCIERS_NAMESPACE} with CURRENT_ENV: {CURRENT_ENV}")
        assert CURRENT_ENV in ALLOWED_ENVIRONMENTS, f"Current environment {CURRENT_ENV} is not allowed. Allowed environments are {ALLOWED_ENVIRONMENTS}."
        assert CURRENT_ENV != FAKE_NOT_ALLOWED_ENV, f"Current environment {CURRENT_ENV} is not allowed. Allowed environments are {ALLOWED_ENVIRONMENTS}."

    test_task()

@dag(
    dag_id="variable_load_dag_PROD",
    schedule=None,
    default_args=default_args,
    is_paused_upon_creation=False,
    tags=['bciers'],
    doc_md="Dag to test if dags load or stay unloaded in the right or wrong namespaces."
)
def variable_load_dag_prod():

    @task
    def test_task():
        print(f"BCIERS_NAMESPACE: {BCIERS_NAMESPACE} with CURRENT_ENV: {FAKE_NOT_ALLOWED_ENV}")

    test_task()


if CURRENT_ENV in ALLOWED_ENVIRONMENTS:
    variable_load_dag_dev()

if FAKE_NOT_ALLOWED_ENV in ALLOWED_ENVIRONMENTS:
    variable_load_dag_prod()
