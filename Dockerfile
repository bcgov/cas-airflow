FROM apache/airflow:2.9.3

COPY --chown=airflow:root ./dags /opt/airflow/dags
