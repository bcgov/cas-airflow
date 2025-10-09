FROM apache/airflow:3.1.0

# Install the standard providers for Airflow 2 -- can be removed when we upgrade to Airflow 3
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" apache-airflow-providers-standard

COPY --chown=airflow:root ./dags /opt/airflow/dags
