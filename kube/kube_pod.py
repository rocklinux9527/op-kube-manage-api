from tools.config import setup_logging, k8sPodHeader
from kubernetes import client, config
import datetime


import os

HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")


class PodManager:
    def __init__(self, client_config_file, namespace="default"):
        self.client_config = client_config_file
        self.namespace = namespace
        config.load_kube_config(config_file=self.client_config)
        self.apps_api = client.CoreV1Api()

    def restart_pod(self, pod_name):
        try:
            # 查询 Pod 状态
            pod_status = self.api.read_namespaced_pod_status(pod_name, self.namespace)

            # 判断 Pod 是否正在运行
            if pod_status.status.phase == "Running":
                # 获取 Pod 对象
                pod = self.api.read_namespaced_pod(pod_name, namespace)

                # 修改 Pod 的 metadata.annotations 字段，更新注释以触发 Pod 重启
                pod.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = str(datetime.datetime.now())
                self.apps_api.patch_namespaced_pod(pod_name, namespace, pod)

                # 记录日志
                message = f"Pod {pod_name} in namespace {namespace} restarted successfully!"
                setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            else:
                # 记录日志
                message = f"Pod {pod_name} in namespace {namespace} is not running, cannot be restarted."
                setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

        except Exception as e:
            # 记录日志
            message = f"Failed to restart Pod {pod_name} in namespace {self.namespace }: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

    def update_pod(self, pod_name, container_name, image):
        try:
            # 获取 Pod 对象
            pod = self.apps_api.read_namespaced_pod(pod_name, self.namespace)

            # 更新容器镜像
            for container in pod.spec.containers:
                if container.name == container_name:
                    container.image = image

            # 更新 Pod 对象
            self.apps_api.patch_namespaced_pod(pod_name, self.namespace, pod)

            # 记录日志
            message = f"Container {container_name} in Pod {pod_name} of namespace {self.namespace} updated successfully to image {image}!"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
        except Exception as e:
            # 记录日志
            message = f"Failed to update container {container_name} in Pod {pod_name} of namespace {self.namespace} to image {image}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

    def delete_pod(self, pod_name):

        try:
            # 删除 Pod 对象
            self.apps_api.delete_namespaced_pod(pod_name, self.namespace)
            # 记录日志
            message = f"Pod {pod_name} in namespace {namespace} deleted successfully!"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
        except Exception as e:
            # 记录日志
            message = f"Failed to delete Pod {pod_name} in namespace {self.namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

    def get_pods(self):
        try:
            # 查询指定 Namespace 下的全部 Pod
            pods = self.apps_api.list_namespaced_pod(self.namespace)
            # 构造结果字典

            result = {"code": 20000, "total": len(pods.items), "data": [], "messages": "query data success", "status": True, "columns": k8sPodHeader}

            # 遍历每一个 Pod 并提取所需信息
            for pod in pods.items:
                pod_name = pod.metadata.name
                pod_namespace = pod.metadata.namespace
                host_ip = pod.status.host_ip
                pod_ip = pod.status.pod_ip
                # # 处理 Pod 的启动时间
                pod_start_time = ""
                if pod.status.start_time is not None:
                    pod_start_time = pod.status.start_time.replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M:%S')
                pod_status = pod.status.phase
                qos_class = pod.status.qos_class
                if pod.status.container_statuses and len(pod.status.container_statuses) > 0:
                    pod_restart_count = str(pod.status.container_statuses[0].restart_count)
                else:
                    pod_restart_count = "0"  # 或者根据实际需求设置一个默认值
                # # 处理 Pod 的运行时间
                pod_uptime_str = ""
                if pod.status.start_time is not None:
                    current_time = datetime.datetime.now()
                    start_time = pod.status.start_time.replace(tzinfo=None)
                    pod_uptime = current_time - start_time
                    pod_uptime_str = str(pod_uptime)[:-7] if str(pod_uptime)[:-7] != '0:00:00' else '<1m'
                pod_image = pod.spec.containers[0].image
                pod_ports = []
                if pod.spec.containers is not None:
                    for container in pod.spec.containers:
                        if container.ports is not None:
                            if isinstance(container.ports, list):  # 多个端口
                                for port in container.ports:
                                    pod_ports.append(str(port.container_port))
                            else:  # 单个端口
                                pod_ports.append(container.ports.container_port)


                # 获取异常状态的错误消息
                failure_reasons = []
                if pod_status != "Running" and pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        if container_status.state and container_status.state.waiting and container_status.state.waiting.reason:
                            failure_reasons.append(container_status.state.waiting.reason)
                # ready_count
                ready_count = "0/1"
                if pod.status.container_statuses is not None:
                    for container_status in pod.status.container_statuses:
                        if container_status.ready:
                            ready_count = f"{int(ready_count.split('/')[0]) + 1}/{ready_count.split('/')[1]}"
                # 新版本方式 获取 READY 数 1/1 格式
                #ready_count = f"{pod.status.ready_replicas}/{pod.status.replicas}" if pod.status.ready_replicas and pod.status.replicas else "0/0"

                # 将提取的信息添加到结果字典中
                result["data"].append(
                    {"namespace": pod_namespace, "pod_name": pod_name, "host_ip": host_ip, "pod_ip": pod_ip, "ports": ','.join(pod_ports), "qos": qos_class, "pod_status": pod_status, "ready_count": ready_count, "pod_error_reasons": failure_reasons, "start_time": pod_start_time,
                     "restarts": pod_restart_count, "uptime_str": pod_uptime_str, "image": pod_image})

            return result
        except Exception as e:
            # 构造错误信息字典
            message = f"Failed to delete Pod  in namespace {self.namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 50000, "total": 0, "data": [], "messages": f"query data failed: {e}", "status": False}
            return result

