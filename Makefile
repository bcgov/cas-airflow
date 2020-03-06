install:
	oc -n wksv3k-tools rsync --exclude=.git ./ cas-airflow-web-56d58766d7-q4hqb:/usr/local/airflow/dags

lint:
	autopep8 --in-place --aggressive --aggressive *.py
