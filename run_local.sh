#! /bin/bash
set -e

# airflow needs a home, this local directory is the default
# but you can lay foundation somewhere else if you prefer
# (optional)
export AIRFLOW_HOME=.
export DYNAMIC_DAGS_PATH=./dags/dynamic

AIRFLOW_VERSION=2.6.1
PYTHON_VERSION="$(python --version | cut -d " " -f 2 | cut -d "." -f 1-2)"
# For example: 3.6
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
# For example: https://raw.githubusercontent.com/apache/airflow/constraints-2.6.1/constraints-3.6.txt
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
pip install apache-airflow['cncf.kubernetes']

# initialize the database (can be skipped later on, needs to be run once)
airflow db init

# initialize the database (can be skipped later on, needs to be run once)
airflow users create \
    --username admin \
    --firstname Peter \
    --lastname Parker \
    --role Admin \
    --email spiderman@superhero.org

# start the web server, default port is 8080
# start the scheduler
#SIGINT (ctrl-c) will kill both subprocesses
(trap 'kill 0' SIGINT; airflow webserver --port 8080 & airflow scheduler)

# visit localhost:8080 in the browser and use the admin account you just
# created to login. Enable the example_bash_operator dag in the home page
