# This is a quickfix to enable an upstream image to function on OpenShift
# see https://docs.openshift.com/container-platform/3.11/creating_images/guidelines.html
# adapted from https://github.com/puckel/docker-airflow
# VERSION 1.10.10

FROM python:3.7-slim-buster

# Never prompt the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

# Airflow
ARG AIRFLOW_VERSION=1.10.10
ARG AIRFLOW_DEPS="gcp,kubernetes"
ARG PYTHON_DEPS=""
ENV AIRFLOW_HOME=/usr/local/airflow
ENV USER_ID=1001

# Define en_US.
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8
ENV LC_MESSAGES en_US.UTF-8

# Disable noisy "Handling signal" log messages:
# ENV GUNICORN_CMD_ARGS --log-level WARNING
RUN set -ex \
    && buildDeps=' \
        freetds-dev \
        libkrb5-dev \
        libsasl2-dev \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        git \
    ' \
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
        $buildDeps \
        freetds-bin \
        build-essential \
        default-libmysqlclient-dev \
        apt-utils \
        curl \
        rsync \
        netcat \
        locales \
    && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && pip install -U pip setuptools wheel \
    && pip install pytz \
    && pip install pyOpenSSL \
    && pip install ndg-httpsclient \
    && pip install pyasn1 \
    && apt-get install python-lxml -yqq \
    && pip install lxml \
    && pip install apache-airflow[crypto,password,celery,postgres,hive,jdbc,mysql,ssh${AIRFLOW_DEPS:+,}${AIRFLOW_DEPS}]==${AIRFLOW_VERSION} \
    && pip install 'redis==3.2' \
    && if [ -n "${PYTHON_DEPS}" ]; then pip install ${PYTHON_DEPS}; fi \
    && apt-get purge --auto-remove -yqq $buildDeps \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/man \
        /usr/share/doc \
        /usr/share/doc-base

# Override the airflow executable with the one in root/bin/airflow
# to ensure that the passwd entry gets added even when the k8s executor bypasses the image's entrypoint
RUN mv /usr/local/bin/airflow /usr/local/bin/airflow-upstream
COPY root /

RUN useradd -ms /bin/bash -d ${AIRFLOW_HOME} --uid ${USER_ID} airflow
RUN chown -R airflow: ${AIRFLOW_HOME}

RUN chmod g=u /etc/passwd && \
    /usr/libexec/fix-permissions ${AIRFLOW_HOME}

EXPOSE 8080 5555 8793

USER ${USER_ID}
WORKDIR ${AIRFLOW_HOME}
ENTRYPOINT ["/entrypoint.sh"]
