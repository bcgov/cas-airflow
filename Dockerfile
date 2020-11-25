FROM gcr.io/ggl-cas-storage/cas-airflow-ocp4:v2-0-0b3-WIP

COPY --chown=airflow:root ./dags /opt/airflow/dags
