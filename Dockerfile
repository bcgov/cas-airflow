FROM apache/airflow:2.10.3

COPY --chown=airflow:root ./dags /opt/airflow/dags
