FROM apache/airflow:2.1.0

COPY --chown=airflow:root ./dags /opt/airflow/dags
