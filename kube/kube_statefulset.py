"""
"""
class k8sStatefulSetManager:
    def __init__(self, config_file):
        self.apps_api = client.AppsV1Api()
        self.client_config = config_file
        config.load_kube_config(config_file=self.client_config)

    def get_kube_stateful_set(self):
        for sts in self.apps_api.list_namespaced_stateful_set(namespace).items:
            name = sts.metadata.name
            namespace = sts.metadata.namespace
            labels = sts.metadata.labels
            selector = sts.spec.selector.match_labels
            replicas = sts.spec.replicas
            ready_replicas = ("0" if sts.status.ready_replicas is None else sts.status.ready_replicas)
            #current_replicas = sts.status.current_replicas
            service_name = sts.spec.service_name
            containers = {}
            for c in sts.spec.template.spec.containers:
                containers[c.name] = c.image
            create_time = k8s.timestamp_format(sts.metadata.creation_timestamp)

            ds = {"name": name, "namespace": namespace, "labels": labels, "replicas": replicas,
                  "ready_replicas": ready_replicas, "service_name": service_name,
                  "selector": selector, "containers": containers, "create_time": create_time}

    def delete_kube_stateful_set(self, stateful_name):
        self.apps_api.delete_namespaced_stateful_set(namespace=self.namespace, name=stateful_name)



