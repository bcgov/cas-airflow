FROM apache/airflow:3.3.0

COPY --chown=airflow:root ./dags /opt/airflow/dags
