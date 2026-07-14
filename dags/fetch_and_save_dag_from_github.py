from airflow.sdk import dag, task
from dag_configuration import default_dag_args
from datetime import datetime, timedelta
import logging
import warnings

START_DATE = datetime.now() - timedelta(days=2)

# Update the UI documentation to prominently display the deprecation notice
DAG_DOC = """
# DEPRECATED

This Dag is **deprecated** and has been replaced by the built-in Airflow Git Dag Sync.
Please update to stop calling this DAG.

**Current Behavior:** This DAG will succeed without fetching or saving any files, to prevent upstream deployment failures.
"""

@dag(
    default_args=default_dag_args,
    schedule=None,
    start_date=START_DATE,
    doc_md=DAG_DOC,
)
def fetch_and_save_dag_from_github(
    org: str = "", repo: str = "", ref: str = "", path: str = ""
):

    @task()
    def log_deprecation_warning(org, repo, ref, path):
        message = (
            f"Dag 'fetch_and_save_dag_from_github' is DEPRECATED. "
            f"The request from repo '{org}/{repo}' (ref: {ref}, path: {path}) was safely skipped. "
        )

        warnings.warn(message, DeprecationWarning, stacklevel=2)

        logging.critical("!" * 80)
        logging.critical(message)
        logging.critical("!" * 80)

    log_deprecation_warning(org, repo, ref, path)


dag = fetch_and_save_dag_from_github()
