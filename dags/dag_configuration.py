from datetime import timedelta

default_dag_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['ggircs@gov.bc.ca', 'matthieu@button.is', 'dylan@button.is', 'pierre.bastianelli@gov.bc.ca'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
