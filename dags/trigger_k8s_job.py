from kubernetes import client, config, utils
import time

def has_job(job_name, namespace):
  configuration = client.Configuration()
  api = client.BatchV1Api(client.ApiClient(configuration))
  namespace_jobs = api.list_namespaced_job(namespace=namespace).items
  return any((job.metadata.name == job_name for job in namespace_jobs))

def trigger_k8s_job(job_name, namespace):
  try:
      config.load_incluster_config()
  except:
      config.load_kube_config()
  configuration = client.Configuration()
  api = client.BatchV1Api(client.ApiClient(configuration))

  if has_job(job_name, namespace):
    previous_job = api.read_namespaced_job(name=job_name, namespace=namespace)
    job = client.V1Job(
      api_version="batch/v1",
      kind="Job",
      metadata=client.V1ObjectMeta(name=job_name),
      spec=previous_job.spec)
    job.spec.selector = None
    job.spec.template.metadata.labels = None
    api.delete_namespaced_job(name=job_name,namespace=namespace)

    while has_job(job_name, namespace):
      time.sleep(5)

    return api.create_namespaced_job(namespace=namespace,body=job)
  else:
    print("job not found")
    return False
