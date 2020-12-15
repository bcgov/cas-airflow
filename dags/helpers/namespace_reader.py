import os
from os import path

def get_namespace(app_name):
  namespace_path = f"cas-namespaces/{app_name}-namespace"
  namespace = ""
  # This requires that the secrets containing the namespaces are mounted to /opt/airflow/dags/cas-namespaces
  if not os.path.exists(namespace_path):
    print(f'{app_name} namespace secret needs to be mounted to ./cas-namespaces/{app_name}-namespace')
    exit(1)

  with open(namespace_path, 'r') as namespace_file:
    namespace = namespace_file.read()

  return namespace