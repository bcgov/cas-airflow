FROM node:12

COPY root /
COPY app /app
WORKDIR /app
RUN npm install
RUN mkdir -p /airflow/xcom
RUN chmod g=u /etc/passwd && \
    /usr/libexec/fix-permissions /app /airflow/xcom
USER 1001
