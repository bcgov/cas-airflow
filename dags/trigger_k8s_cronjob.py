from kubernetes import client, config
from kubernetes.client.rest import ApiException
import datetime
import time
import logging

# Retrieves a cron_job by name & namespace
def get_cronjob(cronjob_name, namespace):
    configuration = client.Configuration()
    # API client for cronjobs
    batch = client.BatchV1beta1Api(client.ApiClient(configuration))
    try:
        cronjobs = batch.list_namespaced_cron_job(namespace).items
        for job in cronjobs:
            # cronjob names must be unique
            if job.metadata.name == cronjob_name:
                return job
    except ApiException as e:
        logging.critical(
            "Exception when calling BatchV1Api->list_namespaced_cron_job: %s\n" % e)
    return False

# Creates a job from a cronjob job_template
def trigger_k8s_cronjob(cronjob_name, namespace):
    try:
        config.load_incluster_config()
    except:
        config.load_kube_config()

    configuration = client.Configuration()
    api = client.BatchV1Api(client.ApiClient(configuration))

    cronjob = get_cronjob(cronjob_name, namespace)

    if cronjob:
        date_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        # Change the name of the job to be created to show that it was manually created at time: date_str
        cronjob.spec.job_template.metadata.name = str(
            date_str + cronjob.metadata.name)[:63]

        # Create an OwnerReference object and add it to the metadata.owner_references list
        owner_reference = client.V1OwnerReference(
          api_version=cronjob.api_version or 'batch/v1beta1',
          controller=True,
          kind=cronjob.kind or 'CronJob',
          name=cronjob.metadata.name,
          uid=cronjob.metadata.uid
        )
        cronjob.spec.job_template.metadata.owner_references = [owner_reference]

        try:
            # Create a job from the job_template of the cronjob
            created_job = api.create_namespaced_job(
                namespace=namespace, body=cronjob.spec.job_template)
        except ApiException as e:
            logging.critical(
                "Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)

        # Get the uid from the newly created job
        controllerUid = created_job.metadata.uid

        core_v1 = client.CoreV1Api(client.ApiClient(configuration))

        # Create a label_selector from the job's UID
        pod_label_selector = "controller-uid=" + controllerUid
        try:
            # Wait a bit for the job to be created
            time.sleep(10)
            # Get the pod name for the newly created job
            pods_list = core_v1.list_namespaced_pod(
                namespace, label_selector=pod_label_selector, timeout_seconds=10)
            pod_name = pods_list.items[0].metadata.name
        except ApiException as e:
            logging.critical(
                "Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

        try:
            # Get the status of the newly created job
            status = core_v1.read_namespaced_pod_status(
                pod_name, namespace).status.phase
        except ApiException as e:
            logging.critical(
                "Exception when calling CoreV1Api->read_namespaced_pod_status: %s\n" % e)

        # Sleep while the pod has not completed, break on Failed or Succeeded status
        pending_statuses = ['Pending', 'Running', 'Unknown']
        while status in pending_statuses:
            try:
                status = core_v1.read_namespaced_pod_status(
                    pod_name, namespace).status.phase
                logging.critical('Current Status: ' + status)
                if status == 'Succeeded' or status == 'Failed':
                    break
                logging.critical('sleeping')
                time.sleep(5)
            except ApiException as e:
                logging.critical(
                    "Exception when calling CoreV1Api->read_namespaced_pod_status: %s\n" % e)

        try:
            # Retrieve and print the log from the finished pod
            pod_log = core_v1.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, pretty=True, timestamps=True)
            logging.critical(pod_log)
        except ApiException as e:
            logging.critical(
                "Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)
        logging.critical(status)
        # Return True if status='Succeeded', False if 'Failed'
        if status == 'Succeeded':
            return 'Job Succeeded'
        raise Exception('Job Failed')

    # get_cronjob() returned False
    else:
        raise Exception("Could not find cronjob")
