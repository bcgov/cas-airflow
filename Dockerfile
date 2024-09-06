FROM apache/airflow:2.10.1

COPY --chown=airflow:root ./dags /opt/airflow/dags
