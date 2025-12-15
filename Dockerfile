FROM apache/airflow:3.1.2

RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" apache-airflow-providers-standard apache-airflow-providers-fab

COPY --chown=airflow:root ./dags /opt/airflow/dags
