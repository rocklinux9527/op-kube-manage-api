from tools.config import setup_logging
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
        self.apps_api = client.AppsV1Api()

    def restart_pod(self, pod_name, namespace):
        try:
            # 查询 Pod 状态
            pod_status = self.api.read_namespaced_pod_status(pod_name, namespace)

            # 判断 Pod 是否正在运行
            if pod_status.status.phase == "Running":
                # 获取 Pod 对象
                pod = self.api.read_namespaced_pod(pod_name, namespace)

                # 修改 Pod 的 metadata.annotations 字段，更新注释以触发 Pod 重启
                pod.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = str(datetime.datetime.now())
                self.api.patch_namespaced_pod(pod_name, namespace, pod)

                # 记录日志
                message = f"Pod {pod_name} in namespace {namespace} restarted successfully!"
                setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            else:
                # 记录日志
                message = f"Pod {pod_name} in namespace {namespace} is not running, cannot be restarted."
                setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

        except Exception as e:
            # 记录日志
            message = f"Failed to restart Pod {pod_name} in namespace {namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

    def update_pod(self, pod_name, namespace, container_name, image):
        try:
            # 获取 Pod 对象
            pod = self.api.read_namespaced_pod(pod_name, namespace)

            # 更新容器镜像
            for container in pod.spec.containers:
                if container.name == container_name:
                    container.image = image

            # 更新 Pod 对象
            self.api.patch_namespaced_pod(pod_name, namespace, pod)

            # 记录日志
            message = f"Container {container_name} in Pod {pod_name} of namespace {namespace} updated successfully to image {image}!"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
        except Exception as e:
            # 记录日志
            message = f"Failed to update container {container_name} in Pod {pod_name} of namespace {namespace} to image {image}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

    def delete_pod(self, pod_name, namespace):

        try:
            # 删除 Pod 对象
            self.api.delete_namespaced_pod(pod_name, namespace)
            # 记录日志
            message = f"Pod {pod_name} in namespace {namespace} deleted successfully!"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
        except Exception as e:
            # 记录日志
            message = f"Failed to delete Pod {pod_name} in namespace {namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)

    def get_pods(self, namespace):
        try:
            # 查询指定 Namespace 下的全部 Pod
            pods = self.api.list_namespaced_pod(namespace)

            # 构造结果字典
            result = {"code": 0, "total": len(pods.items), "data": [], "messages": "query data success", "status": True}

            # 遍历每一个 Pod 并提取所需信息
            for pod in pods.items:
                pod_name = pod.metadata.name
                pod_ip = pod.status.pod_ip
                pod_ready = f"{pod.status.ready}/{'1' if pod.status.phase == 'Running' else '0'}"
                pod_start_time = pod.status.start_time.replace(tzinfo=None).strftime('%Y-%m-%dT%H:%M:%S')
                pod_restart_count = str(pod.status.container_statuses[0].restart_count)
                pod_uptime = datetime.datetime.now() - pod.status.start_time.replace(tzinfo=None)
                pod_uptime_str = str(pod_uptime)[:-7] if str(pod_uptime)[:-7] != '0:00:00' else '<1m'
                pod_image = pod.spec.containers[0].image

                # 将提取的信息添加到结果字典中
                result["data"].append(
                    {"Pod name": pod_name, "Ip": pod_ip, "ready": pod_ready, "start_time": pod_start_time,
                     "restarts": pod_restart_count, "uptime_str": pod_uptime_str, "image": pod_image})

            return result
        except Exception as e:
            # 构造错误信息字典
            message = f"Failed to delete Pod {pod_name} in namespace {namespace}: {e}"
            setup_logging(log_file_path="fastapi.log", project_root=LOG_DIR, message=message)
            result = {"code": 1, "total": 0, "data": [], "messages": f"query data failed: {e}", "status": False}
            return result


pod_manager = PodManager()
# 重启 Pod
pod_manager.restart_pod("my-pod", "my-namespace")
# 更新 Pod
pod_manager.update_pod("my-pod", "my-namespace", "my-container", "my-image")
# 删除 Pod
pod_manager.delete_pod("my-pod", "my-namespace")

# namespace = "default"
# result = get_pods(namespace)
# print(result)