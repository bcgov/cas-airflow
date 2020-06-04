from kubernetes import client, config
import datetime

def get_cronjob(cronjob_name, namespace):
  configuration = client.Configuration()
  api = client.BatchV1Api(client.ApiClient(configuration))
  # API client for cronjobs
  batch = client.BatchV1beta1Api(client.ApiClient(configuration))

  cronjobs = batch.list_namespaced_cron_job(namespace).items
  print('jobs')
  # print(cronjobs)
  for job in cronjobs:
    if job.metadata.name == cronjob_name:
      print(job.metadata.name)
      return job
  return False

def trigger_k8s_cronjob(cronjob_name, namespace):
  try:
      config.load_incluster_config()
  except:
      config.load_kube_config()

  configuration = client.Configuration()
  api = client.BatchV1Api(client.ApiClient(configuration))

  cronjob = get_cronjob(cronjob_name, namespace)

  if cronjob:
    date_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S.%f")
    cronjob.spec.job_template.metadata.name = str(cronjob.metadata.name + '-manual-' + date_str)[:50]

    return api.create_namespaced_job(namespace=namespace,body=cronjob.spec.job_template)

  else:
    print("job not found")
    return False
