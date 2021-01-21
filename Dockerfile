FROM apache/airflow:2.0.0

COPY --chown=airflow:root ./dags /opt/airflow/dags
