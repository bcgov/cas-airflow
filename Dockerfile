FROM apache/airflow:3.1.1

# Install the standard providers for Airflow 2 -- can be removed when we upgrade to Airflow 3
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" apache-airflow-providers-standard

# --- Backport Patch, can be removed when we upgrade to Airflow 3.1.1 or later
# See https://github.com/apache/airflow/issues/56426
USER root
RUN apt update && apt install -y patch curl patchutils

RUN set -ex; \
    cd /home/airflow/.local/lib/python3.12/site-packages/airflow; \
    curl -L https://patch-diff.githubusercontent.com/raw/apache/airflow/pull/56431.patch \
    | filterdiff -p1 -i 'airflow-core/src/airflow/*' | patch -p4 -u --verbose
# --- End of backport patch

COPY --chown=airflow:root ./dags /opt/airflow/dags
