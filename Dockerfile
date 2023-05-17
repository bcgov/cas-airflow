FROM apache/airflow:2.5.3

COPY --chown=airflow:root ./dags /opt/airflow/dags
