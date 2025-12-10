FROM apache/airflow:3.1.4

RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" apache-airflow-providers-standard

COPY --chown=airflow:root ./dags /opt/airflow/dags
