FROM apache/airflow:2.1.2

COPY --chown=airflow:root ./dags /opt/airflow/dags
