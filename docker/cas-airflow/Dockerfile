FROM apache/airflow:1.10.12

# Airflow
ENV AIRFLOW_HOME=/usr/local/airflow
ARG AIRFLOW_HOME=/usr/local/airflow
ARG AIRFLOW_VERSION="1.10.12"
ARG ADDITIONAL_PYTHON_DEPS="pytz, pyOpenSSL, ndg-httpsclient, pyasn1, lxml"
ARG ADDITIONAL_AIRFLOW_EXTRAS="crypto, password, hive, jdbc"
ARG ADDITIONAL_DEV_APT_DEPS="python-lxml"

# Define en_US.
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
ENV LC_MESSAGES en_US.UTF-8

# set locale
RUN set -ex \
    && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

EXPOSE 8080 5555 8793

WORKDIR ${AIRFLOW_HOME}
ENTRYPOINT ["/entrypoint.sh"]
