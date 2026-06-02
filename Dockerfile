FROM apache/airflow:3.2.2

COPY --chown=airflow:root ./dags /opt/airflow/dags
