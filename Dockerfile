FROM apache/airflow:2.10.5

COPY --chown=airflow:root ./dags /opt/airflow/dags
