FROM apache/airflow:3.0.6

COPY --chown=airflow:root ./dags /opt/airflow/dags
