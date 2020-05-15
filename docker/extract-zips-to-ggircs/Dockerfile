FROM node:12

COPY root /
COPY app /app
WORKDIR /app
RUN npm install
RUN mkdir -p /airflow/xcom
RUN chmod g=u /etc/passwd && \
    /usr/libexec/fix-permissions /app
USER 1001
ENTRYPOINT ["node", "/app/index.js"]
