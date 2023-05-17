FROM apache/airflow:2.6.1

COPY --chown=airflow:root ./dags /opt/airflow/dags
