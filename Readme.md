Airflow DAGs
============

This is an experiment coupled with the [cas-helm](https://github.com/bcgov/cas-helm) deployment of Airflow.

Cloning
-------

```bash
mkdir -p ~/airflow
git clone https://github.com/bcgov/cas-airflow-dags.git ~/airflow/dags
cd ~/airflow/dags
```

Getting started
---------------

Use [asdf](https://asdf-vm.com/#/core-manage-asdf-vm) to install the correct version of python.

```bash
asdf install
```

Use [pip](https://pip.pypa.io/en/stable/user_guide/) to install the correct version of airflow.

```bash
pip install -r requirements.txt
```

Then reshim asdf to ensure the correct version of airflow is in your path.

```bash
asdf reshim
```

Set up airflow in a parent folder of this repo (`~/airflow`). Be sure to set `AIRFLOW_HOME` if you cloned do a different path.

```bash
airflow initdb
```

Start airflow locally (optional).

```bash
airflow webserver --daemon
airflow scheduler --daemon
```

Writing
-------

Run a specific task in a specific dag.

```
airflow test hello_world_dag hello_task $(date -u +"%Y-%m-%dT%H:%M:%SZ")
```
