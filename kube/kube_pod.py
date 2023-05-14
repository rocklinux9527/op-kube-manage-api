from tools.config import setup_logging, k8sPodHeader
from kubernetes import client, config
import datetime

import os

HERE = os.path.abspath(__file__)
HOME_DIR = os.path.split(os.path.split(HERE)[0])[0]
LOG_DIR = os.path.join(HOME_DIR, "logs")
import time


class PodManager:
    def __init__(self, client_config_file, namespace="default"):
        self.client_config = client_config_file
        self.namespace = namespace
        config.load_kube_config(config_file=self.client_config)
        self.apps_api = client.CoreV1Api()

    def create_pod(self, pod_name, container_image, container_port):

        container = client.V1Container(
            name=pod_name,
            image=container_image,
            ports=[client.V1ContainerPort(container_port=container_port)]
        )
        spec = client.V1PodSpec(
            containers=[container]
        )
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name),
            spec=spec
        )
        try:
            api_response = self.apps_api.create_namespaced_pod(self.namespace, pod)
            print(api_response)
            message = f"Pod {api_response.metadata.name} in namespace {self.namespace}  Pod created successfully"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 20000, "total": 1, "data": pod_name + "create success", "messages": "pod create  data success",
                      "status": True}
        except client.exceptions.ApiException as e:
            print("Error creating Pod:", e)
            message = f"Failed to delete Pod {pod_name} in namespace {self.namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 50000, "total": 1, "data": "", "messages": str(e), "status": True}
        return result

    def delete_pod(self, pod_name):
        try:
            # 删除 Pod 对象
            self.apps_api.delete_namespaced_pod(pod_name, self.namespace)
            # 记录日志
            message = f"Pod {pod_name} in namespace {self.namespace} deleted successfully!"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 20000, "total": 1, "data": pod_name + "create success", "messages": "pod delete  data success",
                      "status": True}
        except Exception as e:
            # 记录日志
            message = f"Failed to delete Pod {pod_name} in namespace {self.namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 50000, "total": 1, "data": "", "messages": str(e), "status": True}
            return result

    def restart_pod(self, pod_name):
        try:
            # 查询 Pod 状态
            pod_status = self.apps_api.read_namespaced_pod_status(pod_name, self.namespace)
            # 判断 Pod 是否正在运行
            if pod_status.status.phase == "Running":
                delete_status = self.delete_pod(pod_name)
                message = f"Pod {pod_name} in namespace {self.namespace} restarted successfully!"
                setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
                result = {"code": 20000, "total": 1, "data": pod_name + "restart success",
                          "messages": "pod restart  data success", "status": True}
            else:
                # 记录日志
                message = f"Pod {pod_name} in namespace {self.namespace} is not running, cannot be restarted."
                setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
                result = {"code": 20000, "total": 0, "data": "", "messages": "pod is not running, cannot be restarted",
                          "status": True}
            return result
        except Exception as e:
            # 记录日志
            message = f"Failed to restart Pod {pod_name} in namespace {self.namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 50000, "total": 0, "data": str(e), "messages": "pod restarted failure", "status": True}
            return result

    def update_pod(self, pod_name, image):
        try:
            # 获取 Pod 对象
            pod = self.apps_api.read_namespaced_pod(pod_name, self.namespace)
            container_name = pod_name
            # 更新容器镜像
            for container in pod.spec.containers:
                if container.name == container_name:
                    container.image = image

            # 更新 Pod 对象
            self.apps_api.patch_namespaced_pod(pod_name, self.namespace, pod)
            # 记录日志
            message = f"Container {container_name} in Pod {pod_name} of namespace {self.namespace} updated successfully to image {image}!"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 20000, "total": 0, "data": "", "messages": "update pod success", "status": True}
        except Exception as e:
            # 记录日志
            message = f"Failed to update container {container_name} in Pod {pod_name} of namespace {self.namespace} to image {image}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 50000, "total": 0, "data": str(e), "messages": "pod update failure", "status": True}
        return result

    def get_pods(self, env, cluster_name):
        try:
            # 查询指定 Namespace 下的全部 Pod
            pods = self.apps_api.list_namespaced_pod(self.namespace)
            # 构造结果字典
            result = {"code": 20000, "total": len(pods.items), "data": [], "messages": "query data success", "status": True,
                      "columns": k8sPodHeader}
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
                pod_status = "Running"  # 默认将Pod状态设置为"Running"
                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        if container_status.state and container_status.state.waiting:
                            # 如果容器处于等待状态，将Pod状态设置为容器的等待原因
                            pod_status = container_status.state.waiting.reason
                            break
                        elif container_status.state and container_status.state.terminated:
                            # 如果容器处于终止状态，将Pod状态设置为容器的终止原因
                            pod_status = container_status.state.terminated.reason
                            break
                        elif container_status.state and container_status.state.running:
                            # 如果有容器处于"Running"状态，继续检查其他容器
                            continue
                        else:
                            # 如果容器状态为空或未知状态，将Pod状态设置为未知
                            pod_status = "Unknown"
                            break

                qos_class = "低"
                if pod.status.qos_class == "BestEffort":
                    qos_class = "低"
                elif pod.status.qos_class == "Burstable":
                    qos_class = "中"
                elif pod.status.qos_class == "Guaranteed":
                    qos_class = "高"
                else:
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
                            failure_reasons.append(container_status.state.waiting.message)
                        elif container_status.state and container_status.state.terminated and container_status.state.terminated.reason:
                            failure_reasons.append(container_status.state.terminated.message)
                # ready_count
                ready_count = "0/1"
                if pod.status.container_statuses is not None:
                    for container_status in pod.status.container_statuses:
                        if container_status.ready:
                            ready_count = f"{int(ready_count.split('/')[0]) + 1}/{ready_count.split('/')[1]}"
                # 新版本方式 获取 READY 数 1/1 格式
                # ready_count = f"{pod.status.ready_replicas}/{pod.status.replicas}" if pod.status.ready_replicas and pod.status.replicas else "0/0"

                # 将提取的信息添加到结果字典中
                result["data"].append(
                    {"namespace": pod_namespace, "pod_name": pod_name, "host_ip": host_ip, "pod_ip": pod_ip,
                     "ports": ','.join(pod_ports), "qos": qos_class, "pod_status": pod_status, "ready_count": ready_count,
                     "pod_error_reasons": failure_reasons, "start_time": pod_start_time,
                     "restarts": pod_restart_count, "uptime_str": pod_uptime_str, "image": pod_image, "env": env,
                     "cluster": cluster_name})
            return result
        except Exception as e:
            message = f"Failed to delete Pod  in namespace {self.namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 50000, "total": 0, "data": [], "messages": f"query data failed: {e}", "status": False}
            return result
