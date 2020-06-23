FROM python:3.7-slim-buster

# Never prompt the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

COPY root /
COPY app /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN mkdir -p /airflow/xcom
RUN chmod g=u /etc/passwd && \
    /usr/libexec/fix-permissions /app
USER 1001
ENTRYPOINT ["python", "extract_zips.py"]
