FROM gcr.io/ggl-cas-storage/cas-airflow-upstream:v2-0-0rc1

COPY --chown=airflow:root ./dags /opt/airflow/dags
