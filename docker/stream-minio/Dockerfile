FROM registry.access.redhat.com/ubi8/nodejs-12

ENV SUMMARY="An s2i builder image for streaming files to Minio" \
    DESCRIPTION="Airflow Executor"

LABEL summary="$SUMMARY" \
      description="$DESCRIPTION" \
      io.k8s.description="$DESCRIPTION" \
      io.k8s.display-name="Airflow Executor" \
      io.openshift.tags="s2i,minio,builder-image" \
      name="ubi8/stream-minio" \
      version="1" \
      maintainer="Junmin Ahn <junmin@button.is>"

RUN echo ${APP_ROOT}

COPY ./stream-minio.js ${APP_ROOT}/stream-minio.js
