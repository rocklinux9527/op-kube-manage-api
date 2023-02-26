"""
"""


class k8sPodManager:
    def __init__(self):
        self.namespace = namespace
        self.config_file = clint_config_file
        config.load_kube_config(config_file=self.client_config)
        self.core_api = client.CoreV1Api()

    def get_kube_pod(self):
        for po in core_api.list_namespaced_pod(namespace).items:
            name = po.metadata.name
            namespace = po.metadata.namespace
            labels = po.metadata.labels
            pod_ip = po.status.pod_ip

            containers = []  # [{},{},{}]
            status = "None"
            # 只为None说明Pod没有创建（不能调度或者正在下载镜像）
            if po.status.container_statuses is None:
                status = po.status.conditions[-1].reason
            else:
                for c in po.status.container_statuses:
                    c_name = c.name
                    c_image = c.image

                    # 获取重启次数
                    restart_count = c.restart_count

                    # 获取容器状态
                    c_status = "None"
                    if c.ready is True:
                        c_status = "Running"
                    elif c.ready is False:
                        if c.state.waiting is not None:
                            c_status = c.state.waiting.reason
                        elif c.state.terminated is not None:
                            c_status = c.state.terminated.reason
                        elif c.state.last_state.terminated is not None:
                            c_status = c.last_state.terminated.reason

                    c = {'c_name': c_name, 'c_image': c_image, 'restart_count': restart_count, 'c_status': c_status}
                    containers.append(c)

            create_time = k8s.timestamp_format(po.metadata.creation_timestamp)

            po = {"name": name, "namespace": namespace, "pod_ip": pod_ip,
                  "labels": labels, "containers": containers, "status": status,
                  "create_time": create_time}

    def delete_kube_pod(self, pod_name):
        core_api.delete_namespaced_pod(namespace=self.namespace, name=pod_name)

