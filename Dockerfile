FROM apache/airflow:2.4.2

COPY --chown=airflow:root ./dags /opt/airflow/dags
