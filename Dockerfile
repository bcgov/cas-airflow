FROM apache/airflow:3.4.0

COPY --chown=airflow:root ./dags /opt/airflow/dags
