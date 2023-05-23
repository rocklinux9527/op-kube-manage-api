from sql_app.kube_cnfig_db_play import query_kube_db_env_cluster_all
from kube.kube_pod import PodManager

class kubePodService():
    def kube_pod_restart(self, env, cluster, namespace, pod_name):
        if not (env and cluster and namespace and pod_name):
            return {"code": 50000, "message": "The cluster or environment does not exist", "status": True}
        cluster_info = query_kube_db_env_cluster_all(env, cluster)
        for client_path in cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                return {"code": 50000, "message": "获取集群 client path  failure, 请检查问题", "status": True}
            pod_instance = PodManager(client_path.get("client_key_path"), namespace)
            return pod_instance.restart_pod(pod_name)

    def create_pod(self, data):
        env = data.get("env")
        cluster = data.get("cluster")
        container_port = data.get("ports")
        container_image = data.get("image")
        pod_name = data.get("pod_name")
        namespace_name = data.get("namespace")
        cluster_info = query_kube_db_env_cluster_all(env, cluster)
        for client_path in cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                return {"code": 50000, "message": "获取集群 client path  failure, 请检查问题", "status": True}
            pod_instance = PodManager(client_path.get("client_key_path"), namespace_name)
            return pod_instance.create_pod(pod_name, container_image, container_port)

    def update(self, data):
        env = data.get("env")
        cluster = data.get("cluster")
        container_port = data.get("ports")
        container_image = data.get("image")
        pod_name = data.get("pod_name")
        namespace_name = data.get("namespace")
        cluster_info = query_kube_db_env_cluster_all(env, cluster)
        for client_path in cluster_info.get("data"):
            if not (client_path.get("client_key_path")):
                return {"code": 50000, "message": "获取集群 client path  failure, 请检查问题", "status": True}
            pod_instance = PodManager(client_path.get("client_key_path"), namespace_name)
            return pod_instance.update_pod(pod_name, container_image)
